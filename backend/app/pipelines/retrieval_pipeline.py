"""
Retrieval Pipeline (LangGraph)
================================
Hybrid RAG pipeline: Neo4j graph search + Qdrant vector search
→ hybrid re-rank → LLM synthesis.

Upgrades vs v1:
  - Accepts conversation history (list of past turns) and passes to LLM
  - Cache-aware: caller is responsible for cache lookup/write (see chat router)
  - Dynamic prompt: uses CLINICAL_CHAT_SYSTEM_PROMPT (not template-only prompt)
  - State includes `history` field
"""
import asyncio
import time
import structlog
from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END

from app.services.groq_service import GroqService
from app.services.embedding_service import get_embedding_service
from app.services.neo4j_service import Neo4jService
from app.services.qdrant_service import QdrantService
from app.utils.hybrid_ranker import HybridRanker
from app.prompts.clinical_summary import CLINICAL_CHAT_SYSTEM_PROMPT, build_chat_prompt
from app.config import get_settings

logger = structlog.get_logger()


class RetrievalState(TypedDict):
    patient_id: str
    query: str
    consent_scope: str
    consent_filters: dict
    request_id: str
    history: List[dict]             # NEW: prior LLM turns for multi-turn context
    query_embedding: Optional[List[float]]
    graph_results: List[dict]
    vector_results: List[dict]
    ranked_results: List[dict]
    context_pack: Optional[str]
    citations: List[dict]
    llm_response: Optional[str]
    retrieval_start_ms: int
    retrieval_end_ms: int
    llm_start_ms: int
    llm_end_ms: int


class RetrievalPipeline:
    def __init__(self):
        self.groq = GroqService()
        self.embedding_svc = get_embedding_service()
        self.neo4j = Neo4jService()
        self.qdrant = QdrantService()
        self.ranker = HybridRanker()
        self.settings = get_settings()
        self.graph = self._build_graph()

    def _build_graph(self):
        g = StateGraph(RetrievalState)
        g.add_node("validate_scope", self._validate_scope)
        g.add_node("generate_query_embedding", self._generate_query_embedding)
        g.add_node("parallel_search", self._parallel_search)
        g.add_node("hybrid_rank", self._hybrid_rank)
        g.add_node("build_context", self._build_context)
        g.add_node("invoke_llm", self._invoke_llm)
        g.add_node("attach_citations", self._attach_citations)
        g.set_entry_point("validate_scope")
        g.add_edge("validate_scope", "generate_query_embedding")
        g.add_edge("generate_query_embedding", "parallel_search")
        g.add_edge("parallel_search", "hybrid_rank")
        g.add_edge("hybrid_rank", "build_context")
        g.add_edge("build_context", "invoke_llm")
        g.add_edge("invoke_llm", "attach_citations")
        g.add_edge("attach_citations", END)
        return g.compile()

    async def run(
        self,
        patient_id: str,
        query: str,
        consent_scope: str,
        consent_filters: dict,
        request_id: str,
        history: Optional[List[dict]] = None,
    ) -> dict:
        initial: RetrievalState = {
            "patient_id": patient_id,
            "query": query,
            "consent_scope": consent_scope,
            "consent_filters": consent_filters,
            "request_id": request_id,
            "history": history or [],
            "query_embedding": None,
            "graph_results": [],
            "vector_results": [],
            "ranked_results": [],
            "context_pack": None,
            "citations": [],
            "llm_response": None,
            "retrieval_start_ms": int(time.time() * 1000),
            "retrieval_end_ms": 0,
            "llm_start_ms": 0,
            "llm_end_ms": 0,
        }
        final = await self.graph.ainvoke(initial)
        return {
            "response": final["llm_response"] or "No data available for this query.",
            "citations": final["citations"],
            "graph_nodes_used": len(final["graph_results"]),
            "vector_entries_used": len(final["vector_results"]),
            "retrieval_time_ms": max(
                final["retrieval_end_ms"] - final["retrieval_start_ms"], 0
            ),
            "llm_time_ms": max(final["llm_end_ms"] - final["llm_start_ms"], 0),
        }

    async def _validate_scope(self, state: RetrievalState) -> dict:
        logger.info("retrieval_scope", scope=state["consent_scope"])
        return state

    async def _generate_query_embedding(self, state: RetrievalState) -> dict:
        embedding = await self.embedding_svc.embed(state["query"])
        return {**state, "query_embedding": embedding}

    async def _parallel_search(self, state: RetrievalState) -> dict:
        graph_task = self.neo4j.search(
            state["patient_id"],
            state["query"],
            state["consent_scope"],
            state["consent_filters"],
            self.settings.top_k,
        )
        vector_task = self.qdrant.search(
            state["patient_id"],
            state["query_embedding"],
            state["consent_scope"],
            state["consent_filters"],
            self.settings.top_k,
        )
        graph_results, vector_results = await asyncio.gather(graph_task, vector_task)
        return {
            **state,
            "graph_results": graph_results,
            "vector_results": vector_results,
            "retrieval_end_ms": int(time.time() * 1000),
        }

    async def _hybrid_rank(self, state: RetrievalState) -> dict:
        ranked = self.ranker.rank(
            state["graph_results"],
            state["vector_results"],
            self.settings.graph_weight,
            self.settings.vector_weight,
            self.settings.recency_weight,
        )
        return {**state, "ranked_results": ranked}

    async def _build_context(self, state: RetrievalState) -> dict:
        parts = []
        for i, r in enumerate(state["ranked_results"][:8]):
            parts.append(
                f"[Source {i+1} | {r['type']} | Score: {r['score']:.3f} | "
                f"Date: {r.get('date', 'unknown')}]\n{r['content']}"
            )
        context = "\n\n---\n\n".join(parts) if parts else "No relevant records found."
        return {
            **state,
            "context_pack": context,
            "llm_start_ms": int(time.time() * 1000),
        }

    async def _invoke_llm(self, state: RetrievalState) -> dict:
        result = await self.groq.invoke(
            system_prompt=CLINICAL_CHAT_SYSTEM_PROMPT,
            user_message=build_chat_prompt(
                state["query"],
                state["context_pack"] or "No context available.",
                state["patient_id"],
            ),
            temperature=0.3,        # Slightly above 0 for natural conversational tone
            history=state["history"],
        )
        return {
            **state,
            "llm_response": result["text"],
            "llm_end_ms": int(time.time() * 1000),
        }

    async def _attach_citations(self, state: RetrievalState) -> dict:
        """
        Only attach citations for sources the LLM actually referenced.
        If the response contains no [Source N] markers, the query was
        conversational and no citations are relevant.
        """
        import re
        response = state.get("llm_response") or ""

        # Extract which source numbers the LLM cited (e.g. [Source 1], [Source 3])
        cited_indices = set()
        for match in re.finditer(r'\[Source\s+(\d+)\]', response, re.IGNORECASE):
            cited_indices.add(int(match.group(1)) - 1)  # 0-indexed

        # If no citations referenced at all, return empty list (conversational query)
        if not cited_indices:
            return {**state, "citations": []}

        ranked = state["ranked_results"]
        citations = []
        for idx in sorted(cited_indices):
            if idx < len(ranked):
                r = ranked[idx]
                citations.append({
                    "source_type": r["type"],
                    "source_id": r["id"],
                    "relevance_score": r["score"],
                    "excerpt": (
                        r["content"][:200] + "..."
                        if len(r["content"]) > 200
                        else r["content"]
                    ),
                })
        return {**state, "citations": citations}

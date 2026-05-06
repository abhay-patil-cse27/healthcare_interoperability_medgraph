import math
from typing import List
from datetime import datetime, timezone


class HybridRanker:
    def rank(
        self,
        graph_results: List[dict],
        vector_results: List[dict],
        graph_weight: float = 0.5,
        vector_weight: float = 0.3,
        recency_weight: float = 0.2,
    ) -> List[dict]:
        if not graph_results and not vector_results:
            return []

        # Normalize scores within each source
        norm_graph = self._normalize_scores(graph_results)
        norm_vector = self._normalize_scores(vector_results)

        # Build merged dict keyed by content id
        merged: dict[str, dict] = {}

        for r in norm_graph:
            key = self._content_key(r)
            merged[key] = {**r, "graph_score": r["score"], "vector_score": 0.0}

        for r in norm_vector:
            key = self._content_key(r)
            if key in merged:
                merged[key]["vector_score"] = r["score"]
            else:
                merged[key] = {**r, "graph_score": 0.0, "vector_score": r["score"]}

        # Compute final hybrid score
        results = []
        for item in merged.values():
            recency = self._compute_recency_score(item.get("date", ""))
            final_score = (
                item["graph_score"] * graph_weight
                + item["vector_score"] * vector_weight
                + recency * recency_weight
            )
            results.append({**item, "score": round(final_score, 4)})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def _normalize_scores(self, results: List[dict]) -> List[dict]:
        if not results:
            return []
        scores = [r.get("score", 0.0) for r in results]
        min_s, max_s = min(scores), max(scores)
        if max_s == min_s:
            return [{**r, "score": 1.0} for r in results]
        return [
            {**r, "score": (r.get("score", 0.0) - min_s) / (max_s - min_s)}
            for r in results
        ]

    def _compute_recency_score(self, date_str: str) -> float:
        if not date_str:
            return 0.5
        try:
            # Handle both naive and timezone-aware ISO strings
            date_str_clean = date_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(date_str_clean)
            if dt.tzinfo is not None:
                now = datetime.now(timezone.utc)
            else:
                now = datetime.utcnow()
            days_old = max((now - dt).days, 0)
            return math.exp(-0.01 * days_old)
        except (ValueError, TypeError):
            return 0.5

    def _content_key(self, result: dict) -> str:
        return result.get("id", result.get("content", "")[:50])

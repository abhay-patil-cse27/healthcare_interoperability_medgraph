"""
Unit tests for HybridRanker.
Run: venv/Scripts/python.exe -m pytest tests/unit/test_hybrid_ranker.py -v
"""
import sys
import os
import math
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from app.utils.hybrid_ranker import HybridRanker


def make_graph(id_, score, date=None):
    return {"id": id_, "type": "graph_node", "content": f"content {id_}", "score": score, "date": date or ""}


def make_vector(id_, score, date=None):
    return {"id": id_, "type": "vector_entry", "content": f"content {id_}", "score": score, "date": date or ""}


class TestHybridRanker:
    def setup_method(self):
        self.ranker = HybridRanker()

    # ── Basic functionality ────────────────────────────────────────────────

    def test_empty_inputs(self):
        result = self.ranker.rank([], [])
        assert result == []

    def test_empty_graph_only_vector(self):
        result = self.ranker.rank([], [make_vector("a", 0.9)])
        assert len(result) == 1
        assert result[0]["id"] == "a"

    def test_empty_vector_only_graph(self):
        result = self.ranker.rank([make_graph("a", 0.9)], [])
        assert len(result) == 1
        assert result[0]["id"] == "a"

    def test_sorted_descending(self):
        graph = [make_graph("a", 0.9), make_graph("b", 0.1)]
        vector = [make_vector("c", 0.5)]
        result = self.ranker.rank(graph, vector)
        scores = [r["score"] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_rank_basic_returns_all_items(self):
        graph = [make_graph("a", 1.0), make_graph("b", 0.5)]
        vector = [make_vector("c", 0.8), make_vector("d", 0.3)]
        result = self.ranker.rank(graph, vector)
        assert len(result) == 4
        ids = {r["id"] for r in result}
        assert ids == {"a", "b", "c", "d"}

    # ── Deduplication ─────────────────────────────────────────────────────

    def test_deduplication_same_id(self):
        """Same ID in both graph and vector → one merged result."""
        graph = [make_graph("shared", 1.0)]
        vector = [make_vector("shared", 0.8)]
        result = self.ranker.rank(graph, vector)
        assert len(result) == 1
        assert result[0]["id"] == "shared"

    def test_deduplication_merged_score_higher(self):
        """Merged result should have higher score than either source alone."""
        graph_only = self.ranker.rank([make_graph("x", 1.0)], [])
        merged = self.ranker.rank([make_graph("x", 1.0)], [make_vector("x", 1.0)])
        assert merged[0]["score"] >= graph_only[0]["score"]

    # ── Recency scoring ───────────────────────────────────────────────────

    def test_recency_today(self):
        today = datetime.utcnow().isoformat()
        score = self.ranker._compute_recency_score(today)
        assert score > 0.99

    def test_recency_old_date(self):
        old = "2020-01-01T00:00:00"
        score = self.ranker._compute_recency_score(old)
        assert score < 0.1

    def test_recency_unknown_date(self):
        score = self.ranker._compute_recency_score("")
        assert score == 0.5

    def test_recency_invalid_date(self):
        score = self.ranker._compute_recency_score("not-a-date")
        assert score == 0.5

    def test_recency_timezone_aware(self):
        aware = "2026-05-04T00:00:00+00:00"
        score = self.ranker._compute_recency_score(aware)
        assert 0.0 < score <= 1.0

    def test_recency_recent_beats_old(self):
        recent = datetime.utcnow().isoformat()
        old = (datetime.utcnow() - timedelta(days=365)).isoformat()
        assert self.ranker._compute_recency_score(recent) > self.ranker._compute_recency_score(old)

    # ── Weight application ────────────────────────────────────────────────

    def test_graph_weight_dominates(self):
        """With graph_weight=1.0, graph-only items should rank highest."""
        graph = [make_graph("g", 1.0)]
        vector = [make_vector("v", 1.0)]
        result = self.ranker.rank(graph, vector, graph_weight=1.0, vector_weight=0.0, recency_weight=0.0)
        assert result[0]["id"] == "g"

    def test_vector_weight_dominates(self):
        """With vector_weight=1.0, vector-only items should rank highest."""
        graph = [make_graph("g", 0.1)]
        vector = [make_vector("v", 1.0)]
        result = self.ranker.rank(graph, vector, graph_weight=0.0, vector_weight=1.0, recency_weight=0.0)
        assert result[0]["id"] == "v"

    def test_scores_between_zero_and_one(self):
        graph = [make_graph("a", 0.9), make_graph("b", 0.3)]
        vector = [make_vector("c", 0.7)]
        result = self.ranker.rank(graph, vector)
        for r in result:
            assert 0.0 <= r["score"] <= 1.0 + 1e-9  # small float tolerance

    # ── Normalization ─────────────────────────────────────────────────────

    def test_single_item_normalizes_to_one(self):
        """Single item in a source normalizes to score=1.0 for that source."""
        result = self.ranker.rank([make_graph("a", 0.42)], [], graph_weight=1.0, vector_weight=0.0, recency_weight=0.0)
        assert abs(result[0]["score"] - 1.0) < 1e-6

    def test_all_same_scores_normalize(self):
        """All same scores → all normalize to 1.0."""
        graph = [make_graph("a", 0.5), make_graph("b", 0.5), make_graph("c", 0.5)]
        result = self.ranker.rank(graph, [], graph_weight=1.0, vector_weight=0.0, recency_weight=0.0)
        for r in result:
            assert abs(r["score"] - 1.0) < 1e-6

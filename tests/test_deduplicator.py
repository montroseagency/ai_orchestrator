"""Tests for semantic deduplication."""

import pytest
from unittest.mock import MagicMock, patch
from src.rag.deduplicator import SemanticDeduplicator, DedupeResult


class FakeEmbedding:
    """Fake embedding function that returns deterministic vectors."""

    def __init__(self):
        self._counter = 0
        self._cache = {}

    def __call__(self, input: list[str]) -> list[list[float]]:
        results = []
        for text in input:
            if text not in self._cache:
                # Generate a simple embedding based on text hash
                # Identical texts get identical embeddings
                vec = [0.0] * 10
                for i, char in enumerate(text[:10]):
                    vec[i] = ord(char) / 255.0
                self._cache[text] = vec
            results.append(self._cache[text])
        return results


@pytest.fixture
def deduplicator():
    return SemanticDeduplicator(
        similarity_threshold=0.80,
        embed_fn=FakeEmbedding(),
    )


class TestDedupeResult:
    def test_empty_result(self):
        result = DedupeResult()
        assert result.kept == []
        assert result.removed == []
        assert result.similarity_scores == []


class TestDeduplication:
    def test_empty_list(self, deduplicator):
        result = deduplicator.dedupe_lessons([])
        assert result.kept == []
        assert result.removed == []

    def test_single_item_kept(self, deduplicator):
        items = [{"fix": "Use proper error handling"}]
        result = deduplicator.dedupe_lessons(items)
        assert len(result.kept) == 1
        assert len(result.removed) == 0

    def test_identical_items_deduped(self, deduplicator):
        items = [
            {"fix": "Use proper error handling"},
            {"fix": "Use proper error handling"},
        ]
        result = deduplicator.dedupe_lessons(items)
        assert len(result.kept) == 1
        assert len(result.removed) == 1

    def test_different_items_both_kept(self, deduplicator):
        items = [
            {"fix": "Use proper error handling with try-catch"},
            {"fix": "Zzzzz completely different topic about routing"},
        ]
        result = deduplicator.dedupe_lessons(items)
        assert len(result.kept) == 2
        assert len(result.removed) == 0

    def test_sessions_dedupe(self, deduplicator):
        sessions = [
            {"summary": "Added dark mode toggle"},
            {"summary": "Added dark mode toggle"},
            {"summary": "Fixed authentication bug on login page"},
        ]
        result = deduplicator.dedupe_sessions(sessions)
        assert len(result.kept) >= 2


class TestCosineSimliarity:
    def test_identical_vectors(self, deduplicator):
        vec = [1.0, 2.0, 3.0]
        sim = deduplicator._cosine_similarity(vec, vec)
        assert abs(sim - 1.0) < 0.01

    def test_orthogonal_vectors(self, deduplicator):
        vec_a = [1.0, 0.0]
        vec_b = [0.0, 1.0]
        sim = deduplicator._cosine_similarity(vec_a, vec_b)
        assert abs(sim) < 0.01

    def test_zero_vector(self, deduplicator):
        vec_a = [0.0, 0.0]
        vec_b = [1.0, 1.0]
        assert deduplicator._cosine_similarity(vec_a, vec_b) == 0.0


class TestFindDuplicates:
    def test_no_duplicates(self, deduplicator):
        items = [
            {"text": "AAAA completely unique text"},
            {"text": "ZZZZ entirely different content"},
        ]
        dupes = deduplicator.find_duplicates(items)
        assert len(dupes) == 0

    def test_finds_exact_duplicates(self, deduplicator):
        items = [
            {"text": "Exact same content"},
            {"text": "Exact same content"},
        ]
        dupes = deduplicator.find_duplicates(items)
        assert len(dupes) == 1
        assert dupes[0][2] >= 0.99  # High similarity


class TestClearCache:
    def test_clear_cache(self, deduplicator):
        deduplicator._embedding_cache["test"] = [1.0, 2.0]
        deduplicator.clear_cache()
        assert len(deduplicator._embedding_cache) == 0

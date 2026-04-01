"""
Semantic Deduplicator — Remove semantically duplicate content using embeddings.

Uses cosine similarity to identify and remove duplicate lessons or sessions
that convey the same information, reducing noise in RAG results.
"""

import math
from dataclasses import dataclass, field
from typing import Optional, Any

from .server import EmbeddingFunction


@dataclass
class DedupeResult:
    """Result of a deduplication operation."""
    kept: list[dict] = field(default_factory=list)
    removed: list[dict] = field(default_factory=list)
    similarity_scores: list[tuple[int, int, float]] = field(default_factory=list)


class SemanticDeduplicator:
    """
    Removes semantically duplicate items using embedding similarity.

    Uses greedy deduplication: first item is always kept, subsequent items
    are only kept if they're sufficiently different from all kept items.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.80,
        embed_fn: Optional[EmbeddingFunction] = None,
    ):
        """
        Initialize the deduplicator.

        Args:
            similarity_threshold: Cosine similarity above which items are
                                considered duplicates (default 0.80 = 80%)
            embed_fn: Embedding function to use (creates new one if not provided)
        """
        self.similarity_threshold = similarity_threshold
        self.embed_fn = embed_fn or EmbeddingFunction()
        self._embedding_cache: dict[str, list[float]] = {}

    def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text, using cache for efficiency."""
        if text not in self._embedding_cache:
            embeddings = self.embed_fn([text])
            self._embedding_cache[text] = embeddings[0]
        return self._embedding_cache[text]

    def _get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for multiple texts, using cache when possible."""
        # Separate cached and uncached
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            if text not in self._embedding_cache:
                uncached_indices.append(i)
                uncached_texts.append(text)

        # Batch embed uncached texts
        if uncached_texts:
            new_embeddings = self.embed_fn(uncached_texts)
            for idx, text, embedding in zip(uncached_indices, uncached_texts, new_embeddings):
                self._embedding_cache[text] = embedding

        # Return all embeddings in order
        return [self._embedding_cache[text] for text in texts]

    def _cosine_similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Returns value in range [-1, 1] where 1 = identical, 0 = orthogonal.
        """
        if len(vec_a) != len(vec_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        magnitude_a = math.sqrt(sum(a * a for a in vec_a))
        magnitude_b = math.sqrt(sum(b * b for b in vec_b))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    def _extract_text(self, item: dict, text_key: str) -> str:
        """Extract text from an item for embedding."""
        if text_key in item:
            return str(item[text_key])

        # Try common keys
        for key in ["text", "content", "fix", "summary", "prompt", "description"]:
            if key in item:
                return str(item[key])

        # Fallback: concatenate all string values
        texts = [str(v) for v in item.values() if isinstance(v, str)]
        return " ".join(texts)

    def dedupe_lessons(
        self,
        lessons: list[dict],
        text_key: str = "fix",
    ) -> DedupeResult:
        """
        Deduplicate lessons based on semantic similarity.

        Args:
            lessons: List of lesson dicts to deduplicate
            text_key: Key to extract text for comparison (default "fix")

        Returns:
            DedupeResult with kept/removed lists and similarity scores
        """
        return self._dedupe_items(lessons, text_key)

    def dedupe_sessions(
        self,
        sessions: list[dict],
        text_key: str = "summary",
    ) -> DedupeResult:
        """
        Deduplicate sessions based on semantic similarity.

        Args:
            sessions: List of session dicts to deduplicate
            text_key: Key to extract text for comparison (default "summary")

        Returns:
            DedupeResult with kept/removed lists and similarity scores
        """
        return self._dedupe_items(sessions, text_key)

    def _dedupe_items(
        self,
        items: list[dict],
        text_key: str,
    ) -> DedupeResult:
        """
        Core deduplication logic using greedy selection.

        Algorithm:
        1. First item is always kept
        2. For each subsequent item, compare to all kept items
        3. If similarity to ANY kept item exceeds threshold, remove it
        4. Otherwise, keep it
        """
        result = DedupeResult()

        if not items:
            return result

        # Extract texts and get embeddings in batch
        texts = [self._extract_text(item, text_key) for item in items]
        embeddings = self._get_embeddings_batch(texts)

        # Track indices of kept items
        kept_indices: list[int] = []

        for i, (item, embedding) in enumerate(zip(items, embeddings)):
            is_duplicate = False
            max_similarity = 0.0
            most_similar_idx = -1

            # Compare to all kept items
            for kept_idx in kept_indices:
                similarity = self._cosine_similarity(embedding, embeddings[kept_idx])

                if similarity > max_similarity:
                    max_similarity = similarity
                    most_similar_idx = kept_idx

                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    break

            if is_duplicate:
                result.removed.append(item)
                result.similarity_scores.append((i, most_similar_idx, max_similarity))
            else:
                result.kept.append(item)
                kept_indices.append(i)

        return result

    def find_duplicates(
        self,
        items: list[dict],
        text_key: str = "text",
    ) -> list[tuple[int, int, float]]:
        """
        Find all pairs of items that are semantic duplicates.

        Args:
            items: List of items to check
            text_key: Key to extract text for comparison

        Returns:
            List of (idx_a, idx_b, similarity) tuples for duplicate pairs
        """
        duplicates = []

        if len(items) < 2:
            return duplicates

        # Get all embeddings
        texts = [self._extract_text(item, text_key) for item in items]
        embeddings = self._get_embeddings_batch(texts)

        # Compare all pairs
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                similarity = self._cosine_similarity(embeddings[i], embeddings[j])
                if similarity >= self.similarity_threshold:
                    duplicates.append((i, j, similarity))

        return duplicates

    def merge_similar(
        self,
        items: list[dict],
        text_key: str = "text",
        merge_fn: Optional[callable] = None,
    ) -> list[dict]:
        """
        Merge semantically similar items instead of removing duplicates.

        Args:
            items: List of items to merge
            text_key: Key for text comparison
            merge_fn: Function to merge two items (default: keep first, add count)

        Returns:
            List of merged items
        """
        if merge_fn is None:
            def merge_fn(a: dict, b: dict) -> dict:
                merged = dict(a)
                merged["merged_count"] = merged.get("merged_count", 1) + 1
                return merged

        result = self._dedupe_items(items, text_key)

        # Group removed items with their corresponding kept items
        merged_results = list(result.kept)

        for i, removed in enumerate(result.removed):
            # Find which kept item this was most similar to
            removed_idx, kept_idx, _ = result.similarity_scores[i]
            # Find the kept item in our results
            for j, kept in enumerate(merged_results):
                if kept == result.kept[kept_idx] if kept_idx < len(result.kept) else False:
                    merged_results[j] = merge_fn(merged_results[j], removed)
                    break

        return merged_results

    def clear_cache(self):
        """Clear the embedding cache."""
        self._embedding_cache.clear()


# Singleton instance
_deduplicator_instance: Optional[SemanticDeduplicator] = None


def get_deduplicator(threshold: float = 0.80) -> SemanticDeduplicator:
    """Get or create singleton SemanticDeduplicator instance."""
    global _deduplicator_instance
    if _deduplicator_instance is None:
        try:
            from src.config import Config
            threshold = getattr(Config, "SIMILARITY_DEDUPE_THRESHOLD", threshold)
        except ImportError:
            pass
        _deduplicator_instance = SemanticDeduplicator(similarity_threshold=threshold)
    return _deduplicator_instance

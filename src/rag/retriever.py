"""
Progressive Retriever — Hierarchical retrieval with 3 detail levels for token efficiency.

Instead of always fetching full session data, retrieves at the appropriate
detail level based on agent needs:
- Level 1 (METADATA): session_id, outcome, top 3 issues (~10 tokens)
- Level 2 (SUMMARY): + pre-indexed summary, files (~80 tokens)
- Level 3 (FULL): + full plan.md, review.md (~500 tokens)

Uses hybrid BM25 + dense retrieval with Reciprocal Rank Fusion (RRF) for
improved recall on both keyword-sensitive and semantic queries.
"""

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Any

from .server import get_rag_client, RagServer
from .budget import BudgetEnforcer, get_budget_enforcer
from .deduplicator import SemanticDeduplicator, get_deduplicator


# ─────────────────────────────────────────────────────────────────────────────
# Lightweight BM25 + RRF (no external deps)
# ─────────────────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    """Lowercase, split on non-alphanumeric, filter empties."""
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]


def _bm25_scores(query: str, docs: list[str], k1: float = 1.5, b: float = 0.75) -> list[float]:
    """
    Compute BM25 scores for query against a list of document strings.
    Returns a list of floats in the same order as docs.
    """
    if not docs:
        return []

    tokenized_docs = [_tokenize(d) for d in docs]
    query_terms = _tokenize(query)
    if not query_terms:
        return [0.0] * len(docs)

    N = len(docs)
    avgdl = sum(len(d) for d in tokenized_docs) / N if N else 1

    # Document frequency for IDF
    df: Counter = Counter()
    for doc_tokens in tokenized_docs:
        for term in set(doc_tokens):
            df[term] += 1

    scores = []
    for doc_tokens in tokenized_docs:
        doc_len = len(doc_tokens)
        tf_map = Counter(doc_tokens)
        score = 0.0
        for term in query_terms:
            if term not in tf_map:
                continue
            tf = tf_map[term]
            idf = math.log((N - df[term] + 0.5) / (df[term] + 0.5) + 1)
            tf_norm = tf * (k1 + 1) / (tf + k1 * (1 - b + b * doc_len / avgdl))
            score += idf * tf_norm
        scores.append(score)

    return scores


def _rrf_fuse(rankings: list[list[int]], k: int = 60) -> list[float]:
    """
    Reciprocal Rank Fusion over multiple ranked index lists.

    Args:
        rankings: Each inner list is a permutation of doc indices sorted best→worst.
        k: RRF constant (default 60, per original paper).

    Returns:
        List of RRF scores indexed by doc position (higher = better).
    """
    if not rankings:
        return []
    n_docs = max(max(r) for r in rankings) + 1
    rrf: list[float] = [0.0] * n_docs
    for ranking in rankings:
        for rank, doc_idx in enumerate(ranking):
            rrf[doc_idx] += 1.0 / (k + rank + 1)
    return rrf


class DetailLevel(Enum):
    """Detail levels for progressive retrieval."""
    METADATA = 1  # ~10 tokens: session_id, outcome, top 3 issues
    SUMMARY = 2   # ~80 tokens: + pre-indexed summary, files
    FULL = 3      # ~500 tokens: + full plan.md, review.md


# Default detail levels per agent type
AGENT_DETAIL_LEVELS: dict[str, DetailLevel] = {
    "conductor": DetailLevel.METADATA,
    "planner": DetailLevel.SUMMARY,
    "creative_brain": DetailLevel.SUMMARY,
    "implementer": DetailLevel.SUMMARY,
    "reviewer": DetailLevel.METADATA,
}


@dataclass
class RetrievedSession:
    """A retrieved session at a specific detail level."""
    session_id: str
    relevance: float
    outcome: str
    detail_level: DetailLevel

    # Level 1: METADATA
    issues: list[str] = field(default_factory=list)

    # Level 2: SUMMARY
    summary: str = ""
    files: list[str] = field(default_factory=list)
    prompt: str = ""

    # Level 3: FULL
    full_plan: Optional[str] = None
    full_review: Optional[str] = None


@dataclass
class RetrievedContext:
    """Context retrieved for an agent."""
    agent_type: str
    query: str
    sessions: list[RetrievedSession] = field(default_factory=list)
    lessons: list[dict] = field(default_factory=list)
    total_tokens_estimate: int = 0


class ProgressiveRetriever:
    """
    Hierarchical retrieval system with token-aware fetching.

    Retrieves at the minimum detail level needed for each agent,
    with optional upgrade to higher detail levels on demand.
    """

    def __init__(
        self,
        rag: Optional[RagServer] = None,
        budget_enforcer: Optional[BudgetEnforcer] = None,
        deduplicator: Optional[SemanticDeduplicator] = None,
    ):
        """
        Initialize the retriever.

        Args:
            rag: RagServer instance (uses singleton if not provided)
            budget_enforcer: BudgetEnforcer instance
            deduplicator: SemanticDeduplicator instance
        """
        self._rag = rag
        self._budget_enforcer = budget_enforcer
        self._deduplicator = deduplicator

    @property
    def rag(self) -> RagServer:
        """Lazy-load RAG client."""
        if self._rag is None:
            self._rag = get_rag_client()
        return self._rag

    @property
    def budget_enforcer(self) -> BudgetEnforcer:
        """Lazy-load budget enforcer."""
        if self._budget_enforcer is None:
            self._budget_enforcer = get_budget_enforcer()
        return self._budget_enforcer

    @property
    def deduplicator(self) -> SemanticDeduplicator:
        """Lazy-load deduplicator."""
        if self._deduplicator is None:
            self._deduplicator = get_deduplicator()
        return self._deduplicator

    def get_detail_level(self, agent_type: str) -> DetailLevel:
        """
        Get the appropriate detail level for an agent type.

        Args:
            agent_type: Agent type name

        Returns:
            DetailLevel for this agent
        """
        # Normalize agent type
        base_type = agent_type.split("_")[0] if "_" in agent_type else agent_type
        return AGENT_DETAIL_LEVELS.get(base_type, DetailLevel.SUMMARY)

    def get_context(
        self,
        query: str,
        agent_type: str,
        max_sessions: int = 5,
        include_lessons: bool = True,
    ) -> RetrievedContext:
        """
        Retrieve context at the appropriate detail level for an agent.

        Uses hybrid BM25 + dense retrieval with RRF fusion for better recall
        on both keyword-sensitive (identifiers, file names) and semantic queries.

        Args:
            query: Search query (task description)
            agent_type: Agent type for detail level selection
            max_sessions: Maximum sessions to retrieve
            include_lessons: Whether to include relevant lessons

        Returns:
            RetrievedContext with sessions and optional lessons
        """
        detail_level = self.get_detail_level(agent_type)

        # Load config values
        try:
            from src.config import Config
            min_relevance = Config.MIN_RELEVANCE_THRESHOLD
            max_sessions = Config.MAX_SIMILAR_SESSIONS
        except ImportError:
            min_relevance = 0.5

        # Fetch a wider candidate pool so both dense and BM25 can contribute
        candidate_pool = max_sessions * 3
        raw_sessions = self.rag.search_sessions(
            query=query,
            n=candidate_pool,
            min_relevance=0.0,  # No floor — BM25 may rescue low-dense results
        )

        if raw_sessions:
            raw_sessions = self._hybrid_rerank(query, raw_sessions, min_relevance)

        # Deduplicate sessions
        if len(raw_sessions) > 1:
            dedupe_result = self.deduplicator.dedupe_sessions(raw_sessions, text_key="summary")
            raw_sessions = dedupe_result.kept[:max_sessions]
        else:
            raw_sessions = raw_sessions[:max_sessions]

        # Convert to RetrievedSession objects at appropriate detail level
        sessions = [self._build_session(raw, detail_level) for raw in raw_sessions]

        # Search lessons if requested
        lessons = []
        if include_lessons:
            raw_lessons = self.rag.search_lessons(query, n=5)
            if len(raw_lessons) > 1:
                dedupe_result = self.deduplicator.dedupe_lessons(raw_lessons, text_key="fix")
                lessons = dedupe_result.kept[:3]
            else:
                lessons = raw_lessons[:3]

        total_tokens = self._estimate_tokens(sessions, lessons, detail_level)

        return RetrievedContext(
            agent_type=agent_type,
            query=query,
            sessions=sessions,
            lessons=lessons,
            total_tokens_estimate=total_tokens,
        )

    def _hybrid_rerank(
        self,
        query: str,
        raw_sessions: list[dict],
        min_relevance: float,
    ) -> list[dict]:
        """
        Rerank sessions using hybrid BM25 + dense RRF fusion.

        Builds a searchable text string per session from prompt + summary + issues,
        scores with BM25, then fuses with the dense `relevance` ranking via RRF.
        Sessions that pass neither signal are filtered by min_relevance.

        Args:
            query: The search query
            raw_sessions: Sessions from dense search (ordered best→worst by dense score)
            min_relevance: Minimum dense relevance to keep a result

        Returns:
            Sessions reranked by RRF score, filtered to min_relevance
        """
        if len(raw_sessions) <= 1:
            return [s for s in raw_sessions if s.get("relevance", 0) >= min_relevance]

        # Build text corpus for BM25
        def _doc_text(s: dict) -> str:
            parts = [s.get("prompt", ""), s.get("summary", "")]
            issues = s.get("issues", [])
            if isinstance(issues, list):
                parts.extend(issues)
            elif isinstance(issues, str):
                parts.append(issues)
            return " ".join(parts)

        docs = [_doc_text(s) for s in raw_sessions]
        bm25 = _bm25_scores(query, docs)

        # Dense ranking: already sorted best→worst by RAG server
        dense_ranking = list(range(len(raw_sessions)))

        # BM25 ranking: sort by BM25 score descending
        bm25_ranking = sorted(range(len(raw_sessions)), key=lambda i: bm25[i], reverse=True)

        # RRF fusion
        rrf = _rrf_fuse([dense_ranking, bm25_ranking])

        # Sort by RRF score, keep only those meeting min_relevance
        sorted_indices = sorted(range(len(raw_sessions)), key=lambda i: rrf[i], reverse=True)
        return [
            raw_sessions[i] for i in sorted_indices
            if raw_sessions[i].get("relevance", 0) >= min_relevance
        ]

    def _build_session(self, raw: dict, level: DetailLevel) -> RetrievedSession:
        """Build a RetrievedSession at the specified detail level."""
        session = RetrievedSession(
            session_id=raw.get("session_id", "unknown"),
            relevance=raw.get("relevance", 0.0),
            outcome=raw.get("outcome", "unknown"),
            detail_level=level,
        )

        # Level 1: METADATA
        issues = raw.get("issues", [])
        if isinstance(issues, str):
            issues = [i.strip() for i in issues.split(",") if i.strip()]
        session.issues = issues[:3]  # Top 3 issues only

        # Level 2: SUMMARY
        if level.value >= DetailLevel.SUMMARY.value:
            session.summary = raw.get("summary", "")
            files = raw.get("files", [])
            if isinstance(files, str):
                files = [f.strip() for f in files.split(",") if f.strip()]
            session.files = files[:10]  # Top 10 files
            session.prompt = raw.get("prompt", "")[:200]  # Truncate prompt

        # Level 3: FULL - load full artifacts
        if level.value >= DetailLevel.FULL.value:
            session.full_plan, session.full_review = self.load_full_artifacts(raw)

        return session

    def load_full_artifacts(self, session_data: dict) -> tuple[Optional[str], Optional[str]]:
        """
        Load full plan.md and review.md for a session.

        This is expensive (~500 tokens) so only done at FULL detail level.

        Args:
            session_data: Session metadata with full_plan_path and full_review_path

        Returns:
            Tuple of (full_plan, full_review) or (None, None)
        """
        full_plan = None
        full_review = None

        plan_path = session_data.get("full_plan_path")
        if plan_path:
            try:
                path = Path(plan_path)
                if path.exists():
                    full_plan = path.read_text(encoding="utf-8")
            except Exception:
                pass

        review_path = session_data.get("full_review_path")
        if review_path:
            try:
                path = Path(review_path)
                if path.exists():
                    full_review = path.read_text(encoding="utf-8")
            except Exception:
                pass

        return full_plan, full_review

    def _estimate_tokens(
        self,
        sessions: list[RetrievedSession],
        lessons: list[dict],
        level: DetailLevel,
    ) -> int:
        """Estimate total tokens for retrieved context."""
        # Token estimates per detail level
        tokens_per_session = {
            DetailLevel.METADATA: 10,
            DetailLevel.SUMMARY: 80,
            DetailLevel.FULL: 500,
        }

        session_tokens = len(sessions) * tokens_per_session.get(level, 80)
        lesson_tokens = len(lessons) * 50  # ~50 tokens per lesson

        return session_tokens + lesson_tokens

    def format_for_context(
        self,
        retrieved: RetrievedContext,
        agent_type: str,
    ) -> str:
        """
        Format retrieved context as markdown for injection into agent prompt.

        Applies token budget enforcement to keep within limits.

        Args:
            retrieved: RetrievedContext from get_context()
            agent_type: Agent type for budget enforcement

        Returns:
            Formatted markdown string within token budget
        """
        sections = []

        # Format sessions
        if retrieved.sessions:
            session_parts = []
            for session in retrieved.sessions:
                part = self._format_session(session)
                session_parts.append(part)

            sessions_md = "\n\n".join(session_parts)
            sections.append(("Similar Past Tasks", sessions_md))

        # Format lessons
        if retrieved.lessons:
            lesson_parts = []
            for lesson in retrieved.lessons:
                issue_type = lesson.get("issue_type", "general")
                fix = lesson.get("fix", "")
                lesson_parts.append(f"- **{issue_type}**: {fix}")

            lessons_md = "\n".join(lesson_parts)
            sections.append(("Relevant Lessons", lessons_md))

        if not sections:
            return ""

        # Apply budget enforcement
        return self.budget_enforcer.format_with_budget(agent_type, sections)

    def _format_session(self, session: RetrievedSession) -> str:
        """Format a single session based on its detail level."""
        parts = [f"**{session.session_id}** ({session.outcome}, {session.relevance:.0%} match)"]

        # Level 1: Issues
        if session.issues:
            parts.append(f"Issues: {', '.join(session.issues[:3])}")

        # Level 2: Summary and files
        if session.detail_level.value >= DetailLevel.SUMMARY.value:
            if session.summary:
                parts.append(session.summary)
            if session.files:
                parts.append(f"Files: {', '.join(session.files[:5])}")

        # Level 3: Full artifacts are typically not inlined
        # (too large, would be truncated anyway)

        return "\n".join(parts)

    def upgrade_detail_level(
        self,
        session: RetrievedSession,
        target_level: DetailLevel,
    ) -> RetrievedSession:
        """
        Upgrade a session to a higher detail level.

        Useful when an agent needs more detail for a specific session.

        Args:
            session: Session to upgrade
            target_level: Target detail level

        Returns:
            Session with upgraded detail level
        """
        if target_level.value <= session.detail_level.value:
            return session  # Already at or above target

        # Fetch full session data from RAG
        full_data = self.rag.get_session(session.session_id)
        if not full_data:
            return session

        # Rebuild at target level
        return self._build_session(full_data, target_level)


# Singleton instance
_retriever_instance: Optional[ProgressiveRetriever] = None


def get_retriever() -> ProgressiveRetriever:
    """Get or create singleton ProgressiveRetriever instance."""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = ProgressiveRetriever()
    return _retriever_instance

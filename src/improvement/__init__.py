"""
Improvement module — Self-improving capabilities for the Vibe Coding Team.

Provides:
- Self-healing loop: auto-run tests/lint, feed errors back for auto-fix
- LLM-as-Judge quality scoring for pipeline output evaluation
- Post-task reflection cycle for continuous learning
- Stuck detection with kill criteria
- Quality metrics tracking and persistence
"""

from .self_healer import SelfHealingLoop, HealingResult
from .quality_scorer import QualityScorer, QualityScore
from .reflection import ReflectionEngine
from .stuck_detector import StuckDetector
from .metrics import MetricsTracker

__all__ = [
    "SelfHealingLoop",
    "HealingResult",
    "QualityScorer",
    "QualityScore",
    "ReflectionEngine",
    "StuckDetector",
    "MetricsTracker",
]

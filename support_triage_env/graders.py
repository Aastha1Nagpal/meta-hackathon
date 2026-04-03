from __future__ import annotations

from typing import Dict, Tuple

from .models import SupportState
from .tasks import TaskSpec


def _normalize_text(value: str | None) -> str:
    return (value or "").strip().lower()


def grade_state(task: TaskSpec, state: SupportState) -> Tuple[float, Dict[str, float]]:
    reply = _normalize_text(state.drafted_reply)
    tags = {_normalize_text(tag) for tag in state.tags}

    breakdown = {
        "priority": 1.0 if _normalize_text(state.priority) == _normalize_text(task.expected_priority) else 0.0,
        "team": 1.0 if _normalize_text(state.team) == _normalize_text(task.expected_team) else 0.0,
        "tags": 0.0,
        "reply": 0.0,
        "resolution": 1.0 if _normalize_text(state.resolution_status) == _normalize_text(task.expected_resolution) else 0.0,
    }

    if task.required_tags:
        matched_tags = sum(1 for tag in task.required_tags if _normalize_text(tag) in tags)
        breakdown["tags"] = matched_tags / len(task.required_tags)

    if task.required_reply_phrases:
        phrase_hits = sum(1 for phrase in task.required_reply_phrases if _normalize_text(phrase) in reply)
        breakdown["reply"] = phrase_hits / len(task.required_reply_phrases)

    if task.forbidden_reply_phrases and reply:
        forbidden_hits = sum(1 for phrase in task.forbidden_reply_phrases if _normalize_text(phrase) in reply)
        if forbidden_hits:
            breakdown["reply"] = max(0.0, breakdown["reply"] - 0.5 * forbidden_hits)

    score = (
        0.2 * breakdown["priority"]
        + 0.2 * breakdown["team"]
        + 0.2 * breakdown["tags"]
        + 0.25 * breakdown["reply"]
        + 0.15 * breakdown["resolution"]
    )
    return round(min(max(score, 0.0), 1.0), 4), breakdown

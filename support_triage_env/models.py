from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


ActionType = Literal[
    "set_priority",
    "assign_team",
    "add_tag",
    "draft_reply",
    "resolve_ticket",
    "request_clarification",
]

Priority = Literal["low", "medium", "high", "urgent"]


class SupportAction(BaseModel):
    action_type: ActionType = Field(description="The operation the agent wants to perform.")
    value: str = Field(description="Primary value for the action, such as a team name or draft reply.")
    rationale: Optional[str] = Field(
        default=None,
        description="Optional short explanation for the action, useful for debugging.",
    )


class SupportReward(BaseModel):
    value: float = Field(ge=-1.0, le=1.0)
    reason: str
    progress_score: float = Field(ge=0.0, le=1.0)


class SupportObservation(BaseModel):
    task_id: str
    benchmark_name: str = "support_inbox_triage"
    difficulty: Literal["easy", "medium", "hard"]
    objective: str
    ticket_id: str
    customer_tier: str
    customer_message: str
    current_priority: Optional[Priority] = None
    assigned_team: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    drafted_reply: Optional[str] = None
    resolution_status: Optional[str] = None
    remaining_steps: int
    last_action_error: Optional[str] = None
    action_history: List[str] = Field(default_factory=list)
    hints: List[str] = Field(default_factory=list)


class SupportState(BaseModel):
    task_id: Optional[str] = None
    ticket_id: Optional[str] = None
    step_count: int = 0
    max_steps: int = 0
    priority: Optional[Priority] = None
    team: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    drafted_reply: Optional[str] = None
    resolution_status: Optional[str] = None
    done: bool = False
    last_action_error: Optional[str] = None
    action_history: List[str] = Field(default_factory=list)
    progress_score: float = 0.0


class StepInfo(BaseModel):
    progress_score: float = Field(ge=0.0, le=1.0)
    last_action_error: Optional[str] = None
    grader_breakdown: Dict[str, float] = Field(default_factory=dict)


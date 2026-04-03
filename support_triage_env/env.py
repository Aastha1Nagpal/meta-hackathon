from __future__ import annotations

from typing import Optional, Tuple

from .graders import grade_state
from .models import StepInfo, SupportAction, SupportObservation, SupportReward, SupportState
from .tasks import TASKS, TaskSpec


class SupportInboxEnv:
    benchmark_name = "support_inbox_triage"

    def __init__(self, max_steps: int = 8) -> None:
        self.max_steps = max_steps
        self._task: Optional[TaskSpec] = None
        self._state = SupportState(max_steps=max_steps)

    def reset(self, task_id: str = "duplicate_refund") -> SupportObservation:
        if task_id not in TASKS:
            raise ValueError(f"Unknown task_id '{task_id}'. Available tasks: {', '.join(sorted(TASKS))}")
        self._task = TASKS[task_id]
        self._state = SupportState(
            task_id=task_id,
            ticket_id=self._task.ticket_id,
            step_count=0,
            max_steps=self.max_steps,
            priority=None,
            team=None,
            tags=[],
            drafted_reply=None,
            resolution_status=None,
            done=False,
            last_action_error=None,
            action_history=[],
            progress_score=0.0,
        )
        return self._build_observation()

    def state(self) -> SupportState:
        return self._state.model_copy(deep=True)

    def step(self, action: SupportAction) -> Tuple[SupportObservation, SupportReward, bool, StepInfo]:
        if self._task is None:
            raise RuntimeError("Environment has not been reset. Call reset() before step().")
        if self._state.done:
            reward = SupportReward(value=0.0, reason="Episode already finished.", progress_score=self._state.progress_score)
            info = StepInfo(progress_score=self._state.progress_score, last_action_error=self._state.last_action_error, grader_breakdown={})
            return self._build_observation(), reward, True, info

        previous_score, _ = grade_state(self._task, self._state)
        penalty = 0.01
        error: Optional[str] = None
        action_label = f"{action.action_type}:{action.value}"

        if action_label in self._state.action_history:
            penalty += 0.03

        try:
            self._apply_action(action)
        except ValueError as exc:
            error = str(exc)
            penalty += 0.08

        self._state.step_count += 1
        self._state.last_action_error = error
        self._state.action_history.append(action_label)

        progress_score, breakdown = grade_state(self._task, self._state)
        self._state.progress_score = progress_score

        reward_value = round(progress_score - previous_score - penalty, 4)
        reward_reason = "Progress updated based on ticket triage quality."
        if error:
            reward_reason = f"Invalid or incomplete action: {error}"

        if self._state.resolution_status is not None or self._state.step_count >= self.max_steps:
            self._state.done = True

        observation = self._build_observation()
        reward = SupportReward(value=max(-1.0, min(1.0, reward_value)), reason=reward_reason, progress_score=progress_score)
        info = StepInfo(progress_score=progress_score, last_action_error=error, grader_breakdown=breakdown)
        return observation, reward, self._state.done, info

    def _apply_action(self, action: SupportAction) -> None:
        value = action.value.strip()
        if not value:
            raise ValueError("Action value cannot be empty.")

        if action.action_type == "set_priority":
            if value not in {"low", "medium", "high", "urgent"}:
                raise ValueError("Priority must be one of: low, medium, high, urgent.")
            self._state.priority = value
            return

        if action.action_type == "assign_team":
            if value not in {"billing", "security", "incident_response", "technical_support"}:
                raise ValueError("Team must be one of: billing, security, incident_response, technical_support.")
            self._state.team = value
            return

        if action.action_type == "add_tag":
            if value.lower() not in {tag.lower() for tag in self._state.tags}:
                self._state.tags.append(value)
            return

        if action.action_type == "draft_reply":
            self._state.drafted_reply = value
            return

        if action.action_type == "resolve_ticket":
            self._state.resolution_status = value
            return

        if action.action_type == "request_clarification":
            clarification = f"Requested clarification from customer: {value}"
            self._state.drafted_reply = clarification
            return

        raise ValueError(f"Unsupported action_type '{action.action_type}'.")

    def _build_observation(self) -> SupportObservation:
        if self._task is None:
            raise RuntimeError("Environment has not been reset. Call reset() before requesting an observation.")
        return SupportObservation(
            task_id=self._task.task_id,
            difficulty=self._task.difficulty,
            objective=self._task.objective,
            ticket_id=self._task.ticket_id,
            customer_tier=self._task.customer_tier,
            customer_message=self._task.customer_message,
            current_priority=self._state.priority,
            assigned_team=self._state.team,
            tags=list(self._state.tags),
            drafted_reply=self._state.drafted_reply,
            resolution_status=self._state.resolution_status,
            remaining_steps=max(0, self.max_steps - self._state.step_count),
            last_action_error=self._state.last_action_error,
            action_history=list(self._state.action_history),
            hints=list(self._task.hints),
        )

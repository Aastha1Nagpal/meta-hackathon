from __future__ import annotations

import json
import os
from typing import Dict, List

from openai import OpenAI

from support_triage_env.env import SupportInboxEnv
from support_triage_env.models import SupportAction, SupportObservation
from support_triage_env.tasks import list_tasks


API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY = (
    os.getenv("HF_TOKEN")
    or os.getenv("OPENAI_API_KEY")
    or os.getenv("API_KEY")
    or "missing"
)
MAX_STEPS = 8
USE_SCRIPTED_BASELINE = os.getenv("USE_SCRIPTED_BASELINE", "false").lower() == "true"


SYSTEM_PROMPT = """
You are an expert customer support operations agent interacting with a ticket-triage environment.
Choose exactly one action per turn and return valid JSON:
{"action_type":"set_priority|assign_team|add_tag|draft_reply|resolve_ticket|request_clarification","value":"...","rationale":"..."}
Use only the allowed action_type enum values and only valid environment values.
Valid priorities: low, medium, high, urgent.
Valid teams: billing, security, incident_response, technical_support.
When resolving, prefer exact short machine-readable status strings rather than prose.
Use concise, safe, high-signal actions. Draft replies should be realistic and customer-facing.
""".strip()


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action_str: str, reward: float, done: bool, error: str | None) -> None:
    safe_error = error if error else "null"
    print(
        f"[STEP] step={step} action={action_str} reward={reward:.2f} "
        f"done={'true' if done else 'false'} error={safe_error}",
        flush=True,
    )


def log_end(success: bool, rewards: List[float]) -> None:
    reward_str = ",".join(f"{reward:.2f}" for reward in rewards)
    print(
        f"[END] success={'true' if success else 'false'} steps={len(rewards)} rewards={reward_str}",
        flush=True,
    )


def build_user_prompt(observation: SupportObservation) -> str:
    return json.dumps(
        {
            "task_id": observation.task_id,
            "difficulty": observation.difficulty,
            "objective": observation.objective,
            "ticket_id": observation.ticket_id,
            "customer_tier": observation.customer_tier,
            "customer_message": observation.customer_message,
            "current_priority": observation.current_priority,
            "assigned_team": observation.assigned_team,
            "tags": observation.tags,
            "drafted_reply": observation.drafted_reply,
            "resolution_status": observation.resolution_status,
            "remaining_steps": observation.remaining_steps,
            "hints": observation.hints,
            "action_history": observation.action_history,
            "last_action_error": observation.last_action_error,
        },
        indent=2,
    )


def scripted_action(observation: SupportObservation) -> SupportAction:
    if observation.task_id == "duplicate_refund":
        plan = [
            SupportAction(action_type="set_priority", value="medium"),
            SupportAction(action_type="assign_team", value="billing"),
            SupportAction(action_type="add_tag", value="refund_requested"),
            SupportAction(action_type="add_tag", value="duplicate_charge"),
            SupportAction(
                action_type="draft_reply",
                value=(
                    "Sorry about the duplicate charge. We have opened a refund review and "
                    "our billing team will process the refund. You can expect an update within 48 hours."
                ),
            ),
            SupportAction(action_type="resolve_ticket", value="refund_review_opened"),
        ]
        return plan[min(len(observation.action_history), len(plan) - 1)]

    if observation.task_id == "phishing_escalation":
        plan = [
            SupportAction(action_type="set_priority", value="high"),
            SupportAction(action_type="assign_team", value="security"),
            SupportAction(action_type="add_tag", value="phishing"),
            SupportAction(action_type="add_tag", value="account_security"),
            SupportAction(
                action_type="draft_reply",
                value=(
                    "Please do not click any suspicious links. Reset your password immediately "
                    "through the official login page, and forward the email to our security team "
                    "so we can investigate."
                ),
            ),
            SupportAction(action_type="resolve_ticket", value="escalated_to_security"),
        ]
        return plan[min(len(observation.action_history), len(plan) - 1)]

    plan = [
        SupportAction(action_type="set_priority", value="urgent"),
        SupportAction(action_type="assign_team", value="incident_response"),
        SupportAction(action_type="add_tag", value="outage"),
        SupportAction(action_type="add_tag", value="sla_credit"),
        SupportAction(action_type="add_tag", value="vip_customer"),
        SupportAction(
            action_type="draft_reply",
            value=(
                "We have opened an incident and our engineering team is actively working on it now. "
                "We are treating this as an urgent outage for your enterprise workspace, and we will "
                "provide hourly updates until service is restored. We will also review SLA credit once "
                "the incident is resolved."
            ),
        ),
        SupportAction(action_type="resolve_ticket", value="incident_escalated"),
    ]
    return plan[min(len(observation.action_history), len(plan) - 1)]


def call_model(client: OpenAI, observation: SupportObservation) -> SupportAction:
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0.0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(observation)},
        ],
    )
    content = completion.choices[0].message.content or ""
    data = json.loads(content)
    return SupportAction(**data)


def run_task(task_id: str) -> Dict[str, float]:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = SupportInboxEnv(max_steps=MAX_STEPS)
    observation = env.reset(task_id=task_id)

    log_start(task=task_id, env=env.benchmark_name, model=MODEL_NAME)
    rewards: List[float] = []
    success = False

    try:
        for step_idx in range(1, MAX_STEPS + 1):
            if USE_SCRIPTED_BASELINE:
                action = scripted_action(observation)
            else:
                action = call_model(client, observation)
            observation, reward, done, info = env.step(action)
            rewards.append(reward.value)
            log_step(step_idx, f"{action.action_type}({json.dumps(action.value)})", reward.value, done, info.last_action_error)
            if done:
                success = info.progress_score >= 0.8
                break
        else:
            final_state = env.state()
            success = final_state.progress_score >= 0.8
    except Exception:
        success = False
    finally:
        log_end(success, rewards)

    final_state = env.state()
    return {"task_id": task_id, "score": final_state.progress_score, "steps": len(rewards)}


def main() -> None:
    for task in list_tasks():
        run_task(task.task_id)


if __name__ == "__main__":
    main()

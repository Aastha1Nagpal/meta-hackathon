from support_triage_env.env import SupportInboxEnv
from support_triage_env.models import SupportAction


def test_easy_task_reaches_full_score() -> None:
    env = SupportInboxEnv()
    env.reset("duplicate_refund")
    env.step(SupportAction(action_type="set_priority", value="medium"))
    env.step(SupportAction(action_type="assign_team", value="billing"))
    env.step(SupportAction(action_type="add_tag", value="refund_requested"))
    env.step(SupportAction(action_type="add_tag", value="duplicate_charge"))
    env.step(
        SupportAction(
            action_type="draft_reply",
            value="Sorry about the duplicate charge. We have opened a refund review and will update you within 48 hours.",
        )
    )
    _, _, done, info = env.step(SupportAction(action_type="resolve_ticket", value="refund_review_opened"))
    assert done is True
    assert info.progress_score == 1.0

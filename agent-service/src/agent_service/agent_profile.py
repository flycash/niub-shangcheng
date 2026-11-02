from .models import AgentProfile


AGENT_PROFILES: dict[int, AgentProfile] = {
    1: AgentProfile(
        user_id=1,
        preferred_categories=["箱包", "家居"],
        preferred_tags=["通勤", "低糖", "礼物"],
        avoid_tags=["浓郁香精"],
        budget_hint_cents=30000,
        notes="用户多次表达偏好实用型商品，也会关注适合送礼的设计。",
        updated_at="2026-11-01T10:00:00+08:00",
    )
}


def get_agent_profile(user_id: int) -> AgentProfile | None:
    return AGENT_PROFILES.get(user_id)

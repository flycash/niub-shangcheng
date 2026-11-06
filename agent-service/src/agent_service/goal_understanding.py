import json
import re
from pathlib import Path
from typing import Any, Protocol

from agents import Agent, ModelSettings, RunConfig, Runner
from pydantic import ValidationError

from .llm_config import LLMConfig
from .models import (
    ConversationMessage,
    GoalUnderstandingDraft,
    GoalUnderstandingResult,
    IntentType,
    OrderLink,
    Product,
)
from .prompt_loader import PromptLoadError, load_prompt


GOAL_UNDERSTANDING_PROMPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "prompts"
    / "goal_understanding.md"
)

INTENT_LABELS: dict[IntentType, str] = {
    "product_recommendation": "商品推荐",
    "order_query": "订单查询",
    "after_sales": "售后服务",
    "unknown": "其他或未识别",
}


class GoalUnderstandingError(Exception):
    """Raised when the independent goal-understanding action fails."""


class GoalUnderstander(Protocol):
    async def understand(
        self,
        *,
        current_message: str,
        recent_messages: list[ConversationMessage],
        previous_goal: GoalUnderstandingResult | None,
        previous_recommendations: list[Product],
        previous_orders: list[OrderLink],
    ) -> GoalUnderstandingResult: ...


def _json_payload(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < start:
        raise GoalUnderstandingError(
            "goal understanding did not return a JSON object"
        )
    try:
        payload = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise GoalUnderstandingError(
            "goal understanding returned invalid JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise GoalUnderstandingError(
            "goal understanding JSON must be an object"
        )
    return payload


class AgentGoalUnderstander:
    def __init__(self, *, config: LLMConfig, model: Any) -> None:
        self.config = config
        self.model = model

    async def understand(
        self,
        *,
        current_message: str,
        recent_messages: list[ConversationMessage],
        previous_goal: GoalUnderstandingResult | None,
        previous_recommendations: list[Product],
        previous_orders: list[OrderLink],
    ) -> GoalUnderstandingResult:
        try:
            instructions = load_prompt(GOAL_UNDERSTANDING_PROMPT_PATH)
        except PromptLoadError as exc:
            raise GoalUnderstandingError(str(exc)) from exc

        agent = Agent[Any](
            name="goal-understanding",
            instructions=instructions,
            model=self.model,
            model_settings=ModelSettings(
                temperature=self.config.temperature,
                max_tokens=self.config.output_token_limit,
            ),
        )
        payload = {
            "current_message": current_message,
            "recent_messages": [
                message.model_dump(mode="json")
                for message in recent_messages[-12:]
            ],
            "previous_goal": (
                previous_goal.model_dump(mode="json")
                if previous_goal is not None
                else None
            ),
            "previous_recommendations": [
                {
                    "position": index,
                    "product_id": product.id,
                    "name": product.name,
                    "price_cents": product.price_cents,
                }
                for index, product in enumerate(
                    previous_recommendations,
                    start=1,
                )
            ],
            "previous_orders": [
                order.model_dump(mode="json")
                for order in previous_orders
            ],
        }
        try:
            result = await Runner.run(
                agent,
                input=json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                max_turns=1,
                run_config=RunConfig(tracing_disabled=True),
            )
        except Exception as exc:
            raise GoalUnderstandingError(
                "goal understanding model call failed: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        if not isinstance(result.final_output, str):
            raise GoalUnderstandingError(
                "goal understanding returned non-text output"
            )
        try:
            draft = GoalUnderstandingDraft.model_validate(
                _json_payload(result.final_output)
            )
        except ValidationError as exc:
            raise GoalUnderstandingError(
                "goal understanding returned invalid data"
            ) from exc

        intents = list(dict.fromkeys(draft.intents))
        if len(intents) > 1 and "unknown" in intents:
            intents = [
                intent for intent in intents if intent != "unknown"
            ]
        primary_intent = intents[0]
        pending_intents = intents[1:]
        pending_question = None
        if pending_intents:
            labels = "、".join(
                INTENT_LABELS.get(intent, intent) for intent in pending_intents
            )
            pending_question = (
                f"当前已处理第一个意图。需要我继续处理后续意图：{labels}吗？"
            )
        requires_clarification = (
            draft.requires_clarification or draft.confidence < 0.55
        )
        clarification_question = draft.clarification_question
        if requires_clarification and not clarification_question:
            clarification_question = "你希望我具体帮你处理哪件事？"

        return GoalUnderstandingResult(
            primary_intent=primary_intent,
            intents=intents,
            pending_intents=pending_intents,
            goal=draft.goal,
            confidence=draft.confidence,
            slots=draft.slots,
            missing_slots=draft.missing_slots,
            requires_clarification=requires_clarification,
            clarification_question=clarification_question,
            pending_intent_question=pending_question,
        )

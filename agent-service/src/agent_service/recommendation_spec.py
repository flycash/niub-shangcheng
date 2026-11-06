import json
import re
from pathlib import Path
from typing import Any, Protocol

from agents import Agent, ModelSettings, RunConfig, Runner
from pydantic import ValidationError

from .llm_config import LLMConfig
from .models import (
    AgentProfile,
    BrowseEvent,
    GoalUnderstandingResult,
    OrderRecord,
    PlatformProfile,
    ProductList,
    RecommendationSpec,
    RecommendationSpecHardConstraints,
    ShoppingCart,
)
from .prompt_loader import PromptLoadError, load_prompt


RECOMMENDATION_SPEC_PROMPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "prompts"
    / "recommendation_spec.md"
)


class RecommendationSpecError(Exception):
    """Raised when recommendation SPEC generation fails."""


class RecommendationSpecGenerator(Protocol):
    async def generate(
        self,
        *,
        goal: GoalUnderstandingResult,
        agent_profile: AgentProfile | None,
        platform_profile: PlatformProfile | None,
        cart: ShoppingCart,
        browse_history: list[BrowseEvent],
        orders: list[OrderRecord],
        catalog: ProductList,
    ) -> RecommendationSpec: ...


def _json_payload(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < start:
        raise RecommendationSpecError(
            "recommendation SPEC did not return a JSON object"
        )
    try:
        payload = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise RecommendationSpecError(
            "recommendation SPEC returned invalid JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise RecommendationSpecError(
            "recommendation SPEC JSON must be an object"
        )
    return payload


def _string_list(value: object) -> list[str] | None:
    if not isinstance(value, list):
        return None
    return [
        item.strip()
        for item in value
        if isinstance(item, str) and item.strip()
    ]


def _non_negative_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _apply_explicit_goal_constraints(
    spec: RecommendationSpec,
    goal: GoalUnderstandingResult,
) -> RecommendationSpec:
    slots = goal.slots
    hard = spec.hard_constraints
    category = slots.get("category")
    min_price = _non_negative_int(slots.get("min_price_cents"))
    max_price = _non_negative_int(slots.get("max_price_cents"))
    required_tags = _string_list(slots.get("required_tags"))
    excluded_tags = _string_list(slots.get("excluded_tags"))
    normalized_hard = RecommendationSpecHardConstraints(
        category=category if isinstance(category, str) and category else hard.category,
        min_price_cents=(
            min_price if min_price is not None else hard.min_price_cents
        ),
        max_price_cents=(
            max_price if max_price is not None else hard.max_price_cents
        ),
        required_tags=(
            required_tags
            if required_tags is not None
            else hard.required_tags
        ),
        excluded_tags=(
            excluded_tags
            if excluded_tags is not None
            else hard.excluded_tags
        ),
    )
    scenario = slots.get("scenario")
    if scenario not in {"general", "self", "gift", "replenishment"}:
        scenario = spec.scenario
    usage = slots.get("usage")
    recipient = slots.get("recipient")
    queries = list(dict.fromkeys(
        query.strip()
        for query in spec.search_queries
        if query.strip()
    ))[:6]
    if not queries:
        queries = [goal.goal]
    return spec.model_copy(
        update={
            "hard_constraints": normalized_hard,
            "search_queries": queries,
            "scenario": scenario,
            "usage": (
                usage
                if isinstance(usage, str) and usage
                else spec.usage
            ),
            "recipient": (
                recipient
                if isinstance(recipient, str) and recipient
                else spec.recipient
            ),
        }
    )


class AgentRecommendationSpecGenerator:
    def __init__(self, *, config: LLMConfig, model: Any) -> None:
        self.config = config
        self.model = model

    async def generate(
        self,
        *,
        goal: GoalUnderstandingResult,
        agent_profile: AgentProfile | None,
        platform_profile: PlatformProfile | None,
        cart: ShoppingCart,
        browse_history: list[BrowseEvent],
        orders: list[OrderRecord],
        catalog: ProductList,
    ) -> RecommendationSpec:
        try:
            instructions = load_prompt(RECOMMENDATION_SPEC_PROMPT_PATH)
        except PromptLoadError as exc:
            raise RecommendationSpecError(str(exc)) from exc

        agent = Agent[Any](
            name="recommendation-spec-generator",
            instructions=instructions,
            model=self.model,
            model_settings=ModelSettings(
                temperature=self.config.temperature,
                max_tokens=self.config.output_token_limit,
            ),
        )
        payload = {
            "goal": goal.model_dump(mode="json"),
            "agent_profile": (
                agent_profile.model_dump(mode="json")
                if agent_profile is not None
                else None
            ),
            "platform_profile": (
                platform_profile.model_dump(mode="json")
                if platform_profile is not None
                else None
            ),
            "cart": cart.model_dump(mode="json"),
            "browse_history": [
                event.model_dump(mode="json")
                for event in browse_history
            ],
            "orders": [
                order.model_dump(mode="json")
                for order in orders
            ],
            "catalog": [
                {
                    "id": product.id,
                    "name": product.name,
                    "category": product.category,
                    "tags": product.tags,
                    "price_cents": product.price_cents,
                }
                for product in catalog.items
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
            raise RecommendationSpecError(
                "recommendation SPEC model call failed: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        if not isinstance(result.final_output, str):
            raise RecommendationSpecError(
                "recommendation SPEC returned non-text output"
            )
        try:
            spec = RecommendationSpec.model_validate(
                _json_payload(result.final_output)
            )
        except ValidationError as exc:
            raise RecommendationSpecError(
                "recommendation SPEC returned invalid data"
            ) from exc
        return _apply_explicit_goal_constraints(spec, goal)

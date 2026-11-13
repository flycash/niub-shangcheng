import json
import re
from pathlib import Path
from typing import Any, Protocol

from agents import Agent, ModelSettings
from pydantic import ValidationError

from .llm_config import LLMConfig
from .models import (
    ConversationDetail,
    ConversationDigest,
    ConversationEvidence,
    ConversationSummaryDraft,
    Product,
    ProductKeyInformation,
    ProductKeyInformationGroup,
    RecommendedProductSummary,
    RecommendationRoundSummary,
    StoredMessage,
)
from .observability.agents import run_observed_action
from .prompt_loader import PromptLoadError, load_prompt
from .storage import utc_now


CONVERSATION_SUMMARY_PROMPT_VERSION = "conversation-summary-v1"
CONVERSATION_SUMMARY_PROMPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "prompts"
    / "conversation_summary.md"
)


class ConversationSummaryError(Exception):
    """Raised when a conversation digest cannot be generated or validated."""


class ConversationSummarizer(Protocol):
    async def summarize(
        self,
        *,
        conversation: ConversationDetail,
        source_updated_at: str,
    ) -> ConversationDigest: ...


def _json_payload(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < start:
        raise ConversationSummaryError(
            "conversation summary did not return a JSON object"
        )
    try:
        payload = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ConversationSummaryError(
            "conversation summary returned invalid JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise ConversationSummaryError(
            "conversation summary JSON must be an object"
        )
    return payload


def _completed_messages(
    conversation: ConversationDetail,
) -> list[StoredMessage]:
    return [
        message
        for message in conversation.messages
        if message.role == "user" or message.status == "completed"
    ]


def _summary_input(conversation: ConversationDetail) -> dict[str, object]:
    messages: list[dict[str, object]] = []
    for message in _completed_messages(conversation):
        payload: dict[str, object] = {
            "message_id": message.id,
            "role": message.role,
            "content": message.content,
        }
        if message.recommendations:
            payload["recommendations"] = [
                product.model_dump(mode="json")
                for product in message.recommendations
            ]
        if message.recommendation_decision is not None:
            payload["recommendation_decision"] = (
                message.recommendation_decision.model_dump(mode="json")
            )
        messages.append(payload)
    return {
        "conversation_id": conversation.id,
        "conversation_title": conversation.title,
        "messages": messages,
    }


def _normalized_text(value: str) -> str:
    return " ".join(value.split())


def _validate_evidence(
    evidence: ConversationEvidence,
    *,
    user_messages: dict[str, StoredMessage],
) -> None:
    message = user_messages.get(evidence.message_id)
    if message is None:
        raise ConversationSummaryError(
            f"evidence references non-user message {evidence.message_id}"
        )
    if _normalized_text(evidence.quote) not in _normalized_text(message.content):
        raise ConversationSummaryError(
            f"evidence quote is not present in message {evidence.message_id}"
        )


def _product_source_text(product: Product, source_field: str) -> str:
    if source_field == "name":
        return product.name
    if source_field == "description":
        return product.description
    if source_field == "category":
        return product.category
    if source_field == "tags":
        return "\n".join(product.tags)
    if source_field == "badge":
        return product.badge or ""
    return ""


def _validate_key_information(
    information: ProductKeyInformation,
    product: Product,
) -> None:
    source_text = _product_source_text(product, information.source_field)
    if _normalized_text(information.source_text) not in _normalized_text(
        source_text
    ):
        raise ConversationSummaryError(
            f"product {product.id} key information for "
            f"{information.name} is not grounded in {information.source_field}"
        )


def _validate_draft(
    draft: ConversationSummaryDraft,
    conversation: ConversationDetail,
) -> None:
    messages = _completed_messages(conversation)
    user_messages = {
        message.id: message for message in messages if message.role == "user"
    }
    products = {
        product.id: product
        for message in messages
        for product in message.recommendations
    }

    seen_groups: set[str] = set()
    for group in draft.product_key_information:
        if group.product_id in seen_groups:
            raise ConversationSummaryError(
                f"duplicate product key information for {group.product_id}"
            )
        seen_groups.add(group.product_id)
        product = products.get(group.product_id)
        if product is None:
            raise ConversationSummaryError(
                f"product key information references unknown product "
                f"{group.product_id}"
            )
        for information in group.items:
            _validate_key_information(information, product)

    for feedback in draft.product_feedback:
        if feedback.product_id not in products:
            raise ConversationSummaryError(
                f"feedback references unknown product {feedback.product_id}"
            )
        for evidence in feedback.evidence:
            _validate_evidence(evidence, user_messages=user_messages)

    for preference in draft.general_preferences:
        for evidence in preference.evidence:
            _validate_evidence(evidence, user_messages=user_messages)


def assemble_conversation_digest(
    *,
    conversation: ConversationDetail,
    draft: ConversationSummaryDraft,
    source_updated_at: str,
    generated_at: str | None = None,
) -> ConversationDigest:
    _validate_draft(draft, conversation)
    messages = _completed_messages(conversation)
    key_information = {
        group.product_id: group.items
        for group in draft.product_key_information
    }
    rounds: list[RecommendationRoundSummary] = []
    last_user_request = ""

    for message in messages:
        if message.role == "user":
            last_user_request = message.content
            continue
        if not message.recommendations:
            continue

        decision_items = (
            {
                item.product_id: item
                for item in message.recommendation_decision.items
            }
            if message.recommendation_decision is not None
            else {}
        )
        products = []
        for product in message.recommendations:
            decision_item = decision_items.get(product.id)
            products.append(
                RecommendedProductSummary(
                    product=product,
                    key_information=key_information.get(product.id, []),
                    reason=decision_item.reason if decision_item else None,
                    reason_source=(
                        decision_item.reason_source
                        if decision_item
                        else "unavailable"
                    ),
                    environmental_fit=(
                        decision_item.environmental_fit
                        if decision_item
                        else None
                    ),
                )
            )
        rounds.append(
            RecommendationRoundSummary(
                assistant_message_id=message.id,
                user_request=last_user_request or "(用户请求未记录)",
                ranking_summary=(
                    message.recommendation_decision.summary
                    if message.recommendation_decision is not None
                    else ""
                ),
                products=products,
            )
        )

    return ConversationDigest(
        conversation_id=conversation.id,
        source_updated_at=source_updated_at,
        summary=draft.summary,
        user_goals=draft.user_goals,
        explicit_constraints=draft.explicit_constraints,
        recommendation_rounds=rounds,
        product_feedback=draft.product_feedback,
        general_preferences=draft.general_preferences,
        unresolved_items=draft.unresolved_items,
        source_message_ids=[message.id for message in messages],
        generated_at=generated_at or utc_now(),
    )


class AgentConversationSummarizer:
    def __init__(self, *, config: LLMConfig, model: Any) -> None:
        self.config = config
        self.model = model

    async def summarize(
        self,
        *,
        conversation: ConversationDetail,
        source_updated_at: str,
    ) -> ConversationDigest:
        try:
            instructions = load_prompt(CONVERSATION_SUMMARY_PROMPT_PATH)
        except PromptLoadError as exc:
            raise ConversationSummaryError(str(exc)) from exc

        agent = Agent[Any](
            name="conversation-summarizer",
            instructions=instructions,
            model=self.model,
            model_settings=ModelSettings(
                temperature=self.config.temperature,
                max_tokens=self.config.output_token_limit,
            ),
        )
        payload = _summary_input(conversation)
        try:
            result = await run_observed_action(
                agent,
                action_name="conversation_summary",
                model=str(self.config.model),
                input=json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                max_turns=1,
            )
        except Exception as exc:
            raise ConversationSummaryError(
                "conversation summary model call failed: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        if not isinstance(result.final_output, str):
            raise ConversationSummaryError(
                "conversation summary returned non-text output"
            )
        try:
            draft = ConversationSummaryDraft.model_validate(
                _json_payload(result.final_output)
            )
        except ValidationError as exc:
            raise ConversationSummaryError(
                "conversation summary returned invalid data"
            ) from exc
        return assemble_conversation_digest(
            conversation=conversation,
            draft=draft,
            source_updated_at=source_updated_at,
        )

import pytest

from agent_service.conversation_summary import (
    ConversationSummaryError,
    assemble_conversation_digest,
)
from agent_service.models import (
    ConversationDetail,
    ConversationEvidence,
    ConversationSummaryDraft,
    FeedbackAspect,
    FinalRecommendation,
    GeneralPreference,
    Product,
    ProductFeedback,
    ProductKeyInformation,
    ProductKeyInformationGroup,
    RecommendationDecision,
    StoredMessage,
)


def _conversation(*, feedback_quote: str = "这个黑色款太大了，我不喜欢") -> ConversationDetail:
    product = Product(
        id="tote-large",
        name="通勤托特包",
        description="黑色大号容量，可放 16 英寸电脑",
        price_cents=69900,
        category="箱包",
        badge="通勤推荐",
        tags=["通勤", "大容量"],
    )
    return ConversationDetail(
        id="conversation-summary",
        title="通勤包推荐",
        message_count=4,
        created_at="2026-11-13T00:00:00.000+00:00",
        updated_at="2026-11-13T00:05:00.000+00:00",
        messages=[
            StoredMessage(
                id="user-1",
                role="user",
                content="推荐一个适合通勤的包，预算 1000 元以内",
                status="completed",
                created_at="2026-11-13T00:00:00.000+00:00",
            ),
            StoredMessage(
                id="assistant-1",
                role="assistant",
                content="推荐这款通勤托特包，容量大。",
                status="completed",
                created_at="2026-11-13T00:01:00.000+00:00",
                recommendations=[product],
                recommendation_decision=RecommendationDecision(
                    summary="容量和通勤场景更匹配",
                    items=[
                        FinalRecommendation(
                            product_id="tote-large",
                            rank=1,
                            channel="organic",
                            reason="大容量适合携带电脑，且符合通勤场景",
                            reason_source="semantic_reranker",
                        )
                    ],
                ),
            ),
            StoredMessage(
                id="user-2",
                role="user",
                content=feedback_quote,
                status="completed",
                created_at="2026-11-13T00:02:00.000+00:00",
            ),
            StoredMessage(
                id="assistant-2",
                role="assistant",
                content="理解，你更希望尺寸小一些。",
                status="completed",
                created_at="2026-11-13T00:03:00.000+00:00",
            ),
        ],
    )


def _draft(quote: str = "这个黑色款太大了，我不喜欢") -> ConversationSummaryDraft:
    return ConversationSummaryDraft(
        summary="用户寻找预算 1000 元内的通勤包，并认为推荐款尺寸偏大。",
        user_goals=["寻找适合通勤的包"],
        explicit_constraints=["预算不超过 1000 元"],
        product_key_information=[
            ProductKeyInformationGroup(
                product_id="tote-large",
                items=[
                    ProductKeyInformation(
                        name="尺寸",
                        value="大号",
                        source_field="description",
                        source_text="黑色大号容量",
                    ),
                    ProductKeyInformation(
                        name="场景",
                        value="通勤",
                        source_field="tags",
                        source_text="通勤",
                    ),
                ],
            )
        ],
        product_feedback=[
            ProductFeedback(
                product_id="tote-large",
                overall="negative",
                aspects=[
                    FeedbackAspect(
                        name="尺寸",
                        value="偏大",
                        polarity="negative",
                    )
                ],
                evidence=[
                    ConversationEvidence(
                        message_id="user-2",
                        quote=quote,
                    )
                ],
                confidence=0.98,
            )
        ],
        general_preferences=[
            GeneralPreference(
                dimension="重量",
                value="偏轻",
                polarity="prefer",
                evidence=[
                    ConversationEvidence(
                        message_id="user-2",
                        quote=quote,
                    )
                ],
                confidence=0.8,
            )
        ],
        unresolved_items=["尚未确认更小尺寸的替代款"],
    )


def test_summary_keeps_final_reason_and_grounded_product_information() -> None:
    digest = assemble_conversation_digest(
        conversation=_conversation(),
        draft=_draft(),
        source_updated_at="2026-11-13T00:05:00.000+00:00",
        generated_at="2026-11-13T02:00:00.000+00:00",
    )

    assert digest.source_updated_at == "2026-11-13T00:05:00.000+00:00"
    assert len(digest.recommendation_rounds) == 1
    product = digest.recommendation_rounds[0].products[0]
    assert product.product.id == "tote-large"
    assert product.reason == "大容量适合携带电脑，且符合通勤场景"
    assert product.reason_source == "semantic_reranker"
    assert product.key_information[0].value == "大号"
    assert digest.product_feedback[0].evidence[0].message_id == "user-2"


def test_summary_rejects_feedback_that_does_not_quote_user_message() -> None:
    with pytest.raises(ConversationSummaryError, match="quote is not present"):
        assemble_conversation_digest(
            conversation=_conversation(),
            draft=_draft("我从来不喜欢黑色"),
            source_updated_at="2026-11-13T00:05:00.000+00:00",
        )


def test_summary_rejects_ungrounded_product_information() -> None:
    draft = _draft()
    draft.product_key_information[0].items[0].source_text = "限量真皮材质"

    with pytest.raises(ConversationSummaryError, match="not grounded"):
        assemble_conversation_digest(
            conversation=_conversation(),
            draft=draft,
            source_updated_at="2026-11-13T00:05:00.000+00:00",
        )


def test_summary_rejects_assistant_text_as_user_evidence() -> None:
    draft = _draft()
    draft.product_feedback[0].evidence[0].message_id = "assistant-2"
    draft.product_feedback[0].evidence[0].quote = "你更希望尺寸小一些"

    with pytest.raises(ConversationSummaryError, match="non-user message"):
        assemble_conversation_digest(
            conversation=_conversation(),
            draft=draft,
            source_updated_at="2026-11-13T00:05:00.000+00:00",
        )


def test_summary_without_product_feedback_keeps_empty_feedback() -> None:
    draft = _draft()
    draft.product_feedback = []
    draft.general_preferences = []

    digest = assemble_conversation_digest(
        conversation=_conversation(),
        draft=draft,
        source_updated_at="2026-11-13T00:05:00.000+00:00",
    )

    assert digest.product_feedback == []
    assert digest.general_preferences == []

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Product(BaseModel):
    id: str
    name: str
    description: str
    price_cents: int
    category: str
    badge: str | None = None
    stock: int | None = None
    tags: list[str] = Field(default_factory=list)
    image_url: str | None = None
    is_ad: bool = False
    ad_label: str | None = None
    ad_id: str | None = None
    campaign_id: str | None = None


class ProductList(BaseModel):
    items: list[Product]
    total: int


class BrowseEvent(BaseModel):
    event_id: str
    product_id: str
    action: Literal["view", "detail_view"]
    occurred_at: str
    dwell_seconds: int = Field(ge=0)
    source_page: str


class OrderItem(BaseModel):
    product_id: str
    name: str
    image_url: str | None = None
    quantity: int = Field(gt=0)
    unit_price_cents: int = Field(ge=0)
    subtotal_cents: int = Field(ge=0)


class ShippingAddress(BaseModel):
    recipient: str
    phone_masked: str
    region: str
    detail: str


class OrderRecord(BaseModel):
    order_id: str
    user_id: int = 1
    status: Literal[
        "pending_payment",
        "paid",
        "completed",
        "cancelled",
        "refunded",
    ]
    ordered_at: str
    address: ShippingAddress | None = None
    subtotal_cents: int = Field(ge=0)
    shipping_fee_cents: int = Field(default=0, ge=0)
    total_cents: int = Field(ge=0)
    items: list[OrderItem]
    preview_path: str | None = None
    paid_at: str | None = None
    expires_at: str | None = None


class CreateOrderItem(BaseModel):
    product_id: str = Field(min_length=1, max_length=100)
    quantity: int = Field(default=1, ge=1, le=99)


class OrderLink(BaseModel):
    order_id: str
    status: Literal[
        "pending_payment",
        "paid",
        "completed",
        "cancelled",
        "refunded",
    ]
    total_cents: int
    preview_path: str
    ordered_at: str


class CartItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)
    added_at: str


class ShoppingCart(BaseModel):
    updated_at: str | None = None
    items: list[CartItem] = Field(default_factory=list)


class AgentProfile(BaseModel):
    user_id: int
    source: Literal["agent_memory"] = "agent_memory"
    preferred_categories: list[str] = Field(default_factory=list)
    preferred_tags: list[str] = Field(default_factory=list)
    avoid_tags: list[str] = Field(default_factory=list)
    budget_hint_cents: int | None = None
    notes: str | None = None
    updated_at: str


class CategoryAffinity(BaseModel):
    category: str
    score: float = Field(ge=0, le=1)


class PlatformProfile(BaseModel):
    user_id: int
    source: Literal["recommendation_platform"]
    segments: list[str] = Field(default_factory=list)
    category_affinity: list[CategoryAffinity] = Field(default_factory=list)
    price_band_cents: tuple[int, int] | None = None
    preferred_tags: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    updated_at: str


class AdInfo(BaseModel):
    is_ad: Literal[True] = True
    ad_id: str
    campaign_id: str
    label: Literal["广告"] = "广告"


class ProductCandidate(BaseModel):
    product: Product
    source: Literal["product_recommendation", "advertisement"]
    score: float = Field(ge=0, le=1)
    matched_signals: list[str] = Field(default_factory=list)
    ad: AdInfo | None = None


class RecommendationDemand(BaseModel):
    query: str = Field(default="", max_length=500)
    category: str | None = Field(default=None, max_length=100)
    min_price_cents: int | None = Field(default=None, ge=0)
    max_price_cents: int | None = Field(default=None, ge=0)
    required_tags: list[str] = Field(default_factory=list)
    excluded_tags: list[str] = Field(default_factory=list)
    scenario: Literal[
        "general",
        "self",
        "gift",
        "replenishment",
    ] = "general"
    usage: str | None = Field(default=None, max_length=500)
    recipient: str | None = Field(default=None, max_length=200)


IntentType = str


class GoalUnderstandingDraft(BaseModel):
    intents: list[IntentType] = Field(min_length=1, max_length=5)
    goal: str = Field(min_length=1, max_length=2_000)
    confidence: float = Field(ge=0, le=1)
    slots: dict[str, object] = Field(default_factory=dict)
    missing_slots: list[str] = Field(default_factory=list)
    requires_clarification: bool = False
    clarification_question: str | None = Field(default=None, max_length=1_000)


class GoalUnderstandingResult(BaseModel):
    primary_intent: IntentType
    intents: list[IntentType] = Field(min_length=1, max_length=5)
    pending_intents: list[IntentType] = Field(default_factory=list)
    goal: str = Field(min_length=1, max_length=2_000)
    confidence: float = Field(ge=0, le=1)
    slots: dict[str, object] = Field(default_factory=dict)
    missing_slots: list[str] = Field(default_factory=list)
    requires_clarification: bool = False
    clarification_question: str | None = Field(default=None, max_length=1_000)
    pending_intent_question: str | None = Field(default=None, max_length=1_000)


class RecommendationSpecHardConstraints(BaseModel):
    category: str | None = Field(default=None, max_length=100)
    min_price_cents: int | None = Field(default=None, ge=0)
    max_price_cents: int | None = Field(default=None, ge=0)
    required_tags: list[str] = Field(default_factory=list)
    excluded_tags: list[str] = Field(default_factory=list)


class RecommendationSpecEvidence(BaseModel):
    source: str = Field(min_length=1, max_length=100)
    observation: str = Field(min_length=1, max_length=500)
    influence: Literal["high", "medium", "low"]


class RecommendationSpec(BaseModel):
    goal_summary: str = Field(min_length=1, max_length=1_000)
    hard_constraints: RecommendationSpecHardConstraints = Field(
        default_factory=RecommendationSpecHardConstraints
    )
    preferred_categories: list[str] = Field(default_factory=list)
    preferred_tags: list[str] = Field(default_factory=list)
    weak_categories: list[str] = Field(default_factory=list)
    negative_tags: list[str] = Field(default_factory=list)
    search_queries: list[str] = Field(min_length=1, max_length=6)
    scenario: Literal[
        "general",
        "self",
        "gift",
        "replenishment",
    ] = "general"
    usage: str | None = Field(default=None, max_length=500)
    recipient: str | None = Field(default=None, max_length=200)
    source_evidence: list[RecommendationSpecEvidence] = Field(
        default_factory=list
    )
    confidence: float = Field(ge=0, le=1)
    missing_information: list[str] = Field(default_factory=list)


SourceStatus = Literal["ok_with_data", "ok_empty", "unavailable"]


class SourceEvidence(BaseModel):
    source: Literal[
        "need",
        "cart",
        "browse",
        "order",
        "agent_profile",
        "platform_profile",
    ]
    signal_score: float = Field(ge=0, le=1)
    weighted_points: float = Field(ge=0, le=100)
    reason: str = Field(min_length=1, max_length=300)


class ScoredProduct(BaseModel):
    product: Product
    channel: Literal["organic", "ad"]
    score: float = Field(ge=0, le=100)
    confidence: Literal["high", "medium", "low"]
    evidence: list[SourceEvidence] = Field(default_factory=list)
    penalties: list[str] = Field(default_factory=list)
    ad: AdInfo | None = None


class RecommendationBatch(BaseModel):
    demand: RecommendationDemand
    organic_candidates: list[ScoredProduct] = Field(default_factory=list)
    ad_candidates: list[ScoredProduct] = Field(default_factory=list)
    cutoff_score: float | None = None
    competitive_ads: list[ScoredProduct] = Field(default_factory=list)
    requires_semantic_ranking: bool = False
    ad_only: bool = False
    source_statuses: dict[str, SourceStatus] = Field(default_factory=dict)
    generated_at: str


class SemanticRankingItem(BaseModel):
    product_id: str = Field(min_length=1, max_length=100)
    channel: Literal["organic", "ad"]
    reason: str = Field(min_length=1, max_length=500)
    environmental_fit: str | None = Field(default=None, max_length=500)


class SemanticRankingResult(BaseModel):
    items: list[SemanticRankingItem] = Field(default_factory=list)
    summary: str = Field(default="", max_length=1_000)


PlanStepStatus = Literal[
    "pending",
    "in_progress",
    "completed",
    "blocked",
    "skipped",
]


class PlanStep(BaseModel):
    step_id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    objective: str = Field(min_length=1, max_length=1_000)
    kind: str | None = Field(default=None, max_length=100)
    depends_on: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)


class Plan(BaseModel):
    plan_id: str = Field(min_length=1, max_length=100)
    goal: str = Field(min_length=1, max_length=1_000)
    steps: list[PlanStep] = Field(min_length=1, max_length=50)


class PlanStepState(BaseModel):
    step_id: str = Field(min_length=1, max_length=100)
    status: PlanStepStatus
    note: str | None = Field(default=None, max_length=2_000)


class PlanState(BaseModel):
    plan: Plan
    status: Literal["active", "completed", "blocked", "cancelled"] = "active"
    current_step_id: str | None = Field(default=None, max_length=100)
    step_states: list[PlanStepState] = Field(default_factory=list)
    summary: str = Field(default="", max_length=2_000)
    next_action: str | None = Field(default=None, max_length=1_000)
    revision: int = Field(default=1, ge=1)
    updated_at: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=100_000)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be blank")
        return value


class ChatResponse(BaseModel):
    reply: str
    products: list[Product]


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=100_000)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content must not be blank")
        return value


class StreamChatRequest(BaseModel):
    conversation_id: str | None = Field(default=None, max_length=64)
    message: str = Field(min_length=1, max_length=100_000)

    @field_validator("message")
    @classmethod
    def stream_message_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be blank")
        return value


class ToolTrace(BaseModel):
    call_id: str | None = None
    tool: str
    arguments: str = ""
    status: Literal["started", "completed", "failed"] = "started"
    summary: str | None = None


class StoredMessage(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    status: Literal["streaming", "completed", "failed"]
    created_at: str
    recommendations: list[Product] = Field(default_factory=list)
    tool_trace: list[ToolTrace] = Field(default_factory=list)
    plan_state: PlanState | None = None
    goal_understanding: GoalUnderstandingResult | None = None
    recommendation_spec: RecommendationSpec | None = None
    orders: list[OrderLink] = Field(default_factory=list)


class ConversationSummary(BaseModel):
    id: str
    title: str
    message_count: int
    created_at: str
    updated_at: str


class ConversationDetail(ConversationSummary):
    messages: list[StoredMessage]


class ConversationList(BaseModel):
    items: list[ConversationSummary]

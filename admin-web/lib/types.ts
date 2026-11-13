export interface ConversationSummaryItem {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ConversationListPayload {
  items: ConversationSummaryItem[];
}

export interface Product {
  id: string;
  name: string;
  description: string;
  price_cents: number;
  category: string;
  badge?: string | null;
  tags?: string[];
  image_url?: string | null;
  is_ad?: boolean;
  ad_label?: string | null;
}

export interface StoredMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  status: "streaming" | "completed" | "failed";
  created_at: string;
  recommendations?: Product[];
  orders?: Array<{
    order_id: string;
    status: string;
    total_cents: number;
    preview_path: string;
  }>;
}

export interface ConversationDetail {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
  messages: StoredMessage[];
}

export interface ProductKeyInformation {
  name: string;
  value: string;
  source_field: string;
  source_text: string;
}

export interface RecommendedProductSummary {
  product: Product;
  key_information: ProductKeyInformation[];
  reason: string | null;
  reason_source: string;
  environmental_fit?: string | null;
}

export interface RecommendationRoundSummary {
  assistant_message_id: string;
  user_request: string;
  ranking_summary: string;
  products: RecommendedProductSummary[];
}

export interface ProductFeedback {
  product_id: string;
  overall: "positive" | "negative" | "neutral" | "mixed" | "unclear";
  aspects: Array<{
    name: string;
    value?: string | null;
    polarity: "positive" | "negative" | "neutral" | "uncertain";
  }>;
  evidence: Array<{
    message_id: string;
    quote: string;
  }>;
  confidence: number;
}

export interface GeneralPreference {
  dimension: string;
  value: string;
  polarity: "prefer" | "avoid";
  evidence: Array<{
    message_id: string;
    quote: string;
  }>;
  confidence: number;
}

export interface ConversationDigest {
  conversation_id: string;
  source_updated_at: string;
  summary: string;
  user_goals?: string[];
  explicit_constraints?: string[];
  recommendation_rounds?: RecommendationRoundSummary[];
  product_feedback?: ProductFeedback[];
  general_preferences?: GeneralPreference[];
  unresolved_items?: string[];
  source_message_ids?: string[];
  generated_at: string;
}

export interface ConversationAdminDetail {
  conversation: ConversationDetail;
  summary: ConversationDigest | null;
}

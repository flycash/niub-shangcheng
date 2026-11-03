import json
import re
from pathlib import Path
from typing import Any, Protocol

from agents import Agent, ModelSettings, RunConfig, Runner
from pydantic import ValidationError

from .llm_config import LLMConfig
from .models import (
    RecommendationBatch,
    ScoredProduct,
    SemanticRankingResult,
)
from .prompt_loader import PromptLoadError, load_prompt


RERANKER_PROMPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "prompts"
    / "recommendation_reranker.md"
)


class SemanticRerankError(Exception):
    """Raised when semantic recommendation reranking cannot be completed."""


class SemanticReranker(Protocol):
    async def rerank(
        self,
        *,
        batch: RecommendationBatch,
        user_request: str,
        environment_context: str | None = None,
    ) -> SemanticRankingResult: ...


def semantic_candidates(batch: RecommendationBatch) -> list[ScoredProduct]:
    candidates = [
        *batch.organic_candidates,
        *batch.competitive_ads,
    ]
    return sorted(
        candidates,
        key=lambda candidate: (
            -candidate.score,
            candidate.channel,
            candidate.product.price_cents,
            candidate.product.id,
        ),
    )


def _json_payload(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < start:
        raise SemanticRerankError("reranker did not return a JSON object")
    try:
        payload = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise SemanticRerankError("reranker returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise SemanticRerankError("reranker JSON must be an object")
    return payload


def validate_semantic_ranking(
    ranking: SemanticRankingResult,
    batch: RecommendationBatch,
) -> SemanticRankingResult:
    candidates = semantic_candidates(batch)
    by_channel_and_id: dict[tuple[str, str], ScoredProduct] = {
        (candidate.channel, candidate.product.id): candidate
        for candidate in candidates
    }

    if len(ranking.items) > 3:
        raise SemanticRerankError("reranker selected more than three products")
    organic_count = sum(
        1 for item in ranking.items if item.channel == "organic"
    )
    ad_count = sum(1 for item in ranking.items if item.channel == "ad")
    if organic_count > 2:
        raise SemanticRerankError("reranker selected more than two organic products")
    if ad_count > 1:
        raise SemanticRerankError("reranker selected more than one ad product")
    if len({item.product_id for item in ranking.items}) != len(ranking.items):
        raise SemanticRerankError("reranker selected duplicate products")
    if (
        ranking.items
        and ranking.items[0].channel == "ad"
        and not batch.ad_only
    ):
        raise SemanticRerankError(
            "ad product cannot be first when organic candidates exist"
        )

    for item in ranking.items:
        if (item.channel, item.product_id) not in by_channel_and_id:
            raise SemanticRerankError(
                f"reranker selected an ineligible product: {item.product_id}"
            )
    return ranking


class AgentSemanticReranker:
    def __init__(self, *, config: LLMConfig, model: Any) -> None:
        self.config = config
        self.model = model

    def _candidates(self, batch: RecommendationBatch) -> list[dict[str, Any]]:
        return [
            {
                **candidate.model_dump(mode="json"),
                "channel": "ad" if candidate.channel == "ad" else "organic",
            }
            for candidate in semantic_candidates(batch)
        ]

    async def rerank(
        self,
        *,
        batch: RecommendationBatch,
        user_request: str,
        environment_context: str | None = None,
    ) -> SemanticRankingResult:
        try:
            instructions = load_prompt(RERANKER_PROMPT_PATH)
        except PromptLoadError as exc:
            raise SemanticRerankError(str(exc)) from exc

        agent = Agent[Any](
            name="recommendation-semantic-reranker",
            instructions=instructions,
            model=self.model,
            model_settings=ModelSettings(
                temperature=self.config.temperature,
                max_tokens=self.config.output_token_limit,
            ),
        )
        payload = {
            "user_request": user_request,
            "demand": batch.demand.model_dump(mode="json"),
            "environment_context": environment_context,
            "cutoff_score": batch.cutoff_score,
            "ad_only": batch.ad_only,
            "source_statuses": batch.source_statuses,
            "candidates": self._candidates(batch),
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
            raise SemanticRerankError(
                "semantic recommendation reranker failed: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        if not isinstance(result.final_output, str):
            raise SemanticRerankError(
                "semantic recommendation reranker returned non-text output"
            )
        try:
            ranking = SemanticRankingResult.model_validate(
                _json_payload(result.final_output)
            )
        except ValidationError as exc:
            raise SemanticRerankError(
                "semantic recommendation reranker returned invalid data"
            ) from exc
        return validate_semantic_ranking(ranking, batch)

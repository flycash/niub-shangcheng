from opentelemetry import metrics
from opentelemetry.metrics import Histogram, MeterProvider


class ObservabilityMetrics:
    def __init__(self, meter: metrics.Meter) -> None:
        self.chat_duration: Histogram = meter.create_histogram(
            "agent.chat.duration",
            unit="s",
            description="End-to-end chat request duration",
        )
        self.chat_requests = meter.create_counter(
            "agent.chat.requests",
            description="Number of chat requests",
        )
        self.stream_disconnects = meter.create_counter(
            "agent.stream.disconnects",
            description="Number of disconnected chat streams",
        )
        self.react_duration: Histogram = meter.create_histogram(
            "agent.react.duration",
            unit="s",
            description="ReAct loop duration",
        )
        self.llm_first_char: Histogram = meter.create_histogram(
            "agent.llm.first_char.duration",
            unit="s",
            description="Time to first visible model character",
        )
        self.llm_first_output: Histogram = meter.create_histogram(
            "agent.llm.first_output.duration",
            unit="s",
            description="Time to first model output",
        )
        self.llm_duration: Histogram = meter.create_histogram(
            "agent.llm.duration",
            unit="s",
            description="Model call duration",
        )
        self.llm_calls = meter.create_counter(
            "agent.llm.calls",
            description="Number of logical model calls",
        )
        self.llm_tokens = meter.create_counter(
            "agent.llm.tokens",
            unit="{token}",
            description="Number of model tokens",
        )
        self.tool_duration: Histogram = meter.create_histogram(
            "agent.tool.duration",
            unit="s",
            description="Tool call duration",
        )
        self.tool_calls = meter.create_counter(
            "agent.tool.calls",
            description="Number of tool calls",
        )

    def record_token_usage(
        self,
        usage: object,
        attributes: dict[str, object],
    ) -> None:
        prompt_tokens = getattr(usage, "input_tokens", 0) or 0
        completion_tokens = getattr(usage, "output_tokens", 0) or 0
        details = getattr(usage, "input_tokens_details", None)
        output_details = getattr(usage, "output_tokens_details", None)
        cached_tokens = getattr(details, "cached_tokens", 0) or 0
        reasoning_tokens = (
            getattr(output_details, "reasoning_tokens", 0) or 0
        )
        for token_type, value in (
            ("input", prompt_tokens),
            ("output", completion_tokens),
            ("cached_input", cached_tokens),
            ("reasoning", reasoning_tokens),
        ):
            if value:
                self.llm_tokens.add(
                    int(value),
                    {**attributes, "token.type": token_type},
                )


_runtime_metrics: ObservabilityMetrics | None = None


def initialize_metrics(provider: MeterProvider) -> ObservabilityMetrics:
    global _runtime_metrics
    _runtime_metrics = ObservabilityMetrics(provider.get_meter("agent-service"))
    return _runtime_metrics


def get_metrics() -> ObservabilityMetrics | None:
    return _runtime_metrics

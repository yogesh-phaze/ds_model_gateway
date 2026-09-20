from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "gateway_http_requests_total",
    "Total HTTP requests processed by the gateway",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "gateway_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)

MODEL_INFLIGHT_REQUESTS = Gauge(
    "gateway_model_inflight_requests",
    "Requests currently in flight per model",
    ["model"],
)

MODEL_INFERENCE_DURATION_SECONDS = Histogram(
    "gateway_model_inference_duration_seconds",
    "Model backend inference duration in seconds",
    ["model"],
)

MODEL_ERRORS_TOTAL = Counter(
    "gateway_model_errors_total",
    "Model backend errors by type",
    ["model", "error_type"],
)

AUTH_FAILURES_TOTAL = Counter(
    "gateway_auth_failures_total",
    "Requests rejected due to missing or invalid API key",
)

RATE_LIMIT_REJECTIONS_TOTAL = Counter(
    "gateway_rate_limit_rejections_total",
    "Requests rejected due to rate limiting",
)

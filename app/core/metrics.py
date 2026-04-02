from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter

from prometheus_client import Counter, Histogram

from app.core.logging import get_logger

REQUEST_COUNT = Counter(
    "emr_http_requests_total",
    "Total HTTP requests handled by the application.",
    ["method", "path", "status_code"],
)

REQUEST_DURATION = Histogram(
    "emr_http_request_duration_seconds",
    "Latency of HTTP requests.",
    ["method", "path"],
)

BUSINESS_OPERATION_COUNT = Counter(
    "emr_business_operations_total",
    "Business operations grouped by service and status.",
    ["service", "operation", "status"],
)

BUSINESS_OPERATION_DURATION = Histogram(
    "emr_business_operation_duration_seconds",
    "Business operation execution time.",
    ["service", "operation"],
)

_business_logger = get_logger("app.business")


@contextmanager
def observe_business_operation(service: str, operation: str, **context: object):
    started_at = perf_counter()
    _business_logger.info(
        "business_operation_started",
        extra={"service": service, "operation": operation, **context},
    )
    try:
        yield
    except Exception:
        BUSINESS_OPERATION_COUNT.labels(
            service=service,
            operation=operation,
            status="error",
        ).inc()
        BUSINESS_OPERATION_DURATION.labels(service=service, operation=operation).observe(
            perf_counter() - started_at,
        )
        _business_logger.exception(
            "business_operation_failed",
            extra={"service": service, "operation": operation, **context},
        )
        raise
    else:
        BUSINESS_OPERATION_COUNT.labels(
            service=service,
            operation=operation,
            status="success",
        ).inc()
        BUSINESS_OPERATION_DURATION.labels(service=service, operation=operation).observe(
            perf_counter() - started_at,
        )
        _business_logger.info(
            "business_operation_succeeded",
            extra={"service": service, "operation": operation, **context},
        )

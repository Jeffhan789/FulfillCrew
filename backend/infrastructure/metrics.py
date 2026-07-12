"""Prometheus metrics for FulfillCrew.

Defines application-level counters, histograms, gauges and info objects.
If ``prometheus_client`` is not installed, lightweight no-op objects are
provided so the rest of the application does not crash.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# 1. Try to import prometheus_client; if unavailable, use lightweight no-ops
# ---------------------------------------------------------------------------

try:
    from prometheus_client import Counter, Histogram, Gauge, Info  # type: ignore[attr-defined]

    _PROMETHEUS_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PROMETHEUS_AVAILABLE = False

    # Lightweight no-op wrappers so the application never crashes on missing deps

    class _NoOpMetric:  # noqa: D101
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def labels(self, **kwargs: Any) -> "_NoOpMetric":
            return self

        def inc(self, amount: float = 1) -> None:
            pass

        def observe(self, amount: float) -> None:
            pass

        def set(self, value: float) -> None:
            pass

        def info(self, value: dict[str, str]) -> None:
            pass

    class Counter(_NoOpMetric):  # noqa: D101
        pass

    class Histogram(_NoOpMetric):  # noqa: D101
        pass

    class Gauge(_NoOpMetric):  # noqa: D101
        pass

    class Info(_NoOpMetric):  # noqa: D101
        pass


# ---------------------------------------------------------------------------
# 2.  Application metrics
# ---------------------------------------------------------------------------

orders_total = Counter(
    "fulfillcrew_orders_total",
    "Total orders processed",
    ["status"],
)

order_processing_duration = Histogram(
    "fulfillcrew_order_processing_seconds",
    "Order processing time in seconds",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

warehouse_bids_total = Counter(
    "fulfillcrew_warehouse_bids_total",
    "Total warehouse bids submitted",
    ["warehouse_id"],
)

fraud_score = Gauge(
    "fulfillcrew_fraud_score",
    "Latest fraud risk score",
    ["order_id"],
)

demand_prediction_mae = Gauge(
    "fulfillcrew_demand_prediction_mae",
    "Current MAE of demand prediction model",
)

fraud_roc_auc = Gauge(
    "fulfillcrew_fraud_detection_auc",
    "Current ROC-AUC of fraud detection model",
)

app_info = Info("fulfillcrew_app", "Application info")
app_info.info({"version": "2.0.0", "name": "FulfillCrew"})

__all__ = [
    "orders_total",
    "order_processing_duration",
    "warehouse_bids_total",
    "fraud_score",
    "demand_prediction_mae",
    "fraud_roc_auc",
    "app_info",
]

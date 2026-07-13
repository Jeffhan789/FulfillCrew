"""Prometheus metrics endpoint for observability.

This module exposes application metrics in the Prometheus exposition format,
which can be scraped by Prometheus server and visualised in Grafana.

Metrics Exposed:
    - fulfillcrew_orders_total          — Counter with status label
    - fulfillcrew_order_processing_seconds — Histogram with predefined buckets
    - fulfillcrew_warehouse_bids_total  — Counter with warehouse_id label
    - fulfillcrew_fraud_score           — Gauge with order_id label
    - fulfillcrew_demand_prediction_mae — Gauge (model quality)
    - fulfillcrew_fraud_detection_auc   — Gauge (model quality)
    - fulfillcrew_app_info             — Info (version metadata)

Graceful Degradation:
    If prometheus_client is not installed, lightweight no-op metrics are
    provided so the application never crashes. This is useful during
    development or in resource-constrained environments.

Interview Note:
    Q: Why Prometheus instead of logging for metrics?
    A: Logs are for debugging individual events. Metrics are for aggregating
       system behaviour over time (e.g., "99th percentile latency"). Prometheus
       is the industry standard for time-series metrics in cloud-native systems.
       
    Q: What is a histogram with buckets?
    A: A histogram divides observations into predefined buckets (e.g., 0.01s,
       0.05s, 0.1s). Prometheus can calculate quantiles (p50, p99) from
       these buckets without storing every single observation.
       
    Q: How would you alert on these metrics?
    A: Use Prometheus Alertmanager with rules like:
       - rate(fulfillcrew_orders_total{status="rejected_out_of_stock"}[5m]) > 10
       → triggers a "low stock" alert
       - histogram_quantile(0.99, rate(fulfillcrew_order_processing_seconds_bucket[5m])) > 2
       → triggers a "high latency" alert
"""

from fastapi import APIRouter, Response

router = APIRouter(tags=["metrics"])

try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

    @router.get("/metrics")
    async def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
except ImportError:
    @router.get("/metrics")
    async def metrics() -> Response:
        return Response(
            content="# prometheus_client not installed\n",
            media_type="text/plain",
        )

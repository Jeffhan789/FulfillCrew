# FulfillCrew ADR-007：采用 structlog + Prometheus + /health 可观测性方案

## 状态
Accepted — v2.0 已实施

## 背景
v1.0 使用 Python 标准库 `logging`，输出格式不统一，难以解析和分析。v2.0 需要：
- 结构化日志（JSON 格式），便于日志聚合（ELK / Loki）
- 应用指标（订单量、处理延迟、欺诈评分、竞价统计）
- 健康检查端点，用于 Docker 和 K8s 探针
- 架构复盘中展示"可观测性（Observability）"意识

## 决策
采用三件套可观测性方案：
1. **structlog** — 结构化日志（JSON 输出）
2. **Prometheus Client** — 应用指标收集
3. **/health 端点** — 综合健康检查（DB + Redis + ML 模型）

## 考虑方案

### 日志方案
| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| **structlog** | 原生 JSON 输出；与 stdlib logging 兼容；Python 社区标准 | 需要额外依赖 | ✅ 选中 |
| Python stdlib logging | 内置；无需依赖 | 结构化需手动格式化；配置复杂 | ❌ 不满足结构化需求 |
| loguru | 现代化 API；自动结构化 | 与 stdlib 不兼容；架构复盘知名度较低 | ❌ 生态不够 |
| ELK 全家桶 | 完整日志平台 | 需要额外部署 ElasticSearch + Logstash + Kibana；过重 | ❌ 过重（仅采集端） |

### 指标方案
| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| **Prometheus Client** | 云原生标准；易集成；Docker 生态支持 | 需要额外服务（Prometheus 服务器）采集 | ✅ 选中（仅客户端） |
| StatsD | 轻量；推模式 | 需额外 StatsD 服务；架构复盘知名度下降 | ❌ 非云原生标准 |
| 自定义内存计数器 | 无依赖 | 非标准；无法对接现有监控体系 | ❌ 不可扩展 |

## 技术细节

### structlog 配置
```python
# backend/infrastructure/logging.py
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,          # 按级别过滤
        structlog.stdlib.add_logger_name,          # 添加 logger 名
        structlog.stdlib.add_log_level,            # 添加级别
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"), # ISO 8601 时间戳
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,      # 异常格式化
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),        # JSON 输出
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

### 日志使用示例
```python
from backend.infrastructure.logging import logger

logger.info(
    "order.created",
    order_id=order_id,
    user_id=request.user_id,
    item_count=sum(item.quantity for item in request.items),
    event="order.created",
)

# 输出示例（JSON）：
# {
#   "event": "order.created",
#   "order_id": "550e8400-e29b-41d4-a716-446655440000",
#   "user_id": "demo-user",
#   "item_count": 3,
#   "timestamp": "2024-07-13T10:30:00.000Z",
#   "logger": "fulfillcrew",
#   "level": "info"
# }
```

### 回退机制（structlog 不可用时）
```python
# 如果环境中没有 structlog，自动回退到 stdlib logging
class _FallbackLogger:
    def info(self, event: str, **kwargs: Any) -> None:
        if kwargs:
            extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
            self._log.log(logging.INFO, "%s | %s", event, extra)
        else:
            self._log.log(logging.INFO, "%s", event)
```

这是为了：**演示代码中"优雅降级"的设计能力**。如果 Docker 镜像未安装 structlog，日志仍然输出，只是格式变为纯文本。

### Prometheus 指标定义
```python
# backend/infrastructure/metrics.py

# Counter: 累计值，只增不减
orders_total = Counter("fulfillcrew_orders_total", "Total orders processed", ["status"])

# Histogram: 分布统计，自动分桶
order_processing_duration = Histogram(
    "fulfillcrew_order_processing_seconds",
    "Order processing time in seconds",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# Gauge: 可增可减的瞬时值
fraud_score = Gauge("fulfillcrew_fraud_score", "Latest fraud risk score", ["order_id"])
demand_prediction_mae = Gauge("fulfillcrew_demand_prediction_mae", "Current MAE of demand prediction model")

# Info: 静态元数据
app_info = Info("fulfillcrew_app", "Application info")
app_info.info({"version": "2.0.0", "name": "FulfillCrew"})
```

### 指标使用示例
```python
# backend/services/order_service.py
async def create_order(self, request):
    start = time()
    # ... 处理逻辑 ...
    
    # 记录订单量
    orders_total.labels(status=order_status).inc()
    
    # 记录处理延迟
    order_processing_duration.observe(time() - start)
    
    # 记录欺诈评分
    fraud_score.labels(order_id=order_id).set(risk_score_val)
```

### 为什么定义这些指标？
| 指标 | 类型 | 用途 | 架构复盘说明 |
|------|------|------|----------|
| `orders_total` | Counter | 监控各状态订单量 | "用 Counter 因为订单量只增不减" |
| `order_processing_duration` | Histogram | 监控 P50/P95/P99 延迟 | "Histogram 自动分桶，Prometheus 可以计算 quantile" |
| `warehouse_bids_total` | Counter | 监控各仓库竞价频率 | "发现某仓库 bid 太少，可能是负载过高" |
| `fraud_score` | Gauge | 最新欺诈评分 | "Gauge 可增可减，适合瞬时值" |
| `demand_prediction_mae` | Gauge | 模型误差 | "监控模型漂移" |
| `fraud_roc_auc` | Gauge | 模型 AUC | "评估模型质量" |

### 健康检查端点
```python
# backend/api/health.py
@router.get("/health", response_model=HealthCheck)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthCheck:
    db_ok = await check_db_connection()
    redis_ok = await check_redis_connection()
    demand_model_ok = await check_demand_model()
    fraud_model_ok = await check_fraud_model()
    
    checks = {
        "database": db_ok,
        "redis": redis_ok,
        "demand_model": demand_model_ok,
        "fraud_model": fraud_model_ok,
    }
    status = "healthy" if all(checks.values()) else "degraded"
    return HealthCheck(status=status, checks=checks)
```

### 健康检查的多重用途
1. **Docker HEALTHCHECK**：容器健康探针
2. **Kubernetes livenessProbe**：容器是否存活
3. **Kubernetes readinessProbe**：容器是否可接收流量
4. **负载均衡器**：判断后端是否可用，自动剔除故障节点
5. **前端展示**：SystemHealthPanel 组件调用此端点展示系统状态

### 指标端点
```python
# backend/api/metrics.py
@router.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

Prometheus 服务器通过轮询 `/metrics` 抓取指标，存储在 TSDB 中，通过 Grafana 可视化。

## 权衡与风险

| 风险 | 缓解措施 |
|------|----------|
| Prometheus 服务器未部署，指标无处展示 | 指标客户端已就绪，架构复盘时可说明"已预留 Prometheus + Grafana 集成路径" |
| structlog JSON 输出在开发环境可读性差 | 开发环境可通过环境变量切换为纯文本格式（未实现，但架构支持） |
| 指标过多影响性能 | 当前指标都是轻量操作（内存计数器），开销可忽略 |
| 健康检查中的模型文件检查过于简单 | 当前仅检查文件存在性；未来可扩展为实际加载验证 |

## 架构复盘要点

### Q1: 什么是结构化日志？为什么不用 printf 风格？
> "结构化日志以 JSON 等机器可读格式输出，每个字段有明确的键。传统 printf 风格如'Order 123 created by user 456' 需要正则解析才能提取 order_id 和 user_id。结构化日志可以直接被 ELK/Loki 索引，支持精确查询如 `order_id=123`。structlog 让我们用 Python 关键字参数写日志，自动输出 JSON。"

### Q2: Counter、Histogram、Gauge 有什么区别？
> "Counter 是只增不减的累计值，如订单总数。Histogram 是分布统计，记录值落在哪个桶里，如请求延迟的 P50/P95。Gauge 是可增可减的瞬时值，如当前内存使用量或最新的欺诈评分。选择正确的类型让 Prometheus 能正确计算聚合。"

### Q3: 健康检查和存活检查（liveness）有什么区别？
> "健康检查是业务层面的：数据库、缓存、模型文件是否就绪。存活检查是系统层面的：进程是否还在运行。在 Kubernetes 中，livenessProbe 失败会重启容器，readinessProbe 失败只是将容器从 Service 端点列表移除。我们的 `/health` 同时服务于两者，但架构复盘中可以区分讨论。"

### Q4: 如果 Prometheus 挂了，应用会受影响吗？
> "不会。Prometheus 是拉模式（pull）采集，应用只是暴露一个 `/metrics` 端点，被动等待被采集。即使 Prometheus 服务器不可用，应用内存中的计数器仍然累计，恢复后可以获取历史数据。这与推模式（如 StatsD）不同，推模式需要网络连接才能上报。"

### Q5: 日志级别在生产环境怎么配置？
> "通过环境变量 `BACKEND_LOG_LEVEL` 控制。开发环境用 `debug`，生产环境用 `info` 或 `warning`。structlog 的 `filter_by_level` 处理器会自动丢弃低于阈值的日志。"

## 相关文件
- `backend/infrastructure/logging.py` — structlog 配置与回退
- `backend/infrastructure/metrics.py` — Prometheus 指标定义
- `backend/api/health.py` — 健康检查端点
- `backend/api/metrics.py` — 指标暴露端点
- `backend/services/order_service.py` — 指标埋点

## 参考
- [structlog 文档](https://www.structlog.org/)
- [Prometheus 最佳实践](https://prometheus.io/docs/practices/)
- [Google SRE Book — Monitoring](https://sre.google/sre-book/monitoring-distributed-systems/)
- [The Three Pillars of Observability](https://www.oreilly.com/library/view/distributed-systems-observability/9781492033431/)

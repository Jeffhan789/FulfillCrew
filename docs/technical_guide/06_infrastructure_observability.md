# 06 基础设施与可观测性 —— 事件总线、日志、指标、健康检查

---

## 1. 事件总线（Event Bus）

### 1.1 为什么需要事件总线？

订单处理中有多个异步步骤（fraud 检测、库存检查、竞价），每个步骤完成后需要：
- 发送 WebSocket 消息给前端
- 记录结构化日志
- 更新 Prometheus 指标

如果不解耦，Service 层需要直接调用 WebSocket、日志、指标模块，形成紧耦合：

```python
# 紧耦合（坏）
async def create_order(self, request):
    # ... 处理逻辑
    await websocket_manager.send_update(...)  # 直接依赖 WebSocket
    logger.info(...)                          # 直接依赖日志
    metrics.orders_total.inc()                # 直接依赖指标
```

事件总线通过 **发布-订阅（Pub/Sub）** 模式解耦：

```python
# 松耦合（好）
await event_bus.publish("order.created", {...})  # 只发事件
# WebSocket 监听器、日志处理器、指标处理器各自订阅处理
```

### 1.2 抽象设计

```python
from abc import ABC, abstractmethod

class EventBus(ABC):
    @abstractmethod
    async def publish(self, channel: str, event: dict) -> None:
        """发布事件，立即返回，不等待处理"""

    @abstractmethod
    async def subscribe(self, channel: str, handler: Callable) -> None:
        """订阅通道，注册处理器"""

    @abstractmethod
    async def close(self) -> None:
        """释放资源"""
```

### 1.3 Redis 实现

```python
class RedisEventBus(EventBus):
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self._redis_url = redis_url
        self._handlers: dict[str, list[Callable]] = {}
        self._listener_task: asyncio.Task | None = None

    async def _listen_loop(self):
        pubsub = await self._get_pubsub()
        await pubsub.subscribe(*self._handlers.keys())
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            channel = message["channel"]
            event = json.loads(message["data"])
            handlers = self._handlers.get(channel, [])
            for handler in handlers:
                if asyncio.iscoroutine(handler):
                    asyncio.create_task(self._run_handler(handler, event))
```

**关键设计**：
- `_listen_loop` 是后台任务，通过 `asyncio.create_task` 启动
- 消息通过 Redis `PUBLISH/SUBSCRIBE` 广播，支持多进程/多节点
- 支持动态订阅：运行时可以新增监听器，自动 `pubsub.subscribe(channel)`

### 1.4 InMemory 回退

```python
class InMemoryEventBus(EventBus):
    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._dispatcher_task: asyncio.Task | None = None

    async def _dispatch_loop(self):
        while not self._closed:
            try:
                channel, event = await asyncio.wait_for(self._queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            handlers = self._handlers.get(channel, [])
            for handler in handlers:
                handler(event)
            self._queue.task_done()
```

**设计意图**：
- 开发/测试环境无需启动 Redis，降低上手门槛
- 工厂函数自动探测 Redis 可用性，不可用时静默降级

```python
async def get_event_bus(redis_url: str | None = None) -> EventBus:
    if redis_url:
        try:
            bus = RedisEventBus(redis_url)
            r = await bus._get_redis()
            await r.ping()  # 连通性检测
            return bus
        except Exception:
            pass  # 回退
    return InMemoryEventBus()
```

**面试表达**："事件总线设计了两层回退：Redis 优先，InMemory 兜底。这体现防御性编程——核心功能不依赖外部服务可用性。如果后续扩展到微服务，Redis pub/sub 天然支持跨进程通信。"

---

## 2. 结构化日志（structlog）

### 2.1 为什么不用 print/logging？

传统日志：
```
2024-01-15 10:23:45 INFO: Order created by demo-user
```

结构化日志：
```json
{
  "event": "order.created",
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "demo-user",
  "item_count": 2,
  "timestamp": "2024-01-15T10:23:45.123Z",
  "level": "info"
}
```

**优势**：
- 每个字段可索引、可过滤、可聚合
- 直接对接 ELK（Elasticsearch + Logstash + Kibana）或 Loki
- 便于做日志分析（如统计某个用户的订单量）

### 2.2 Processor 链

```python
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,        # 按级别过滤
        structlog.stdlib.add_logger_name,        # 添加 logger 名称
        structlog.stdlib.add_log_level,          # 添加日志级别
        structlog.stdlib.PositionalArgumentsFormatter(),  # 格式化位置参数
        structlog.processors.TimeStamper(fmt="iso"),      # ISO 8601 时间戳
        structlog.processors.StackInfoRenderer(),         # 堆栈信息
        structlog.processors.format_exc_info,             # 异常格式化
        structlog.processors.UnicodeDecoder(),            # Unicode 解码
        structlog.processors.JSONRenderer(),              # 输出 JSON
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
)
```

**面试表达**："structlog 的 processor 链是函数式管道设计，每个 processor 接收事件字典、加工后传给下一个。最终 JSONRenderer 输出结构化日志。这种链式处理让日志格式完全可定制，比如我可以插入一个 processor 自动脱敏敏感字段。"

### 2.3 使用示例

```python
from backend.infrastructure.logging import logger

logger.info(
    "order.created",
    order_id=order_id,
    user_id=request.user_id,
    item_count=sum(item.quantity for item in request.items),
    event="order.created",
)
```

输出：
```json
{
  "event": "order.created",
  "order_id": "550e8400...",
  "user_id": "demo-user",
  "item_count": 2,
  "level": "info",
  "timestamp": "2024-01-15T10:23:45.123Z",
  "logger": "fulfillcrew"
}
```

### 2.4 Fallback 机制

如果 structlog 未安装，自动回退到标准库 logging：

```python
try:
    import structlog
    _STRUCTLOG_AVAILABLE = True
except ImportError:
    _STRUCTLOG_AVAILABLE = False

# FallbackLogger 将 kwargs 格式化为 "key=value" 字符串
class _FallbackLogger:
    def info(self, event: str, **kwargs):
        extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
        self._log.log(logging.INFO, "%s | %s", event, extra)
```

**设计意图**：降低依赖门槛，教学环境中不强制安装 structlog。

---

## 3. Prometheus 指标

### 3.1 四大指标类型

| 类型 | 用途 | 示例 |
|------|------|------|
| Counter | 单调递增的计数器 | 订单总数、竞价次数 |
| Gauge | 可增可减的瞬时值 | 当前风险分数、库存数量 |
| Histogram | 采样分布（分桶） | 订单处理耗时 |
| Summary | 滑动时间窗口分位值 | 延迟 P99（本项目未使用） |

### 3.2 定义的指标

```python
orders_total = Counter(
    "fulfillcrew_orders_total",
    "Total orders processed",
    ["status"],  # 标签：按状态分组（created, review_required, rejected_out_of_stock）
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
```

### 3.3 No-op 回退

```python
try:
    from prometheus_client import Counter, Histogram, Gauge, Info
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False
    
    class _NoOpMetric:
        def labels(self, **kwargs): return self
        def inc(self, amount=1): pass
        def observe(self, amount): pass
        def set(self, value): pass
```

**设计意图**：不强制安装 prometheus_client，教学环境轻量运行。

### 3.4 指标暴露

```python
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@router.get("/metrics")
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

Prometheus 服务器定期 `GET /metrics` 拉取数据，存储在 TSDB 中，供 Grafana 可视化。

---

## 4. 健康检查（Health Check）

### 4.1 检查维度

```python
@router.get("/health", response_model=HealthCheck)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthCheck:
    db_ok = await check_db_connection()           # 数据库连通性
    redis_ok = await check_redis_connection()     # Redis 连通性
    demand_model_ok = await check_demand_model()  # ML 模型文件存在性
    fraud_model_ok = await check_fraud_model()    # ML 模型文件存在性

    checks = {
        "database": db_ok,
        "redis": redis_ok,
        "demand_model": demand_model_ok,
        "fraud_model": fraud_model_ok,
    }
    status = "healthy" if all(checks.values()) else "degraded"
    return HealthCheck(status=status, checks=checks)
```

### 4.2 Docker Compose 依赖链

```yaml
backend:
  depends_on:
    postgres:
      condition: service_healthy  # 等 PostgreSQL healthcheck 通过
    redis:
      condition: service_healthy  # 等 Redis healthcheck 通过

frontend:
  depends_on:
    backend:
      condition: service_healthy  # 等后端 healthcheck 通过
```

**启动顺序**：
1. PostgreSQL 启动 → healthcheck `pg_isready` 通过
2. Redis 启动 → healthcheck `redis-cli ping` 通过
3. Backend 启动 → 依赖 postgres 和 redis
4. Frontend 启动 → 依赖 backend

**面试表达**："健康检查不只是返回 200，而是探测所有关键依赖（数据库、缓存、模型文件）。Docker Compose 的 `condition: service_healthy` 让服务按正确顺序启动，避免后端在数据库未就绪时报错。"

---

## 5. WebSocket 实时推送

### 5.1 连接管理

```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, order_id: str):
        await websocket.accept()
        self.active_connections[order_id] = websocket

    def disconnect(self, order_id: str):
        self.active_connections.pop(order_id, None)

    async def send_order_update(self, order_id: str, data: dict):
        if order_id in self.active_connections:
            await self.active_connections[order_id].send_json(data)

manager = ConnectionManager()
```

### 5.2 生命周期

```python
@router.websocket("/ws/orders/{order_id}")
async def websocket_endpoint(websocket: WebSocket, order_id: str):
    await manager.connect(websocket, order_id)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"event": "pong", "order_id": order_id})
    except WebSocketDisconnect:
        manager.disconnect(order_id)
```

**面试表达**："WebSocket 用于订单状态实时推送。每个订单对应一个 WebSocket 连接（按 order_id 隔离）。后端在 Agent 处理每个步骤后主动推送事件，前端通过 `useOrderSocket` hook 接收并更新 UI。这比轮询更高效，延迟从秒级降到毫秒级。"

### 5.3 扩展：心跳机制

当前实现中前端发送消息触发 pong 响应。生产环境应增加：
- **服务端心跳**：每 30 秒发送 `{"event": "ping"}`，客户端回复 `pong`
- **超时断开**：60 秒未收到任何消息，主动关闭连接释放资源
- **重连逻辑**：前端检测到断开后，指数退避重连

---

## 6. 面试高频题

**Q: 事件总线用 Redis pub/sub 还是 Kafka？**

> A: 取决于场景。Redis pub/sub 适合低延迟、简单广播、消息可丢失的场景（如实时通知）。Kafka 适合高吞吐、消息持久化、需要重放历史的场景（如订单流水审计）。本项目用 Redis 是因为简单，且已在 Docker Compose 中部署。如果订单量暴增，可以无缝替换为 Kafka。

**Q: 结构化日志和普通日志在存储成本上有什么区别？**

> A: 结构化日志（JSON）通常比普通文本日志大 20-50%，因为包含大量字段名和引号。但收益是查询效率提升 10-100 倍——可以用 Elasticsearch 的倒排索引秒级搜索任意字段。成本权衡下，结构化日志在生产环境是标准做法。

**Q: Prometheus 是拉（Pull）模式还是推（Push）模式？**

> A: 默认是 Pull 模式——Prometheus 服务器定期从目标 `GET /metrics` 抓取数据。Pull 的优势：1) 目标不需要知道 Prometheus 地址；2) 便于故障检测（抓不到 = 服务可能挂了）；3) 支持多 Prometheus 实例抓取同一目标做高可用。Push 模式通过 Pushgateway 实现，适合短生命周期任务（如批处理作业）。

**Q: 健康检查返回 "degraded" 时，Docker 会做什么？**

> A: Docker 本身的 healthcheck 只认 exit code（0=健康，非0=不健康），不会解析 JSON。`degraded` 是我们应用层的状态语义。Docker 会在 healthcheck 连续失败指定次数后标记容器为 unhealthy，然后根据 `restart` 策略决定是否重启。对于 "degraded"（部分依赖不可用），通常不重启，而是让运维人员介入。

**Q: WebSocket 连接数上限是多少？**

> A: 理论上无上限（协议本身不限），实际受限于：
> 1. 文件描述符（Linux 默认 1024，可改 `ulimit`）
> 2. 内存（每个连接占用约 10-50KB）
> 3. CPU（消息序列化/反序列化）
> Uvicorn 默认单进程，可用 `--workers 4` 启动多进程，但需注意 `ConnectionManager` 的 `active_connections` 是进程内字典，多进程间不共享。解决方案：用 Redis Pub/Sub 广播消息，每个进程订阅 Redis 再推送给本进程的 WebSocket 连接。

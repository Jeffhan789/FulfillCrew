# FulfillCrew 技术原理深度解析

> 深入理解每个核心模块的设计决策、算法原理和工程权衡。

---

## 目录

1. [Contract Net Protocol 简化实现](#1-contract-net-protocol-简化实现)
2. [SQLAlchemy 2.0 Async + Repository 模式](#2-sqlalchemy-20-async--repository-模式)
3. [WebSocket 实时推送机制](#3-websocket-实时推送机制)
4. [Event Bus：Redis / InMemory 双模式设计](#4-event-bus-redis--inmemory-双模式设计)
5. [结构化日志与可观测性](#5-结构化日志与可观测性)
6. [ML 模型推理接口设计模式](#6-ml-模型推理接口设计模式)
7. [Docker Compose 多服务编排原理](#7-docker-compose-多服务编排原理)

---

## 1. Contract Net Protocol 简化实现

### 1.1 理论背景

Contract Net Protocol（合同网协议）由 Smith 于 1980 年提出，是多智能体系统中**任务分配**的经典协议。完整协议包含以下消息类型：

| 消息 | 发送方 | 接收方 | 含义 |
|------|--------|--------|------|
| `call-for-proposal` (CFP) | Manager | All Contractors | 任务招标 |
| `propose` | Contractor | Manager | 投标 |
| `refuse` | Contractor | Manager | 拒绝投标 |
| `accept-proposal` | Manager | Contractor | 授予合同 |
| `reject-proposal` | Manager | Contractor | 拒绝投标 |
| `inform-done` | Contractor | Manager | 任务完成 |
| `failure` | Contractor | Manager | 任务失败 |

### 1.2 FulfillCrew 的简化版

我们的实现保留了核心思想，但做了教学友好的简化：

```
CFP: CoordinatorAgent.request_bids(item_count)
    ├── Warehouse A: bid() → WarehouseBid
    ├── Warehouse B: bid() → WarehouseBid
    └── Warehouse C: bid() → WarehouseBid

Award: min(bids, key=lambda b: b.bid) → winner
```

**省略的部分及理由：**

| 省略内容 | 理由 |
|----------|------|
| `refuse` | 固定 3 个仓库，都参与投标更简单 |
| `reject-proposal` | 最低 bid 直接胜出，无需通知落选者 |
| `inform-done` / `failure` | 履约执行在当前版本中是同步立即完成的 |
| 多轮协商 | MVP 不需要讨价还价机制 |

### 1.3 竞价算法的数学原理

竞价公式是一个**多目标优化问题**的标量化（scalarization）：

```
bid = base + Σ(penalty_i) - Σ(bonus_j)

其中：
  base = 5（固定成本）
  penalty_stock = max(0, Q_ordered - Q_stock) × 2.0
  penalty_workload = workload × 0.8
  penalty_distance = distance × 0.15
  bonus_speed = processing_speed × 1.1
```

**各因子的设计逻辑：**

| 因子 | 系数 | 单位 | 物理意义 |
|------|------|------|----------|
| stock_penalty | 2.0 | £/unit | 缺货导致的紧急采购/调货成本 |
| workload_penalty | 0.8 | £/task | 当前负载对处理效率的影响 |
| distance_penalty | 0.15 | £/km | 运输成本（燃油、人力、车辆折旧） |
| speed_bonus | 1.1 | £/(unit/hr) | 快速处理带来的客户满意度价值 |

**这个公式的本质是：** 将多维能力（库存、负载、距离、速度）映射为一维标量 bid，使得 `min()` 操作有意义。

### 1.4 可解释性设计

每个 bid 都附带 `reason` 字段：

```python
reason = (
    f"workload={self.current_workload}, stock={self.stock_level}, "
    f"distance={self.distance}km, speed={self.processing_speed}; lower bid is better"
)
```

这是 **XAI（可解释 AI）** 的简化实践——即使是一个启发式公式，也要能解释"为什么 Warehouse A 胜出"。

---

## 2. SQLAlchemy 2.0 Async + Repository 模式

### 2.1 SQLAlchemy 2.0 的类型声明式映射

SQLAlchemy 2.0 引入了 `Mapped[T]` 类型注解，这是从 1.x 的声明式基类到**类型驱动**的重大转变：

```python
class ProductORM(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
```

**类型系统的价值：**
- IDE 自动补全和类型检查
- `mypy` 静态分析可以捕获类型错误
- 自动生成的外键类型推断减少人为错误

### 2.2 异步引擎与连接池

```python
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
```

**关键参数解析：**

| 参数 | 默认值 | 作用 |
|------|--------|------|
| `echo=False` | False | 关闭 SQL 输出，生产环境必需 |
| `future=True` | True | 启用 2.0 风格 API |
| `expire_on_commit=False` | True | 提交后不让 ORM 对象过期 |

**为什么 `expire_on_commit=False` 很重要？**

在默认设置（`expire_on_commit=True`）下：
```python
async with session.begin():
    order = await session.get(OrderORM, order_id)
    # commit 后，order 的属性变为 "expired"
# 离开 async context 后访问 order.items → 需要新查询 → 但 session 已关闭 → 异常！
```

设置 `expire_on_commit=False` 后，提交后对象属性保持有效，可以在 session 外安全访问。

### 2.3 selectinload 的 N+1 解决方案

**问题：** 查询订单并访问关联 items：
```python
# N+1 问题
order = await session.get(OrderORM, "order-123")  # 1 次查询
for item in order.items:                          # 触发 N 次查询
    print(item.product_id)
```

**解决：selectinload**
```python
result = await session.execute(
    select(OrderORM)
    .where(OrderORM.order_id == order_id)
    .options(
        selectinload(OrderORM.items),
        selectinload(OrderORM.decisions),
        selectinload(OrderORM.bids),
    )
)
```

**内部执行：**
1. `SELECT * FROM orders WHERE order_id = 'order-123'`
2. `SELECT * FROM order_items WHERE order_id IN ('order-123')`
3. `SELECT * FROM agent_decisions WHERE order_id IN ('order-123')`
4. `SELECT * FROM warehouse_bids WHERE order_id IN ('order-123')`

总共 4 次查询，与 items/decisions/bids 的数量无关。

### 2.4 Repository 模式的实现细节

**核心原则：Repository 不控制事务**

```python
class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_order(self, order: OrderORM) -> OrderORM:
        self.session.add(order)
        await self.session.flush()  # 只 flush，不 commit
        return order
```

**Service 层控制事务：**
```python
async def _persist_order(self, ...):
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        # ... 多个操作
        await session.commit()  # 所有操作原子提交
```

**好处：**
1. 一个业务操作涉及多张表时，要么全部成功，要么全部回滚
2. Repository 可以在不同事务中复用
3. 测试时可以 mock Repository 而不需要真实事务

---

## 3. WebSocket 实时推送机制

### 3.1 WebSocket vs SSE vs 长轮询

| 技术 | 协议 | 方向 | 连接数 | 适用场景 |
|------|------|------|--------|----------|
| WebSocket | WS/WSS | 双向 | 1/客户端 | 实时双向通信、聊天、游戏 |
| SSE | HTTP | 服务端→客户端 | 1/客户端 | 单向推送、股票行情、日志流 |
| 长轮询 | HTTP | 客户端→服务端 | N/客户端 | 兼容性优先、简单场景 |

**FulfillCrew 选择 WebSocket 的原因：**
- 需要双向心跳（前端可以发 ping，后端回复 pong）
- 未来可能扩展为"用户取消订单"等客户端主动操作
- FastAPI 原生支持 WebSocket，实现简单

### 3.2 连接管理器的实现

```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, order_id: str):
        await websocket.accept()
        self.active_connections[order_id] = websocket

    async def send_order_update(self, order_id: str, data: dict):
        if order_id in self.active_connections:
            await self.active_connections[order_id].send_json(data)
```

**单实例限制：**
当前实现将连接存储在**内存字典**中，这意味着：
- 如果启动多个 backend 实例，WebSocket 连接无法共享
- 用户可能连接到 Instance A，但订单更新由 Instance B 处理 → 收不到推送

**生产级方案：Redis Pub/Sub 广播**

```python
# 每个实例订阅 Redis 频道
async def redis_listener():
    pubsub = redis.pubsub()
    await pubsub.subscribe("order_updates")
    async for message in pubsub.listen():
        order_id = message["data"]["order_id"]
        if order_id in manager.active_connections:
            await manager.send_order_update(order_id, message["data"])

# 发布更新
await redis.publish("order_updates", json.dumps(data))
```

### 3.3 消息协议设计

```json
{
  "event": "fraud.checked",
  "order_id": "order-uuid",
  "data": {
    "risk_score": 0.45,
    "fraud_status": "approved",
    "timestamp": "2024-01-15T10:23:45Z"
  }
}
```

**协议设计原则：**
- `event` 字段标识事件类型，便于前端路由处理
- `order_id` 用于验证消息归属
- `data` 包含具体业务数据
- ISO 8601 时间戳，便于排序和时区处理

---

## 4. Event Bus：Redis / InMemory 双模式设计

### 4.1 抽象接口设计

```python
class EventBus(ABC):
    @abstractmethod
    async def publish(self, channel: str, event: dict[str, Any]) -> None: ...
    @abstractmethod
    async def subscribe(self, channel: str, handler: Callable) -> None: ...
    @abstractmethod
    async def close(self) -> None: ...
```

**设计模式：Strategy + Factory**
- `EventBus` 是策略接口
- `RedisEventBus` 和 `InMemoryEventBus` 是具体策略
- `get_event_bus()` 是工厂函数，根据环境自动选择

### 4.2 Redis Pub/Sub 实现

```python
class RedisEventBus(EventBus):
    async def _listen_loop(self) -> None:
        pubsub = await self._get_pubsub()
        await pubsub.subscribe(*self._handlers.keys())
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            channel = message["channel"]
            event = json.loads(message["data"])
            handlers = self._handlers.get(channel, [])
            for handler in handlers:
                # 支持同步和异步 handler
                result = handler(event)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(self._run_handler(handler, event))
```

**关键设计点：**

1. **连接懒加载**：`_get_redis()` 在首次使用时创建连接，避免启动时阻塞
2. **Handler 类型兼容**：同时支持 `def handler(event)` 和 `async def handler(event)`
3. **异常隔离**：单个 handler 异常不影响其他 handler
4. **优雅关闭**：`close()` 方法取消监听任务、关闭连接、释放资源

### 4.3 InMemory 实现

```python
class InMemoryEventBus(EventBus):
    async def _dispatch_loop(self) -> None:
        while not self._closed:
            try:
                channel, event = await asyncio.wait_for(self._queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            handlers = self._handlers.get(channel, [])
            for handler in handlers:
                # ... 调用 handler
            self._queue.task_done()
```

**实现细节：**
- 使用 `asyncio.Queue` 作为事件队列，保证线程安全
- `wait_for(timeout=0.5)` 让循环可以定期检查 `_closed` 标志
- `task_done()` 配合 `queue.join()` 支持优雅关闭时等待未处理事件

### 4.4 自动降级机制

```python
async def get_event_bus(redis_url: str | None = None) -> EventBus:
    if redis_url:
        try:
            bus = RedisEventBus(redis_url)
            r = await bus._get_redis()
            await r.ping()  # 连接测试
            return bus
        except Exception:
            logger.warning("Redis connection failed, falling back to InMemoryEventBus")
    return InMemoryEventBus()
```

**降级策略：**
- 优先尝试 Redis（生产环境）
- 如果 Redis 不可用，自动回退到 InMemory（开发/测试环境）
- 回退时记录 warning 日志，便于排查

---

## 5. 结构化日志与可观测性

### 5.1 structlog 的处理器链

```python
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,      # 按级别过滤
        structlog.stdlib.add_logger_name,      # 添加 logger 名
        structlog.stdlib.add_log_level,        # 添加日志级别
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),  # ISO 8601 时间戳
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,  # 异常信息格式化
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),   # 输出 JSON
    ],
)
```

**处理器链的执行顺序（从上到下）：**
1. 首先过滤掉低于配置级别的日志
2. 添加 logger 名称和日志级别元数据
3. 格式化位置参数
4. 添加时间戳
5. 如果有异常，格式化异常栈
6. 最终输出为 JSON

### 5.2 日志中的结构化上下文

```python
logger.info(
    "order.created",
    order_id=order_id,
    user_id=request.user_id,
    item_count=sum(item.quantity for item in request.items),
    event="order.created",
)
```

**输出示例：**
```json
{
  "event": "order.created",
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "demo-user",
  "item_count": 2,
  "logger": "fulfillcrew",
  "level": "info",
  "timestamp": "2024-01-15T10:23:45.123456Z"
}
```

**可观测性价值：**
- 在 ELK/Loki 中搜索：`event="order.created" AND item_count > 1`
- 统计：`count(event="order.created") by user_id`
- 追踪：同一个 `order_id` 的所有日志构成完整的订单生命周期

### 5.3 Fallback Logger 设计

```python
class _FallbackLogger:
    def _log_with_kwargs(self, level: int, event: str, **kwargs: Any) -> None:
        if kwargs:
            extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
            self._log.log(level, "%s | %s", event, extra)
        else:
            self._log.log(level, "%s", event)

    def info(self, event: str, **kwargs: Any) -> None:
        self._log_with_kwargs(logging.INFO, event, **kwargs)
```

**设计考量：**
- structlog 未安装时（如最小化环境），系统仍然可以运行
- Fallback logger 保持相同的 API：`logger.info("event", key=value)`
- 输出格式兼容：纯文本中 `key=value` 对便于 grep

### 5.4 Prometheus 指标设计

**Counter：单调递增计数器**
```python
orders_total = Counter(
    "fulfillcrew_orders_total",
    "Total orders processed",
    ["status"],  # 标签维度
)
```
使用方式：`orders_total.labels(status="created").inc()`

**Histogram：采样分布**
```python
order_processing_duration = Histogram(
    "fulfillcrew_order_processing_seconds",
    "Order processing time in seconds",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)
```
Prometheus 自动计算：
- `fulfillcrew_order_processing_seconds_count`：总样本数
- `fulfillcrew_order_processing_seconds_sum`：总和
- `fulfillcrew_order_processing_seconds_bucket{le="0.5"}`：≤0.5s 的样本数

**Gauge：当前值**
```python
fraud_score = Gauge(
    "fulfillcrew_fraud_score",
    "Latest fraud risk score",
    ["order_id"],
)
```
注意：Gauge 标签 `order_id` 会导致**高基数问题**（high cardinality），生产环境应谨慎使用。

---

## 6. ML 模型推理接口设计模式

### 6.1 统一接口模式

所有 ML 模块遵循相同的接口契约：

```
输入: dict[str, Any] (特征字典)
输出: Union[int, float, tuple] (预测结果)
fallback: 模型文件不存在时返回启发式结果
```

**Demand Prediction：**
```python
def predict_demand(product_features: Dict[str, Any]) -> int:
    if not MODEL_PATH.exists():
        return _heuristic_fallback(product_features)
    # 加载 PyTorch 模型并推理
```

**Fraud Detection：**
```python
class FraudDetector:
    def __init__(self, model_path: str | None = None):
        if self._model_path.exists():
            self.model = xgb.XGBClassifier()
            self.model.load_model(str(self._model_path))
        else:
            self.model = LightweightFraudClassifier()
```

### 6.2 特征编码的一致性

训练和推理必须使用**相同的特征编码**：

```python
CATEGORY_MAP = {
    "electronics": 1.0,
    "home": 0.5,
}

TYPE_MAP = {
    "device": 1.0,
    "audio": 0.8,
    "lighting": 0.6,
}

def _encode_features(product_features: Dict[str, Any]) -> np.ndarray:
    category_enc = CATEGORY_MAP.get(category, 0.5)
    type_enc = TYPE_MAP.get(type_, 0.6)
    # ... 构建 9 维向量
```

**训练-推理一致性（Training-Serving Skew）是 ML 系统的经典陷阱。** 如果训练时用 one-hot 编码，推理时用 label encoding，模型会输出无意义的结果。

### 6.3 延迟加载与单例模式

```python
def predict_demand(product_features: Dict[str, Any]) -> int:
    # 延迟加载：首次调用时才加载模型
    if not hasattr(predict_demand, "_model"):
        predict_demand._model = load_model(MODEL_PATH)
    model = predict_demand._model
    # ... 推理
```

**设计考量：**
- **启动速度**：应用启动时不需要加载模型，减少启动时间
- **内存效率**：模型只加载一次，作为函数属性（类似单例）
- **线程安全**：`torch.no_grad()` 保证推理时不需要梯度计算，节省内存

### 6.4 SHAP 可解释性集成

```python
def score(self, order_features: dict) -> tuple[float, str, dict[str, float]]:
    X = self._to_array(order_features)
    risk_score = float(self.model.predict_proba(X)[0, 1])

    if self.explainer is not None:
        shap_values = self.explainer.shap_values(X)
        fraud_shap = shap_values[1][0]  # 取 fraud 类别
        shap_explanation = {
            col: round(float(val), 6)
            for col, val in zip(FEATURE_COLUMNS, fraud_shap)
        }

    decision = "review_required" if risk_score >= THRESHOLD else "approved"
    return risk_score, decision, shap_explanation
```

**SHAP 值的意义：**
- 正 SHAP 值 → 该特征推动预测向 fraud 方向
- 负 SHAP 值 → 该特征推动预测向 normal 方向
- 绝对值越大 → 影响越强

---

## 7. Docker Compose 多服务编排原理

### 7.1 服务依赖拓扑

```
postgres (基础存储)
    ↓
redis (缓存/消息)
    ↓
backend (业务逻辑)
    ↓
frontend (静态资源)
```

**为什么是这个顺序？**
- PostgreSQL 和 Redis 是无状态基础设施，最先启动
- Backend 依赖数据库连接和缓存
- Frontend 只依赖 Backend 的 API，不直接访问数据库

### 7.2 健康检查链

```yaml
postgres:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 10s
    timeout: 5s
    retries: 5
    # → 最多 10s × 5 = 50s 判定为 healthy

backend:
  depends_on:
    postgres:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "python", "-c", "urllib.request.urlopen('http://localhost:8000/health')"]
    interval: 30s
    start_period: 5s
    # → start_period 内失败不计入 retries
```

### 7.3 Nginx 作为 API 网关

```nginx
location /api/ {
    proxy_pass http://backend:8000/;
    # 尾部斜杠的关键作用：
    # /api/products → backend:8000/products (正确)
    # 如果没有尾部斜杠：
    # /api/products → backend:8000/api/products (错误)
}
```

**反向代理的隐藏价值：**
1. **统一入口**：前端只认识 Nginx，不需要知道 backend 的地址
2. **SSL 终止**：HTTPS 证书配置在 Nginx，backend 无需处理 TLS
3. **负载均衡**：`upstream backend { server backend1:8000; server backend2:8000; }`
4. **静态缓存**：`expires 1y` 让浏览器缓存 JS/CSS/图片

### 7.4 开发环境 vs 生产环境

| 环境 | 前端端口 | 后端热重载 | 数据库 |
|------|----------|-----------|--------|
| Production | 80 (Nginx) | 否 | PostgreSQL |
| Development | 8080 (Nginx) | 是 (volume mount) | PostgreSQL |
| Manual | 5173 (Vite dev) | 是 (uvicorn --reload) | 本地/远程 |

**docker-compose.dev.yml 的特殊配置：**
```yaml
backend:
  volumes:
    - ./backend:/app/backend:ro  # 只读挂载，代码修改立即生效
    - ./ml_models:/app/ml_models:ro
  command: uvicorn backend.main:app --reload --host 0.0.0.0
```

---

> 技术原理是架构复盘中的"深水区"问题。掌握这些细节，可以让你从"用过"上升到"理解为什么这样设计"。💡

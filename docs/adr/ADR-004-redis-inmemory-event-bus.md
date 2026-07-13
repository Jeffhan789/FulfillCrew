# FulfillCrew ADR-004：采用 Redis / InMemory 双模式事件总线

## 状态
Accepted — v2.0 已实施

## 背景
多智能体系统需要组件间通信：
- 订单创建后，需要通知欺诈检测、库存、仓库竞价等模块
- WebSocket 需要实时推送订单状态更新
- 未来可能需要事件溯源（Event Sourcing）或 Saga 模式

v1.0 使用直接函数调用，智能体之间是紧耦合的。v2.0 需要解耦，同时保持简单（不引入 Kafka/RabbitMQ 等重量级消息队列）。

## 决策
采用 **抽象事件总线（Event Bus）** 设计，支持两种实现：
- **Redis Pub/Sub** — 生产环境，支持跨容器/跨服务通信
- **InMemory asyncio.Queue** — 开发环境，零外部依赖

## 考虑方案

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| **Redis Pub/Sub + InMemory 回退** | 轻量；双模式切换；Redis 在 Docker Compose 中易部署 | Pub/Sub 不持久化（消息不保留） | ✅ 选中 |
| Kafka | 高吞吐；持久化；消费者组 | 过重；需要 ZooKeeper/KRaft；学生项目学习成本高 | ❌ 过重 |
| RabbitMQ | 成熟；AMQP 协议；路由灵活 | 额外容器；配置复杂；对学生不友好 | ❌ 过重 |
| 纯函数调用（v1.0 方式） | 最简单；零延迟 | 紧耦合；无法扩展；无法实时推送 | ❌ 不满足解耦需求 |
| FastAPI 内置 BackgroundTasks | 简单；无需额外组件 | 不适合多步骤工作流；无法跨请求通信 | ❌ 不适合复杂协调 |

## 技术细节

### 抽象基类设计
```python
# backend/infrastructure/event_bus.py
class EventBus(ABC):
    @abstractmethod
    async def publish(self, channel: str, event: dict[str, Any]) -> None:
        """发布事件，不等待处理完成（fire-and-forget）"""

    @abstractmethod
    async def subscribe(self, channel: str, handler: Callable) -> None:
        """订阅通道，新事件到达时调用 handler"""

    @abstractmethod
    async def close(self) -> None:
        """释放资源"""
```

### Redis 实现
```python
class RedisEventBus(EventBus):
    async def publish(self, channel: str, event: dict) -> None:
        r = await self._get_redis()
        await r.publish(channel, json.dumps(event))
    
    async def _listen_loop(self) -> None:
        pubsub = await self._get_pubsub()
        await pubsub.subscribe(*self._handlers.keys())
        async for message in pubsub.listen():
            if message["type"] == "message":
                event = json.loads(message["data"])
                for handler in self._handlers.get(message["channel"], []):
                    asyncio.create_task(self._run_handler(handler, event))
```

### InMemory 实现
```python
class InMemoryEventBus(EventBus):
    def __init__(self) -> None:
        self._queue: asyncio.Queue[tuple[str, dict]] = asyncio.Queue()
    
    async def _dispatch_loop(self) -> None:
        while not self._closed:
            channel, event = await self._queue.get()
            for handler in self._handlers.get(channel, []):
                handler(event)
            self._queue.task_done()
```

### 为什么使用 Pub/Sub 而非 Redis Streams
Redis 提供两种消息机制：
- **Pub/Sub**：广播，不持久化，无消费者组概念
- **Streams**：类似 Kafka 的日志结构，支持消费组和持久化

我们选择 Pub/Sub 的原因：
1. 更轻量，无需管理消费者组 offset
2. 当前场景是"通知"而非"任务队列"（不需要保证送达）
3. Streams 的学习成本更高，对学生项目不友好
4. 未来如需持久化，可以平滑升级到 Streams 或引入 Celery

### 事件通道定义
```python
ORDER_CREATED = "order.created"        # 订单创建
FRAUD_CHECKED = "fraud.checked"        # 欺诈检测完成
INVENTORY_CHECKED = "inventory.checked"  # 库存检查完成
WAREHOUSE_BID = "warehouse.bid"      # 仓库提交竞价
FULFILLMENT_COMPLETED = "fulfillment.completed"  # 履约完成
```

## 当前使用方式（v2.0 实际模式）

值得注意的是，v2.0 中事件总线**已经构建但并未在核心工作流中深度使用**。当前订单工作流仍然是通过 `OrderService` 中的直接函数调用串联的：
```python
# backend/services/order_service.py（实际实现）
async def create_order(self, request):
    # 直接调用，不是通过事件总线
    risk_score = self.fraud_agent.score(...)
    stock_ok = self.inventory_agent.check_stock(...)
    bids = self.coordinator_agent.request_bids(...)
    # ...
```

事件总线主要用于：
1. WebSocket 推送（通过 `manager.send_order_update`）
2. 健康检查中的 Redis 连通性验证
3. 为未来扩展预留（如事件溯源、异步处理）

**设计意图：** 在课程项目中展示"事件驱动架构"的设计能力，同时保持核心工作流的简单可预测。

## 权衡与风险

| 风险 | 缓解措施 |
|------|----------|
| Redis Pub/Sub 消息不持久化 | 当前场景是状态通知，不要求持久化；关键数据已写入 PostgreSQL |
| 事件总线增加了架构复杂度 | 有 InMemory 回退，开发环境无需 Redis 即可运行 |
| handler 异常可能导致事件丢失 | 每个 handler 包装 try/except；不影响其他 handler |
| 没有消费者确认机制 | 这是 Pub/Sub 的限制；如需确认，未来升级到 Redis Streams |

## 面试要点

### Q1: 为什么需要事件总线？直接函数调用不行吗？
> "直接函数调用在简单场景下没问题，但会导致紧耦合。比如库存检查和欺诈检测是独立的，如果直接调用，库存模块要知道欺诈模块的接口。事件总线解耦了它们：欺诈检测完成后发布一个事件，库存模块订阅这个事件。更重要的是，事件总线让 WebSocket 实时推送变得自然——每个智能体步骤完成时都可以广播状态更新。"

### Q2: Redis Pub/Sub 和 Kafka 有什么区别？你们为什么选 Pub/Sub？
> "Redis Pub/Sub 是广播模式，消息不持久化，没有消费者组概念。Kafka 是持久化日志，支持高吞吐、消费者组和重放。我们的场景是'状态通知'而非'任务队列'，不需要保证每条消息都被消费。Redis 更轻量，在 Docker Compose 中只需要一个容器。"

### Q3: 如果 Redis 挂了怎么办？
> "我们的工厂函数 `get_event_bus()` 会在 Redis 连接失败时自动回退到 `InMemoryEventBus`。这意味着在开发环境或 Redis 不可用时，系统仍然可以运行，只是不能跨服务通信。对于单容器部署，InMemory 完全够用。"

### Q4: 事件总线如何保证顺序？
> "Redis Pub/Sub 保证同一 channel 内消息的顺序性。在我们的实现中，每个订单的事件通过不同的 order_id 标识，前端 WebSocket 按时间戳排序。如果需要严格的顺序保证，可以引入 Redis Streams 或 Kafka。"

## 相关文件
- `backend/infrastructure/event_bus.py` — 事件总线实现
- `backend/api/websocket.py` — WebSocket 连接管理
- `backend/infrastructure/health.py` — Redis 健康检查
- `docker-compose.yml` — Redis 服务配置

## 参考
- [Redis Pub/Sub 文档](https://redis.io/docs/manual/pubsub/)
- [asyncio Queue 文档](https://docs.python.org/3/library/asyncio-queue.html)

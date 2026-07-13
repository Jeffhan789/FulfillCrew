# 04 多智能体系统深入 —— Contract Net Protocol 与 Agent 设计

---

## 1. 多智能体系统的核心问题

在分布式系统中，多个独立实体需要：
1. **协作**完成共同目标（订单履约）
2. **自主**决策（每个 Agent 有自己的判断逻辑）
3. **通信**交换信息（通过消息传递）
4. **协调**避免冲突（只有一个仓库能被选中）

本系统使用 **FIPA Contract Net Protocol** 的简化版实现仓库竞价协调。

---

## 2. Contract Net Protocol 原理

### 2.1 协议流程

```text
阶段 1: 任务广播 (Task Announcement)
    Coordinator Agent → 所有 Warehouse Agents
    "有一个订单需要履约，请提交你的 bid"

阶段 2: 投标提交 (Bid Submission)
    Warehouse Agent A → bid = 12.5, reason = "workload=5, stock=80..."
    Warehouse Agent B → bid = 18.3, reason = "workload=2, stock=55..."
    Warehouse Agent C → bid = 25.1, reason = "workload=1, stock=40..."

阶段 3: 投标评估与选择 (Bid Evaluation)
    Coordinator Agent: min(bid) = Warehouse A (12.5)

阶段 4: 结果通知 (Award Notification)
    Coordinator Agent → 所有 Warehouse Agents
    "Warehouse A 中标"
```

### 2.2 为什么是"简化版"？

标准 FIPA CNP 包含：
- 明确的 `CFP` (Call for Proposals) 消息类型
- 超时机制（Agent 必须在 deadline 前回复）
- 拒绝通知（未中标的 Agent 收到 explicit reject）
- 任务确认（中标 Agent 确认接受任务）
- 结果报告（任务完成后报告状态）

本项目的简化：
- 使用 Python 方法调用而非 ACL 消息（因为所有 Agent 在同进程内）
- 无超时（假设计算瞬时完成）
- 隐式拒绝（只有 winner 被记录，其他 Agent 默认未中标）

**面试表达**："我实现了简化的 Contract Net Protocol，核心思想是 Manager 广播任务、Contractor 提交 bid、Manager 按最低 bid 选择 winner。这在单进程内用方法调用模拟，如果部署到分布式环境，可以替换为消息队列（如 RabbitMQ）实现真正的异步通信。"

---

## 3. Agent 基类设计

```python
from backend.database.models import AgentDecision

class BaseAgent:
    name = "Base Agent"

    def log(self, message: str) -> AgentDecision:
        return AgentDecision(agent=self.name, message=message)
```

### 3.1 设计哲学

- **单一职责**：每个 Agent 只负责一个决策点
- **可观测**：所有 Agent 通过 `log()` 方法输出决策日志，形成可审计的决策链
- **可扩展**：新增 Agent 只需继承 `BaseAgent`，不影响现有 Agent

### 3.2 继承体系

```
BaseAgent
├── OrderAgent              # 工作流入口，记录订单接收
├── FraudDetectionAgent   # 欺诈评分（调用 ML 模型）
├── InventoryAgent        # 库存检查与预留
├── CoordinatorAgent      # 仓库竞价协调
├── DemandPredictionAgent # 需求预测（调用 ML 模型）
└── WarehouseAgent        # 仓库实体，独立计算 bid
```

---

## 4. 各 Agent 详细解析

### 4.1 OrderAgent —— 工作流入口

```python
class OrderAgent(BaseAgent):
    name = "Order Agent"
```

**职责**：标记工作流开始，记录订单接收事件。

```python
decision_log = [
    self.order_agent.log(f"Received order from {request.user_id} with {item_count} item(s).")
]
```

### 4.2 FraudDetectionAgent —— 风险评分

```python
class FraudDetectionAgent(BaseAgent):
    name = "Fraud Detection Agent"

    def score(self, features: dict) -> tuple[float, str]:
        risk_score = predict_risk(features)  # 调用 ML 模型
        status = "review_required" if risk_score >= 0.65 else "approved"
        return risk_score, status
```

**特征工程**：
```python
features = {
    "order_total": order_total,           # 订单金额
    "number_of_items": item_count,        # 商品数量
    "average_item_price": average_item_price,  # 平均单价
    "is_new_user": request.is_new_user,  # 是否新用户（风险信号）
    "shipping_distance": request.shipping_distance,  # 配送距离
}
```

**阈值设计**：0.65 是经验阈值，实际生产环境中应通过 ROC 曲线选择最优阈值（最大化 TPR - FPR）。

### 4.3 InventoryAgent —— 库存管理

```python
class InventoryAgent(BaseAgent):
    name = "Inventory Agent"

    def check_stock(self, items: list[BasketItem], products: dict[str, Product]) -> tuple[bool, list[str]]:
        unavailable = []
        for item in items:
            product = products.get(item.product_id)
            if product is None or product.quantity < item.quantity:
                unavailable.append(item.product_id)
        return len(unavailable) == 0, unavailable

    def reserve_stock(self, items: list[BasketItem], products: dict[str, Product]) -> None:
        for item in items:
            product = products[item.product_id]
            product.quantity -= item.quantity
```

**关键点**：
- `check_stock` 是只读操作，不修改数据
- `reserve_stock` 是写操作，只在 fraud 通过后执行
- 分离读写使逻辑更清晰，便于测试和回滚

### 4.4 CoordinatorAgent —— 竞价协调

```python
class CoordinatorAgent(BaseAgent):
    name = "Coordinator Agent"

    def __init__(self) -> None:
        self.warehouses = [
            WarehouseAgent("Warehouse A", "London", current_workload=5, stock_level=80, processing_speed=3.0, distance=8),
            WarehouseAgent("Warehouse B", "Birmingham", current_workload=2, stock_level=55, processing_speed=2.7, distance=22),
            WarehouseAgent("Warehouse C", "Manchester", current_workload=1, stock_level=40, processing_speed=2.1, distance=35),
        ]

    def request_bids(self, item_count: int) -> tuple[list[WarehouseBid], WarehouseBid]:
        bids = [warehouse.bid(item_count) for warehouse in self.warehouses]
        winner = min(bids, key=lambda bid: bid.bid)  # 最低 bid 获胜
        return bids, winner
```

### 4.5 WarehouseAgent —— 竞价策略（核心算法）

```python
@dataclass
class WarehouseAgent:
    warehouse_id: str
    location: str
    current_workload: int
    stock_level: int
    processing_speed: float
    distance: float

    def bid(self, item_count: int) -> WarehouseBid:
        # 惩罚项：库存不足时 penalty 倍增
        stock_penalty = max(0, item_count - self.stock_level) * 2.0
        # 惩罚项：工作量越高，bid 越高
        workload_penalty = self.current_workload * 0.8
        # 惩罚项：距离越远，配送成本越高
        distance_penalty = self.distance * 0.15
        # 奖励项：处理速度越快，bid 越低（更优）
        speed_bonus = self.processing_speed * 1.1
        
        bid_value = round(5 + stock_penalty + workload_penalty + distance_penalty - speed_bonus, 2)
        
        # 适配度：bid 越低，适配度越高（指数映射）
        suitability_score = round(100 / (1 + max(0.1, bid_value)), 1)
        
        reason = (
            f"workload={self.current_workload}, stock={self.stock_level}, "
            f"distance={self.distance}km, speed={self.processing_speed}; lower bid is better"
        )
        
        return WarehouseBid(
            warehouse_id=self.warehouse_id,
            bid=max(0.1, bid_value),  # 保证 bid > 0
            workload=self.current_workload,
            distance=self.distance,
            stock_level=self.stock_level,
            processing_speed=self.processing_speed,
            suitability_score=suitability_score,
            reason=reason,
        )
```

#### 竞价公式拆解

```
bid = 5 (base) 
      + max(0, item_count - stock_level) * 2.0   ← 库存惩罚
      + current_workload * 0.8                   ← 工作量惩罚
      + distance * 0.15                          ← 距离惩罚
      - processing_speed * 1.1                   ← 速度奖励
```

**设计意图**：
- 这是一个**启发式评分函数**（Heuristic Scoring Function），非机器学习模型
- 权重（2.0, 0.8, 0.15, 1.1）是人工调参的经验值
- 生产环境中可用历史数据训练权重（如线性回归或神经网络）

**可解释性**：每个 bid 都附带 `reason` 字符串，说明基于哪些因素计算，这是"可解释 AI"（XAI）的简化版。

### 4.6 DemandPredictionAgent —— 需求预测

```python
class DemandPredictionAgent(BaseAgent):
    name = "Demand Prediction Agent"

    def predict(self, products: list[Product]) -> int:
        return sum(predict_demand(product.model_dump()) for product in products)
```

**注意**：`model_dump()` 是 Pydantic v2 的方法，将对象转换为 dict，便于 ML 模型处理。

---

## 5. OrderService：Agent 编排器

```python
class OrderService:
    def __init__(self, product_service: ProductService) -> None:
        self.product_service = product_service
        self.order_agent = OrderAgent()
        self.inventory_agent = InventoryAgent()
        self.coordinator_agent = CoordinatorAgent()
        self.demand_agent = DemandPredictionAgent()
        self.fraud_agent = FraudDetectionAgent()

    async def create_order(self, request: OrderRequest) -> OrderResponse:
        # 1. 订单创建日志
        # 2. 欺诈检测
        # 3. 库存检查（短路：缺货直接返回）
        # 4. 仓库竞价
        # 5. 需求预测
        # 6. 库存预留（仅 approved）
        # 7. 持久化
        # 8. WebSocket 推送
```

### 5.1 编排顺序的设计理由

```
订单创建 → 欺诈检测 → 库存检查 → 仓库竞价 → 需求预测 → 库存预留 → 持久化
```

- **欺诈检测在库存检查之前**：如果明显欺诈，无需浪费库存查询
- **库存检查在竞价之前**：如果缺货，无需触发仓库计算
- **需求预测在竞价之后**：预测可以基于"已选中的商品"做更精准分析
- **库存预留在最后**：只有 fraud_status == approved 才扣减库存，避免审核中订单占用库存

### 5.2 短路模式（Short-circuit Pattern）

```python
stock_available, unavailable = self.inventory_agent.check_stock(request.items, products)
if not stock_available:
    # 直接返回，跳过后续所有步骤
    return OrderResponse(order_status="rejected_out_of_stock", ...)
```

这是条件逻辑的经典优化，避免不必要的计算。

---

## 6. 决策日志与可审计性

```python
decision_log = [
    AgentDecision(agent="Order Agent", message="Received order from demo-user with 2 item(s)."),
    AgentDecision(agent="Fraud Detection Agent", message="Risk score 0.42; status approved."),
    AgentDecision(agent="Inventory Agent", message="Stock checked: available."),
    AgentDecision(agent="Coordinator Agent", message="Warehouse A submitted bid 12.5 with suitability 88.5. ..."),
    AgentDecision(agent="Coordinator Agent", message="Selected Warehouse A using the lowest-bid policy."),
    AgentDecision(agent="Demand Prediction Agent", message="Predicted next 7-day demand: 145 unit(s)."),
    AgentDecision(agent="Inventory Agent", message="Inventory reserved for approved order."),
]
```

**价值**：
- **调试**：追溯订单处理的每一步
- **审计**：监管要求（如金融电商）
- **面试**：展示系统设计时考虑了可观测性

---

## 7. 面试高频题

**Q: Contract Net Protocol 与拍卖协议（Auction）有什么区别？**

> A: CNP 是**任务分配**协议：Manager 有任务，找最合适的 Contractor 执行。拍卖是**资源分配**协议：多个买家竞争同一资源。CNP 中 Contractor 评估自身能力后提交 bid，Manager 按最优 bid 选择；拍卖中通常是最高价获胜。在仓库场景中，我们用的是 CNP（最低成本中标），但概念上类似反向拍卖（Reverse Auction）。

**Q: 如果 Warehouse Agent 数量从 3 个扩展到 100 个，当前架构有什么问题？**

> A: 当前所有 Agent 在同进程内，100 个 Agent 意味着 100 次方法调用。问题：
> 1. 计算时间线性增长，可能阻塞事件循环
> 2. 无超时机制，某个 Agent 卡住会导致整个订单延迟
> 3. 无容错，某个 Agent 崩溃会影响整个流程
> 改进：使用消息队列（RabbitMQ/Kafka）解耦，每个 Agent 独立进程，带超时和重试；或使用 gRPC 实现真正的分布式 Agent。

**Q: 为什么不用 Reinforcement Learning 训练 Agent？**

> A: RL 需要大量交互数据和环境仿真。本项目是教学级系统，目标是展示协议设计和协调逻辑，而非训练最优策略。如果要引入 RL，可以定义状态（库存、工作量、距离）和动作（bid 值），用历史订单数据训练 Q-learning 或 PPO，但复杂度远超教学范围。

**Q: 竞价函数中的权重是怎么确定的？**

> A: 目前是人工经验值。可以改为数据驱动：收集历史订单数据（实际选择哪个仓库、配送时间、客户满意度），用线性回归或神经网络拟合最优权重，使总成本/满意度最优化。这体现"从启发式到数据驱动"的演进路径。

**Q: 如何保证订单处理的一致性（Consistency）？**

> A: 通过数据库事务保证：订单、订单项、Agent 决策、仓库竞价、库存扣减全部在同一个 `async with AsyncSessionLocal()` 事务中提交。如果任何步骤失败，整个事务回滚。 fraud 检测通过的订单才扣减库存，避免不一致状态。

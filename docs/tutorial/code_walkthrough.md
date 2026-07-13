# FulfillCrew 代码走读指南

> 逐行解读关键代码文件，理解每行代码背后的设计意图。

---

## 目录

1. [OrderService 完整流程走读](#1-orderservice-完整流程走读)
2. [前端 Dashboard 数据流](#2-前端-dashboard-数据流)
3. [ML 模型推理接口设计](#3-ml-模型推理接口设计)
4. [数据库模型与关系映射](#4-数据库模型与关系映射)
5. [测试用例设计思路](#5-测试用例设计思路)

---

## 1. OrderService 完整流程走读

文件：`backend/services/order_service.py`

### 1.1 初始化与依赖注入

```python
class OrderService:
    def __init__(self, product_service: ProductService) -> None:
        self.product_service = product_service
        self.order_agent = OrderAgent()
        self.inventory_agent = InventoryAgent()
        self.coordinator_agent = CoordinatorAgent()
        self.demand_agent = DemandPredictionAgent()
        self.fraud_agent = FraudDetectionAgent()
```

**走读要点：**
- `product_service` 通过构造函数注入——便于测试时替换为 mock
- 每个 Agent 在 `__init__` 中实例化——确保每次 `OrderService` 创建时 Agent 状态干净
- **为什么不把 Agent 做成单例？** 因为每个订单的 Agent 决策应该独立，单例会共享状态

### 1.2 订单创建主流程

```python
async def create_order(self, request: OrderRequest) -> OrderResponse:
    start = time()
    order_id = str(uuid4())
```

- `time()` 记录处理开始时间，用于计算 `order_processing_duration` 指标
- `uuid4()` 生成全局唯一订单 ID，分布式环境下无冲突

```python
    logger.info(
        "order.created",
        order_id=order_id,
        user_id=request.user_id,
        item_count=sum(item.quantity for item in request.items),
        event="order.created",
    )
```

- 结构化日志：每个关键步骤都记录，便于后续追踪和问题排查
- `event="order.created"` 是统一的事件标识符，日志聚合系统可以按此分组

```python
    await manager.send_order_update(order_id, {
        "event": "order.created",
        "order_id": order_id,
        "data": {
            "order_status": "pending",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    })
```

- WebSocket 实时推送：用户刚点击"结账"，前端立即显示"pending"状态
- `timezone.utc` 确保时间戳无时区歧义，ISO 8601 格式便于前端解析

### 1.3 商品加载与订单总价计算

```python
    products = await self.product_service.get_product_map()
    selected_products = [products[item.product_id] for item in request.items if item.product_id in products]
    item_count = sum(item.quantity for item in request.items)
    order_total = round(
        sum(products[item.product_id].price * item.quantity for item in request.items if item.product_id in products),
        2,
    )
    average_item_price = order_total / item_count if item_count else 0
```

- `get_product_map()` 返回 `dict[str, Product]`，O(1) 查找商品
- `if item.product_id in products` 防御式编程：防止前端传入无效 product_id
- `round(..., 2)` 确保金额精确到分，避免浮点误差
- `average_item_price = order_total / item_count if item_count else 0` 防止除零

### 1.4 欺诈检测

```python
    risk_score_val, fraud_status = self.fraud_agent.score(
        {
            "order_total": order_total,
            "number_of_items": item_count,
            "average_item_price": average_item_price,
            "is_new_user": request.is_new_user,
            "shipping_distance": request.shipping_distance,
        }
    )
```

- 特征工程在 Service 层完成：从原始请求中提取 ML 模型需要的特征
- **为什么不把所有字段都传给 Fraud Agent？** Agent 的接口应该稳定，不应暴露原始请求结构

```python
    fraud_score.labels(order_id=order_id).set(risk_score_val)
```

- Prometheus Gauge 记录每个订单的风险评分
- 注意：以 `order_id` 为标签会导致高基数，生产环境应谨慎使用

### 1.5 库存检查分支

```python
    stock_available, unavailable = self.inventory_agent.check_stock(request.items, products)
    if not stock_available:
        # ... 大量缺货处理逻辑
        order_status = "rejected_out_of_stock"
        # ... 构建 OrderORM（无 warehouse、demand=0）
        # ... 持久化
        # ... 返回 OrderResponse
```

- **早返回（Early Return）模式**：缺货时立即终止流程，不执行后续 Agent
- 这种情况下不调用 Coordinator、Demand Prediction——节省计算资源
- `orders_total.labels(status="rejected_out_of_stock").inc()` 记录该状态订单数

### 1.6 仓库竞价

```python
    bids, winner = self.coordinator_agent.request_bids(item_count)
    for bid in bids:
        decision_log.append(
            self.coordinator_agent.log(
                f"{bid.warehouse_id} submitted bid {bid.bid} with suitability {bid.suitability_score}. {bid.reason}."
            )
        )
        warehouse_bids_total.labels(warehouse_id=bid.warehouse_id).inc()
```

- `request_bids` 返回 `(所有 bids, 胜出者)` 的元组
- 遍历所有 bids 记录日志和指标——不只是胜出者，落选的也要记录（用于审计）
- `warehouse_bids_total` 是 Counter，每个仓库的投标次数单调递增

```python
    await manager.send_order_update(order_id, {
        "event": "warehouse.bid",
        "order_id": order_id,
        "data": {
            "bids": jsonable_encoder(bids),
            "winner": winner.warehouse_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    })
```

- `jsonable_encoder` 是 FastAPI 的工具函数，将 Pydantic 模型转为 JSON 可序列化的 dict
- 前端收到此消息后更新 WarehouseBidChart

### 1.7 需求预测

```python
    predicted_demand = self.demand_agent.predict(selected_products)
    restock_recommendation = "restock recommended" if predicted_demand > sum(product.quantity for product in selected_products) else "no restock needed"
```

- `predicted_demand` 是未来 7 天预测销量
- `sum(product.quantity for product in selected_products)` 是当前库存
- 简单规则：预测需求 > 当前库存 → 建议补货

### 1.8 库存预留与状态确定

```python
    if fraud_status == "approved":
        self.inventory_agent.reserve_stock(request.items, products)
        order_status = "created"
    else:
        order_status = "review_required"
```

- **关键业务规则**：只有 fraud approved 的订单才扣减库存
- 如果是 review_required，库存不扣减——人工审核通过后再处理
- 这意味着**订单创建和库存扣减不是原子操作**——生产环境应该用数据库事务

### 1.9 持久化

```python
    async def _persist_order(self, ...):
        async with AsyncSessionLocal() as session:
            order_repo = OrderRepository(session)
            product_repo = ProductRepository(session)
            agent_decision_repo = AgentDecisionRepository(session)
            warehouse_bid_repo = WarehouseBidRepository(session)

            await order_repo.create_order(order_orm)
            await order_repo.add_items(order_orm.order_id, item_orms)
            for dec in decision_orms:
                await agent_decision_repo.save(dec)
            for bid in bid_orms:
                await warehouse_bid_repo.save(bid)

            if update_stock and products and request_items:
                for item in request_items:
                    if item.product_id in products:
                        await product_repo.update_stock(item.product_id, -item.quantity)

            await session.commit()
```

- 所有 Repository 共享同一个 `session`
- `session.commit()` 在最后统一提交——原子性保证
- 如果中间任何一步失败，整个事务回滚
- `update_stock` 的条件判断：只有 approved 订单才扣库存

### 1.10 完整流程图

```
create_order()
├── 生成 order_id (UUID4)
├── 记录日志 + WebSocket 推送 ("pending")
├── 加载商品 + 计算总价
├── Fraud Detection → risk_score, fraud_status
│   ├── 记录 fraud_score Gauge
│   └── WebSocket 推送
├── Inventory Check → stock_available?
│   ├── NO → rejected_out_of_stock（立即返回）
│   └── YES → 继续
├── Coordinator Agent → bids + winner
│   ├── 记录 warehouse_bids_total Counter
│   └── WebSocket 推送
├── Demand Prediction → predicted_demand
├── 确定 order_status (created / review_required)
│   └── approved → reserve_stock()
├── 持久化（PostgreSQL 事务）
│   ├── orders 表
│   ├── order_items 表
│   ├── agent_decisions 表
│   └── warehouse_bids 表
├── 记录 orders_total Counter + order_processing_duration Histogram
├── 记录日志 + WebSocket 推送 ("fulfillment.completed")
└── 返回 OrderResponse
```

---

## 2. 前端 Dashboard 数据流

文件：`frontend/src/main.tsx` + 各 Dashboard 组件

### 2.1 数据获取时机

```tsx
useEffect(() => {
  fetch(`${API_BASE}/products`).then(r => r.json()).then(setProducts);
  fetch(`${API_BASE}/agents/course-map`).then(r => r.json()).then(setCourseMap);
  fetch(`${API_BASE}/agents/model-evaluations`).then(r => r.json()).then(setModelEvaluations);
}, []);
```

- 三个 `fetch` **并行执行**——不互相等待
- 空依赖数组 `[]` 表示只在组件挂载时执行一次
- 每个 `.catch(() => setXxx([]))` 提供失败回退

### 2.2 商品筛选与排序

```tsx
const visibleProducts = useMemo(() => {
  return products
    .filter((product) => product.name.toLowerCase().includes(query.toLowerCase()))
    .filter((product) => !inStockOnly || product.quantity > 0)
    .sort((a, b) => {
      if (sortBy === "name") return a.name.localeCompare(b.name);
      return sortBy === "price" ? a.price - b.price : b.rating - a.rating;
    });
}, [products, query, sortBy, inStockOnly]);
```

- `useMemo` 避免每次渲染都重新过滤排序——仅当依赖变化时重算
- 两个 `filter` 链式调用：先按名称匹配，再按库存过滤
- `sort` 用三元表达式根据 `sortBy` 选择排序逻辑
- `b.rating - a.rating` 降序排列（评分高的在前）

### 2.3 WebSocket 状态消费

```tsx
const { status: wsStatus, connected } = useOrderSocket(order?.order_id || null);
```

- `order?.order_id || null`：没有订单时不创建 WebSocket 连接
- `connected` 布尔值控制 UI 显示 "● Live" 或 "○ Offline"
- `wsStatus` 包含最新的事件数据，用于更新界面

### 2.4 Dashboard Grid 渲染

```tsx
<div className="dashboard-grid">
  <div className="dashboard-card">
    <h3>Risk Score</h3>
    <RiskScoreGauge riskScore={order.risk_score} fraudStatus={order.fraud_status} />
  </div>
  <div className="dashboard-card">
    <h3>Warehouse Bids</h3>
    <WarehouseBidChart bids={order.bids} />
  </div>
  <div className="dashboard-card">
    <h3>Demand Prediction</h3>
    <DemandPredictionChart predictedDemand={order.predicted_demand_next_7_days} recommendation={order.restock_recommendation} />
  </div>
  <div className="dashboard-card">
    <h3>Decision Timeline</h3>
    <OrderStatusTimeline logs={order.decision_log} />
  </div>
</div>
```

- 4 个 Dashboard 组件**独立渲染**，互不阻塞
- 每个组件接收最小必要的数据子集——React props 的单一职责
- 如果某个组件渲染失败，Error Boundary 可以隔离，不影响其他组件

### 2.5 OrderStatusTimeline 组件解析

```tsx
function getAgentMeta(agentName: string) {
  const name = agentName.toLowerCase();
  if (name.includes("order")) return { icon: ClipboardList, color: "#256d57" };
  if (name.includes("inventory")) return { icon: Package, color: "#4e8a7a" };
  if (name.includes("coordinator")) return { icon: Bot, color: "#5b7a9e" };
  if (name.includes("warehouse")) return { icon: Truck, color: "#c9a227" };
  if (name.includes("demand")) return { icon: TrendingUp, color: "#7a5eb5" };
  if (name.includes("fraud")) return { icon: ShieldCheck, color: "#c44536" };
  return { icon: AlertTriangle, color: "#6c7c75" };
}
```

- 通过字符串匹配将 Agent 名称映射到图标和颜色
- `toLowerCase()` 保证大小写不敏感
- 默认回退到 `AlertTriangle`——防御式编程

```tsx
function buildTimeline(logs: DecisionLogEntry[]) {
  const now = Date.now();
  const stepMs = 3500;
  return logs.map((log, i) => {
    const time = new Date(now - (logs.length - i) * stepMs);
    return {
      ...log,
      timeLabel: time.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
      relativeTime: `+${(i * 3.5).toFixed(1)}s`,
    };
  });
}
```

- 生成**合成时间戳**：因为后端日志没有时间戳字段，前端根据日志顺序推算
- `stepMs = 3500` 假设每个 Agent 步骤间隔 3.5 秒
- `relativeTime` 显示相对偏移（如 "+7.0s"）

---

## 3. ML 模型推理接口设计

### 3.1 Demand Prediction 推理流程

文件：`ml_models/demand_prediction/predict.py`

```python
def predict_demand(product_features: Dict[str, Any]) -> int:
    if not MODEL_PATH.exists():
        return _heuristic_fallback(product_features)

    # 延迟加载模型
    if not hasattr(predict_demand, "_model"):
        predict_demand._model = load_model(MODEL_PATH)

    model = predict_demand._model
    vec = _encode_features(product_features)
    tensor = torch.from_numpy(vec).unsqueeze(0)  # (1, 9)

    with torch.no_grad():
        pred = model(tensor).item()

    return max(0, int(round(pred)))
```

**走读要点：**

1. **文件存在检查优先**：`MODEL_PATH.exists()` 是最快的检查，避免不必要的加载
2. **函数属性作为单例缓存**：`predict_demand._model` 是函数的属性，Python 允许这样做。首次调用后模型缓存在函数对象上，后续调用直接复用。
3. **`unsqueeze(0)`**：PyTorch 模型期望 batch 维度。`(9,)` → `(1, 9)`
4. **`torch.no_grad()`**：推理时不需要梯度计算，节省内存和计算
5. **`max(0, int(round(pred)))`**：需求不能为负，四舍五入取整

### 3.2 特征编码一致性

```python
def _encode_features(product_features: Dict[str, Any]) -> np.ndarray:
    price = float(product_features.get("price", 50.0))
    rating = float(product_features.get("rating", 3.0))
    category = str(product_features.get("category", "home")).lower()
    category_enc = CATEGORY_MAP.get(category, 0.5)

    day_of_week = float(product_features.get("day_of_week", 2.0))
    month = float(product_features.get("month", 6.0))
    is_weekend = float(product_features.get("is_weekend", 0.0))

    sales_last_7 = float(product_features.get("sales_last_7_days", quantity * 0.7))
    sales_last_30 = float(product_features.get("sales_last_30_days", quantity * 3.0))
```

- **默认值设计**：每个特征都有合理的默认值，缺失时不会崩溃
- `quantity * 0.7` 假设过去 7 天销量约为当前库存的 70%——业务启发式
- `quantity * 3.0` 假设过去 30 天销量约为当前库存的 3 倍
- 所有值转为 `float`——保证类型一致性

### 3.3 Fraud Detection 的 XGBoost + SHAP

文件：`ml_models/fraud_detection/predict.py`

```python
class FraudDetector:
    def __init__(self, model_path: str | None = None) -> None:
        if self._model_path.exists():
            self.model = xgb.XGBClassifier()
            self.model.load_model(str(self._model_path))
            self.explainer = shap.TreeExplainer(self.model)
            self._is_xgb = True
        else:
            self.model = LightweightFraudClassifier()
            self.explainer = None
            self._is_xgb = False
```

- `_is_xgb` 标志位：避免每次推理都检查文件存在性
- `TreeExplainer` 只在 XGBoost 模式下创建——SHAP 需要树结构

```python
    def score(self, order_features: dict) -> tuple[float, str, dict[str, float]]:
        if self._is_xgb:
            X = self._to_array(order_features)
            risk_score = float(self.model.predict_proba(X)[0, 1])
            # ... SHAP 解释
        else:
            risk_score = self.model.predict_proba(order_features)
            shap_explanation = {}

        decision = "review_required" if risk_score >= THRESHOLD else "approved"
        return risk_score, decision, shap_explanation
```

- `predict_proba(X)[0, 1]`：取第 0 个样本、第 1 类（fraud）的概率
- 返回三元组：`(风险分, 决策, SHAP 解释)`——完整的信息
- fallback 模式下 SHAP 为空 dict——调用方需要处理这种情况

---

## 4. 数据库模型与关系映射

文件：`backend/database/models.py`

### 4.1 订单模型

```python
class OrderORM(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, nullable=False, default="guest")
    order_status: Mapped[str] = mapped_column(String, nullable=False)
    order_total: Mapped[float] = mapped_column(Float, nullable=False)
    selected_warehouse: Mapped[str | None] = mapped_column(String, nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fraud_status: Mapped[str | None] = mapped_column(String, nullable=True)
    predicted_demand: Mapped[int | None] = mapped_column(Integer, nullable=True)
    restock_recommendation: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

- `Mapped[str | None]`：Python 3.10+ 的联合类型语法，表示可为空
- `default=lambda: str(uuid.uuid4())`：lambda 延迟执行，每个实例生成新 UUID
- `server_default=func.now()`：数据库端生成时间戳，避免应用服务器时钟不一致
- `onupdate=func.now()`：每次更新自动更新时间戳

### 4.2 关系映射

```python
    items: Mapped[List["OrderItemORM"]] = relationship(
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    decisions: Mapped[List["AgentDecisionORM"]] = relationship(
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    bids: Mapped[List["WarehouseBidORM"]] = relationship(
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
```

| 参数 | 含义 |
|------|------|
| `back_populates="order"` | 双向关系：OrderItemORM 也有 `order` 属性指向 OrderORM |
| `lazy="selectin"` | 用 SELECT IN 批量加载关联数据 |
| `cascade="all, delete-orphan"` | 删除订单时级联删除所有关联的 items/decisions/bids |

### 4.3 AgentDecision 审计表

```python
class AgentDecisionORM(Base):
    __tablename__ = "agent_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String, ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    decision_type: Mapped[str] = mapped_column(String, nullable=False)
    decision_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- `JSON` 类型：存储灵活的决策数据，无需预定义 schema
- `ondelete="CASCADE"`：删除订单时自动清理决策记录
- 这是**审计追踪（Audit Trail）**设计——每个 Agent 的每个决策都持久化

---

## 5. 测试用例设计思路

文件：`tests/test_agents.py` + `tests/test_api.py`

### 5.1 Agent 层测试

```python
def test_order_service_returns_agent_decisions(order_service: OrderService) -> None:
    result = order_service.create_order(...)
    assert result.order_status in {"created", "review_required"}
    assert result.selected_warehouse is not None
    assert len(result.decision_log) >= 5
    assert len(result.course_trace) == 3
    assert len(result.model_evaluations) == 2
    assert result.bids[0].reason
```

- 测试**结构完整性**：返回的数据结构符合预期
- `>= 5` 而不是 `== 5`：给未来扩展留空间
- `bids[0].reason` 检查可解释性字段存在

```python
def test_order_created_with_approved_fraud_status(order_service: OrderService) -> None:
    request = OrderRequest(
        user_id="trusted-user",
        items=[BasketItem(product_id="p-1001", quantity=1)],
        shipping_distance=5,       # 短距离 = 低风险
        is_new_user=False,         # 老用户 = 低风险
    )
    result = order_service.create_order(request)
    assert result.order_status == "created"
    assert result.fraud_status == "approved"
    assert result.risk_score < 0.65
```

- **测试特定业务规则**：低风险特征组合应该通过欺诈检测
- 显式设置 `shipping_distance=5` 和 `is_new_user=False`——控制变量

```python
def test_order_review_required_high_risk(order_service: OrderService) -> None:
    request = OrderRequest(
        user_id="new-user",
        items=[BasketItem(product_id="p-1002", quantity=5)],  # 多商品
        shipping_distance=50,   # 长距离
        is_new_user=True,       # 新用户
    )
    result = order_service.create_order(request)
    assert result.fraud_status == "review_required"
    assert result.risk_score >= 0.65
```

- **测试边界条件**：高风险特征组合应该触发人工审核
- 这是阈值测试——验证 0.65 的阈值设置合理

```python
def test_inventory_reservation_for_approved_order(order_service: OrderService, valid_order_request: OrderRequest) -> None:
    initial_stock = order_service.product_service.products["p-1001"].quantity
    result = order_service.create_order(valid_order_request)
    if result.order_status == "created":
        assert order_service.product_service.products["p-1001"].quantity == initial_stock - 1
```

- **测试副作用**：库存确实被扣减了
- `if result.order_status == "created"`：只有 approved 的订单才扣库存
- 用 `initial_stock` 快照验证变化量

### 5.2 API 层测试

```python
def test_create_order_invalid_payload(client: TestClient) -> None:
    payload = {
        "user_id": "test-user",
        "items": [],  # 空购物篮
        "shipping_distance": 10,
        "is_new_user": False,
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 422  # Unprocessable Entity
```

- 测试**输入验证**：Pydantic 的 `min_length=1` 应该拒绝空 items
- 422 是 FastAPI/Pydantic 的标准验证错误码

```python
def test_cors_headers_present(client: TestClient) -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
```

- 测试**安全配置**：CORS 中间件是否正确工作
- 使用 `OPTIONS` 预检请求——这是浏览器跨域请求的标准做法

---

> 代码走读是面试准备中最有效的学习方式。建议你打开 IDE，对照这份指南逐行阅读代码，理解每一行背后的"为什么"。🔍

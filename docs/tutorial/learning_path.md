# FulfillCrew 学习路径教程

> 目标：从零开始，按阶段掌握 FulfillCrew（智仓通）的技术栈，能够在架构复盘中清晰讲解每个设计决策。

---

## 学习路线图总览

```
阶段 1: 项目概览与运行（1-2 天）
    ↓
阶段 2: 前端技术栈（2-3 天）
    ↓
阶段 3: 后端 API 与架构（3-4 天）
    ↓
阶段 4: 多智能体系统（3-4 天）
    ↓
阶段 5: 机器学习模块（3-4 天）
    ↓
阶段 6: DevOps 与部署（2-3 天）
    ↓
阶段 7: 架构复盘准备与深度问答（持续）
```

---

## 阶段 1：项目概览与运行（1-2 天）

### 目标
- 理解项目定位：不是一个简单的 CRUD 电商，而是一个**多智能体订单履约系统**
- 成功运行项目，看到完整的下单流程
- 理解三门课程如何映射到代码

### 关键概念

**项目核心理念：**
> 将一个简单的课程作业电商原型，工程化升级为一个完整的订单智能履约系统。

这意味着评审者看到的不是一个"做作业"的项目，而是一个展示了**工程化思维**、**升级迭代能力**的作品。

**三门课程映射：**

| 课程 | 核心概念 | 代码中的体现 |
|------|----------|-------------|
| COMP315 Cloud Computing | 云计算、容器化、数据清洗 | React + FastAPI + Docker + Nginx + 数据清洗管道 |
| COMP310 Multi-Agent Systems | 自主智能体、协商、合同网协议 | 6 个智能体协调履约流程 |
| ELEC320 Neural Networks | MLP、二分类、监督学习 | PyTorch MLP 需求预测 + XGBoost 欺诈检测 + 分类器 |

### 动手实验

1. **Docker 一键运行：**
   ```bash
   cd FulfillCrew
   cp .env.example .env
   docker compose up --build -d
   docker compose ps
   open http://localhost
   ```

2. **走通完整下单流程：**
   - 浏览商品 → 搜索/排序/过滤 → 加入购物篮 → 结账
   - 观察订单结果：warehouse bids、risk score、demand prediction、decision log
   - 打开浏览器 DevTools → Network 面板，观察 API 请求

3. **验证 API 端点：**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/products
   curl http://localhost:8000/agents/course-map
   curl http://localhost:8000/agents/model-evaluations
   ```

### 架构复盘要点
> "这个项目不是普通的电商购物车，它展示了**课程知识的工程化落地**。三门课的核心概念——云计算架构、多智能体协调、神经网络——都被整合在一个可运行的系统中。"

---

## 阶段 2：前端技术栈（2-3 天）

### 目标
- 理解 React 18 + TypeScript + Vite 的技术选型理由
- 掌握 6 个 Dashboard 组件的设计思路
- 理解 WebSocket 实时推送的实现

### 2.1 技术选型深度解析

**为什么选 React 18 + TypeScript + Vite？**

| 技术 | 架构复盘中的回答要点 |
|------|-----------------|
| React 18 | 函数组件 + Hooks 模式，Concurrent Features 为将来升级留空间 |
| TypeScript | 类型安全，接口（`OrderResponse`、`WarehouseBid`）即文档，减少运行时错误 |
| Vite | 比 Create React App 快 10-100 倍的 HMR，原生 ESM，构建产物更小 |
| Recharts | 声明式图表库，6 个 Dashboard 组件统一使用，数据驱动渲染 |
| Lucide React | 轻量级图标，tree-shakeable，按需加载 |

### 2.2 核心组件解析

**main.tsx — 主应用架构：**

这是一个单文件组件架构（Single File Component）的 React 应用，包含：
- **状态管理**：`useState` + `useMemo`（无 Redux，足够轻量）
- **数据获取**：`useEffect` + `fetch`（无 React Query，MVP 足够）
- **实时通信**：`useOrderSocket` 自定义 Hook

```tsx
// 关键状态设计
const [products, setProducts] = useState<Product[]>([]);
const [basket, setBasket] = useState<BasketItem[]>([]);
const [order, setOrder] = useState<OrderResponse | null>(null);

// WebSocket 实时状态
const { status: wsStatus, connected } = useOrderSocket(order?.order_id || null);
```

**为什么用 useState 而不是 Redux/Zustand？**
- 状态层级浅（3-4 个顶层状态）
- 无跨组件深层传递需求
- 架构复盘中可以展示"**根据复杂度选择工具**"的工程判断力

**6 个 Dashboard 组件分工：**

| 组件 | 职责 | 数据流 |
|------|------|--------|
| `OrderStatusTimeline` | 垂直时间线展示 Agent 决策步骤 | `decision_log` → 图标 + 颜色映射 |
| `RiskScoreGauge` | 风险评分仪表盘 | `risk_score` + `fraud_status` → 环形图 |
| `WarehouseBidChart` | 仓库竞价对比 | `bids[]` → 条形图 + 胜出高亮 |
| `DemandPredictionChart` | 需求预测 + 补货建议 | `predictedDemand` → 柱状图 + 参考线 |
| `ModelEvaluationPanel` | ML 模型评估指标展示 | `model_evaluations[]` → 卡片列表 |
| `SystemHealthPanel` | 系统健康状态面板 | `GET /health` → 状态徽章 |

### 2.3 WebSocket 实时通信

**useOrderSocket Hook：**

```typescript
// 核心设计：一个订单对应一个 WebSocket 连接
export function useOrderSocket(orderId: string | null) {
  const [status, setStatus] = useState<SocketMessage | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!orderId) return;  // 无订单时不连接，节省资源
    const ws = new WebSocket(`${WS_BASE}/ws/orders/${orderId}`);
    ws.onopen = () => setConnected(true);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStatus(data);
    };
    return () => ws.close();  // 清理：组件卸载时关闭连接
  }, [orderId]);

  return { status, connected };
}
```

**架构复盘必问：为什么 WebSocket 而不是轮询？**
- 轮询：客户端每隔 N 秒请求一次，浪费带宽和服务器资源
- WebSocket：服务端推送，即时、单向（服务端→客户端）、连接复用
- 订单状态变更是**事件驱动**的，不是时间驱动的

**WebSocket 后端实现（FastAPI）：**

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

> 注意：这里用的是**内存中的字典**管理连接，生产环境可替换为 Redis Pub/Sub 实现多实例共享。

### 2.4 动手实验

1. **修改排序逻辑**：在 `main.tsx` 中添加一个"按库存排序"选项
2. **添加 Loading 状态**：在 `fetch` 请求期间显示 loading spinner
3. **WebSocket 调试**：在浏览器 Console 中观察 WebSocket 消息流

### 架构复盘要点
> "前端采用**轻量级状态管理**（useState/useMemo）而非重型状态库，因为状态层级浅。Dashboard 组件用 **Recharts 声明式渲染**，6 个组件统一数据流。WebSocket 提供**实时订单状态推送**，替代了低效的轮询机制。"

---

## 阶段 3：后端 API 与架构（3-4 天）

### 目标
- 掌握 FastAPI 异步架构
- 理解 SQLAlchemy 2.0 async + Repository 模式
- 掌握 Pydantic Schema 验证层
- 理解依赖注入和生命周期管理

### 3.1 FastAPI 应用入口（main.py）

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application_startup", event="startup")
    await init_db()  # 启动时创建表
    yield
    logger.info("application_shutdown", event="shutdown")

app = FastAPI(
    title="Cloud Multi-Agent E-Commerce Intelligence System",
    lifespan=lifespan,
)
```

**架构复盘要点：为什么用 `lifespan` 而不是 `on_event`？**
- `on_event("startup")` / `on_event("shutdown")` 在 FastAPI 0.95+ 已标记为弃用
- `lifespan` 是 ASGI 标准，支持异步上下文管理，更现代、更规范

**CORS 配置：**
```python
default_origins = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:8080",   # Docker dev frontend
    "http://localhost",        # Nginx production
]
```

> 架构复盘中说：CORS 配置**区分了开发环境和生产环境**，Docker 内外网络不同，不能一刀切。

### 3.2 SQLAlchemy 2.0 Async + Repository 模式

**SQLAlchemy 2.0 新特性：**

```python
class ProductORM(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    # ...
    order_items: Mapped[List["OrderItemORM"]] = relationship(
        back_populates="product", lazy="selectin"
    )
```

**架构复盘要点：**
- `Mapped[T]` 类型注解：SQLAlchemy 2.0 的**类型声明式映射**，IDE 友好
- `lazy="selectin"`：避免 N+1 查询，用 `SELECT IN` 批量加载关联数据
- `cascade="all, delete-orphan"`：删除订单时自动删除关联的 items/decisions/bids

**Repository 模式：**

```python
class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_order(self, order: OrderORM) -> OrderORM:
        self.session.add(order)
        await self.session.flush()
        return order

    async def get_by_id(self, order_id: str) -> OrderORM | None:
        result = await self.session.execute(
            select(OrderORM)
            .where(OrderORM.order_id == order_id)
            .options(
                selectinload(OrderORM.items),
                selectinload(OrderORM.decisions),
                selectinload(OrderORM.bids),
            )
        )
        return result.scalar_one_or_none()
```

**架构复盘必问：Repository 模式的优势？**
1. **抽象数据访问**：业务逻辑不直接操作 SQL/ORM，便于切换数据库
2. **测试友好**：可以 mock Repository 而不是 mock 整个数据库
3. **事务边界清晰**：Repository 的方法内部不处理 commit，由调用方控制事务

**数据库引擎配置：**
```python
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
```

> `expire_on_commit=False`：提交后不让对象过期，避免 async 上下文中的意外查询。

### 3.3 Pydantic Schema 验证层

```python
class OrderRequest(BaseModel):
    user_id: str = "guest"
    items: list[BasketItem] = Field(min_length=1)  # 至少一个商品
    shipping_distance: float = Field(default=12.0, ge=0)  # 非负
    is_new_user: bool = True
```

**架构复盘要点：**
- Pydantic v2 的 `Field()` 验证：在请求到达业务逻辑之前就拒绝无效数据
- FastAPI 自动将 Pydantic 模型转换为 OpenAPI Schema，生成 `/docs` 交互文档
- 类型安全：`OrderResponse` 严格定义了 API 返回的字段，前后端契约清晰

### 3.4 服务层与依赖注入

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

**设计模式：Service 层聚合 Agent**
- `OrderService` 不直接处理 Agent 细节，而是**编排**它们
- 每个 Agent 是独立可测试的单元
- 新增 Agent 时只需修改 Service 的 `__init__` 和 `create_order` 方法

### 3.5 动手实验

1. **添加一个 Repository 方法**：在 `OrderRepository` 中添加 `get_orders_by_user(user_id)`
2. **添加一个 API 端点**：在 `orders.py` 中添加 `GET /orders/{order_id}`
3. **修改 Schema 验证**：在 `OrderRequest` 中添加 `shipping_address` 字段并验证不为空

### 架构复盘要点
> "后端采用 **FastAPI 异步架构**，SQLAlchemy 2.0 的 `Mapped` 类型注解配合 `selectinload` 避免 N+1。Repository 模式抽象了数据访问层，Pydantic Schema 在请求入口就完成验证。Service 层作为**编排器**协调多个 Agent，保持了关注点分离。"

---

## 阶段 4：多智能体系统（3-4 天）

### 目标
- 理解 Contract Net Protocol（合同网协议）
- 掌握 6 个 Agent 的职责和协作流程
- 理解为什么用多智能体而不是单一服务函数

### 4.1 Contract Net Protocol 简化版

**什么是 Contract Net Protocol？**

合同网协议是多智能体系统中经典的**任务分配与协商**机制：
1. **Manager**（协调者）发布任务招标（announce）
2. **Contractors**（竞标者）评估自身能力并提交报价（bid）
3. **Manager** 选择最优报价并授予合同（award）
4. **Contractor** 执行合同并报告结果

**在 FulfillCrew 中的简化实现：**

```
Coordinator Agent (Manager)
    ├── announce: "需要履约订单，包含 X 件商品"
    ├── Warehouse A bid: 15.2 (workload=5, stock=80, distance=8km, speed=3.0)
    ├── Warehouse B bid: 18.5 (workload=2, stock=55, distance=22km, speed=2.7)
    ├── Warehouse C bid: 22.1 (workload=1, stock=40, distance=35km, speed=2.1)
    └── award: Warehouse A (lowest bid)
```

**核心代码（CoordinatorAgent）：**

```python
class CoordinatorAgent(BaseAgent):
    def __init__(self) -> None:
        self.warehouses = [
            WarehouseAgent("Warehouse A", "London", current_workload=5, ...),
            WarehouseAgent("Warehouse B", "Birmingham", current_workload=2, ...),
            WarehouseAgent("Warehouse C", "Manchester", current_workload=1, ...),
        ]

    def request_bids(self, item_count: int) -> tuple[list[WarehouseBid], WarehouseBid]:
        bids = [warehouse.bid(item_count) for warehouse in self.warehouses]
        winner = min(bids, key=lambda bid: bid.bid)  # 最低竞价胜出
        return bids, winner
```

**架构复盘必问：为什么选择最低竞价而不是加权评分？**
- 最低竞价是**最直接、最可解释**的策略
- 加权评分需要调参，且参数选择主观
- 竞价公式本身已经包含了 workload、stock、distance、speed 的加权
- 系统可扩展：未来可以改为多目标优化（Pareto frontier）

### 4.2 竞价公式详解

```python
def bid(self, item_count: int) -> WarehouseBid:
    stock_penalty = max(0, item_count - self.stock_level) * 2.0
    workload_penalty = self.current_workload * 0.8
    distance_penalty = self.distance * 0.15
    speed_bonus = self.processing_speed * 1.1
    bid_value = round(5 + stock_penalty + workload_penalty + distance_penalty - speed_bonus, 2)
    suitability_score = round(100 / (1 + max(0.1, bid_value)), 1)
```

**每个因子的意义：**

| 因子 | 系数 | 逻辑 |
|------|------|------|
| 基础值 | 5.0 | 固定成本，确保 bid 始终为正 |
| stock_penalty | 2.0 | 库存不足时惩罚：缺 N 件罚 2N |
| workload_penalty | 0.8 | 工作量越高，处理能力越差 |
| distance_penalty | 0.15 | 距离越远，配送成本越高 |
| speed_bonus | 1.1 | 处理速度越快， bid 越低（负向） |

> **架构复盘要点**：这是一个**启发式评分函数**（heuristic scoring function），不是训练出来的模型。它展示了"在没有训练数据时，如何用领域知识设计可解释的决策逻辑"。

### 4.3 6 个 Agent 的完整协作流程

```
┌─────────────┐
│  OrderAgent │  接收订单，记录日志
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  FraudDetectionAgent │  评分：risk_score = predict_risk(features)
│                      │  阈值 0.65 → approved / review_required
└──────┬───────────────┘
       │
       ▼
┌─────────────────────┐
│  InventoryAgent     │  检查库存：products.get(item.product_id).quantity >= item.quantity
│                      │  缺货 → 直接返回 rejected_out_of_stock
└──────┬───────────────┘
       │ (库存充足)
       ▼
┌─────────────────────┐
│  CoordinatorAgent   │  发布任务 → 收集 3 个 Warehouse 的 bids
│                      │  选择最低 bid
└──────┬───────────────┘
       │
       ▼
┌─────────────────────┐
│  DemandPredictionAgent│ 预测未来 7 天需求
│                      │  restock_recommendation 基于预测 vs 库存
└──────┬───────────────┘
       │
       ▼
┌─────────────────────┐
│  InventoryAgent       │  如果 fraud_status == approved，预留库存
└─────────────────────┘
```

**为什么不是单一函数而是多个 Agent？**

| 维度 | 单一函数 | 多智能体 |
|------|----------|----------|
| 可测试性 | 一个 400 行函数，难以测试 | 每个 Agent 独立可测 |
| 可扩展性 | 新增逻辑需要修改核心函数 | 新增 Agent 只需在 Service 中注册 |
| 可解释性 | 日志混在一起 | 每个 Agent 的决策独立记录 |
| 课程映射 | 无法对应 COMP310 | 直接对应 Multi-Agent Systems 课程内容 |
| 替换能力 | 改一处可能影响全局 | 替换 Fraud Detection Agent 不影响其他 Agent |

> **架构复盘金句**："多智能体架构不是过度设计，而是**课程知识的直接映射**。COMP310 讲的就是自主 Agent 协商，代码里就是 6 个 Agent 协作。"

### 4.4 Agent 决策日志（决策可解释性）

```python
def _course_trace(self) -> list[AgentDecision]:
    return [
        AgentDecision(
            agent="COMP315 Cloud Computing",
            message="Frontend, FastAPI backend, API boundaries and Docker...",
        ),
        AgentDecision(
            agent="COMP310 Multi-Agent Systems",
            message="Order, Inventory, Coordinator and Warehouse agents cooperate...",
        ),
        AgentDecision(
            agent="ELEC320 Neural Networks",
            message="Demand and fraud modules expose training/online inference...",
        ),
    ]
```

**为什么每个订单都返回 course_trace？**
- 这是一个**教学/展示项目**，需要向用户（和评审者）证明系统设计是有理论依据的
- `course_trace` 不是业务逻辑，是**元数据**——证明"这不是拍脑袋做的"

### 4.5 动手实验

1. **修改竞价公式**：添加一个新的因子（如"天气因子"），观察 bid 变化
2. **添加新 Agent**：创建一个 `ShippingAgent`，负责选择物流方式
3. **修改 Fraud 阈值**：将 0.65 改为 0.5，观察订单状态变化

### 架构复盘要点
> "订单履约流程采用**简化版 Contract Net Protocol**：Coordinator Agent 发布任务，3 个 Warehouse Agent 基于 workload、stock、distance、speed 计算可解释竞价，最低 bid 胜出。6 个 Agent 各司其职，Fraud → Inventory → Coordinator → Demand 形成**流水线式决策链**。每个 Agent 的决策独立记录，保证了可解释性。"

---

## 阶段 5：机器学习模块（3-4 天）

### 目标
- 理解 PyTorch MLP 需求预测模型
- 理解 XGBoost + SHAP 欺诈检测模型
- 理解"训练模式/在线模式"接口设计
- 掌握模型推理接口的 fallback 机制

### 5.1 Demand Prediction — PyTorch MLP

**模型架构（`DemandMLP`）：**

```python
class DemandMLP(nn.Module):
    def __init__(self, input_dim: int = 9) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),   # 输入层 → 隐藏层 1
            nn.ReLU(),
            nn.Dropout(0.2),            # 防止过拟合
            nn.Linear(64, 32),          # 隐藏层 1 → 隐藏层 2
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1),           # 输出层：预测销量
        )
```

**输入特征（9 维）：**

| 特征 | 维度 | 含义 |
|------|------|------|
| price | 1 | 商品价格 |
| rating | 1 | 商品评分 |
| category_enc | 1 | 品类编码（electronics=1.0, home=0.5） |
| type_enc | 1 | 类型编码（device=1.0, audio=0.8） |
| day_of_week | 1 | 星期几（0-6） |
| month | 1 | 月份（1-12） |
| is_weekend | 1 | 是否周末（0/1） |
| sales_last_7_days | 1 | 过去 7 天销量 |
| sales_last_30_days | 1 | 过去 30 天销量 |

**Fallback 机制：**

```python
def predict_demand(product_features: Dict[str, Any]) -> int:
    if not MODEL_PATH.exists():
        return _heuristic_fallback(product_features)  # 无模型时走启发式
    # ... 加载 PyTorch 模型并推理
```

> **架构复盘要点**：这种设计叫做 **Graceful Degradation（优雅降级）**。系统在没有训练好的模型时仍能运行，用启发式函数替代。这保证了 MVP 可立即运行，同时为后续模型升级预留接口。

### 5.2 Fraud Detection — XGBoost + SHAP

**模型架构：**
- 训练好的模型：`fraud_xgb.json`（XGBoost 二进制分类器）
- 解释器：`shap.TreeExplainer`（基于博弈论的特征重要性解释）
- Fallback：`LightweightFraudClassifier`（逻辑式启发式评分器）

**特征列：**

```python
FEATURE_COLUMNS = [
    "order_total", "number_of_items", "average_item_price",
    "is_new_user", "account_age_days", "shipping_distance",
    "billing_shipping_match", "order_hour", "is_night_order",
    "orders_in_last_hour",
]
```

**SHAP 解释：**

```python
shap_values = self.explainer.shap_values(X)
# TreeExplainer.shap_values 返回 [normal, fraud] 列表
fraud_shap = shap_values[1][0]
shap_explanation = {
    col: round(float(val), 6)
    for col, val in zip(FEATURE_COLUMNS, fraud_shap)
}
```

> **架构复盘要点**：SHAP（SHapley Additive exPlanations）基于**博弈论中的 Shapley 值**，计算每个特征对预测结果的边际贡献。这满足了**模型可解释性**的需求——不仅是"这个订单有风险"，还要解释"为什么"。

**风险评分计算（启发式 Fallback）：**

```python
logit = (
    -3.4
    + 0.004 * order_total
    + 0.08 * number_of_items
    + 0.003 * average_item_price
    + 0.75 * is_new_user
    + 0.006 * shipping_distance
)
risk_score = 1 / (1 + math.exp(-logit))  # Sigmoid 激活
```

**系数解读：**
- `is_new_user` 系数 0.75 最大：新用户风险最高
- `order_total` 系数 0.004：订单金额影响较小
- 负截距 -3.4：基准风险较低，需要多个因素叠加才会触发 review

### 5.3 "训练模式 / 在线模式"接口设计

```python
class ModelEvaluation(BaseModel):
    model_name: str
    course_topic: str
    metric: str
    score: float
    interpretation: str
    training_mode: str      # 如何在历史数据上训练
    online_mode: str        # 结账时如何调用
```

**为什么每个模型都暴露这两种模式？**

| 模式 | 用途 | 说明 |
|------|------|------|
| training_mode | 展示理论理解 | "用历史特征训练回归权重"——证明你知道怎么训练 |
| online_mode | 展示工程理解 | "在结账时调用模型预测"——证明你知道怎么部署 |

> **架构复盘金句**："每个 ML 模块都设计了**稳定的推理接口**，包含 `training_mode` 和 `online_mode` 描述。这意味着即使现在用的是启发式 fallback，后续替换为真实训练模型时，**Agent 契约不需要改变**。"

### 5.4 动手实验

1. **训练一个 Fraud 模型**：用 scikit-learn 生成模拟数据，训练 XGBoost 并保存为 `fraud_xgb.json`
2. **修改 MLP 架构**：将 `DemandMLP` 的隐藏层从 [64, 32] 改为 [128, 64, 32]，观察推理速度
3. **SHAP 可视化**：在 Jupyter Notebook 中加载 TreeExplainer，绘制 SHAP summary plot

### 架构复盘要点
> "需求预测使用 **PyTorch MLP**（2 隐藏层 + Dropout），输入 9 维特征，输出未来 7 天销量。欺诈检测使用 **XGBoost + SHAP**，XGBoost 提供高准确率的二分类，SHAP 提供基于博弈论的特征可解释性。每个模型都设计了 **fallback 机制**（启发式函数），确保无训练模型时系统仍可运行。"

---

## 阶段 6：DevOps 与部署（2-3 天）

### 目标
- 理解 Docker 多阶段构建
- 掌握 Docker Compose 服务编排
- 理解 Nginx 反向代理配置
- 掌握健康检查和监控指标

### 6.1 Docker 多阶段构建

**前端 Dockerfile（多阶段）：**

```dockerfile
# ---- Build stage ----
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ENV VITE_API_BASE=/api
RUN npm run build

# ---- Runtime stage ----
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

**架构复盘要点：**
- 多阶段构建的核心优势：**构建产物（node_modules、TypeScript 编译器）不进入最终镜像**
- 最终镜像只包含 Nginx + 静态文件，体积极小（~20MB vs 几百MB）
- 攻击面更小：运行时不包含 npm、node 等工具

**后端 Dockerfile：**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6.2 Docker Compose 服务编排

```yaml
services:
  postgres:
    image: postgres:15-alpine
    # ...
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]

  redis:
    image: redis:7-alpine
    # ...

  backend:
    build:
      context: .
      dockerfile: Dockerfile
    depends_on:
      postgres:
        condition: service_healthy  # 关键：等 PostgreSQL 就绪后再启动
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "urllib.request.urlopen('http://localhost:8000/health')"]

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    depends_on:
      backend:
        condition: service_healthy
```

**架构复盘要点：**
- `condition: service_healthy` 是 Docker Compose 3.20+ 的特性，确保**依赖服务真正就绪**才开始启动
- 没有 `depends_on` 的 `condition`，服务可能启动了但数据库还没准备好，导致连接失败
- 健康检查链：`postgres → redis → backend → frontend`，形成**有序启动**

### 6.3 Nginx 反向代理配置

```nginx
location /api/ {
    proxy_pass http://backend:8000/;  # 注意尾部斜杠！
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**关键配置解析：**

| 配置 | 作用 |
|------|------|
| `proxy_pass http://backend:8000/` | 反向代理到后端服务（Docker 网络内 DNS 解析） |
| `proxy_http_version 1.1` | 支持 WebSocket（需要 HTTP/1.1） |
| `Upgrade` / `Connection` | WebSocket 协议升级头 |
| `X-Real-IP` / `X-Forwarded-For` | 传递真实客户端 IP（后端日志用） |
| `try_files $uri $uri/ /index.html` | SPA 路由回退（React Router 需要） |

> **架构复盘要点**：Nginx 在这里扮演**网关层**角色：静态文件服务、API 反向代理、WebSocket 升级、SPA 回退，全部在一个配置中完成。

### 6.4 健康检查与监控

**结构化日志（structlog）：**

```python
# 配置 JSON 输出
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),  # 输出 JSON，便于日志聚合
    ],
)
```

**架构复盘要点：**
- JSON 日志可以直接被 **ELK Stack**（Elasticsearch + Logstash + Kibana）或 **Grafana Loki** 消费
- 每个日志事件包含 `order_id`、`event` 等上下文，便于**分布式追踪**
- Fallback 机制：structlog 不可用时自动回退到 stdlib logging，确保系统不崩溃

**Prometheus 指标：**

```python
orders_total = Counter(
    "fulfillcrew_orders_total", "Total orders processed", ["status"]
)
order_processing_duration = Histogram(
    "fulfillcrew_order_processing_seconds",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)
warehouse_bids_total = Counter(
    "fulfillcrew_warehouse_bids_total", "Total warehouse bids submitted", ["warehouse_id"]
)
fraud_score = Gauge(
    "fulfillcrew_fraud_score", "Latest fraud risk score", ["order_id"]
)
```

**架构复盘要点：**
- Counter：单调递增的计数器（如订单总数）
- Histogram：分布型指标（如处理延迟），Prometheus 自动计算分位数
- Gauge：可增可减的指标（如当前风险评分）
- No-op Fallback：prometheus_client 未安装时自动使用空实现，保证系统运行

**健康检查端点（/health）：**

```python
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

> **架构复盘要点**：健康检查不是简单的 `{"status": "ok"}`，而是**分级检查**每个依赖（数据库、Redis、模型文件）。"degraded" 状态告诉运维"系统还能运行，但某些功能受限"。

### 6.5 Event Bus — Redis / InMemory

```python
class EventBus(ABC):
    @abstractmethod
    async def publish(self, channel: str, event: dict[str, Any]) -> None: ...
    @abstractmethod
    async def subscribe(self, channel: str, handler: Callable) -> None: ...

class RedisEventBus(EventBus): ...  # 生产环境
class InMemoryEventBus(EventBus): ...  # 开发环境

async def get_event_bus(redis_url: str | None = None) -> EventBus:
    if redis_url:
        try:
            bus = RedisEventBus(redis_url)
            r = await bus._get_redis()
            await r.ping()  # 连接测试
            return bus
        except Exception:
            pass
    return InMemoryEventBus()  # 自动降级
```

**架构复盘要点：**
- **抽象接口**：`EventBus` 是抽象基类，Redis 和 InMemory 是两种实现
- **自动降级**：Redis 不可用时自动回退到内存实现，开发环境无需安装 Redis
- **统一的事件常量**：`ORDER_CREATED`, `FRAUD_CHECKED`, `INVENTORY_CHECKED` 等，避免魔法字符串

### 6.6 动手实验

1. **修改 Docker Compose**：添加一个 `pgadmin` 服务用于可视化数据库
2. **添加 Prometheus 指标**：在 `OrderService` 中新增一个指标（如 `inventory_check_duration`）
3. **配置日志级别**：通过环境变量 `BACKEND_LOG_LEVEL=debug` 观察详细日志

### 架构复盘要点
> "部署采用 **Docker 多阶段构建**，前端镜像从 ~300MB 压缩到 ~20MB。Docker Compose 使用 `depends_on.condition: service_healthy` 实现**有序启动**。Nginx 作为网关统一处理静态文件、API 代理和 WebSocket 升级。日志使用 **structlog 输出 JSON**，指标使用 **Prometheus Counter/Histogram/Gauge**，全部带有 **fallback 机制**确保系统鲁棒性。"

---

## 阶段 7：架构复盘准备与深度问答（持续）

### 7.1 项目介绍（2 分钟版本）

> "FulfillCrew 是一个**多智能体电商订单履约系统**。用户结账后，订单不是直接进入数据库，而是进入一个由 6 个自主 Agent 协调的履约工作流：Fraud Detection 评估风险，Inventory 检查库存，Coordinator 通过简化版 Contract Net Protocol 选择最优仓库，Demand Prediction 预测补货需求。整个系统基于 React 18 + FastAPI + Docker 构建，三门大学课程（云计算、多智能体、神经网络）直接映射到代码架构。"

### 7.2 项目亮点（30 秒版本）

> "亮点有三个：第一，**多智能体协调**不是过度设计，而是课程知识的直接映射；第二，**ML 模型接口**设计了 fallback 机制，确保无训练数据时系统仍可运行；第三，**工程化细节**到位——结构化 JSON 日志、Prometheus 指标、分级健康检查、Docker 有序启动。"

### 7.3 常见技术架构复盘问题速查

**关于架构：**
- Q: 为什么用多智能体而不是单一函数？
  - A: 可测试性、可扩展性、可解释性、课程映射。每个 Agent 独立可测，替换一个不影响其他。

- Q: 如果订单量增大 100 倍，系统哪里会成为瓶颈？
  - A: 三个潜在瓶颈：(1) 内存中的 WebSocket 连接字典 → 需要 Redis Pub/Sub 共享；(2) 单线程竞价计算 → 可以并行化；(3) 数据库写入 → 可以引入消息队列异步处理。

**关于数据库：**
- Q: 为什么用 SQLAlchemy 2.0 而不是 1.4？
  - A: 2.0 的 `Mapped` 类型注解更现代，`selectinload` 解决 N+1，异步原生支持更好。

- Q: Repository 模式和直接在 Service 里写 SQL 有什么区别？
  - A: 抽象、测试友好、事务边界清晰。Repository 只负责数据访问，Service 负责业务编排。

**关于 ML：**
- Q: 为什么 Fraud Detection 用 XGBoost 而不是神经网络？
  - A: XGBoost 在表格数据上通常比神经网络效果更好，且 TreeExplainer 的 SHAP 解释更可靠。神经网络的可解释性较弱。

- Q: 需求预测模型的特征怎么选？
  - A: 领域知识 + 可获取性。price、rating、category 是商品固有属性；day_of_week、month 捕捉季节性；sales_last_7/30_days 捕捉趋势。

**关于 DevOps：**
- Q: Docker 健康检查为什么用 `condition: service_healthy`？
  - A: 防止"服务启动了但还没准备好"的 race condition。比如 backend 依赖 postgres，但 postgres 容器启动后还需要初始化数据库。

- Q: 为什么 JSON 日志而不是纯文本？
  - A: 结构化日志可以被日志聚合系统（ELK、Loki）直接解析，支持按字段搜索和告警。纯文本需要正则解析，脆弱且慢。

---

## 附录：学习资源推荐

### 必读文档
1. [FastAPI 官方文档](https://fastapi.tiangolo.com/) — 重点看"Dependency Injection"和"Background Tasks"
2. [SQLAlchemy 2.0 教程](https://docs.sqlalchemy.org/en/20/tutorial/) — 重点看 ORM 映射和异步会话
3. [PyTorch 官方教程](https://pytorch.org/tutorials/) — 重点看 `nn.Module` 和 `torch.no_grad()`
4. [XGBoost 文档](https://xgboost.readthedocs.io/) — 重点看 `XGBClassifier` 和 `save_model`
5. [SHAP 文档](https://shap.readthedocs.io/) — 重点看 `TreeExplainer`

### 实践建议
- 每周至少运行一次完整系统，保持熟悉度
- 尝试修改一个 Agent 的逻辑，观察系统行为变化
- 用 `pytest` 运行测试套件，确保修改不破坏现有功能
- 在 Docker 容器内运行 `curl http://backend:8000/metrics`，观察 Prometheus 指标输出

---

> 祝你架构复盘顺利！有任何问题，随时回到这份教程查阅。🚀

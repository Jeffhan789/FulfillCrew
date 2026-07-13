# 按模块学习：4 周全栈深入

> **预计时间**：4 周（每周 5 天，每天 1.5-2 小时）  
> **前置知识**：已完成 [00_quickstart.md](./00_quickstart.md)，系统能正常运行；了解 Python 基础、JavaScript/TypeScript 基础、SQL 基础概念  
> **目标**：逐模块深入理解代码，能够独立修改、扩展系统

---

## 目录

- [Week 1: Cloud Computing（COMP315）](#week-1-cloud-computingcomp315)
- [Week 2: Multi-Agent Systems（COMP310）](#week-2-multi-agent-systemscomp310)
- [Week 3: Neural Networks（ELEC320）](#week-3-neural-networkselec320)
- [Week 4: Engineering Upgrade（v2.0）](#week-4-engineering-upgradev20)
- [自测检查清单](#自测检查清单)

---

## Week 1: Cloud Computing（COMP315）

> **目标**：理解云原生电商工程的完整链路：数据 → 后端 API → 前端 → 容器化部署

### Day 1: 数据清洗流水线

> **预计时间**：1 小时

**核心文件**：`data_cleaning/` 目录

**学习内容**：
1. 打开 `data_cleaning/` 目录，查看原始数据文件（JSON/CSV）
2. 理解数据清洗 pipeline 的输入 → 处理 → 输出流程
3. 了解数据如何被导入到 PostgreSQL 数据库中

**关键问题**：
- 原始数据有哪些字段？哪些字段需要清洗？
- 数据清洗步骤如何处理缺失值、异常值？
- 清洗后的数据如何与 `backend/database/models.py` 中的 ORM 模型对应？

**动手练习**：
- 修改一个商品的价格，重新运行数据清洗，观察数据库中的变化
- 尝试添加一个新的商品品类到数据文件中

**自测问题**：
- [ ] 数据清洗 pipeline 的入口文件是什么？
- [ ] 清洗后的数据存储在哪个表中？对应哪个 ORM 模型？

---

### Day 2: FastAPI 后端入门

> **预计时间**：2 小时

**核心文件**：
- `backend/main.py` — FastAPI 应用入口
- `backend/api/products.py` — 商品 API
- `backend/api/orders.py` — 订单 API
- `backend/schemas.py` — Pydantic 数据模型

**学习内容**：
1. **应用生命周期**（`backend/main.py`）
   - `lifespan` 上下文管理器：启动时初始化数据库，关闭时清理连接
   - CORS 中间件配置：开发环境允许跨域，生产环境由 Nginx 代理
   - Router 注册：每个 API 模块独立注册

2. **API 端点**（`backend/api/`）
   - `products.py`：`GET /products` 返回商品列表
   - `orders.py`：`POST /orders` 创建订单，`GET /orders/{id}` 查询订单
   - `agents.py`：`GET /agents/course-map` 返回课程映射
   - `health.py`：`GET /health` 健康检查
   - `metrics.py`：`GET /metrics` Prometheus 指标

3. **数据验证**（`backend/schemas.py`）
   - Pydantic 模型定义请求/响应的数据结构
   - `OrderRequest` 验证结账请求的数据格式
   - `OrderResponse` 定义订单响应的完整字段

**关键代码片段**：

```python
# backend/main.py — 应用生命周期
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application_startup", event="startup")
    await init_db()          # ← 启动时创建数据库表
    yield
    logger.info("application_shutdown", event="shutdown")
```

**动手练习**：
- 在 `backend/api/products.py` 中添加一个新的 `GET /products/{id}` 端点
- 修改 `backend/schemas.py` 中的 `Product` 模型，增加一个 `description` 字段
- 使用 Swagger UI 测试你的新 API

**自测问题**：
- [ ] FastAPI 的 `lifespan` 替代了哪个旧版 API？为什么更好？
- [ ] Pydantic 模型在系统中起什么作用？
- [ ] `jsonable_encoder` 的作用是什么？

---

### Day 3: React 前端基础

> **预计时间**：2 小时

**核心文件**：
- `frontend/src/main.tsx` — 主应用组件（单文件完整实现）
- `frontend/src/hooks/useOrderSocket.ts` — WebSocket Hook
- `frontend/src/components/` — 6 个可视化组件

**学习内容**：
1. **主应用组件**（`frontend/src/main.tsx`）
   - 使用 React 18 `createRoot` API
   - `useState` 管理商品列表、购物车、订单状态
   - `useEffect` 在组件挂载时获取商品数据和课程映射
   - `useMemo` 优化商品过滤和排序性能

2. **WebSocket Hook**（`frontend/src/hooks/useOrderSocket.ts`）
   - 建立到 `ws://localhost/ws/orders/{order_id}` 的 WebSocket 连接
   - 接收后端推送的实时订单状态更新
   - 管理连接状态（connected / disconnected）

3. **可视化组件**（`frontend/src/components/`）
   - `WarehouseBidChart.tsx` — 仓库竞价对比图（Recharts）
   - `DemandPredictionChart.tsx` — 需求预测柱状图
   - `RiskScoreGauge.tsx` — 风险仪表盘
   - `OrderStatusTimeline.tsx` — 决策时间线
   - `SystemHealthPanel.tsx` — 系统健康面板
   - `ModelEvaluationPanel.tsx` — 模型评估面板

**关键代码片段**：

```typescript
// frontend/src/main.tsx — 结账函数
async function checkout() {
  const response = await fetch(`${API_BASE}/orders`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: "demo-user",
      shipping_distance: 18,
      is_new_user: true,
      items: basket.map((item) => ({ product_id: item.product.id, quantity: item.quantity })),
    }),
  });
  const result = await response.json();
  setOrder(result);  // ← 触发订单面板渲染
}
```

**动手练习**：
- 在 `main.tsx` 的 `App` 组件中添加一个显示当前购物车总价的标题
- 修改 `useOrderSocket.ts`，在连接断开时显示一个 toast 提示
- 尝试修改 `WarehouseBidChart.tsx` 的图表颜色

**自测问题**：
- [ ] React 18 的 `createRoot` 与 React 17 的 `ReactDOM.render` 有什么区别？
- [ ] `useOrderSocket` 是如何在订单 ID 变化时重新建立连接的？
- [ ] 前端使用的是 Recharts 还是 D3.js？图表数据从哪里来？

---

### Day 4: Docker 部署

> **预计时间**：1.5 小时

**核心文件**：
- `docker-compose.yml` — 多服务编排
- `Dockerfile` — 后端多阶段构建
- `frontend/Dockerfile` — 前端构建 + Nginx 托管

**学习内容**：
1. **Docker Compose 服务定义**（`docker-compose.yml`）
   - `postgres`：PostgreSQL 15 数据库，持久化数据卷
   - `redis`：Redis 7 缓存/事件总线
   - `backend`：FastAPI 后端，依赖 postgres 和 redis
   - `frontend`：Nginx 托管静态资源，反向代理 `/api` 到后端

2. **服务依赖与健康检查**
   - `depends_on` + `condition: service_healthy` 确保依赖服务就绪后才启动
   - 每个服务都有 `healthcheck` 定义

3. **网络隔离**
   - 所有服务加入 `fulfillcrew-network` 桥接网络
   - 服务间通过容器名通信（如 `postgres:5432`）

**关键代码片段**：

```yaml
# docker-compose.yml — 后端服务定义
backend:
  build:
    context: .
    dockerfile: Dockerfile
  environment:
    - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/fulfillcrew
    - REDIS_URL=redis://redis:6379/0
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
```

**动手练习**：
- 修改 `docker-compose.yml`，将后端端口从 8000 改为 8080
- 查看 `Dockerfile` 的多阶段构建，理解为什么用多阶段构建减小镜像体积
- 尝试使用 `docker compose -f docker-compose.dev.yml up` 启动开发模式

**自测问题**：
- [ ] Docker Compose 中 `depends_on` 的 `condition: service_healthy` 是什么意思？
- [ ] 后端如何通过容器名访问 PostgreSQL？
- [ ] 前端 Nginx 的反向代理配置在哪里？

---

### Day 5: 整合测试 + 问题排查

> **预计时间**：1.5 小时

**核心文件**：`tests/` 目录、`backend/api/health.py`

**学习内容**：
1. 运行测试套件：`pytest` 或 `docker compose exec backend pytest`
2. 理解测试覆盖范围：API 端点、Agent 行为、服务逻辑
3. 健康检查端点：`/health` 返回数据库连接、Redis 连接状态

**动手练习**：
- 故意修改一个 API 返回格式，运行测试看失败结果
- 使用 `docker compose logs` 查看各服务日志
- 模拟数据库连接失败，观察系统的 fallback 行为

**自测问题**：
- [ ] 测试文件在哪里？如何运行？
- [ ] 健康检查返回哪些子系统状态？
- [ ] 如果 Redis 不可用，系统会怎么表现？（提示：fallback 到 InMemoryEventBus）

---

## Week 2: Multi-Agent Systems（COMP310）

> **目标**：深入理解 Multi-Agent 系统的核心设计：BaseAgent 模板方法、Contract Net Protocol、订单编排流水线

### Day 1: BaseAgent 设计模式

> **预计时间**：1 小时

**核心文件**：`backend/agents/base_agent.py`

**学习内容**：
1. **Template Method 模式**
   - `BaseAgent` 定义所有 Agent 的公共接口（`name`、`log()`）
   - 每个子类（`OrderAgent`、`FraudDetectionAgent` 等）继承并实现特定行为

2. **结构化审计日志**
   - 每次 Agent 决策都会生成 `AgentDecision` 对象
   - 可序列化为 JSON，发送到前端时间线组件

**关键代码片段**：

```python
# backend/agents/base_agent.py
class BaseAgent:
    name = "Base Agent"

    def log(self, message: str) -> AgentDecision:
        """Produce a structured audit log entry."""
        return AgentDecision(agent=self.name, message=message)
```

**动手练习**：
- 创建一个新的 `QualityCheckAgent` 继承 `BaseAgent`
- 在 `OrderService` 中调用它的 `log()` 方法，观察前端时间线变化

**自测问题**：
- [ ] 为什么使用基类而不是纯函数？
- [ ] `AgentDecision` 的结构是什么？前端如何消费它？

---

### Day 2: Contract Net Protocol

> **预计时间**：2 小时

**核心文件**：
- `backend/agents/coordinator_agent.py` — Coordinator（任务发布者）
- `backend/agents/warehouse_agent.py` — Warehouse Agent（任务投标者）

**学习内容**：
1. **Contract Net Protocol（CNP）简化版**
   - **Call for Proposals (CFP)**：Coordinator 向所有 Warehouse 广播任务
   - **Bid**：每个 Warehouse 根据自身条件计算成本并提交报价
   - **Award**：Coordinator 选择最低报价（最低成本）作为中标者

2. **竞价策略公式**
   - 每个 Warehouse 的成本函数综合考虑：workload、distance、stock_level、processing_speed
   - 生成 `suitability_score` 和 `reason` 字符串（可解释性）

3. **代码实现**
   - `coordinator_agent.request_bids()`：生成 CFP，收集 bids，选择 winner
   - `warehouse_agent.bid()`：计算成本，返回 bid 对象

**关键代码片段**：

```python
# 简化示意：仓库竞价流程
bids, winner = self.coordinator_agent.request_bids(item_count)
# 每个 bid 包含：warehouse_id, bid, workload, distance, stock_level, 
#                processing_speed, suitability_score, reason
```

**动手练习**：
- 修改 `warehouse_agent.py` 的成本函数权重，观察订单结果中 winner 的变化
- 增加一个 Warehouse Agent（从 3 个变成 4 个），看 CNP 如何自动适应

**自测问题**：
- [ ] CNP 的三个阶段是什么？（CFP → Bid → Award）
- [ ] 为什么系统选择最低报价而不是最高 suitability_score？
- [ ] `reason` 字段的作用是什么？为什么可解释性很重要？

---

### Day 3: 订单履约流水线

> **预计时间**：2 小时

**核心文件**：`backend/services/order_service.py`

**学习内容**：
1. **流水线 7 步骤**（在 `create_order()` 方法中）：

| 步骤 | 操作 | Agent | 关键决策点 |
|------|------|-------|------------|
| 0 | 订单创建 + WebSocket 通知 | OrderAgent | 生成 UUID |
| 1 | 欺诈检测 | FraudDetectionAgent | risk_score > 0.65 → review |
| 2 | 库存检查 | InventoryAgent | 库存不足 → 立即拒绝 |
| 3 | 仓库竞价 | CoordinatorAgent | CFP → 最低 bid wins |
| 4 | 需求预测 | DemandPredictionAgent | 预测未来 7 天销量 |
| 5 | 库存预留 | InventoryAgent | 仅对 approved 订单扣减库存 |
| 6 | 原子持久化 | Repository 层 | 单事务写入所有表 |
| 7 | 指标记录 + 最终推送 | OrderAgent | Prometheus + WebSocket |

2. **为什么顺序执行？**
   - 欺诈检测必须在库存预留之前（安全）
   - 库存检查必须在仓库竞价之前（无库存则不竞价）
   - 所有数据写入在一个 SQLAlchemy 事务中，保证 ACID

3. **WebSocket 实时推送**
   - 每个步骤完成后都调用 `manager.send_order_update()`
   - 前端通过 WebSocket 实时更新状态

**关键代码片段**：

```python
# backend/services/order_service.py — 核心流水线
async def create_order(self, request: OrderRequest) -> OrderResponse:
    order_id = str(uuid4())
    
    # Step 1: FRAUD DETECTION
    risk_score_val, fraud_status = self.fraud_agent.score(...)
    
    # Step 2: INVENTORY CHECK
    stock_available, unavailable = self.inventory_agent.check_stock(...)
    if not stock_available:
        return rejected_order_response
    
    # Step 3: WAREHOUSE BIDDING (CNP)
    bids, winner = self.coordinator_agent.request_bids(item_count)
    
    # Step 4: DEMAND PREDICTION
    predicted_demand = self.demand_agent.predict(selected_products)
    
    # Step 5: STOCK RESERVATION (conditional)
    if fraud_status == "approved":
        self.inventory_agent.reserve_stock(...)
    
    # Step 6: PERSISTENCE (atomic transaction)
    await self._persist_order(order_orm, item_orms, decision_orms, bid_orms)
    
    # Step 7: METRICS & COMPLETION
    orders_total.labels(status=order_status).inc()
    return OrderResponse(...)
```

**动手练习**：
- 在 `create_order()` 中故意修改 fraud 阈值（0.65 → 0.3），观察更多订单进入 review 状态
- 在 Step 2 和 Step 3 之间插入一个新的步骤（例如：优惠券检查）

**自测问题**：
- [ ] 为什么流水线必须是顺序的而不是并行的？哪些步骤可以并行化？
- [ ] `_persist_order()` 如何保证数据一致性？
- [ ] WebSocket 推送失败会影响订单持久化吗？

---

### Day 4: Agent 编排与决策日志

> **预计时间**：1.5 小时

**核心文件**：`backend/agents/` 全部 Agent 文件

**学习内容**：
1. 6 个 Agent 的分工：

| Agent | 职责 | 关键方法 |
|-------|------|----------|
| `OrderAgent` | 订单生命周期管理 | `log()` |
| `FraudDetectionAgent` | 欺诈风险评分 | `score()` |
| `InventoryAgent` | 库存检查与预留 | `check_stock()`, `reserve_stock()` |
| `CoordinatorAgent` | 仓库竞价协调 | `request_bids()` |
| `DemandPredictionAgent` | 需求预测 | `predict()` |
| `WarehouseAgent` | 仓库成本计算 | `bid()` |

2. 决策日志（`decision_log`）如何被收集和展示
   - 每个步骤调用 `agent.log()` 生成日志条目
   - 所有日志随 `OrderResponse` 返回前端
   - 前端 `OrderStatusTimeline` 组件渲染时间线

**动手练习**：
- 为每个 Agent 添加一个 `get_status()` 方法，返回当前状态
- 在 `OrderService` 中收集所有 Agent 状态，作为新的 API 返回

**自测问题**：
- [ ] 6 个 Agent 中，哪些是有状态的？哪些是无状态的？
- [ ] `decision_log` 是什么数据类型？如何持久化到数据库？
- [ ] 如果新增一个 Agent，需要修改哪些地方？

---

### Day 5: 扩展：添加新 Agent

> **预计时间**：2 小时

**动手任务**：创建一个 `ShippingAgent`

**步骤**：
1. 在 `backend/agents/` 下创建 `shipping_agent.py`，继承 `BaseAgent`
2. 实现 `estimate_delivery_time(shipping_distance, warehouse_id)` 方法
3. 在 `backend/services/order_service.py` 中实例化 `ShippingAgent`
4. 在流水线中插入一个步骤：仓库选择后，计算预计送达时间
5. 在 `backend/schemas.py` 中给 `OrderResponse` 添加 `estimated_delivery_days` 字段
6. 在前端 `main.tsx` 的订单结果面板中显示送达时间

**自测问题**：
- [ ] 我能否独立添加一个完整的 Agent 并让它在流水线中工作？
- [ ] 新 Agent 的日志是否出现在前端时间线中？
- [ ] 如果需要添加新字段到数据库，需要修改哪些文件？

---

## Week 3: Neural Networks（ELEC320）

> **目标**：理解三个 ML 模型的原理、实现和可解释性，能够替换或扩展模型

### Day 1: MLP 原理 + PyTorch 实现

> **预计时间**：2 小时

**核心文件**：`ml_models/demand_prediction/`

**学习内容**：
1. **MLP 架构**
   - 输入层：商品特征（价格、品类、历史销量等）
   - 隐藏层：全连接层 + ReLU 激活
   - 输出层：预测未来 7 天销量（回归任务）

2. **PyTorch 实现**
   - 模型定义：`torch.nn.Module` 子类
   - 训练循环：前向传播 → 计算 loss → 反向传播 → 更新权重
   - 推理：`model.eval()` + `torch.no_grad()`

3. **合成数据生成**
   - 系统使用合成数据训练模型（因为真实电商数据难以获取）
   - 理解数据分布如何影响模型性能

**关键代码片段**：

```python
# 示意：MLP 前向传播
class DemandMLP(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, output_dim)
    
    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x
```

**动手练习**：
- 修改 MLP 的隐藏层神经元数量，观察预测结果变化
- 尝试添加 Dropout 层，理解正则化作用

**自测问题**：
- [ ] MLP 的输入维度、输出维度分别是什么？
- [ ] 为什么用 ReLU 而不是 Sigmoid 作为隐藏层激活函数？
- [ ] `torch.no_grad()` 在推理时有什么作用？

---

### Day 2: XGBoost + SHAP 可解释性

> **预计时间**：2 小时

**核心文件**：`ml_models/fraud_detection/`

**学习内容**：
1. **XGBoost 原理**
   - 梯度提升决策树（GBDT）的优化实现
   - 适合表格数据的二分类任务（欺诈 / 正常）

2. **SHAP 可解释性**
   - SHAP（SHapley Additive exPlanations）解释每个特征对预测的贡献
   - 每个预测结果可以拆解为：`base_value + sum(feature_contributions)`
   - 让"黑盒"模型变得可解释

3. **特征工程**
   - `order_total`：订单总金额
   - `number_of_items`：商品数量
   - `average_item_price`：平均商品单价
   - `is_new_user`：是否新用户
   - `shipping_distance`：配送距离

**关键代码片段**：

```python
# 示意：XGBoost 欺诈检测 + SHAP 解释
import xgboost as xgb
import shap

model = xgb.XGBClassifier()
model.fit(X_train, y_train)

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)
# shap_values 显示每个特征如何影响预测结果
```

**动手练习**：
- 修改欺诈特征，增加一个 `time_of_day` 特征，看 SHAP 如何解释它
- 调整 `fraud_threshold`（默认 0.65），观察 approved/review 比例变化

**自测问题**：
- [ ] XGBoost 和 MLP 分别适合什么类型的数据？
- [ ] SHAP 的 "base_value" 是什么？
- [ ] 为什么欺诈检测需要可解释性？（提示：监管、用户信任）

---

### Day 3: TF-IDF + LogisticRegression

> **预计时间**：1.5 小时

**核心文件**：`ml_models/product_category_classifier/`

**学习内容**：
1. **TF-IDF 向量化**
   - TF（Term Frequency）：词在文档中出现的频率
   - IDF（Inverse Document Frequency）：词在全局文档中的稀缺程度
   - TF-IDF = TF × IDF，衡量词对文档的独特性

2. **Logistic Regression 分类**
   - 线性分类器，通过 sigmoid 函数输出概率
   - 适合高维稀疏特征（如 TF-IDF 向量）

3. **应用场景**
   - 自动将商品描述分类到品类（如 "Electronics"、"Clothing"）

**关键代码片段**：

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

vectorizer = TfidfVectorizer(max_features=5000)
X = vectorizer.fit_transform(product_descriptions)

classifier = LogisticRegression(max_iter=1000)
classifier.fit(X, y)
```

**动手练习**：
- 添加几个新的商品描述，观察分类结果
- 对比使用 Naive Bayes 和 Logistic Regression 的效果差异

**自测问题**：
- [ ] TF-IDF 为什么比单纯词频更适合文本分类？
- [ ] Logistic Regression 的输出是什么？如何转换为类别？
- [ ] 这个分类器在系统中的实际用途是什么？

---

### Day 4: 模型评估指标

> **预计时间**：1.5 小时

**核心文件**：
- `backend/services/order_service.py` 中模型评估数据收集
- `frontend/src/components/ModelEvaluationPanel.tsx`

**学习内容**：
1. **回归指标（需求预测）**
   - MAE（Mean Absolute Error）：平均绝对误差
   - MSE（Mean Squared Error）：均方误差（对大误差更敏感）
   - RMSE（Root MSE）：与原始单位一致

2. **分类指标（欺诈检测）**
   - Accuracy：准确率
   - Precision / Recall：精确率 / 召回率
   - ROC-AUC：ROC 曲线下面积（衡量排序能力）
   - F1-Score：Precision 和 Recall 的调和平均

3. **分类指标（商品分类）**
   - Accuracy
   - Confusion Matrix（混淆矩阵）

**动手练习**：
- 在 `ModelEvaluationPanel.tsx` 中增加一个新的指标展示
- 计算当前模型的 ROC-AUC 值，与随机猜测（0.5）对比

**自测问题**：
- [ ] MAE 和 RMSE 的区别是什么？什么场景下 RMSE 更优？
- [ ] 为什么欺诈检测不能只看 Accuracy？（提示：类别不平衡）
- [ ] ROC-AUC = 0.85 意味着什么？

---

### Day 5: 替换自己的模型

> **预计时间**：2 小时

**动手任务**：将欺诈检测模型替换为 LightGBM

**步骤**：
1. 安装 `lightgbm`：`pip install lightgbm`
2. 在 `ml_models/fraud_detection/` 下创建 `lightgbm_model.py`
3. 实现与 `XGBoost` 模型相同的接口：`fit()`、`predict()`、`explain()`
4. 在 `FraudDetectionAgent` 中切换模型引用
5. 运行订单测试，对比 XGBoost 和 LightGBM 的预测结果
6. 对比 SHAP 解释结果是否一致

**自测问题**：
- [ ] 模型替换时，哪些接口必须保持一致？
- [ ] 如果新模型没有内置 SHAP 支持，如何处理可解释性？
- [ ] 模型文件（.pkl / .pt）应该如何版本管理？

---

## Week 4: Engineering Upgrade（v2.0）

> **目标**：理解 v2.0 的工程升级：异步数据库、事件总线、WebSocket、可观测性

### Day 1: SQLAlchemy 2.0 async + Repository 模式

> **预计时间**：2 小时

**核心文件**：
- `backend/database/engine.py` — 异步引擎配置
- `backend/database/models.py` — ORM 模型定义
- `backend/repositories/` — Repository 层

**学习内容**：
1. **SQLAlchemy 2.0 async 配置**
   - `create_async_engine()` + `async_sessionmaker()`
   - 使用 `asyncpg` 驱动进行异步数据库操作

2. **Repository 模式**
   - `OrderRepository`：封装订单的增删改查
   - `ProductRepository`：封装商品查询和库存更新
   - `AgentDecisionRepository`：封装决策日志写入
   - `WarehouseBidRepository`：封装竞价记录写入

3. **为什么用 Repository 模式？**
   - 隔离数据访问逻辑与业务逻辑
   - 便于单元测试（mock repository）
   - 未来数据库迁移时不影响业务代码

**关键代码片段**：

```python
# backend/repositories/order_repository.py（示意）
class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_order(self, order: OrderORM) -> None:
        self.session.add(order)
        # 不在这里 commit，由调用方控制事务边界
```

**动手练习**：
- 在 `OrderRepository` 中添加一个 `get_orders_by_user()` 方法
- 实现一个分页查询，使用 `limit` 和 `offset`

**自测问题**：
- [ ] SQLAlchemy 2.0 的 `async_session` 与 1.4 的 `session` 有什么区别？
- [ ] Repository 模式和 DAO 模式的区别是什么？
- [ ] 为什么 `_persist_order()` 中所有写入在一个事务中？

---

### Day 2: Redis 事件总线 + 异步通信

> **预计时间**：1.5 小时

**核心文件**：`backend/infrastructure/event_bus.py`

**学习内容**：
1. **EventBus 抽象基类**
   - 定义 `publish()`、`subscribe()`、`close()` 接口
   - 允许不同实现（Redis / InMemory）无缝切换

2. **RedisEventBus**
   - 使用 `redis.asyncio` 进行异步 pub/sub
   - 后台监听任务 `_listen_loop()` 持续接收消息
   - 支持多个 handler 订阅同一个 channel

3. **InMemoryEventBus（Fallback）**
   - 使用 `asyncio.Queue` 实现内存中的事件队列
   - 当 Redis 不可用时自动降级
   - 开发环境无需安装 Redis 即可运行

4. **工厂函数**
   - `get_event_bus()`：尝试连接 Redis，失败则回退到 InMemory

**关键代码片段**：

```python
# backend/infrastructure/event_bus.py — 工厂函数
async def get_event_bus(redis_url: str | None = None) -> EventBus:
    if redis_url:
        try:
            bus = RedisEventBus(redis_url)
            r = await bus._get_redis()
            await r.ping()  # 连通性检查
            return bus
        except Exception:
            logger.warning("Redis failed, falling back to InMemoryEventBus")
    return InMemoryEventBus()
```

**动手练习**：
- 在 `event_bus.py` 中添加一个新的 channel `ORDER_CANCELLED`
- 订阅该 channel，当订单取消时打印日志

**自测问题**：
- [ ] EventBus 抽象基类用了什么设计模式？
- [ ] 为什么需要 InMemoryEventBus fallback？
- [ ] Redis pub/sub 的 listen 循环是如何工作的？

---

### Day 3: WebSocket 实时推送

> **预计时间**：1.5 小时

**核心文件**：
- `backend/api/websocket.py` — WebSocket 后端管理器
- `frontend/src/hooks/useOrderSocket.ts` — WebSocket 前端 Hook

**学习内容**：
1. **后端 WebSocket Manager**
   - 维护订单 ID → WebSocket 连接的映射
   - `send_order_update()`：向特定订单的连接推送状态更新
   - 连接断开时自动清理映射

2. **前端 useOrderSocket Hook**
   - 接收 `order_id`，建立 WebSocket 连接
   - 监听 `onmessage` 事件，更新本地状态
   - 连接状态管理：`connected` / `disconnected`

3. **为什么用 WebSocket 而不是轮询？**
   - 实时性：订单状态变化立即推送
   - 服务器资源：无需客户端频繁请求
   - 用户体验：更流畅的状态更新动画

**关键代码片段**：

```typescript
// frontend/src/hooks/useOrderSocket.ts（示意）
function useOrderSocket(orderId: string | null) {
  const [status, setStatus] = useState(null);
  const [connected, setConnected] = useState(false);
  
  useEffect(() => {
    if (!orderId) return;
    const ws = new WebSocket(`ws://localhost/ws/orders/${orderId}`);
    ws.onopen = () => setConnected(true);
    ws.onmessage = (event) => setStatus(JSON.parse(event.data));
    return () => ws.close();
  }, [orderId]);
  
  return { status, connected };
}
```

**动手练习**：
- 在 WebSocket 消息中添加一个心跳机制（ping/pong）
- 实现断线重连：连接断开后 3 秒自动重试

**自测问题**：
- [ ] WebSocket 与 HTTP 长轮询的区别是什么？
- [ ] 后端如何知道向哪个连接发送更新？
- [ ] 如果 WebSocket 推送失败，系统如何保证数据不丢失？

---

### Day 4: 可观测性（structlog + Prometheus）

> **预计时间**：1.5 小时

**核心文件**：
- `backend/infrastructure/logging.py` — structlog 结构化日志
- `backend/infrastructure/metrics.py` — Prometheus 指标
- `backend/api/metrics.py` — 指标暴露端点

**学习内容**：
1. **结构化日志（structlog）**
   - 每个日志事件都是 JSON，便于机器解析
   - 字段：`event`、`order_id`、`agent`、`risk_score` 等
   - 可搜索、可过滤、可聚合

2. **Prometheus 指标**
   - `Counter`：订单总数（按状态分类）
   - `Histogram`：订单处理耗时分布
   - `Gauge`：当前欺诈风险分数
   - 所有指标在 `/metrics` 端点以文本格式暴露

3. **为什么不用 print？**
   - 结构化日志可被 ELK / Grafana 等工具直接消费
   - 统一格式，便于日志聚合和告警
   - 支持日志级别动态调整（debug / info / warning / error）

**关键代码片段**：

```python
# backend/infrastructure/metrics.py（示意）
from prometheus_client import Counter, Histogram, Gauge

orders_total = Counter(
    "orders_total",
    "Total orders processed",
    ["status"]
)

order_processing_duration = Histogram(
    "order_processing_duration_seconds",
    "Order processing time"
)

fraud_score = Gauge(
    "fraud_score",
    "Risk score per order",
    ["order_id"]
)
```

**动手练习**：
- 添加一个新的 Counter：统计 WebSocket 推送次数
- 添加一个新的 Gauge：当前活跃 WebSocket 连接数

**自测问题**：
- [ ] Counter 和 Gauge 的区别是什么？
- [ ] 为什么日志要结构化（JSON）而不是纯文本？
- [ ] 如果日志系统（structlog）初始化失败，系统会怎样？（提示：fallback 到标准库 logging）

---

### Day 5: 系统健康检查 + 性能优化

> **预计时间**：1.5 小时

**核心文件**：
- `backend/api/health.py` — 健康检查端点
- `backend/api/metrics.py` — 指标端点

**学习内容**：
1. **健康检查维度**
   - API 服务本身：是否存活
   - 数据库连接：PostgreSQL 是否可访问
   - Redis 连接：Redis 是否可访问（如果配置了）
   - 自定义检查：磁盘空间、内存使用等

2. **健康检查返回值**
   - `{"status": "healthy"}` — 全部正常
   - `{"status": "unhealthy", "details": {...}}` — 部分子系统异常

3. **性能优化方向**
   - 数据库查询：添加索引、避免 N+1 查询
   - 缓存：Redis 缓存商品数据，减少数据库压力
   - 异步：所有 I/O 操作都使用 async/await
   - 连接池：数据库连接池、Redis 连接池

**动手练习**：
- 在健康检查中添加 ML 模型加载状态的检查
- 使用 `EXPLAIN ANALYZE` 分析数据库查询性能

**自测问题**：
- [ ] 健康检查返回 `unhealthy` 时，Docker 会做什么？
- [ ] 系统做了哪些防御性编程（fallback）？
- [ ] 如果要支持 1000 QPS，需要优化哪些部分？

---

## 自测检查清单

完成 4 周学习后，你应该能够：

### 云工程（Week 1）
- [ ] 解释 FastAPI lifespan 的生命周期管理
- [ ] 在 Swagger UI 中手动调用任意 API 并解释参数
- [ ] 修改 React 组件状态并观察 UI 变化
- [ ] 解释 Docker Compose 中服务依赖和健康检查机制
- [ ] 独立排查 "服务启动失败" 问题

### 多智能体（Week 2）
- [ ] 画出 BaseAgent 的继承关系图
- [ ] 解释 Contract Net Protocol 的三个阶段（CFP → Bid → Award）
- [ ] 逐步走读 `OrderService.create_order()` 的 7 个步骤
- [ ] 独立添加一个新的 Agent 并让它在流水线中工作
- [ ] 解释为什么顺序执行优于并行执行（在这个场景下）

### 神经网络（Week 3）
- [ ] 解释 MLP 的前向传播和反向传播
- [ ] 解释 XGBoost 的梯度提升原理
- [ ] 解释 SHAP 如何使模型可解释
- [ ] 解释 TF-IDF 的计算公式和作用
- [ ] 独立替换一个 ML 模型并对比效果

### 工程升级（Week 4）
- [ ] 解释 SQLAlchemy 2.0 async 与 1.4 的区别
- [ ] 解释 Repository 模式的优点
- [ ] 解释 Redis pub/sub 和 InMemory fallback 的切换机制
- [ ] 解释 WebSocket 的实时推送流程
- [ ] 解释结构化日志和 Prometheus 指标的作用
- [ ] 提出至少 3 个系统性能优化方向

---

> 🎉 恭喜完成 4 周学习！现在你已经具备：
> - 独立阅读、修改、扩展系统的能力
> - 架构复盘中讲解项目的技术深度
> - 理解现代全栈工程实践的基础
>
> 下一步：前往 [`03_deep_dive.md`](./03_deep_dive.md) 按专题继续深入。

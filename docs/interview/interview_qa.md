# FulfillCrew（智仓通）面试 Q&A 教学文档

> **适用对象**：项目作者复习技术原理、准备技术面试（实习/初级/中级后端/全栈岗位）  
> **文档定位**：以 FulfillCrew 代码为锚点，覆盖三门课程核心知识 + v2.0 工程实践  
> **建议用法**：先通读代码再对照 Q&A，遇到不会的题回到对应源码文件定位理解。

---

## 目录

1. [项目架构概览](#一项目架构概览)
2. [COMP315 Cloud Computing](#二comp315-cloud-computing)
3. [COMP310 Multi-Agent Systems](#三comp310-multi-agent-systems)
4. [ELEC320 Neural Networks](#四elec320-neural-networks)
5. [v2.0 工程升级深度题](#五v20-工程升级深度题)
6. [系统设计 & 综合场景题](#六系统设计--综合场景题)
7. [代码走读题](#七代码走读题)

---

## 一、项目架构概览

### Q1. 请用一句话描述 FulfillCrew 是什么系统，核心解决什么问题？

**参考答案**：  
FulfillCrew 是一个**基于 Multi-Agent 协作的电商订单履约系统**。用户下单后，系统通过 Order、Fraud、Inventory、Coordinator、Warehouse、Demand 六个智能体协同完成欺诈检测、库存检查、仓库竞价选择、需求预测与补货建议，最终返回订单结果并通过 WebSocket 实时推送状态。

**关键文件**：
- `backend/services/order_service.py` — 编排完整订单履约流水线
- `docs/system_design.md` — 系统架构总览

---

### Q2. 画一下 v2.0 的完整架构图，并说明各层职责。

**参考答案**：

```
┌─────────────────────────────────────────────────────────────┐
│  前端层 (React 18 + TypeScript + Vite + Recharts)           │
│  - 6 个 Dashboard 组件 + useOrderSocket WebSocket Hook      │
│  - 实时订单状态时间线、仓库竞价图表、风险仪表盘               │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼──────────────────────────────────────┐
│  API 网关层 (Nginx)                                         │
│  - 静态资源托管 + /api 反向代理到 FastAPI                   │
│  - 负载均衡、CORS、压缩（生产环境）                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  后端层 (FastAPI + async Python)                            │
│  - REST API (/products, /orders, /agents, /health, /metrics)│
│  - WebSocket /ws/orders/{order_id} 实时推送                  │
│  - Repository 模式 + SQLAlchemy 2.0 async ORM               │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  Multi-Agent 协调层                                         │
│  - OrderService 编排 6 个 Agent 的协作流程                   │
│  - 简化版 Contract Net Protocol（仓库竞价）                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│  数据与 ML 层                                               │
│  - PostgreSQL (asyncpg): 订单、商品、决策记录、竞价记录       │
│  - Redis / InMemory: 事件总线 pub/sub                       │
│  - ML Models: PyTorch MLP, XGBoost+SHAP, TF-IDF+LR          │
└─────────────────────────────────────────────────────────────┘
```

**关键文件**：
- `docker-compose.yml` — 多服务编排
- `backend/main.py` — FastAPI 应用入口
- `frontend/vite.config.ts` — 开发代理配置

---

### Q3. 项目如何体现三门课程的融合？

**参考答案**：

| 课程 | 核心概念 | 在系统中的体现 |
|------|----------|----------------|
| COMP315 Cloud Computing | 云原生电商工程 | React + FastAPI + Docker Compose + Nginx + 数据清洗流水线 |
| COMP310 Multi-Agent Systems | 自主智能体、Contract Net Protocol | 6 个 Agent 协作，Coordinator 发布任务、Warehouse Agent 竞价 |
| ELEC320 Neural Networks | MLP 回归、二分类、特征工程 | PyTorch MLP 需求预测、XGBoost 欺诈检测、TF-IDF+LR 品类分类 |

**关键文件**：
- `docs/course_mapping.md` — 课程映射详细说明
- `backend/api/agents.py` — `/agents/course-map` 端点直接暴露映射

---

## 二、COMP315 Cloud Computing

### Q4. 为什么前端选择 Vite 而不是 Create React App？

**参考答案**：
1. **启动速度快**：Vite 基于原生 ESM，开发服务器冷启动毫秒级，CRA 需要 webpack 打包整个应用。
2. **热更新高效**：Vite 的 HMR 只更新变更模块，CRA 需要重新编译更多文件。
3. **TypeScript 原生支持**：Vite 内置对 `.ts` / `.tsx` 的支持，无需额外配置 `ts-loader`。
4. **生产构建优化**：使用 Rollup 打包，Tree-shaking 更高效，产物更小。
5. **代理配置简单**：`vite.config.ts` 中通过 `server.proxy` 即可代理 `/api` 和 `/health` 到后端。

**代码佐证**（`frontend/vite.config.ts`）：
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
```

---

### Q5. FastAPI 的 `lifespan` 上下文管理器做了什么？为什么比传统的 `@app.on_event` 更好？

**参考答案**：
- **作用**：在应用启动时调用 `init_db()` 创建数据库表，在应用关闭时记录 shutdown 日志。
- **优势**：`@app.on_event("startup")` / `@app.on_event("shutdown")` 在 FastAPI 0.93+ 已被标记为弃用。`lifespan` 使用异步上下文管理器，代码更紧凑，启动和关闭逻辑天然配对，避免分散在两个装饰器中。

**代码佐证**（`backend/main.py`）：
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application_startup", event="startup")
    await init_db()
    yield
    logger.info("application_shutdown", event="shutdown")

app = FastAPI(title="...", lifespan=lifespan)
```

---

### Q6. CORS 配置是如何实现的？生产环境如何灵活调整？

**参考答案**：
- 代码先从环境变量 `CORS_ORIGINS` 读取，逗号分隔多个 origin；若未设置则使用默认的本地开发地址。
- 这样开发环境和生产环境可以通过同一套代码、不同环境变量来运行，符合 12-Factor App 原则。

**代码佐证**（`backend/main.py`）：
```python
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    ...
]
raw_cors = os.getenv("CORS_ORIGINS", "")
if raw_cors:
    allowed_origins = [o.strip() for o in raw_cors.split(",") if o.strip()]
else:
    allowed_origins = default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Q7. Dockerfile 为什么使用多阶段构建（multi-stage build）？

**参考答案**：
- **减小镜像体积**：第一阶段使用 `python:3.12-slim` 安装编译依赖（gcc）并 `pip install`，第二阶段只复制已安装的包到新的 `python:3.12-slim` 镜像，不包含 gcc 等编译工具。
- **提高安全性**：运行时不包含构建工具，减少攻击面。
- **加快部署**：产物镜像更小，push/pull 更快。

**代码佐证**（`Dockerfile`）：
```dockerfile
# ---- Build stage ----
FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends gcc
COPY backend/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ---- Runtime stage ----
FROM python:3.12-slim
COPY --from=builder /root/.local /root/.local
COPY backend ./backend
COPY ml_models ./ml_models
```

---

### Q8. Docker Compose 中各服务的依赖顺序和 healthcheck 是如何设计的？

**参考答案**：
1. **依赖链**：`postgres` → `redis` → `backend` → `frontend`。Backend 等待 postgres 和 redis 都 healthy 后才启动；frontend 等待 backend healthy 后启动。
2. **Healthcheck 设计**：
   - Postgres：`pg_isready -U postgres` 检查数据库是否就绪。
   - Redis：`redis-cli ping` 检查 Redis 是否响应。
   - Backend：Python urllib 请求 `/health` 端点。
   - Frontend：`wget --spider http://localhost/` 检查 Nginx 是否正常运行。
3. **重启策略**：`restart: unless-stopped` 保证服务异常退出后自动重启，但手动停止不会自动重启。

**代码佐证**（`docker-compose.yml` 节选）：
```yaml
backend:
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
    interval: 30s
    timeout: 5s
    retries: 3
```

---

### Q9. 数据清洗流水线在项目中扮演什么角色？

**参考答案**：
- 将含噪声的原始商品 JSON（`data_cleaning/raw_products/products.json`）转换为结构化、已验证的记录（`data_cleaning/cleaned_products/products.json`）。
- 清洗后的数据被 Docker 构建阶段复制到容器内（`COPY data_cleaning/cleaned_products ./data_cleaning/cleaned_products`），作为 ProductService 的初始数据源。
- 这体现了 COMP315 课程中"数据预处理"的作业要求，同时也为 ML 模型提供干净的特征输入。

---

## 三、COMP310 Multi-Agent Systems

### Q10. 什么是 Contract Net Protocol（合同网协议）？FulfillCrew 如何简化实现它？

**参考答案**：
- **标准 CNP**：Manager 广播任务 Announcement → 各 Contractor 评估并提交 Bid → Manager 评估 Bids 并 Award 合同 → Contractor 确认/拒绝。
- **FulfillCrew 的简化实现**：
  1. Coordinator Agent 持有 3 个 Warehouse Agent 实例。
  2. 下单时，Coordinator 向每个 Warehouse Agent 请求 `bid(item_count)`。
  3. 每个 Warehouse 根据库存惩罚、工作负载惩罚、距离惩罚、速度加成计算 bid 值。
  4. Coordinator 选择 `min(bids, key=lambda bid: bid.bid)` 作为 winner。
  5. 没有选择 winner 的确认/拒绝阶段，直接执行最低竞价策略。

**代码佐证**（`backend/agents/coordinator_agent.py`）：
```python
class CoordinatorAgent(BaseAgent):
    def request_bids(self, item_count: int) -> tuple[list[WarehouseBid], WarehouseBid]:
        bids = [warehouse.bid(item_count) for warehouse in self.warehouses]
        winner = min(bids, key=lambda bid: bid.bid)
        return bids, winner
```

---

### Q11. Warehouse Agent 的 bid 算法具体是什么？为什么这样设计？

**参考答案**：
```
bid = 5 + stock_penalty + workload_penalty + distance_penalty - speed_bonus

其中：
- stock_penalty = max(0, item_count - stock_level) * 2.0   // 缺货惩罚
- workload_penalty = current_workload * 0.8                // 工作负载惩罚
- distance_penalty = distance * 0.15                       // 距离惩罚
- speed_bonus = processing_speed * 1.1                     // 处理速度加成
- suitability_score = 100 / (1 + max(0.1, bid_value))      // 适配度分数（越高越好）
```

**设计理由**：
- bid 值越低代表仓库越适合履约，符合 CNP "最低竞价获胜" 的直觉。
- 各惩罚/加成项权重可调整，体现不同业务策略（如偏远地区配送可以调高 distance_penalty）。
- `reason` 字段提供可解释性，方便前端展示决策依据。

**代码佐证**（`backend/agents/warehouse_agent.py`）：
```python
def bid(self, item_count: int) -> WarehouseBid:
    stock_penalty = max(0, item_count - self.stock_level) * 2.0
    workload_penalty = self.current_workload * 0.8
    distance_penalty = self.distance * 0.15
    speed_bonus = self.processing_speed * 1.1
    bid_value = round(5 + stock_penalty + workload_penalty + distance_penalty - speed_bonus, 2)
    ...
```

---

### Q12. OrderService 中的订单履约流水线是怎样的？请按步骤描述。

**参考答案**：

```
1. 生成 order_id，记录结构化日志，WebSocket 推送 "order.created"
2. 加载商品映射，计算 order_total 和 item_count
3. 【Fraud Detection】FraudDetectionAgent.score() 计算风险分
   - risk_score >= 0.65 → "review_required"
   - 推送 fraud.checked WebSocket 事件
4. 【Inventory Check】InventoryAgent.check_stock()
   - 库存不足 → 直接拒绝，status = "rejected_out_of_stock"
   - 推送 inventory.checked WebSocket 事件
5. 【Warehouse Bidding】CoordinatorAgent.request_bids()
   - 收集 3 个 Warehouse 的 bid
   - 选择最低 bid 的仓库
   - 推送 warehouse.bid WebSocket 事件
6. 【Demand Prediction】DemandPredictionAgent.predict()
   - 预测未来 7 天需求
   - 若 predicted_demand > current_stock → "restock recommended"
7. 【库存预留】仅 fraud_status == "approved" 时 reserve_stock()
   - 否则 status = "review_required"
8. 持久化到 PostgreSQL（Order + OrderItem + AgentDecision + WarehouseBid）
9. 推送 fulfillment.completed WebSocket 事件
10. 返回 OrderResponse
```

**关键设计点**：
- 欺诈检测在库存检查之前，避免高风险订单占用库存。
- 库存不足直接短路返回，不执行后续竞价和预测，提升效率。
- WebSocket 每个关键步骤都推送事件，前端可实时展示进度。

**代码佐证**：`backend/services/order_service.py` 的 `create_order()` 方法（约 86-417 行）。

---

### Q13. 为什么说 Fraud Detection 必须在 Inventory Check 之前执行？如果反过来会怎样？

**参考答案**：
- **当前设计理由**：高风险订单若先被预留库存，会造成正常用户可购买商品被可疑订单占用，导致库存浪费和用户体验下降。
- **反过来会怎样**：
  1. 高风险订单占用库存 → 正常用户看到"缺货"。
  2. 后续 Fraud Detection 发现风险，订单被拒绝或进入人工审核 → 库存释放，但期间已造成销售损失。
  3. 在电商高并发场景下，这会导致大量库存抖动（reserve → release）。
- **扩展思考**：对于"秒杀"场景，更常见的做法是**先扣库存再校验**，因为库存是稀缺资源，需要快速锁定。但 FulfillCrew 作为通用履约系统，优先保证安全性。

---

### Q14. BaseAgent 的设计意图是什么？如果新增一个 Shipping Agent，需要改多少代码？

**参考答案**：
- **设计意图**：BaseAgent 提供统一的日志接口 `log(message)`，所有 Agent 继承后自动获得标准化的决策记录能力。这符合开闭原则——新增 Agent 无需修改已有代码。
- **新增 Shipping Agent 的工作量**：
  1. 新建 `backend/agents/shipping_agent.py`，继承 `BaseAgent`。
  2. 在 `OrderService.__init__` 中实例化 Shipping Agent。
  3. 在 `create_order()` 的适当位置调用 `shipping_agent.some_method()`。
  4. 在 `backend/api/agents.py` 的 `list_agents()` 中添加新 Agent 名称。
  5. 可选：前端 `OrderStatusTimeline.tsx` 的 `getAgentMeta()` 添加图标映射。

**代码佐证**（`backend/agents/base_agent.py`）：
```python
class BaseAgent:
    name = "Base Agent"
    def log(self, message: str) -> AgentDecision:
        return AgentDecision(agent=self.name, message=message)
```

---

## 四、ELEC320 Neural Networks

### Q15. Demand Prediction 的 MLP 架构是怎样的？输入输出分别是什么？

**参考答案**：
- **架构**：2 层全连接 MLP
  - Input: 9 维特征向量
  - Hidden 1: Linear(9→64) + ReLU + Dropout(0.2)
  - Hidden 2: Linear(64→32) + ReLU + Dropout(0.2)
  - Output: Linear(32→1) + squeeze
- **输入特征**（9 维）：
  1. price
  2. rating
  3. category_encoded（electronics=1.0, home=0.5）
  4. type_encoded（device=1.0, audio=0.8, lighting=0.6）
  5. day_of_week
  6. month
  7. is_weekend
  8. sales_last_7_days
  9. sales_last_30_days
- **输出**：标量，表示未来 7 天预测销量。
- **推理方式**：`torch.no_grad()` 上下文 + `model.eval()` 保证推理时不计算梯度、不更新权重。

**代码佐证**（`ml_models/demand_prediction/model.py`）：
```python
class DemandMLP(nn.Module):
    def __init__(self, input_dim: int = 9):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(64, 32), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(32, 1),
        )
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)
```

---

### Q16. 如果训练好的 MLP 模型文件不存在，系统会怎么做？这种设计叫什么？

**参考答案**：
- **Fallback（回退）机制**：若 `models/demand_mlp.pt` 不存在，则调用 `_heuristic_fallback()` 返回基于启发式的预测值。
- **优点**：
  1. 系统永不崩溃，MVP 阶段无需真实训练数据即可运行。
  2. 真实模型训练好后，只需将 `.pt` 文件放入对应目录即可无缝切换，零代码改动。
- **启发式公式**：
```python
activation = 2.5 + sum(w * v for w, v in zip(weights, features))
output = 1 + 6 / (1 + math.exp(-hidden / 4))
```

**代码佐证**（`ml_models/demand_prediction/predict.py`）：
```python
def predict_demand(product_features):
    if not MODEL_PATH.exists():
        return _heuristic_fallback(product_features)
    ...
```

---

### Q17. Fraud Detection 使用了什么模型？SHAP 可解释性是如何集成的？

**参考答案**：
- **主模型**：XGBoost 二分类器（`XGBClassifier`，模型文件 `fraud_xgb.json`）。
- **Fallback**：若 XGBoost 模型不存在，回退到 `LightweightFraudClassifier`（基于 sigmoid 的启发式评分器）。
- **SHAP 集成**：
  1. 使用 `shap.TreeExplainer(self.model)` 创建解释器。
  2. 对每个订单特征向量计算 SHAP values。
  3. 将每个特征的贡献值映射为字典返回，前端可展示"哪些特征导致了这个风险分"。
  4. 若使用 fallback，则返回空字典（无解释能力）。

**代码佐证**（`ml_models/fraud_detection/predict.py`）：
```python
class FraudDetector:
    def __init__(self, model_path=None):
        if self._model_path.exists():
            self.model = xgb.XGBClassifier()
            self.model.load_model(str(self._model_path))
            self.explainer = shap.TreeExplainer(self.model)
        else:
            self.model = LightweightFraudClassifier()
            self.explainer = None

    def score(self, order_features):
        if self._is_xgb:
            X = self._to_array(order_features)
            risk_score = float(self.model.predict_proba(X)[0, 1])
            shap_values = self.explainer.shap_values(X)
            fraud_shap = shap_values[1][0]  # 取 fraud 类的 SHAP 值
            shap_explanation = {col: round(float(val), 6) for col, val in zip(FEATURE_COLUMNS, fraud_shap)}
        ...
```

---

### Q18. 为什么 Fraud Detection 的 SHAP 取 `shap_values[1][0]` 而不是 `[0][0]`？

**参考答案**：
- `TreeExplainer.shap_values(X)` 对于二分类问题返回一个列表 `[shap_for_class_0, shap_for_class_1]`，即每个类别的 SHAP 值数组。
- 我们关心的是** fraud 类（正类，index=1）**对每个特征的贡献，所以取 `shap_values[1][0]`（第一个样本的 fraud 类 SHAP 值）。
- 如果 `shap_values` 不是列表（某些版本返回 ndarray），则直接取第一个元素作为 fallback。

**代码佐证**：
```python
if isinstance(shap_values, list):
    fraud_shap = shap_values[1][0]
else:
    fraud_shap = shap_values[0]
```

---

### Q19. Product Category Classifier 的技术栈是什么？如何做到模型热插拔？

**参考答案**：
- **技术栈**：TF-IDF 文本向量化 + Logistic Regression 多分类。
- **模型文件**：`vectorizer.pkl`、`classifier.pkl`、`categories.json`。
- **热插拔机制**：
  1. `CategoryClassifier.__init__` 尝试加载模型文件。
  2. 若任一文件缺失，自动降级到 `classify_category()` 关键词启发式分类器。
  3. 生产环境只需替换 `models/` 目录下的 `.pkl` 文件即可切换模型，无需重启服务。
- **概率输出**：`predict_proba()` 返回各类别概率，可用于前端展示置信度。

**代码佐证**（`ml_models/product_category_classifier/predict.py`）：
```python
class CategoryClassifier:
    def _load_model(self):
        if not all(p.exists() for p in (vectorizer_path, classifier_path, categories_path)):
            self.categories = None  # 标记为不可用，后续 fallback
            return
        # 加载 TF-IDF + LR
```

---

### Q20. 三个 ML 模型各解决什么问题？如果面试中被问到"你项目里用了什么 ML 模型"，怎么组织回答？

**参考答案**（建议的面试话术）：

> "FulfillCrew 中集成了三个 ML 模块：
> 1. **需求预测（回归）**：PyTorch 2 层 MLP，输入 9 维商品特征，输出未来 7 天预测销量，支持 `.pt` 模型热加载 + 启发式 fallback。
> 2. **欺诈检测（二分类）**：XGBoost + SHAP 可解释性，输入 10 维订单特征，输出 0-1 风险分，阈值 0.65 触发人工审核。
> 3. **品类分类（多分类）**：TF-IDF + Logistic Regression，输入商品名称文本，输出 6 个品类标签之一，支持概率输出和关键词 fallback。
> 
> 所有模型都遵循'训练模式/在线模式'分离的设计，模型文件缺失时自动降级为启发式算法，保证系统永不崩溃。"

---

## 五、v2.0 工程升级深度题

### Q21. 为什么从 in-memory 存储升级到 PostgreSQL + SQLAlchemy 2.0 async？

**参考答案**：
- **持久化**：in-memory 数据重启即丢失，PostgreSQL 保证订单、决策记录长期保存。
- **并发**：asyncpg + SQLAlchemy 2.0 async 支持高并发订单处理，避免阻塞事件循环。
- **关系建模**：ORM 的 relationship（`OrderORM.items`, `.decisions`, `.bids`）天然支持一对多查询，配合 `selectinload` 解决 N+1 问题。
- **数据审计**：`AgentDecisionORM` 和 `WarehouseBidORM` 记录每次决策，支持事后追溯。

**代码佐证**（`backend/database/models.py`）：
```python
class OrderORM(Base):
    items: Mapped[List["OrderItemORM"]] = relationship(back_populates="order", lazy="selectin", cascade="all, delete-orphan")
    decisions: Mapped[List["AgentDecisionORM"]] = relationship(...)
    bids: Mapped[List["WarehouseBidORM"]] = relationship(...)
```

---

### Q22. Repository 模式解决了什么问题？对比直接在 Service 里写 SQL 有什么优势？

**参考答案**：
- **职责分离**：Repository 负责数据访问细节，Service 负责业务逻辑编排。
- **可测试性**：Repository 可被 mock，Service 层单元测试无需真实数据库。
- **可替换性**：若未来从 PostgreSQL 迁移到 MongoDB，只需替换 Repository 实现，Service 代码不变。
- **代码复用**：多个 Service 可共享同一个 Repository。

**代码佐证**：
- `backend/repositories/order_repository.py` — 封装 Order CRUD
- `backend/repositories/product_repository.py` — 封装 Product 查询和库存更新
- `backend/services/order_service.py` — 在 `_persist_order` 中组合使用多个 Repository

---

### Q23. Event Bus 支持 Redis 和 InMemory 两种实现，这是怎么做到的？为什么要这样设计？

**参考答案**：
- **抽象基类**：`EventBus` 定义了 `publish` / `subscribe` / `close` 三个抽象方法。
- **两种实现**：
  - `RedisEventBus`：基于 `redis.asyncio` 的 pub/sub，适合生产环境多实例部署。
  - `InMemoryEventBus`：基于 `asyncio.Queue`，适合本地开发，无需启动 Redis。
- **工厂函数**：`get_event_bus(redis_url)` 先尝试连接 Redis，失败则自动降级到 InMemory。
- **设计理由**：
  1. 开发体验：本地 `docker compose up` 可以只启动 backend + frontend，Redis 可选。
  2. 零配置降级：生产配了 `REDIS_URL` 就用 Redis，没配也不报错。

**代码佐证**（`backend/infrastructure/event_bus.py`）：
```python
class EventBus(ABC):
    @abstractmethod
    async def publish(self, channel: str, event: dict) -> None: ...
    @abstractmethod
    async def subscribe(self, channel: str, handler) -> None: ...

async def get_event_bus(redis_url: str | None = None) -> EventBus:
    if redis_url:
        try:
            bus = RedisEventBus(redis_url)
            await bus._get_redis().ping()
            return bus
        except Exception:
            pass
    return InMemoryEventBus()
```

---

### Q24. structlog 的结构化日志和 Python 标准 logging 相比有什么优势？FallbackLogger 是怎么实现的？

**参考答案**：
- **结构化日志优势**：
  1. 输出 JSON 格式，可直接被 ELK/Loki 等日志系统解析和索引。
  2. 支持键值对（`logger.info("event", key=value)`），便于后续按字段过滤和聚合。
  3. 统一的 processor 链（timestamp、log level、stack info、JSON renderer）。
- **FallbackLogger 实现**：
  - 当 `structlog` 未安装时，提供一个兼容的 `_FallbackLogger` 类。
  - 将 `**kwargs` 格式化为 `key=value` 字符串，拼接在日志消息后输出到 stdout。
  - 保证 `logger.info("event", order_id="xxx")` 这种调用方式永远不会报错。

**代码佐证**（`backend/infrastructure/logging.py`）：
```python
class _FallbackLogger:
    def _log_with_kwargs(self, level: int, event: str, **kwargs: Any) -> None:
        if kwargs:
            extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
            self._log.log(level, "%s | %s", event, extra)
        else:
            self._log.log(level, "%s", event)
```

---

### Q25. Prometheus 指标如何做到"可选依赖"？如果 `prometheus_client` 没安装会怎样？

**参考答案**：
- 通过 `try/except ImportError` 捕获导入失败。
- 若未安装，定义 `_NoOpMetric` 类，提供与真实 Counter/Histogram/Gauge/Info 相同的接口（`labels()`, `inc()`, `observe()`, `set()`, `info()`），但方法体为空。
- 这样 `orders_total.labels(status="created").inc()` 这种代码在有无 prometheus_client 时都能正常运行，不会抛异常。

**代码佐证**（`backend/infrastructure/metrics.py`）：
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
    class Counter(_NoOpMetric): pass
    class Histogram(_NoOpMetric): pass
    class Gauge(_NoOpMetric): pass
```

---

### Q26. WebSocket 实时推送是如何实现的？ConnectionManager 是线程/协程安全的吗？

**参考答案**：
- **实现**：`ConnectionManager` 维护一个字典 `active_connections: Dict[str, WebSocket]`，以 `order_id` 为 key 存储连接。
- **生命周期**：
  1. 客户端连接 `ws://host/ws/orders/{order_id}`，`connect()` 方法 `await websocket.accept()` 并注册到字典。
  2. OrderService 每完成一个关键步骤调用 `manager.send_order_update(order_id, data)` 推送 JSON。
  3. 客户端断开时触发 `WebSocketDisconnect` 异常，`disconnect()` 从字典移除。
- **协程安全性**：在当前单进程 FastAPI 场景下是安全的，因为 Python async 是单线程事件循环，字典操作不会被并发打断。但如果扩展为多进程部署（多个 Uvicorn worker），每个进程有独立的 `ConnectionManager`，需要通过 Redis Pub/Sub 做跨进程广播。

**代码佐证**（`backend/api/websocket.py`）：
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

---

### Q27. `/health` 健康检查端点检查了哪些组件？为什么要检查 ML 模型文件？

**参考答案**：
- **检查项**：
  1. `database` — 执行 `SELECT 1` 验证 PostgreSQL 连通性。
  2. `redis` — 验证 EventBus 是否由 Redis 支持且可达。
  3. `demand_model` — 检查 `demand_mlp.pt` 文件是否存在。
  4. `fraud_model` — 检查 `fraud_xgb.json` 文件是否存在。
- **检查 ML 模型的原因**：
  - 模型文件是推理正确性的关键依赖。若文件丢失，系统会回退到启发式算法，虽然不会崩溃，但预测质量下降。
  - 在 Kubernetes 等编排环境中，健康检查失败可触发 Pod 重启或告警，及时发现模型部署问题。

**代码佐证**（`backend/api/health.py`）：
```python
async def check_demand_model() -> bool:
    model_path = Path(__file__).parents[2] / "ml_models" / "demand_prediction" / "models" / "demand_mlp.pt"
    return model_path.exists()

@router.get("/health", response_model=HealthCheck)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthCheck:
    db_ok = await check_db_connection()
    redis_ok = await check_redis_connection()
    demand_model_ok = await check_demand_model()
    fraud_model_ok = await check_fraud_model()
    status = "healthy" if all(checks.values()) else "degraded"
    return HealthCheck(status=status, checks=checks)
```

---

### Q28. OrderService 中的 `_persist_order` 方法为什么要在同一个事务中完成所有写入？

**参考答案**：
- **数据一致性**：订单主记录、订单项、决策日志、仓库竞价必须在同一个事务中提交。如果分开提交，可能出现"订单已创建但竞价记录丢失"的不一致状态。
- **回滚能力**：若中间任何一步失败，整个事务回滚，不会出现脏数据。
- **性能**：单次 commit 比多次 commit 开销更小。
- **库存更新原子性**：`update_stock` 也在同一事务中，避免"订单已创建但库存未扣"的竞态条件。

**代码佐证**（`backend/services/order_service.py`）：
```python
async def _persist_order(..., update_stock=False, products=None, request_items=None):
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        ...
        await order_repo.create_order(order_orm)
        await order_repo.add_items(...)
        for dec in decision_orms:
            await agent_decision_repo.save(dec)
        for bid in bid_orms:
            await warehouse_bid_repo.save(bid)
        if update_stock:
            for item in request_items:
                await product_repo.update_stock(item.product_id, -item.quantity)
        await session.commit()  # 同一事务提交
```

---

## 六、系统设计 & 综合场景题

### Q29. 如果订单量从每天 100 单增长到 10 万单，系统需要哪些改进？

**参考答案**（按优先级）：

1. **数据库**
   - 添加读写分离（主库写、从库读）。
   - 对 `orders.created_at`、`orders.order_status` 添加索引。
   - 考虑按时间分表/分区（如按月 partition）。

2. **缓存**
   - 商品数据读多写少，使用 Redis 缓存 `ProductService.get_product_map()`，设置合理 TTL。
   - 缓存穿透防护：空值缓存 + Bloom Filter。

3. **异步化**
   - 需求预测和补货建议可以异步执行（放入 Celery/RQ 任务队列），不阻塞订单创建响应。
   - WebSocket 推送也可改为消息队列驱动。

4. **负载均衡**
   - 多个 backend 实例 behind Nginx 负载均衡。
   - WebSocket 需要 sticky session 或改用 Redis Pub/Sub 广播。

5. **ML 服务拆分**
   - 将欺诈检测、需求预测拆分为独立微服务，支持独立扩缩容。
   - 使用 gRPC 或 HTTP/2 进行内部通信。

6. **监控告警**
   - Prometheus + Grafana 可视化订单处理延迟、错误率、库存预警。
   - 设置 P99 延迟告警阈值。

---

### Q30. 如果需要在高并发下保证库存不超卖，当前代码有什么问题？如何解决？

**参考答案**：
- **当前问题**：`inventory_agent.reserve_stock()` 和 `product_repo.update_stock()` 是两个步骤，之间没有数据库级锁。如果两个订单同时检查同一商品库存都通过，然后同时扣减，会导致超卖（Lost Update）。
- **解决方案**：
  1. **悲观锁**：`SELECT ... FOR UPDATE` 在检查库存时锁定商品行，保证串行扣减。
  2. **乐观锁**：商品表添加 `version` 字段，更新时校验 `WHERE version = ?`，失败则重试。
  3. **Redis 原子操作**：使用 `DECR` 原子扣减库存，扣减成功才允许下单，失败直接拒绝。
  4. **数据库约束**：在 `quantity` 上添加 `CHECK (quantity >= 0)`，超卖时数据库抛异常，事务回滚。

---

### Q31. 面试中如何向非技术面试官（如产品经理）解释这个项目？

**参考答案**（30 秒电梯演讲）：

> "FulfillCrew 是一个智能订单履约系统。想象你在线下单后，系统里有一组'数字员工'（Agent）自动帮你做四件事：
> 1. **防骗检测** — 判断这笔订单是否可疑；
> 2. **库存检查** — 确认仓库有货；
> 3. **智能选仓** — 让几个仓库'竞价'，选最快最便宜的；
> 4. **需求预测** — 告诉商家该补什么货。
> 整个过程通过 WebSocket 实时推送到你的页面，让你看到订单走到哪一步了。"

---

## 七、代码走读题

### Q32. 阅读以下代码片段，找出潜在问题并给出改进建议。

**片段 A**（`backend/api/orders.py`）：
```python
@router.post("", response_model=OrderResponse)
async def create_order(request: OrderRequest) -> OrderResponse:
    product_service = ProductService()
    order_service = OrderService(product_service)
    return await order_service.create_order(request)
```

**参考答案**：
- **问题 1**：每次请求都新建 `ProductService` 和 `OrderService` 实例，若服务内部有状态（如缓存连接）会导致资源浪费。
- **问题 2**：`ProductService` 若连接数据库，每次请求新建连接开销大。
- **改进**：使用 FastAPI 的 `Depends` 依赖注入，将 Service 实例作为单例或请求级依赖管理。

```python
# 改进示例
def get_order_service() -> OrderService:
    # 可结合 lru_cache 或全局单例
    return OrderService(ProductService())

@router.post("", response_model=OrderResponse)
async def create_order(
    request: OrderRequest,
    order_service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    return await order_service.create_order(request)
```

---

**片段 B**（`backend/api/websocket.py`）：
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

**参考答案**：
- **问题**：没有处理 `receive_text()` 可能抛出的其他异常（如 `RuntimeError: WebSocket is not connected`），异常未被捕获会导致连接未从 `manager` 中移除，造成内存泄漏。
- **改进**：使用更广泛的异常捕获，确保 `disconnect` 一定被调用。

```python
@router.websocket("/ws/orders/{order_id}")
async def websocket_endpoint(websocket: WebSocket, order_id: str):
    await manager.connect(websocket, order_id)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"event": "pong", "order_id": order_id})
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("websocket_error", order_id=order_id)
    finally:
        manager.disconnect(order_id)
```

---

**片段 C**（`backend/services/order_service.py` 库存拒绝路径）：
```python
order_orm = OrderORM(
    order_id=order_id,
    user_id=request.user_id,
    order_status="rejected_out_of_stock",
    order_total=order_total,
    ...
)
```

**参考答案**：
- **问题**：库存不足时仍然将订单写入数据库。从业务角度看，"缺货拒绝"的订单通常不需要持久化，或至少不应占用 `order_id` 序列。
- **但此设计也有合理性**：审计追踪——记录用户曾尝试下单但因缺货被拒绝，后续可用于分析"流失订单"。
- **改进建议**：若确需审计，可考虑单独一张 `rejected_orders` 表，避免污染主订单表；或在 `orders` 表上加索引过滤 `rejected_out_of_stock` 状态，避免查询时扫描大量拒绝订单。

---

### Q33. 如果你是面试官，你会怎么问这个项目？请列出 3 个追问。

**参考答案**（模拟面试官视角）：

1. **"你的 MLP 模型训练数据从哪来？如果没有历史数据，你怎么验证模型的有效性？"**
   - 考察点：对 ML 工程落地难度的认知，是否理解 MVP 阶段 fallback 的必要性。

2. **"如果 Coordinator 的最低竞价策略在实际业务中导致某个仓库永远抢不到订单，你怎么优化？"**
   - 考察点：对负载均衡、公平性、多目标优化的理解。可回答加权轮询、引入负载上限、动态调价等策略。

3. **"你的 WebSocket 推送在 Docker Compose 多实例场景下还能工作吗？如果不能，怎么解决？"**
   - 考察点：对分布式 WebSocket、共享状态、消息队列的理解。可回答 Redis Pub/Sub 广播、引入 Socket.io + Redis Adapter 等方案。

---

## 附录：核心文件速查表

| 知识点 | 关键文件路径 |
|--------|-------------|
| FastAPI 应用入口 | `backend/main.py` |
| Pydantic Schema | `backend/schemas.py` |
| SQLAlchemy ORM 模型 | `backend/database/models.py` |
| 异步数据库引擎 | `backend/database/engine.py` |
| 订单履约编排 | `backend/services/order_service.py` |
| 事件总线 | `backend/infrastructure/event_bus.py` |
| 结构化日志 | `backend/infrastructure/logging.py` |
| Prometheus 指标 | `backend/infrastructure/metrics.py` |
| WebSocket 管理 | `backend/api/websocket.py` |
| 健康检查 | `backend/api/health.py` |
| Coordinator Agent | `backend/agents/coordinator_agent.py` |
| Warehouse Agent | `backend/agents/warehouse_agent.py` |
| 需求预测 MLP | `ml_models/demand_prediction/model.py` |
| 需求预测推理 | `ml_models/demand_prediction/predict.py` |
| 欺诈检测 XGBoost | `ml_models/fraud_detection/predict.py` |
| 品类分类 TF-IDF+LR | `ml_models/product_category_classifier/predict.py` |
| React WebSocket Hook | `frontend/src/hooks/useOrderSocket.ts` |
| 订单状态时间线 | `frontend/src/components/OrderStatusTimeline.tsx` |
| 仓库竞价图表 | `frontend/src/components/WarehouseBidChart.tsx` |
| Docker Compose | `docker-compose.yml` |
| 后端 Dockerfile | `Dockerfile` |
| 前端 Dockerfile | `frontend/Dockerfile` |

---

> **最后提醒**：面试时不要背诵答案，而是理解代码背后的设计取舍。当面试官追问"为什么"时，能回到项目代码中给出具体文件路径和代码行号，是最有力的回答。

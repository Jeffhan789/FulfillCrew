# 深度原理：按需深入技术专题

> **预计时间**：按需（每个专题 1-3 小时）  
> **前置知识**：已完成 [00_quickstart.md](./00_quickstart.md)，系统能正常运行  
> **目标**：针对感兴趣的模块深入理解原理，能够回答"为什么这样设计"和"如果不这样会怎样"

---

## 目录

- [如何选择阅读顺序](#如何选择阅读顺序)
- [专题一：FastAPI 异步生命周期](#专题一fastapi-异步生命周期)
- [专题二：Contract Net Protocol](#专题二contract-net-protocol)
- [专题三：MLP 前向传播与 PyTorch 实现](#专题三mlp-前向传播与-pytorch-实现)
- [专题四：Docker 多阶段构建](#专题四docker-多阶段构建)
- [专题五：前端 React 并发特性](#专题五前端-react-并发特性)
- [专题六：可观测性体系](#专题六可观测性体系)
- [专题七：SQLAlchemy 2.0 async 迁移](#专题七sqlalchemy-20-async-迁移)
- [自测检查清单](#自测检查清单)

---

## 如何选择阅读顺序

```
┌─────────────────────────────────────────────────────────────┐
│                     深度阅读路线选择器                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  你是...？                                                   │
│                                                             │
│  A. "我想理解后端是怎么跑起来的"                              │
│     → 专题一（FastAPI）→ 专题七（SQLAlchemy 2.0）            │
│                                                             │
│  B. "Agent 之间的协作逻辑很有趣"                              │
│     → 专题二（Contract Net Protocol）→ 走读 coordinator_agent │
│                                                             │
│  C. "ML 模型部分需要加强"                                    │
│     → 专题三（MLP）→ technical_guide/05_ml_models_deep_dive   │
│                                                             │
│  D. "架构复盘时被问了 Docker 和部署"                             │
│     → 专题四（Docker 多阶段构建）→ technical_guide/07_docker   │
│                                                             │
│  E. "前端架构复盘准备"                                           │
│     → 专题五（React 并发）→ technical_guide/02_frontend        │
│                                                             │
│  F. "运维/SRE 方向"                                          │
│     → 专题六（可观测性）→ technical_guide/06_infrastructure    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 专题一：FastAPI 异步生命周期

> **预计时间**：1.5 小时  
> **推荐阅读**：`docs/technical_guide/03_backend_deep_dive.md`  
> **对应代码**：`backend/main.py`

### 核心问题

1. **为什么用 `lifespan` 而不是 `@app.on_event("startup")`？**
   - `@app.on_event` 已被标记为 deprecated
   - `lifespan` 使用 `asynccontextmanager`，可以在 startup 和 shutdown 之间 `yield`，确保资源正确释放
   - 支持依赖注入和嵌套上下文

2. **CORS 配置的原理**
   - 开发环境：前端（`:5173`）和后端（`:8000`）在不同端口，需要 CORS
   - 生产环境：Nginx 将两者代理到同一域名，CORS 不再需要
   - 环境变量 `CORS_ORIGINS` 控制允许的源

3. **Router 注册的设计**
   - 每个 API 模块（products、orders、agents、health、metrics、websocket）独立注册
   - 符合单一职责原则，便于模块化测试和维护

### 代码走读

```python
# backend/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application_startup", event="startup")
    await init_db()          # ← startup：创建数据库表
    yield                    # ← 应用运行期间
    logger.info("application_shutdown", event="shutdown")

app = FastAPI(
    title="Cloud Multi-Agent E-Commerce Intelligence System",
    lifespan=lifespan,       # ← 绑定生命周期
)
```

### 延伸阅读

- [FastAPI 官方文档 - Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
- [Python contextlib.asynccontextmanager](https://docs.python.org/3/library/contextlib.html#contextlib.asynccontextmanager)

---

## 专题二：Contract Net Protocol

> **预计时间**：2 小时  
> **推荐阅读**：`docs/technical_guide/04_multi_agent_system.md`  
> **对应代码**：
> - `backend/agents/coordinator_agent.py`
> - `backend/agents/warehouse_agent.py`
> - `docs/adr/ADR-005-contract-net-protocol.md`

### 核心问题

1. **什么是 Contract Net Protocol？**
   - FIPA 标准协议之一，用于多智能体系统中的任务分配
   - 三个阶段：**Call for Proposals (CFP)** → **Bid** → **Award**
   - Manager（Coordinator）发布任务，Contractors（Warehouses）竞标

2. **本项目的简化版 CNP**
   - Coordinator 向所有 Warehouse 广播 CFP（商品数量）
   - 每个 Warehouse 计算成本函数，返回 bid
   - Coordinator 选择最低 bid 作为 winner
   - 每个 bid 附带 `reason` 字符串，实现可解释性

3. **竞价策略公式**

   成本函数综合考虑：
   - `workload`：当前工作量（越高成本越高）
   - `distance`：配送距离（越远成本越高）
   - `stock_level`：库存水平（越低成本越高）
   - `processing_speed`：处理速度（越快成本越低）

   ```
   bid = f(workload, distance, stock_level, processing_speed)
   suitability_score = 综合评分（越高越好）
   ```

### 代码走读

```python
# backend/agents/coordinator_agent.py（示意）
class CoordinatorAgent(BaseAgent):
    def request_bids(self, item_count: int) -> tuple[list[WarehouseBid], WarehouseBid]:
        # 1. CFP：向所有仓库广播任务
        bids = [warehouse.bid(item_count) for warehouse in self.warehouses]
        
        # 2. 选择最低 bid（简化策略）
        winner = min(bids, key=lambda b: b.bid)
        
        return bids, winner
```

### 为什么这样设计？

| 设计决策 | 原因 |
|----------|------|
| 最低 bid 胜出 | 简化实现，模拟成本最优选择 |
| 每个 bid 带 reason | 可解释性：知道为什么选这个仓库 |
| 同进程 Agent | 简化部署，未来可扩展为分布式消息队列 |
| 3 个仓库 | 足够演示 CNP 原理，又不复杂 |

### 如果不这样设计？

| 替代方案 | 问题 |
|----------|------|
| 固定分配（轮流） | 无法适应仓库负载变化 |
| 随机选择 | 不考虑成本，效率低 |
| 最高 suitability_score | 需要调参权重，增加复杂度 |
| 分布式消息队列 | 增加部署复杂度，超出课程范围 |

### 延伸阅读

- [FIPA Contract Net Protocol Specification](http://www.fipa.org/specs/fipa00029/SC00029H.html)
- `docs/adr/ADR-005-contract-net-protocol.md` — 架构决策记录

---

## 专题三：MLP 前向传播与 PyTorch 实现

> **预计时间**：2 小时  
> **推荐阅读**：`docs/technical_guide/05_ml_models_deep_dive.md`  
> **对应代码**：`ml_models/demand_prediction/`

### 核心问题

1. **MLP 架构**
   - 输入层：`input_dim` 个神经元（商品特征维度）
   - 隐藏层：全连接层 + ReLU 激活
   - 输出层：1 个神经元（预测未来 7 天销量）

2. **前向传播**

   ```
   h = ReLU(W₁ · x + b₁)    # 隐藏层
   ŷ = W₂ · h + b₂           # 输出层（回归，无激活函数）
   ```

3. **训练 vs 推理**
   - 训练：`model.train()` + `loss.backward()` + `optimizer.step()`
   - 推理：`model.eval()` + `torch.no_grad()`（禁用梯度计算，节省内存）

4. **合成数据**
   - 系统使用合成数据训练（真实电商数据难以获取）
   - 合成数据需要模拟真实分布，否则模型泛化能力差

### 代码走读

```python
# ml_models/demand_prediction/model.py（示意）
import torch.nn as nn

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

### 为什么用 PyTorch 而不是 TensorFlow？

| 维度 | PyTorch | TensorFlow |
|------|---------|------------|
| 学习曲线 | 更直观（动态图） | 相对陡峭 |
| 调试 | 与 Python 调试器兼容 | 需要专用工具 |
| 课程要求 | ELEC320 课程使用 PyTorch | — |
| 部署 | torchscript / onnx | TensorFlow Serving |

### 延伸阅读

- [PyTorch 官方教程](https://pytorch.org/tutorials/)
- `docs/technical_guide/05_ml_models_deep_dive.md` — MLP 深入讲解

---

## 专题四：Docker 多阶段构建

> **预计时间**：1 小时  
> **推荐阅读**：`docs/technical_guide/07_docker_deployment.md`  
> **对应代码**：`Dockerfile`、`frontend/Dockerfile`

### 核心问题

1. **什么是多阶段构建？**
   - 一个 Dockerfile 中定义多个 `FROM` 阶段
   - 每个阶段可以独立选择基础镜像
   - 最终只保留最后一个阶段的文件，前面阶段不进入最终镜像

2. **为什么用多阶段构建？**
   - **减小镜像体积**：构建依赖（如 gcc、node_modules dev 依赖）不进入生产镜像
   - **安全性**：生产镜像不包含编译工具，减少攻击面
   - **缓存优化**：依赖安装层可以缓存，加速后续构建

3. **后端 Dockerfile 的结构**

   ```dockerfile
   # 阶段一：构建
   FROM python:3.11-slim AS builder
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --user -r requirements.txt
   
   # 阶段二：生产
   FROM python:3.11-slim AS production
   WORKDIR /app
   COPY --from=builder /root/.local /root/.local
   COPY backend/ ./backend/
   CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

### 代码走读

对比单阶段 vs 多阶段构建的镜像大小：

```bash
# 构建
docker build -t fulfillcrew-backend .

# 查看镜像大小
docker images | grep fulfillcrew
```

### 延伸阅读

- [Docker 多阶段构建官方文档](https://docs.docker.com/build/building/multi-stage/)
- `docs/adr/ADR-009-docker-compose-deployment.md` — 部署架构决策

---

## 专题五：前端 React 并发特性

> **预计时间**：1.5 小时  
> **推荐阅读**：`docs/technical_guide/02_frontend_deep_dive.md`  
> **对应代码**：`frontend/src/main.tsx`

### 核心问题

1. **React 18 的并发特性**
   - `createRoot()`：启用并发模式（Concurrent Mode）
   - `useTransition()`：标记非紧急更新，避免阻塞 UI
   - `useDeferredValue()`：延迟低优先级渲染

2. **本项目中的 React 18 实践**
   - 使用 `createRoot()` 而不是 `ReactDOM.render`
   - `useMemo` 优化商品过滤和排序（大量计算时避免重复执行）
   - `useEffect` 管理副作用（API 请求、WebSocket 连接）

3. **WebSocket Hook 设计**
   - `useOrderSocket` 封装 WebSocket 连接逻辑
   - 依赖 `orderId`，订单变化时自动重建连接
   - 清理函数 `ws.close()` 防止内存泄漏

### 代码走读

```typescript
// frontend/src/main.tsx — React 18 createRoot
import { createRoot } from "react-dom/client";

createRoot(document.getElementById("root")!).render(<App />);
// ↑ React 18 的并发入口
```

```typescript
// frontend/src/main.tsx — useMemo 优化
const visibleProducts = useMemo(() => {
  return products
    .filter((product) => product.name.toLowerCase().includes(query.toLowerCase()))
    .filter((product) => !inStockOnly || product.quantity > 0)
    .sort((a, b) => { ... });
}, [products, query, sortBy, inStockOnly]);
// ↑ 只有依赖变化时才重新计算
```

### 延伸阅读

- [React 18 并发特性](https://react.dev/blog/2022/03/29/react-v18)
- `docs/technical_guide/02_frontend_deep_dive.md`

---

## 专题六：可观测性体系

> **预计时间**：2 小时  
> **推荐阅读**：`docs/technical_guide/06_infrastructure_observability.md`  
> **对应代码**：
> - `backend/infrastructure/logging.py`
> - `backend/infrastructure/metrics.py`
> - `backend/api/health.py`

### 核心问题

1. **可观测性的三大支柱**
   - **日志（Logs）**：发生了什么？（结构化 JSON 日志）
   - **指标（Metrics）**：系统运行得怎么样？（Prometheus 计数器/仪表盘/直方图）
   - **追踪（Traces）**：请求经过了哪些服务？（本项目未实现，可扩展）

2. **结构化日志（structlog）**
   - 每个日志事件是 JSON，包含 `event`、`order_id`、`agent` 等字段
   - 可被 ELK Stack（Elasticsearch + Logstash + Kibana）直接消费
   - 支持日志级别动态调整

3. **Prometheus 指标**
   - `Counter`：单调递增的计数器（如订单总数）
   - `Gauge`：可增可减的仪表盘（如当前欺诈分数）
   - `Histogram`：采样分布（如订单处理耗时）

4. **健康检查**
   - `/health` 返回 API、DB、Redis 状态
   - Docker 根据健康检查结果决定是否重启容器

### 代码走读

```python
# backend/infrastructure/logging.py（示意）
import structlog

logger = structlog.get_logger()

# 使用
logger.info(
    "order.created",           # event 类型
    order_id=order_id,         # 结构化字段
    user_id=request.user_id,
    event="order.created",
)
# 输出：{"event": "order.created", "order_id": "xxx", "user_id": "demo-user", "timestamp": "..."}
```

```python
# backend/infrastructure/metrics.py（示意）
from prometheus_client import Counter, Histogram

orders_total = Counter("orders_total", "Total orders", ["status"])
order_processing_duration = Histogram("order_processing_duration_seconds", "Order processing time")
```

### 防御性编程：Fallback 机制

| 组件 | 正常情况 | Fallback |
|------|----------|----------|
| structlog | 结构化 JSON 日志 | 标准库 logging |
| Redis | Redis pub/sub | InMemoryEventBus |
| DB | PostgreSQL 查询 | JSON 文件（ProductService） |

### 延伸阅读

- [12-Factor App — Logs](https://12factor.net/logs)
- [Prometheus 最佳实践](https://prometheus.io/docs/practices/)

---

## 专题七：SQLAlchemy 2.0 async 迁移

> **预计时间**：2 小时  
> **推荐阅读**：`docs/technical_guide/03_backend_deep_dive.md`  
> **对应代码**：
> - `backend/database/engine.py`
> - `backend/database/models.py`
> - `backend/repositories/`

### 核心问题

1. **SQLAlchemy 1.4 vs 2.0 的关键变化**
   - `session.execute()` 返回 `Result` 对象，需要 `.scalars()` / `.all()` 提取数据
   - `Mapped` 类型注解声明模型
   - 异步支持更完善：`create_async_engine()` + `AsyncSession`

2. **asyncpg 驱动**
   - PostgreSQL 的纯 Python 异步驱动
   - 使用 PostgreSQL 二进制协议，性能优于 psycopg2
   - 支持连接池和 prepared statement

3. **Repository 模式实现**
   - `OrderRepository`：封装订单 CRUD
   - `ProductRepository`：封装商品查询和库存更新
   - 构造函数接收 `AsyncSession`，由调用方控制事务边界

### 代码走读

```python
# backend/database/engine.py（示意）
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(
    DATABASE_URL,  # postgresql+asyncpg://...
    echo=False,
    pool_size=20,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)
```

```python
# backend/repositories/order_repository.py（示意）
class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_order(self, order: OrderORM) -> None:
        self.session.add(order)
        # 注意：不在这里 commit！
```

### 事务管理

```python
# backend/services/order_service.py
async with AsyncSessionLocal() as session:
    order_repo = OrderRepository(session)
    product_repo = ProductRepository(session)
    
    await order_repo.create_order(order_orm)
    await product_repo.update_stock(product_id, -quantity)
    
    await session.commit()  # ← 所有操作在一个事务中
```

### 常见陷阱

| 问题 | 原因 | 解决 |
|------|------|------|
| `RuntimeError: Task attached to a different loop` | 在全局作用域创建 engine | 在应用启动时创建，或使用 lifespan |
| `ResourceWarning: unclosed connection` | Session 没有正确关闭 | 使用 `async with` 上下文管理器 |
| N+1 查询 | 懒加载在异步中触发额外查询 | 使用 `selectinload` 或 `joinedload` 预加载 |

### 延伸阅读

- [SQLAlchemy 2.0 迁移指南](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html)
- [asyncpg 文档](https://magicstack.github.io/asyncpg/current/)

---

## 自测检查清单

完成任意专题后，你应该能够：

### 通用能力
- [ ] 解释"为什么这样设计"（至少 3 个理由）
- [ ] 解释"如果不这样会怎样"（至少 2 个替代方案和问题）
- [ ] 画出该模块的核心数据流图
- [ ] 找到对应代码并解释关键行

### 专题特定
- [ ] **FastAPI**：解释 lifespan 替代 on_event 的原因
- [ ] **CNP**：解释 CFP → Bid → Award 的完整流程
- [ ] **MLP**：手推一次前向传播（给输入向量，计算输出）
- [ ] **Docker**：解释多阶段构建减小镜像体积的原理
- [ ] **React**：解释 createRoot 与 ReactDOM.render 的区别
- [ ] **可观测性**：解释 Counter/Gauge/Histogram 的区别和使用场景
- [ ] **SQLAlchemy 2.0**：解释 async session 的生命周期管理

---

> 💡 **建议**：不要一次性读完所有专题。先选择最感兴趣或架构复盘最需要的 1-2 个专题深入，其他作为备用参考。

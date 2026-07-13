# FulfillCrew 架构复盘问答手册

> 按模块分类的深度架构复盘问答，每个问题包含：问题解析 → 标准回答 → 扩展讨论 → 代码示例

---

## 目录

1. [项目概览与动机](#1-项目概览与动机)
2. [前端技术栈](#2-前端技术栈)
3. [后端架构与 API](#3-后端架构与-api)
4. [数据库与持久化](#4-数据库与持久化)
5. [多智能体系统](#5-多智能体系统)
6. [机器学习模块](#6-机器学习模块)
7. [DevOps 与部署](#7-devops-与部署)
8. [系统设计与扩展](#8-系统设计与扩展)
9. [行为架构复盘与项目展示](#9-行为架构复盘与项目展示)

---

## 1. 项目概览与动机

### Q1: 请用 2 分钟介绍这个项目

**回答框架：**

> "FulfillCrew 是一个**多智能体电商订单履约系统**。核心理念是：将一个简单的课程作业电商原型，工程化升级为一个完整的订单智能履约系统。
>
> 系统围绕三门大学课程构建：COMP315 云计算负责前端+后端+容器化部署；COMP310 多智能体系统负责 6 个自主 Agent 协调履约；ELEC320 神经网络负责需求预测和欺诈检测。
>
> 用户结账后，订单进入一个由 Fraud Detection → Inventory Check → Warehouse Bidding（Contract Net Protocol）→ Demand Prediction 组成的多 Agent 流水线。每个 Agent 的决策独立记录，保证可解释性。整个系统基于 React 18 + TypeScript + FastAPI + PostgreSQL + Docker 构建。"

**评审者可能追问：**
- "和普通的电商系统有什么区别？" → 强调"**下单后的智能履约工作流**"而非"购物车+支付"
- "项目的难点在哪里？" → 多 Agent 协调、ML 接口的 fallback 设计、异步数据库操作

---

### Q2: 为什么要做这个项目？它解决了什么真实问题？

**标准回答：**

> "这个项目的起点是一个课程作业——做一个简单的 React 电商界面。但大多数课程作业提交后就丢弃了，我想展示**如何将课程知识工程化落地**。
>
> 真实问题有两个层面：
> 1. **学术层面**：课程作业往往只做前端展示，没有后端逻辑。我扩展了完整的订单履约流程，让三门课的知识在一个系统中产生关联。
> 2. **工程层面**：电商履约是一个真实的工业问题——订单来了，怎么选择仓库？怎么判断风险？怎么预测补货？这些不是简单的 CRUD，需要多系统协调。"

**扩展讨论：**
- 可以提到 Amazon 的供应链优化、淘宝的订单履约系统等真实案例
- 强调"课程作业升级"的叙事比"从头做一个项目"更有说服力——展示了**迭代思维**

---

### Q3: 项目的技术栈选型理由是什么？

| 技术 | 选型理由 | 替代方案及为何不选 |
|------|----------|-------------------|
| React 18 + TypeScript | 类型安全、组件化、生态成熟 | Vue/Svelte 也可行；React 的组件与可视化生态更完整 |
| Vite | HMR 极快、ESM 原生、构建产物小 | CRA 太慢，Webpack 配置复杂 |
| FastAPI | 异步原生、自动 OpenAPI 文档、Pydantic 验证 | Django 太重，Flask 异步支持弱 |
| SQLAlchemy 2.0 async | 类型友好的 ORM、异步原生 | Django ORM 绑定框架、raw SQL 维护难 |
| PostgreSQL | 开源、功能丰富、JSON 支持好 | SQLite 仅适合单机、MySQL 功能略少 |
| Redis | 内存缓存 + Pub/Sub | Memcached 无 Pub/Sub |
| Docker | 环境一致性、部署标准化 | 直接部署依赖管理复杂 |
| PyTorch + XGBoost | 灵活 + 表格数据最优 | TensorFlow 更重、纯 sklearn 能力弱 |

---

## 2. 前端技术栈

### Q4: 为什么用 useState 而不是 Redux/Zustand？

**标准回答：**

> "状态管理层级很浅——只有 `products`、`basket`、`order`、`courseMap` 等 4-5 个顶层状态。没有跨多层组件传递的需求，也没有复杂的状态派生逻辑。
>
> Redux 在这种场景下是**过度工程**——需要写 actions、reducers、selectors，代码量翻倍但收益有限。我用 `useState` + `useMemo` 的组合，简单、可测试、没有学习成本。
>
> 但如果项目规模扩大（比如添加用户登录、多页面购物车持久化），我会考虑 Zustand 或 Redux Toolkit。"

**扩展讨论：**
- 展示**根据复杂度选择工具**的工程判断力
- 提到 `useMemo` 用于 `visibleProducts` 的计算缓存，避免每次渲染重新过滤排序

---

### Q5: WebSocket 和 HTTP 轮询有什么区别？为什么选择 WebSocket？

**标准回答：**

| 维度 | HTTP 轮询 | WebSocket |
|------|-----------|-----------|
| 通信方向 | 客户端主动拉取 | 服务端主动推送 |
| 连接开销 | 每次请求都新建 TCP + HTTP 头 | 一次握手，长连接复用 |
| 实时性 | 取决于轮询间隔（通常 1-5 秒） | 毫秒级 |
| 带宽效率 | 大量重复 HTTP 头 | 仅数据帧，头部极小 |
| 适用场景 | 低频更新、简单场景 | 高频推送、实时协作 |

> "订单状态变更是**事件驱动**的——Fraud 检测完成、库存检查完成、仓库竞价完成，这些事件何时发生不确定。如果用轮询，要么延迟高（间隔长），要么浪费资源（间隔短）。WebSocket 让服务端在事件发生时**即时推送**到前端，延迟最低且带宽最省。"

**代码示例：**

```typescript
// useOrderSocket.ts — 一个订单一个连接
export function useOrderSocket(orderId: string | null) {
  const [status, setStatus] = useState<SocketMessage | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!orderId) return;  // 无订单时不连接
    const ws = new WebSocket(`${WS_BASE}/ws/orders/${orderId}`);
    ws.onopen = () => setConnected(true);
    ws.onmessage = (event) => setStatus(JSON.parse(event.data));
    return () => ws.close();  // 清理
  }, [orderId]);

  return { status, connected };
}
```

---

### Q6: React 的 `useMemo` 和 `useCallback` 有什么区别？你在项目中用了哪个？

**标准回答：**

> "`useMemo` 缓存**计算结果**，`useCallback` 缓存**函数引用**。
>
> 我在项目中用了 `useMemo` 来缓存 `visibleProducts`：
> ```tsx
> const visibleProducts = useMemo(() => {
>   return products
>     .filter(p => p.name.toLowerCase().includes(query.toLowerCase()))
>     .filter(p => !inStockOnly || p.quantity > 0)
>     .sort((a, b) => /* ... */);
> }, [products, query, sortBy, inStockOnly]);
> ```
> 这样当 `products` 不变但组件因其他状态重渲染时，过滤排序不会重复执行。
>
> 我没有用 `useCallback`，因为回调函数（`addToBasket`、`removeFromBasket`）没有被传递给用 `React.memo` 优化的子组件，缓存函数引用没有收益。"

**扩展讨论：**
- 过早优化是万恶之源：不要默认给所有函数包 `useCallback`
- 展示你理解**什么时候不需要优化**

---

### Q7: 前端如何做错误处理？

**标准回答：**

> "当前版本采用**防御式编程**——每个 `fetch` 都有 `.catch()` 回退：
> ```tsx
> fetch(`${API_BASE}/products`)
>   .then(r => r.json())
>   .then(setProducts)
>   .catch(() => setProducts([]));  // 失败时静默回退到空列表
> ```
>
> 更完善的方案（生产环境）会添加：
> 1. **全局错误边界**（Error Boundary）捕获 React 渲染错误
> 2. **重试机制**：指数退避重试 API 请求
> 3. **用户反馈**：Toast 通知替代静默失败
> 4. **日志上报**：Sentry 等工具捕获前端异常"

---

## 3. 后端架构与 API

### Q8: FastAPI 的依赖注入系统是怎么工作的？

**标准回答：**

> "FastAPI 的依赖注入基于 Python 的**类型注解**和 `yield` 生成器。
>
> 例如数据库会话依赖：
> ```python
> async def get_db():
>     async with AsyncSessionLocal() as session:
>         try:
>             yield session  # 注入到路由函数
>         finally:
>             await session.close()  # 请求结束后自动关闭
>
> @router.get("/health")
> async def health_check(db: AsyncSession = Depends(get_db)):
>     db_ok = await check_db_connection()
>     ...
> ```
>
> `Depends(get_db)` 告诉 FastAPI：每次请求这个路由时，先执行 `get_db()`，把 yield 的值注入到 `db` 参数。请求结束后执行 `finally` 块关闭会话。"

**扩展讨论：**
- 依赖可以嵌套：`get_current_user` 依赖 `get_db`
- 依赖可以缓存：同一个请求内多次使用同一依赖时，只执行一次

---

### Q9: 为什么用 `lifespan` 而不是 `on_event("startup")`？

**标准回答：**

> "`on_event("startup")` 和 `on_event("shutdown")` 在 FastAPI 0.95+ 已标记为弃用，未来版本可能移除。
>
> `lifespan` 是 ASGI 标准（PEP 3333 扩展），它使用 Python 的 `asynccontextmanager`，提供更现代的生命周期管理：
> ```python
> @asynccontextmanager
> async def lifespan(app: FastAPI):
>     await init_db()  # 启动时
>     yield           # 应用运行期间
>     # 关闭时自动清理
> ```
>
> 优势：支持异步初始化、异常处理更优雅、符合 ASGI 标准。"

---

### Q10: Pydantic v2 相比 v1 有什么改进？

**标准回答：**

> "Pydantic v2 是 2023 年的重大重构，核心改进：
> 1. **性能提升 5-50 倍**——用 Rust 重写了核心验证逻辑
> 2. **严格模式**——默认更严格的类型检查，减少隐式转换
> 3. **JSON Schema 生成更完善**——FastAPI 的 `/docs` 自动文档更精确
> 4. **Validator 装饰器变化**——`@field_validator` 替代 `@validator`
> 5. **`model_dump()` 替代 `dict()`**——更符合 PEP 8
>
> 例如 `OrderRequest` 中的验证：
> ```python
> class OrderRequest(BaseModel):
>     items: list[BasketItem] = Field(min_length=1)  # 至少一个商品
>     shipping_distance: float = Field(default=12.0, ge=0)  # 非负
> ```
> 这些验证在请求到达业务逻辑之前就完成，返回 422 错误。"

---

### Q11: 异步编程在 Python 中的优势是什么？你的项目哪里用了 async/await？

**标准回答：**

> "Python 的 `asyncio` 允许**单线程并发处理 I/O 密集型任务**。当一个请求等待数据库查询时，事件循环可以切换到处理另一个请求，而不是阻塞等待。
>
> 在 FulfillCrew 中，以下场景使用 async：
> 1. **数据库操作**：`AsyncSession` 执行 SQL 查询时释放事件循环
> 2. **WebSocket**：`await websocket.receive_text()` 等待客户端消息时，不阻塞其他连接
> 3. **Event Bus**：Redis Pub/Sub 的 `async for message in pubsub.listen()`
>
> 不适合 async 的场景（项目中未涉及）：
> - CPU 密集型计算（如模型训练）——应该用多进程
> - 简单的同步 API——async 增加复杂度但无收益"

**扩展讨论：**
- Python 的 GIL（全局解释器锁）限制真正的并行，asyncio 是**并发不是并行**
- 对于 CPU 密集型任务，用 `ProcessPoolExecutor` 或多进程

---

### Q12: 你的 API 设计遵循了什么原则？

**标准回答：**

> "遵循 RESTful 设计原则和领域驱动设计的分层思想：
>
> **URL 设计：**
> - `GET /products` — 资源集合
> - `POST /orders` — 创建资源
> - `GET /agents/course-map` — 子资源
> - `GET /health` — 系统状态
>
> **响应设计：**
> - 统一用 Pydantic Schema 定义响应结构
> - `OrderResponse` 包含完整的履约结果，前端无需二次请求
> - 错误用 HTTP 状态码：`200` 成功，`422` 验证失败，`500` 服务器错误
>
> **分层架构：**
> ```
> API Layer (routers)     →  负责 HTTP 协议、请求验证、响应序列化
> Service Layer           →  负责业务逻辑、Agent 编排
> Repository Layer        →  负责数据访问抽象
> Model Layer (ORM)       →  负责数据库映射
> ```
> 每层只与相邻层交互，不越级调用。"

---

## 4. 数据库与持久化

### Q13: 为什么从内存存储升级到 PostgreSQL？

**标准回答：**

> "v1.0 使用内存字典存储数据，优势是简单、无需配置，但致命缺陷：
> 1. **数据丢失**：服务重启后所有数据消失
> 2. **无法并发**：多进程/多实例无法共享内存数据
> 3. **无事务**：无法保证订单创建和库存扣减的原子性
> 4. **无法查询**：没有 SQL 查询能力，无法做复杂分析
>
> v2.0 升级到 PostgreSQL + SQLAlchemy 2.0 async：
> - ACID 保证数据一致性
> - `AsyncSession` 支持高并发
> - `relationship` + `selectinload` 解决 N+1 查询问题
> - 为将来分片、读写分离预留空间"

---

### Q14: 什么是 N+1 查询问题？你的项目怎么解决的？

**标准回答：**

> "N+1 查询问题：查询 1 个订单 + N 个关联查询（items、decisions、bids），总共 N+1 次数据库往返。
>
> **反例（N+1）：**
> ```python
> orders = await session.execute(select(OrderORM))  # 1 次查询
> for order in orders:
>     print(order.items)  # 每次访问触发 1 次查询 → N 次
> ```
>
> **解决：selectinload（项目中使用）：**
> ```python
> result = await session.execute(
>     select(OrderORM)
>     .where(OrderORM.order_id == order_id)
>     .options(
>         selectinload(OrderORM.items),      # 用 IN 批量加载
>         selectinload(OrderORM.decisions),
>         selectinload(OrderORM.bids),
>     )
> )
> ```
> `selectinload` 会执行 `SELECT ... WHERE order_id IN (...)` 批量加载所有关联数据，总共 4 次查询（1 次主表 + 3 次关联表），与订单数量无关。"

**扩展讨论：**
- 其他解决方式：`joinedload`（JOIN）、`subqueryload`（子查询）
- `selectinload` 的优势：不增加主查询复杂度，适合多对多/一对多关系

---

### Q15: Repository 模式的优势是什么？

**标准回答：**

> "Repository 模式是**数据访问层**的抽象，优势有三：
>
> **1. 解耦**
> Service 层不直接操作 SQL/ORM，而是通过 Repository 接口。如果未来从 PostgreSQL 换成 MongoDB，只需替换 Repository 实现，Service 代码不变。
>
> **2. 测试友好**
> 单元测试可以 mock Repository：
> ```python
> @pytest.fixture
def mock_order_repo():
>     repo = Mock(spec=OrderRepository)
>     repo.get_by_id.return_value = sample_order
>     return repo
> ```
> 不需要启动真实数据库。
>
> **3. 事务边界清晰**
> Repository 的方法内部不 `commit`，由调用方（Service）控制事务：
> ```python
> async with AsyncSessionLocal() as session:
>     order_repo = OrderRepository(session)
>     product_repo = ProductRepository(session)
>     # 多个操作在同一个事务中
>     await order_repo.create_order(order)
>     await product_repo.update_stock(product_id, -quantity)
>     await session.commit()  # 原子提交
> ```
> 如果中间出错，`session.rollback()` 保证数据一致性。"

---

## 5. 多智能体系统

### Q16: 什么是 Contract Net Protocol？你的简化版做了什么取舍？

**标准回答：**

> "Contract Net Protocol（合同网协议）是多智能体系统中经典的任务分配机制，包含 4 个阶段：
> 1. **Announce**：Manager 发布任务
> 2. **Bid**：Contractors 评估并报价
> 3. **Award**：Manager 选择最优报价
> 4. **Execute**：Contractor 执行并报告
>
> **完整 CNP 的复杂之处：**
> - 投标者可以拒绝投标（refuse）
> - 投标者可以讨价还价（counter-offer）
> - 合同可以被取消或重新分配
> - 多轮协商
>
> **我的简化版取舍：**
> - ✅ 保留核心流程：Announce → Bid → Award
> - ❌ 去掉拒绝机制：所有 Warehouse 必须投标
> - ❌ 去掉讨价还价：一轮投标即确定
> - ❌ 去掉合同取消：无动态重分配
>
> **取舍理由：** 这是 MVP，核心目标是**展示课程知识映射**。完整 CNP 的复杂度会让代码量增加 5 倍，但教学价值提升有限。"

---

### Q17: 为什么用多智能体而不是一个大的服务函数？

**标准回答：**

| 维度 | 单一函数 | 多智能体 |
|------|----------|----------|
| 代码复杂度 | 400+ 行，难以阅读 | 每个 Agent < 50 行，职责单一 |
| 可测试性 | 需要 mock 整个数据库+ML | 每个 Agent 独立可测 |
| 可替换性 | 改一处可能全局影响 | 替换 Fraud Agent 不影响 Inventory Agent |
| 可解释性 | 日志混在一起 | 每个 Agent 的决策独立记录 |
| 课程映射 | 无法对应 COMP310 | 直接对应 Multi-Agent Systems |
| 扩展性 | 新增逻辑侵入核心函数 | 新增 Agent 只需在 Service 注册 |

> "最关键的点是**课程映射**。COMP310 的课程内容是自主 Agent 协商，如果代码里只是一个大函数，就无法在架构复盘中展示课程知识的应用。"

---

### Q18: 竞价公式是怎么设计的？如果业务需求变了怎么调整？

**标准回答：**

> "竞价公式是一个**启发式评分函数**：
> ```
> bid = 5 + stock_penalty + workload_penalty + distance_penalty - speed_bonus
> stock_penalty = max(0, item_count - stock_level) * 2.0
> workload_penalty = current_workload * 0.8
> distance_penalty = distance * 0.15
> speed_bonus = processing_speed * 1.1
> ```
>
> **设计思路：**
> - 基础值 5：确保 bid 始终为正，避免除零
> - 库存不足惩罚最高（系数 2.0）：缺货是最致命的履约失败
> - 距离惩罚次之（系数 0.15）：配送成本
> - 速度是负向因子：处理越快，bid 越低
>
> **业务需求变更时的调整：**
> - 如果公司策略是"优先服务大客户" → 添加 `order_value_bonus`
> - 如果某仓库有促销 → 添加 `promotion_discount`
> - 如果考虑碳排放 → 添加 `carbon_penalty = distance * emission_factor`
>
> 这些调整只需要修改 `WarehouseAgent.bid()` 方法，不影响其他 Agent。"

---

### Q19: Fraud Detection 的阈值 0.65 是怎么确定的？

**标准回答：**

> "当前版本 0.65 是一个**经验值**，基于以下考虑：
> 1. **业务容忍度**：电商通常希望误杀率（把正常订单标记为风险）低于 5%
> 2. **启发式模型的特性**：LightweightFraudClassifier 的 sigmoid 输出分布较集中
> 3. **测试验证**：通过 `test_order_review_required_high_risk` 测试用例确认阈值有效性
>
> **生产环境的阈值确定方法：**
> 1. 收集历史标注数据（正常订单 vs 欺诈订单）
> 2. 训练 XGBoost 模型
> 3. 绘制 ROC 曲线，选择使 F1-score 或业务指标最优的阈值
> 4. 用 A/B 测试验证线上效果
> 5. 定期重新评估（欺诈模式会变化）
>
> 当前代码已经预留了接口：`THRESHOLD = 0.65` 是模块级常量，易于调整。"

---

## 6. 机器学习模块

### Q20: 需求预测为什么用 MLP 而不是时间序列模型（如 ARIMA）？

**标准回答：**

> "这是一个好问题。选择 MLP 而非 ARIMA 的原因是：
>
> **ARIMA 的局限：**
> - 需要大量历史时间序列数据
> - 假设数据平稳（stationary），电商销量通常有季节性、促销冲击
> - 难以融入非时间特征（如价格、评分、品类）
>
> **MLP 的优势：**
> - 可以同时使用**时间特征**（day_of_week, month）和**商品特征**（price, rating, category）
> - 捕捉非线性关系：评分和价格对销量的影响不是线性的
> - 与课程映射直接对应：ELEC320 讲 MLP 回归
>
> **更优方案（未来）：**
> - 数据量充足时：LSTM/Transformer 时间序列模型（如 DeepAR, TFT）
> - 多商品联合预测：图神经网络（Graph Neural Network）
> - 冷启动问题：结合商品 embedding 和协同过滤"

---

### Q21: XGBoost 相比随机森林有什么优势？

**标准回答：**

| 维度 | 随机森林 | XGBoost |
|------|----------|---------|
| 训练方式 | Bagging（并行训练多棵树） | Boosting（串行，每棵树修正前一棵的错误） |
| 正则化 | 无内置正则化 | L1/L2 正则化 + 树复杂度惩罚 |
| 缺失值处理 | 需要预处理 | 自动学习缺失值分支 |
| 特征重要性 | 基于基尼不纯度 | 基于分裂增益 + SHAP 值 |
| 过拟合 | 较容易 | 正则化 + early stopping 控制 |
| 速度 | 快 | 更快（C++ 优化，支持 GPU） |

> "XGBoost 的核心优势是**Boosting + 正则化**。每棵树学习前一棵树的残差（梯度），逐步逼近最优解；同时 L1/L2 正则化防止过拟合。在欺诈检测这种**类别不平衡**问题上，XGBoost 的 `scale_pos_weight` 参数可以有效调整正负样本权重。"

---

### Q22: SHAP 值是什么？为什么用它而不是特征重要性？

**标准回答：**

> "SHAP（SHapley Additive exPlanations）基于**博弈论中的 Shapley 值**，计算每个特征对预测结果的边际贡献。
>
> **传统特征重要性的问题：**
> - `feature_importances_` 只告诉"哪个特征重要"，不告诉"怎么重要"
> - 无法解释**单个预测**——"这个订单为什么被标记为风险？"
>
> **SHAP 的优势：**
> - **局部解释**：每个预测都有独立的 SHAP 值解释
> - **可加性**：所有特征的 SHAP 值之和等于预测值与基准值的差
> - **一致性**：特征值增加时预测值也增加，则 SHAP 值非负
>
> **代码示例：**
> ```python
> shap_values = explainer.shap_values(X)
> fraud_shap = shap_values[1][0]  # 取 fraud 类别的 SHAP
> explanation = {
>     col: round(float(val), 6)
>     for col, val in zip(FEATURE_COLUMNS, fraud_shap)
> }
> # 结果示例：{"is_new_user": 0.45, "order_total": 0.12, ...}
> ```
> 这告诉我们：这个订单被标记为风险，主要是因为 `is_new_user` 贡献了 +0.45 的风险分。"

---

### Q23: 模型的 fallback 机制是怎么设计的？

**标准回答：**

> "核心思想是 **Graceful Degradation（优雅降级）**——系统在没有训练好的模型时仍能运行。
>
> **Demand Prediction 的 fallback：**
> ```python
> def predict_demand(product_features):
>     if not MODEL_PATH.exists():
>         return _heuristic_fallback(product_features)  # 启发式计算
>     # ... 加载 PyTorch 模型
> ```
>
> **Fraud Detection 的 fallback：**
> ```python
> if self._model_path.exists():
>     self.model = xgb.XGBClassifier()
>     self.model.load_model(str(self._model_path))
> else:
>     self.model = LightweightFraudClassifier()  # 启发式评分器
> ```
>
> **设计理由：**
> 1. **MVP 可立即运行**：不需要先收集数据、训练模型
> 2. **接口稳定**：Agent 调用 `predict_demand()` 时，不需要知道底层是 PyTorch 还是启发式
> 3. **渐进式升级**：后续替换为真实模型时，只需放文件到 `models/` 目录，Agent 代码不变"

---

## 7. DevOps 与部署

### Q24: Docker 多阶段构建的优势是什么？

**标准回答：**

> "多阶段构建的核心优势是**构建产物不进入最终镜像**。
>
> **前端 Dockerfile 的两阶段：**
> ```dockerfile
> # Stage 1: Build
> FROM node:20-alpine AS builder
> RUN npm ci
> RUN npm run build
>
> # Stage 2: Runtime
> FROM nginx:alpine
> COPY --from=builder /app/dist /usr/share/nginx/html
> ```
>
> **效果对比：**
> | 指标 | 单阶段（含 node） | 多阶段（仅 nginx） |
> |------|------------------|-------------------|
> | 镜像大小 | ~400MB | ~20MB |
> | 攻击面 | node, npm, gcc 等 | 仅 nginx |
> | 启动时间 | 慢 | 快 |
>
> 最终镜像只包含运行所需的最小文件集——Nginx + 静态 HTML/CSS/JS。"

---

### Q25: `depends_on.condition: service_healthy` 解决了什么问题？

**标准回答：**

> "解决了**启动顺序 race condition**。
>
> **问题场景：**
> ```yaml
> # 没有 condition 的旧写法
> backend:
>   depends_on:
>     - postgres
> ```
> 这只能保证 postgres **容器启动**，但不能保证 postgres **服务就绪**（数据库初始化完成、可以接受连接）。
>
> **结果：** backend 启动后立即连接数据库 → 连接失败 → 崩溃重启
>
> **解决方案：**
> ```yaml
> backend:
>   depends_on:
>     postgres:
>       condition: service_healthy  # 等 healthcheck 通过
>
> postgres:
>   healthcheck:
>     test: ["CMD-SHELL", "pg_isready -U postgres"]
>     interval: 10s
>     retries: 5
> ```
> 启动链：`postgres (healthy) → redis (healthy) → backend (healthy) → frontend`
> 每个服务只在前置依赖真正就绪后才启动。"

---

### Q26: 为什么 JSON 日志而不是纯文本日志？

**标准回答：**

> "结构化日志（JSON）vs 非结构化日志（纯文本）的核心差异：
>
> **纯文本日志：**
> ```
> 2024-01-15 10:23:45 INFO: Order created by user-123, total=59.99, items=2
> ```
> 需要正则解析：`(\d{4}-\d{2}-\d{2}) (\w+): Order created by (\w+), total=([\d.]+)`
> - 脆弱：日志格式一变，解析器就失效
> - 慢：正则匹配开销大
> - 难查询：无法直接按字段筛选
>
> **JSON 日志：**
> ```json
> {"timestamp": "2024-01-15T10:23:45Z", "level": "info", "event": "order.created", "user_id": "user-123", "order_total": 59.99, "item_count": 2}
> ```
> - 可直接被 **Elasticsearch**、**Grafana Loki**、**Splunk** 索引
> - 按字段搜索：`event="order.created" AND order_total > 50`
> - 聚合统计：`group by event, count()`
>
> 项目中用 `structlog.processors.JSONRenderer()` 统一输出 JSON，同时保留了 fallback 到纯文本的能力。"

---

### Q27: Prometheus 的 Counter、Histogram、Gauge 有什么区别？

**标准回答：**

| 类型 | 特性 | 示例 | 架构复盘关键词 |
|------|------|------|-----------|
| Counter | 单调递增，只能增加 | `orders_total{status="created"}` | 累计计数、请求总量 |
| Histogram | 采样分布，自动分桶 | `order_processing_seconds` | P50/P95/P99 延迟、SLA |
| Gauge | 可增可减，当前值 | `fraud_score{order_id="xxx"}` | 温度、队列长度、当前连接数 |
| Summary | 类似 Histogram，但客户端计算分位 | — | 已较少使用 |

> "项目中使用了三种：
> - `orders_total`（Counter）：追踪各状态订单数量
> - `order_processing_duration`（Histogram）：追踪处理延迟，Prometheus 自动计算分位数
> - `fraud_score`（Gauge）：记录最新风险评分
>
> 同时实现了 No-op fallback：prometheus_client 未安装时自动使用空实现，保证系统不崩溃。"

---

## 8. 系统设计与扩展

### Q28: 如果订单量增大 100 倍，系统哪里会成为瓶颈？如何扩展？

**标准回答：**

> "三个潜在瓶颈和扩展方案：
>
> **1. 数据库写入**
> - 瓶颈：单个 PostgreSQL 实例的写入吞吐量有限
> - 方案：
>   - 读写分离：1 主（写）+ N 从（读）
>   - 分库分表：按 `order_id` 哈希分片
>   - 消息队列：订单创建先写入 Kafka/RabbitMQ，消费者异步落库
>
> **2. WebSocket 连接管理**
> - 瓶颈：内存中的 `active_connections` 字典无法跨实例共享
> - 方案：
>   - Redis Pub/Sub：每个实例订阅 Redis 频道，实现多实例广播
>   - 专门的 WebSocket 服务：如 Socket.IO + Redis Adapter
>
> **3. ML 推理延迟**
> - 瓶颈：PyTorch/XGBoost 推理是 CPU 密集型，单线程处理慢
> - 方案：
>   - 模型服务化：TorchServe、Triton Inference Server
>   - 批处理：累积多个订单一起推理
>   - GPU 加速：特别是 MLP 推理"

---

### Q29: 如何确保订单创建和库存扣减的原子性？

**标准回答：**

> "当前实现通过 **SQLAlchemy 事务** 保证原子性：
>
> ```python
> async with AsyncSessionLocal() as session:
>     order_repo = OrderRepository(session)
>     product_repo = ProductRepository(session)
>     await order_repo.create_order(order_orm)
>     await product_repo.update_stock(product_id, -quantity)
>     await session.commit()  # 原子提交
> ```
>
> 如果 `update_stock` 失败（如库存被其他事务扣完），`session.commit()` 会抛出异常，订单也不会创建。
>
> **更严格的方案（生产环境）：**
> - **乐观锁**：`UPDATE products SET quantity = quantity - ? WHERE id = ? AND quantity >= ?`
> - **分布式锁**：Redis Redlock 防止并发扣减
> - ** Saga 模式**：订单服务和库存服务分离时，用补偿事务保证最终一致性"

---

### Q30: 如果仓库数量从 3 个增加到 100 个，竞价逻辑需要怎么改？

**标准回答：**

> "当前实现是 O(N) 遍历所有仓库，100 个仓库仍然很快（<1ms）。但业务逻辑需要调整：
>
> **1. 竞价策略升级**
> - 当前：最低 bid 胜出
> - 升级：Top-K 候选 + 二次评分（如考虑配送时效、客户满意度历史）
>
> **2. 竞价并行化**
> - 当前：顺序计算每个仓库的 bid
> - 升级：`asyncio.gather(*[warehouse.bid() for warehouse in warehouses])`
>
> **3. 仓库筛选**
> - 不需要所有仓库都投标——先按地理位置筛选（如 500km 内）
> - 再用库存过滤（只考虑有货的仓库）
>
> **4. 动态定价**
> - 引入实时需求数据：如果某地区订单激增，提高该地区仓库的优先级"

---

## 9. 行为架构复盘与项目展示

### Q31: 这个项目中最有挑战的部分是什么？

**建议回答结构（STAR 法则）：**

> "最有挑战的是**多智能体系统的协调设计**。
>
> **Situation**：课程要求展示 Multi-Agent Systems 的知识，但代码示例大多是概念性的，没有完整的履约流程。
> **Task**：我需要设计一个可运行的系统，让 6 个 Agent 协作完成订单履约。
> **Action**：
> 1. 先画状态机图，确定每个 Agent 的触发条件和输出
> 2. 设计 `BaseAgent` 基类统一日志接口，每个 Agent 独立实现核心逻辑
> 3. 用 `OrderService` 作为编排器，按顺序调用 Agent，同时通过 WebSocket 实时推送状态
> 4. 写测试用例验证各种边界情况（缺货、高风险、多商品）
> **Result**：系统可以正确处理正常订单、高风险订单和缺货订单，每个 Agent 的决策都有独立日志。架构复盘时我可以打开浏览器现场演示完整流程。"

---

### Q32: 如果你重做这个项目，会有什么不同？

**建议回答：**

> "我会从三个方面改进：
>
> **1. 架构层面**
> - 引入事件驱动架构：用 Kafka/RabbitMQ 替代同步 Agent 调用
> - 每个 Agent 成为独立微服务，通过事件总线通信
> - 好处：解耦、可独立扩展、支持 Saga 事务
>
> **2. 数据层面**
> - 添加数据管道：Airflow 定时清洗和导入商品数据
> - 引入特征存储：统一管理 ML 特征，避免训练-推理不一致
>
> **3. 工程层面**
> - 添加端到端测试：Playwright 自动化浏览器测试
> - 添加性能测试：Locust 模拟高并发下单
> - 添加 CI/CD：GitHub Actions 自动化测试和部署"

---

### Q33: 这个项目展示了你的什么能力？

**建议回答：**

> "这个项目展示了四个核心能力：
>
> **1. 全栈开发能力**
> 从前端 React 到后端 FastAPI，从数据库设计到 Docker 部署，覆盖完整的软件生命周期。
>
> **2. 系统架构能力**
> 不是简单的 CRUD，而是设计了多智能体协调、ML 推理接口、事件总线等复杂模块。每个模块都有明确的职责边界和接口契约。
>
> **3. 工程化思维**
> 考虑到了测试（pytest）、日志（structlog）、监控（Prometheus）、健康检查、fallback 机制。这些不是课程要求，而是工程实践的自觉。
>
> **4. 学习能力**
> 三门课程的知识被整合在一个系统中——这要求理解每门课的核心概念，并找到它们在工程中的映射点。"

---

> 祝架构复盘顺利！记住：回答问题时，先给**结论**，再讲**理由**，最后补**例子/代码**。🎯

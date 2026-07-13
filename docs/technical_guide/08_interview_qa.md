# 08 面试问答 —— FulfillCrew 高频面试题与参考答案

> 本文档按技术栈分类，每道题包含：参考答案、追问方向、常见陷阱。

---

## 一、项目概述与架构设计

### Q1: 请用 2 分钟介绍这个项目

**参考答案**：
> "FulfillCrew 是一个基于多智能体协调的电商订单履约系统。用户在前端选择商品并结账后，订单进入一个由 6 个 Agent 组成的协作工作流：欺诈检测 Agent 评分风险，库存 Agent 检查可用性，协调 Agent 通过简化的 Contract Net Protocol 让三个仓库 Agent 竞价，最终选出最优仓库，同时需求预测 Agent 估算未来销量。后端使用 FastAPI + SQLAlchemy 2.0 async + PostgreSQL，前端使用 React 18 + TypeScript + Vite，支持 WebSocket 实时推送。整个系统通过 Docker Compose 编排，包含 Nginx 反向代理、Redis 事件总线和 Prometheus 监控。"

**追问方向**：
- 6 个 Agent 的具体职责和协作顺序？
- 为什么用 Contract Net Protocol 而不是其他协调机制？
- 如果订单量增长 100 倍，架构怎么扩展？

**常见陷阱**：不要说"这是一个电商网站"——太浅。要说"多智能体协调 + ML 推理 + 事件驱动"的完整链路。

---

### Q2: 为什么把课程作业升级为这个项目？

**参考答案**：
> "原始课程作业是一个简单的 React 购物车，功能停在商品展示和结账。我意识到大多数学生的项目都止步于此，而面试中需要展示的是**工程化思维**和**系统设计能力**。于是我将三门课程的知识点串联：云计算（前端+后端+部署）、多智能体（协调协议）、神经网络（需求预测+欺诈检测），形成一个从下单到履约的完整闭环。这样既展示了课程知识，又体现了将零散功能整合为系统的工程能力。"

---

## 二、前端技术栈

### Q3: React 18 的 Concurrent Features 在这个项目中如何体现？

**参考答案**：
> "WebSocket 消息推送是高频事件——订单每经过一个 Agent 步骤，后端就推送一次更新。React 18 的 Automatic Batching 确保同一事件循环中的多次 `setStatus` 调用合并为一次重渲染，避免高频更新导致 UI 卡顿。如果后续引入更复杂的场景（如实时竞价数据流），可以使用 `useTransition` 区分紧急更新（如输入框）和非紧急更新（如大数据列表）。"

**追问**：
- `useTransition` 和 `useDeferredValue` 的区别？
- 如果 WebSocket 每秒推送 100 次，React 还撑得住吗？

---

### Q4: 为什么用 Vite 而不是 Create React App？

**参考答案**：
> "Vite 使用原生 ESM 和 esbuild 预构建，开发服务器启动在毫秒级，HMR 更新即时。CRA 的 webpack 在开发阶段也需要完整打包，随着项目增大启动时间越来越长。此外 Vite 的生产构建使用 Rollup，tree-shaking 更彻底，产物更小。"

**追问**：
- Vite 的 `import.meta.env` 在构建时怎么处理？
- Vite 的预构建（pre-bundling）解决了什么问题？

---

### Q5: WebSocket 连接管理中，如果 orderId 切换，旧连接怎么处理？

**参考答案**：
> "`useOrderSocket` hook 的 `useEffect` 依赖数组是 `[orderId]`，当 orderId 变化时，React 先执行清理函数 `ws.close()` 关闭旧连接，再建立新连接。这避免了内存泄漏和连接残留。组件卸载时（如页面跳转），同样通过清理函数关闭连接。"

**追问**：
- 如果前端崩溃后重新打开，怎么恢复之前的 WebSocket 连接？
- 如何防止 WebSocket 连接被中间代理（如 Nginx）超时断开？

---

## 三、后端与数据库

### Q6: FastAPI 的 `lifespan` 是什么？和 `on_event` 有什么区别？

**参考答案**：
> "`lifespan` 是 FastAPI 的现代生命周期管理方式，使用 `asynccontextmanager`。`yield` 之前执行初始化（如创建数据库表），`yield` 之后执行清理。相比旧的 `@app.on_event('startup')`，`lifespan` 与 ASGI 规范对齐，支持依赖注入，且事件顺序可控。"

**追问**：
- 如果初始化失败（如数据库连不上），应用会启动吗？
- 如何优雅地处理数据库初始化中的并发问题？

---

### Q7: SQLAlchemy 2.0 的 `Mapped` 和 `mapped_column` 相比 1.x 有什么改进？

**参考答案**：
> "`Mapped[T]` 是类型注解，让 IDE 和类型检查器能推断模型字段类型。`mapped_column()` 替代了 `Column()`，语义更清晰。最关键的是 SQLAlchemy 2.0 原生支持 async，使用 `AsyncSession` 和 `async_sessionmaker`，不再依赖 `databases` 等第三方库。`selectinload` 等 eager loading 策略也完全支持 async，避免 N+1 查询问题。"

**追问**：
- `expire_on_commit=False` 是做什么的？
- 如果不用 `selectinload`，访问 `order.items` 会发生什么？

---

### Q8: Repository 模式有什么好处？和 DAO 有什么区别？

**参考答案**：
> "Repository 将数据访问逻辑从业务逻辑中分离，Service 层只关注业务编排，不关注 SQL 细节。这带来了几个好处：1) 单元测试时可以注入 mock Repository；2) 更换数据库（如从 PostgreSQL 到 MongoDB）只需改 Repository 实现；3) 领域逻辑更纯净。DAO 粒度更细，通常直接映射数据库表，适合简单 CRUD。Repository 面向聚合根，更适合复杂业务领域。"

**追问**：
- 如果 Repository 方法越来越多，怎么避免类膨胀？
- CQRS 和 Repository 有什么关系？

---

### Q9: 为什么用异步数据库（asyncpg）而不是同步的 psycopg2？

**参考答案**：
> "FastAPI 基于 ASGI，原生支持 async/await。如果使用同步的 psycopg2，数据库查询会阻塞整个事件循环，导致其他请求无法处理。asyncpg 是 PostgreSQL 的原生异步驱动，配合 SQLAlchemy 2.0 的 `AsyncSession`，可以实现真正的并发 I/O——一个 worker 进程在等待数据库响应时，事件循环可以调度其他请求。"

**追问**：
- 异步数据库查询的并发上限是多少？
- 如果某个查询特别慢（如 10 秒），会影响其他请求吗？

---

## 四、多智能体系统

### Q10: 什么是 Contract Net Protocol？在这个项目中如何简化？

**参考答案**：
> "Contract Net Protocol 是 FIPA 定义的多智能体任务分配协议。标准流程包含：Manager 广播 CFP（Call for Proposal）→ Contractor 评估能力并提交 bid → Manager 评估 bids 并选择 winner → 通知所有 Contractor。在本项目中简化为：Coordinator Agent 直接调用 `warehouse.bid()` 方法（同进程内），用 `min(bid)` 选择 winner。省去了消息序列化、超时机制和 ACL 消息格式，但保留了协议的核心思想：任务广播 + 投标 + 选择。"

**追问**：
- 如果扩展到分布式，用什么消息队列替代方法调用？
- 最低 bid 策略是否最优？有没有更好的选择策略？

---

### Q11: 仓库竞价的公式是怎么设计的？权重可以学习吗？

**参考答案**：
> "竞价公式是启发式评分函数：`bid = 5 + stock_penalty + workload_penalty + distance_penalty - speed_bonus`。权重（2.0, 0.8, 0.15, 1.1）是人工经验值。可以改为数据驱动：收集历史订单数据（实际选择的仓库、配送时间、客户满意度），用线性回归或神经网络学习最优权重，使总成本最小化。这体现了从规则系统到数据驱动系统的演进路径。"

**追问**：
- 如果库存不足，库存惩罚为什么乘 2.0？
- 如何用强化学习（RL）优化竞价策略？

---

### Q12: 为什么先 fraud 检测再 inventory 检查？

**参考答案**：
> "这是短路优化（Short-circuit Pattern）。如果订单明显欺诈（风险分数高），直接返回 review_required，无需查询库存，节省一次数据库查询。如果先查库存，再发现欺诈，库存查询就浪费了。同理，如果库存不足，也直接返回，跳过仓库竞价和需求预测。这种顺序设计在系统层面减少了不必要的计算。"

**追问**：
- 如果欺诈模型和库存查询可以并行，你会怎么改？
- 这种顺序对用户体验有什么影响？

---

## 五、机器学习

### Q13: 需求预测的 MLP 网络结构是怎样的？为什么这样设计？

**参考答案**：
> "网络有 3 层：输入层（9 维特征）→ 隐藏层1（64 神经元，ReLU，Dropout 0.2）→ 隐藏层2（32 神经元，ReLU，Dropout 0.2）→ 输出层（1 神经元，标量预测）。使用 ReLU 激活引入非线性，Dropout 防止过拟合。损失函数是 MSE（回归任务），优化器是 Adam（自适应学习率）。训练数据是 2000 条合成样本，从 4 个商品目录扰动生成。"

**追问**：
- 为什么用 MSE 而不是 MAE？
- 如果训练数据只有 4 条真实商品，模型能泛化吗？
- 合成数据的生成逻辑是什么？如何确保数据分布合理？

---

### Q14: XGBoost 和 LightGBM 有什么区别？为什么选 XGBoost？

**参考答案**：
> "XGBoost 和 LightGBM 都是梯度提升框架，核心区别：
> 1. **树生长策略**：XGBoost 使用 level-wise（按层生长），LightGBM 使用 leaf-wise（按叶子生长），后者更快但可能过拟合
> 2. **分裂点查找**：XGBoost 预排序，LightGBM 基于 Histogram，内存效率更高
> 3. **类别特征**：LightGBM 原生支持类别特征，XGBoost 需要手动编码
> 选 XGBoost 是因为教学项目需要稳定可靠的实现，且 XGBoost 的 SHAP 集成成熟。LightGBM 在大数据场景下更快，但本项目数据量小，差异不明显。"

**追问**：
- Gradient Boosting 和 Random Forest 的区别？
- 如果特征维度从 10 增加到 1000，XGBoost 还能用吗？

---

### Q15: SHAP 可解释性在 fraud 检测中怎么用？

**参考答案**：
> "SHAP（SHapley Additive exPlanations）基于博弈论的 Shapley Value，计算每个特征对预测结果的贡献。对于每个订单，SHAP 输出一组值：正值表示该特征增加了风险，负值表示降低了风险。例如 'is_new_user=1' 可能贡献 +0.15，'order_total=20' 可能贡献 -0.05。这让模型从黑盒变成可解释系统，满足金融合规的"可解释 AI"要求。前端可以展示每个特征的风险贡献，帮助审核人员理解为什么订单被标记。"

**追问**：
- SHAP 值和特征重要性（Feature Importance）有什么区别？
- SHAP 计算成本如何？高并发场景下怎么处理？

---

## 六、基础设施与可观测性

### Q16: Redis pub/sub 和 RabbitMQ 有什么区别？为什么选 Redis？

**参考答案**：
> "Redis pub/sub 是内存中的消息广播，低延迟、无持久化，适合实时通知。RabbitMQ 是消息队列，支持持久化、ACK、路由、死信队列，适合可靠性要求高的任务队列。本项目选 Redis 是因为：1) 已在 Docker Compose 中部署，无需额外服务；2) 消息可丢失（WebSocket 推送不是关键业务）；3) 简单，教学场景够用。如果后续需要可靠消息（如订单状态必须不丢失），可以替换为 RabbitMQ 或 Kafka。"

**追问**：
- Redis pub/sub 的 consumer 挂掉后，消息会丢失吗？
- 如果 Redis 也挂了，事件总线怎么工作？

---

### Q17: Prometheus 的 Pull 模式和 Push 模式有什么区别？

**参考答案**：
> "Prometheus 默认是 Pull 模式：Prometheus 服务器定期（通常 15 秒）从目标 `GET /metrics` 抓取数据。优势：目标不需要知道 Prometheus 地址，便于多 Prometheus 实例抓取同一目标做高可用，且能自然检测目标是否存活（抓不到 = 可能挂了）。Push 模式通过 Pushgateway 实现，适合短生命周期任务（如批处理）。本项目用 Pull 模式，因为后端是长运行服务。"

**追问**：
- 如果后端有 100 个实例，Prometheus 怎么抓取？
- Histogram 的 bucket 怎么选择？

---

### Q18: 健康检查返回 degraded 时，Docker 会做什么？

**参考答案**：
> "Docker 的 healthcheck 只检查 exit code（0 = 健康，非 0 = 不健康），不会解析 JSON 中的 'degraded' 语义。如果连续失败（默认 retries=3），容器被标记为 unhealthy，然后根据 `restart` 策略决定是否重启。'degraded' 是我们应用层的状态，表示部分依赖不可用（如 Redis 挂了但数据库还在），通常不触发重启，而是让运维人员介入。更精确的做法是：为不同严重级别设置不同的 HTTP 状态码（200=健康，503=degraded，500=不健康）。"

**追问**：
- 健康检查的频率和超时怎么设置？
- 如果健康检查本身挂了，怎么发现？

---

## 七、Docker 与部署

### Q19: Docker 多阶段构建的好处是什么？

**参考答案**：
> "多阶段构建将构建环境和运行环境分离。第一阶段（builder）安装编译依赖（如 gcc、node_modules），第二阶段只复制构建产物。好处：1) 镜像体积更小（最终镜像不含编译工具）；2) 攻击面更小（运行环境只有必要文件）；3) 构建缓存更高效（依赖层未变更时直接复用）。例如前端镜像：builder 阶段用 Node 编译，运行阶段只用 Nginx 服务静态文件。"

**追问**：
- `COPY --from=builder` 的原理是什么？
- 如果构建阶段失败，后续阶段还会执行吗？

---

### Q20: Nginx 的 `try_files $uri $uri/ /index.html` 是什么意思？

**参考答案**：
> "这是 SPA（单页应用）路由的关键配置。当用户访问 `/orders/123` 时，Nginx 先尝试查找 `/orders/123` 文件（不存在），再尝试 `/orders/123/` 目录（不存在），最后回退到 `/index.html`。React 应用加载后，React Router 读取浏览器 URL 并渲染对应组件。如果没有这个配置，用户刷新页面会返回 404。"

**追问**：
- 这种回退对 SEO 有什么影响？
- 如果要做服务端渲染（SSR），这个配置怎么改？

---

## 八、系统设计与扩展

### Q21: 如果订单量从每天 100 增长到 10 万，怎么扩展？

**参考答案**：
> "水平扩展的几个层面：
> 1. **前端**：CDN 缓存静态资源，Nginx 做负载均衡
> 2. **后端**：多进程/多容器部署（Uvicorn `--workers` 或 Docker 多实例），前置负载均衡器（Nginx 或 HAProxy）
> 3. **数据库**：读写分离（主库写、从库读），分库分表（按 user_id 或 order_id 哈希），连接池扩容
> 4. **缓存**：Redis 缓存商品列表和热点库存，减少数据库压力
> 5. **事件总线**：从 Redis pub/sub 升级到 Kafka，支持消息持久化和回溯
> 6. **ML 推理**：模型服务独立部署（TF Serving / TorchServe），支持 GPU 加速和批量推理
> 7. **异步处理**：订单创建后写入消息队列，Worker 进程异步处理 fraud、inventory、竞价等步骤，减少 API 响应时间"

**追问**：
- 分库分表后，怎么保证订单 ID 全局唯一？
- 如果数据库主库挂了，怎么保证一致性？

---

### Q22: 如何保证订单处理的幂等性？

**参考答案**：
> "当前实现中，如果客户端重试 POST /orders，会创建重复订单。幂等性改进方案：
> 1. **客户端生成幂等键**：请求头携带 `Idempotency-Key: <uuid>`，后端用 Redis 缓存键（TTL 24 小时），重复请求返回缓存结果
> 2. **数据库唯一约束**：order_id 本身由 UUID 生成，天然唯一，但需确保业务逻辑不重复执行（如库存只扣一次）
> 3. **状态机**：订单状态流转（pending → fraud_checked → inventory_checked → ...），每个状态转换幂等，重复操作被忽略"

---

## 九、行为面试与项目反思

### Q23: 这个项目最大的技术挑战是什么？你怎么解决的？

**参考答案**：
> "最大的挑战是**如何在不引入微服务复杂度的情况下，展示多智能体协调**。我选择在单进程内用 Python class 模拟 Agent，通过简化的 Contract Net Protocol 实现仓库竞价。这样既展示了多智能体概念，又保持了代码的可读性。如果一开始就引入 RabbitMQ 或 gRPC，代码量翻倍，学生难以理解。这个设计决策体现了**渐进复杂度**的工程思维：先跑通核心逻辑，再按需扩展。"

---

### Q24: 如果你重新设计这个项目，会改什么？

**参考答案**：
> "几个改进方向：
> 1. **状态机**：将订单状态流转从硬编码的 `if/else` 改为显式状态机（如 `transitions` 库），更易于维护和扩展
> 2. **异步任务队列**：用 Celery + Redis 将 fraud 检测、竞价等步骤异步化，API 响应时间从秒级降到毫秒级
> 3. **测试覆盖**：当前测试主要是冒烟测试，可以增加单元测试覆盖率（如 Agent 的边界条件）、集成测试（数据库事务回滚）、性能测试（Locust 压测）
> 4. **前端状态管理**：用 Zustand 或 Redux Toolkit 替代组件内状态，便于跨组件共享订单数据
> 5. **真实数据**：接入公开电商数据集（如 UCI Online Retail），用真实数据训练模型"

---

### Q25: 你怎么向别人证明这个项目的价值？

**参考答案**：
> "三个维度：
> 1. **技术深度**：不是简单的 CRUD，而是多智能体协调 + ML 推理 + 事件驱动 + 可观测性，技术栈覆盖全栈开发、分布式系统、数据科学
> 2. **工程实践**：遵循 12-Factor App 原则，有 Docker 化部署、健康检查、结构化日志、监控指标，可直接用于生产环境演示
> 3. **可扩展性**：每个模块都有清晰的接口和升级路径，如 ML 模型从启发式到神经网络、事件总线从 InMemory 到 Redis 到 Kafka，展示了架构演进能力"

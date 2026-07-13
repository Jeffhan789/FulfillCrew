# 面试突击：3 天备战指南

> **预计时间**：3 天（Day 1: 2h, Day 2: 4h, Day 3: 3h）  
> **前置知识**：已完成 [01_module_by_module.md](./01_module_by_module.md) 或至少通读 `docs/technical_guide/01_architecture_overview.md`  
> **目标**：能够在面试中流畅讲解项目、回答高频问题、完成代码走读

---

## 目录

- [Day 1: 项目 Elevator Pitch](#day-1-项目-elevator-pitch)
- [Day 2: 高频问题速查](#day-2-高频问题速查)
- [Day 3: 代码走读练习](#day-3-代码走读练习)
- [自测检查清单](#自测检查清单)

---

## Day 1: 项目 Elevator Pitch

> **预计时间**：2 小时（练习 + 录音/录像自检）

### 1.1 15 秒版本（电梯演讲）

**模板**：

> "FulfillCrew 是一个**多智能体电商订单履约系统**。用户下单后，6 个 AI Agent 协作完成欺诈检测、库存检查、仓库竞价选择、需求预测，支持 WebSocket 实时推送和 Docker 容器化部署。技术栈是 React 18 + FastAPI + PostgreSQL + Redis + PyTorch/XGBoost。"

**练习要求**：
- 在 15 秒内说完，不卡顿
- 语速适中，重点突出"多智能体"和"6 个 Agent"
- 根据面试官背景调整侧重点（后端面试官强调 FastAPI + async；ML 面试官强调 MLP + XGBoost + SHAP）

### 1.2 3 分钟版本（项目介绍）

**结构**：

```
第 0-30s:  项目背景 → 为什么做这个项目？
第 30-90s: 核心架构 → 画架构图，讲解各层职责
第 90-150s: 技术亮点 → 3 个最有深度的技术点
第 150-180s: 个人贡献 → 你做了什么？遇到什么挑战？
```

**详细脚本模板**：

> "这个项目叫 FulfillCrew，是我三门课程（云计算、多智能体、神经网络）的综合实践。
>
> **背景**：电商订单履约涉及多个环节——欺诈检测、库存检查、仓库选择——传统做法是硬编码规则，我尝试用 Multi-Agent 协作来模拟更智能的决策。
>
> **架构**：前端是 React 18 + TypeScript + Vite，后端是 FastAPI + SQLAlchemy 2.0 async + PostgreSQL，6 个 Agent 通过 Contract Net Protocol 协作完成订单处理，ML 模块用 PyTorch MLP 做需求预测、XGBoost + SHAP 做欺诈检测。整个系统用 Docker Compose 部署，Nginx 做反向代理。
>
> **亮点**：
> 1. **防御性编程**：Redis 不可用时自动回退到 InMemoryEventBus；structlog 不可用时回退到标准库 logging
> 2. **可观测性**：结构化日志 + Prometheus 指标 + 多维度健康检查
> 3. **可解释性**：每个仓库 bid 附带 reason 字符串；fraud 检测集成 SHAP 解释
>
> **我的贡献**：我独立完成了从架构设计到部署上线的全流程，最深的挑战是理解 SQLAlchemy 2.0 async 的 session 生命周期——花了两天排查一个 connection pool 耗尽的问题，最后发现是 session 没有正确关闭。"

### 1.3 手绘架构图练习

**面试时常见要求**："画一下你们的架构图"

练习在纸上或白板上画出以下架构图，控制在 60 秒内：

```
Browser → Nginx → FastAPI → PostgreSQL (数据)
                     ↓
              ┌─────┴─────┐
            Agents     ML Models
            (6个)      (3个)
                     ↓
              Redis (事件总线)
```

**每个层级的职责一句话**：
- **Nginx**：静态资源托管 + 反向代理
- **FastAPI**：REST API + WebSocket + Agent 编排
- **PostgreSQL**：订单、商品、决策记录持久化
- **Agents**：6 个 Agent 协作完成订单履约
- **ML Models**：需求预测、欺诈检测、商品分类
- **Redis**：事件总线 pub/sub

### 1.4 针对不同岗位的 pitch 调整

| 岗位 | 强调重点 | 一句话概括 |
|------|----------|------------|
| **后端开发** | FastAPI async、SQLAlchemy 2.0、Repository 模式、事务管理 | "我设计了一个全异步的订单处理流水线，使用 SQLAlchemy 2.0 async + Repository 模式保证数据一致性" |
| **前端开发** | React 18 并发特性、WebSocket 实时推送、Recharts 可视化 | "我实现了一个实时订单追踪 Dashboard，用 WebSocket 推送 + Recharts 可视化多智能体决策过程" |
| **ML 工程师** | PyTorch MLP、XGBoost、SHAP、模型可解释性 | "我训练了三个 ML 模型，重点解决了可解释性问题——用 SHAP 解释每次欺诈检测的原因" |
| **DevOps/SRE** | Docker Compose、健康检查、Prometheus、结构化日志 | "我用 Docker Compose 部署了 4 个服务，配置了完整的可观测性体系——日志 + 指标 + 健康检查" |
| **全栈** | 端到端交付能力、三门课程融合 | "我从 0 到 1 构建了一个全栈系统，融合了三门课程的理论知识" |

---

## Day 2: 高频问题速查

> **预计时间**：4 小时
> **核心文档**：`docs/interview/interview_qa.md`（33 道高频题 + 参考答案）

### 2.1 问题分类速查表

`interview_qa.md` 中的 33 道题分为 7 大类。下面是每类高频题索引，建议按顺序复习：

#### 第一类：项目架构概览（Q1-Q3）

| 题号 | 问题 | 面试频率 | 难度 |
|------|------|----------|------|
| Q1 | 请用一句话描述 FulfillCrew 是什么系统？ | ⭐⭐⭐⭐⭐ | 简单 |
| Q2 | 画一下 v2.0 的完整架构图 | ⭐⭐⭐⭐⭐ | 中等 |
| Q3 | 项目如何体现三门课程的融合？ | ⭐⭐⭐⭐ | 中等 |

**速读建议**：直接背诵 Q1 的标准答案，反复画 Q2 的架构图。

📎 **直达链接**：[interview_qa.md — 一、项目架构概览](../interview/interview_qa.md#一项目架构概览)

#### 第二类：COMP315 Cloud Computing（Q4-Q10）

| 题号 | 问题 | 面试频率 | 难度 |
|------|------|----------|------|
| Q4 | 为什么前端选择 Vite 而不是 CRA？ | ⭐⭐⭐⭐ | 中等 |
| Q5 | FastAPI 相比 Flask/Django 的优势？ | ⭐⭐⭐⭐⭐ | 中等 |
| Q6 | 解释一下 CORS 配置 | ⭐⭐⭐⭐ | 简单 |
| Q7 | Docker Compose 如何管理服务依赖？ | ⭐⭐⭐⭐ | 中等 |
| Q8 | 为什么用 Docker 多阶段构建？ | ⭐⭐⭐⭐ | 中等 |

📎 **直达链接**：[interview_qa.md — 二、COMP315 Cloud Computing](../interview/interview_qa.md#二comp315-cloud-computing)

#### 第三类：COMP310 Multi-Agent Systems（Q11-Q18）

| 题号 | 问题 | 面试频率 | 难度 |
|------|------|----------|------|
| Q11 | 什么是 Contract Net Protocol？ | ⭐⭐⭐⭐⭐ | 中等 |
| Q12 | 为什么用 BaseAgent 基类？ | ⭐⭐⭐⭐ | 中等 |
| Q13 | 订单流水线为什么顺序执行？ | ⭐⭐⭐⭐⭐ | 困难 |
| Q14 | 如何确保数据一致性？ | ⭐⭐⭐⭐⭐ | 困难 |
| Q15 | 仓库竞价策略是什么？ | ⭐⭐⭐⭐ | 中等 |

📎 **直达链接**：[interview_qa.md — 三、COMP310 Multi-Agent Systems](../interview/interview_qa.md#三comp310-multi-agent-systems)

#### 第四类：ELEC320 Neural Networks（Q19-Q25）

| 题号 | 问题 | 面试频率 | 难度 |
|------|------|----------|------|
| Q19 | MLP 的输入输出是什么？ | ⭐⭐⭐⭐ | 简单 |
| Q20 | 为什么用 XGBoost 做欺诈检测？ | ⭐⭐⭐⭐⭐ | 中等 |
| Q21 | SHAP 是什么？为什么重要？ | ⭐⭐⭐⭐⭐ | 中等 |
| Q22 | TF-IDF + LR 适合什么场景？ | ⭐⭐⭐⭐ | 中等 |
| Q23 | 模型评估指标怎么选？ | ⭐⭐⭐⭐ | 中等 |

📎 **直达链接**：[interview_qa.md — 四、ELEC320 Neural Networks](../interview/interview_qa.md#四elec320-neural-networks)

#### 第五类：v2.0 工程升级（Q26-Q30）

| 题号 | 问题 | 面试频率 | 难度 |
|------|------|----------|------|
| Q26 | SQLAlchemy 2.0 async 有什么变化？ | ⭐⭐⭐⭐⭐ | 困难 |
| Q27 | Repository 模式的优缺点？ | ⭐⭐⭐⭐⭐ | 中等 |
| Q28 | Redis 不可用时怎么办？ | ⭐⭐⭐⭐ | 中等 |
| Q29 | WebSocket 断线怎么处理？ | ⭐⭐⭐⭐ | 中等 |
| Q30 | 结构化日志比 print 好在哪里？ | ⭐⭐⭐⭐ | 简单 |

📎 **直达链接**：[interview_qa.md — 五、v2.0 工程升级深度题](../interview/interview_qa.md#五v20-工程升级深度题)

#### 第六类：系统设计 & 综合场景（Q31-Q32）

| 题号 | 问题 | 面试频率 | 难度 |
|------|------|----------|------|
| Q31 | 如何把这个系统扩展为分布式？ | ⭐⭐⭐⭐⭐ | 困难 |
| Q32 | 如果订单量增长 10 倍，你会怎么优化？ | ⭐⭐⭐⭐⭐ | 困难 |

📎 **直达链接**：[interview_qa.md — 六、系统设计 & 综合场景题](../interview/interview_qa.md#六系统设计--综合场景题)

#### 第七类：代码走读（Q33）

| 题号 | 问题 | 面试频率 | 难度 |
|------|------|----------|------|
| Q33 | 走读 `OrderService.create_order()` 方法 | ⭐⭐⭐⭐⭐ | 困难 |

📎 **直达链接**：[interview_qa.md — 七、代码走读题](../interview/interview_qa.md#七代码走读题)

### 2.2 面试追问应对

面试官不会只问一个问题，而是会**追问**。**每个答案背后准备 2-3 层追问**：

**示例**：

> **面试官**："为什么用 FastAPI？"
>
> **你**："FastAPI 原生支持 async/await，自动生成 OpenAPI 文档，有 Pydantic 数据验证。"
>
> **面试官（追问 1）**："那 Django 也有 async 支持了，为什么不用 Django？"
>
> **你**："Django 的 async 是后来添加的，很多 ORM 操作仍需要同步 fallback。而且这个项目不需要 Django 的 admin、auth 等重型功能，FastAPI 更轻量。"
>
> **面试官（追问 2）**："如果项目需要后台管理界面，你会怎么选？"
>
> **你**："如果规模小，可以在 FastAPI 上叠加一个轻量 admin 或者用 React 单独做一个管理后台。如果规模大、团队熟悉 Django，可以考虑 Django + Django REST Framework 做后端，前端仍用 React。"

### 2.3 技术亮点清单（面试加分项）

背诵以下 5 个技术亮点，面试时主动提及：

1. **防御性编程**
   - Redis → InMemoryEventBus fallback
   - structlog → 标准库 logging fallback
   - ProductService → JSON 文件 fallback（DB 不可用时）

2. **可观测性**
   - 结构化日志（JSON）：可搜索、可聚合
   - Prometheus 指标：订单数、处理耗时、欺诈分数
   - 多维度健康检查：API、DB、Redis

3. **可解释性**
   - 仓库 bid 附带 `reason` 字符串
   - 欺诈检测集成 SHAP，解释每个特征的贡献
   - 前端 Dashboard 可视化决策过程

4. **渐进复杂度**
   - 从同进程 Agent（当前）→ 可扩展为分布式消息队列（未来）
   - 从 InMemoryEventBus（开发）→ Redis（生产）

5. **全异步**
   - FastAPI + SQLAlchemy 2.0 async + asyncpg
   - 无阻塞 I/O，支持高并发

---

## Day 3: 代码走读练习

> **预计时间**：3 小时
> **目标**：能够在面试中快速走读代码，指出问题和改进点

### 3.1 练习 1：OrderService.create_order()

**代码位置**：`backend/services/order_service.py`（第 147-588 行）

**任务**：
1. 5 分钟内，向面试官口头走读这个方法的核心流程
2. 指出至少 2 个可以改进的地方

**参考答案要点**：
- 7 步流水线：创建 → 欺诈 → 库存 → 竞价 → 需求预测 → 预留 → 持久化 → 指标
- 顺序执行的原因：安全依赖（欺诈在库存前）、数据一致性（单事务）
- **改进点 1**：fraud 和 demand 可以并行（它们互相独立）
- **改进点 2**：WebSocket 是 fire-and-forget，可以增加重试机制
- **改进点 3**：`_persist_order()` 中 ORM 对象创建可以抽离为 builder 模式

### 3.2 练习 2：EventBus 抽象设计

**代码位置**：`backend/infrastructure/event_bus.py`

**任务**：
1. 解释 `EventBus` 抽象基类的作用
2. 为什么需要 `InMemoryEventBus` fallback？
3. 如果要增加 Kafka 支持，需要改哪些地方？

**参考答案要点**：
- 抽象基类定义统一接口，`publish()` / `subscribe()` / `close()`
- 符合开闭原则：新增 KafkaEventBus 不需要修改现有代码
- InMemory fallback：开发环境无需 Redis 即可运行；Redis 故障时不影响核心功能

### 3.3 练习 3：Repository 模式

**代码位置**：`backend/repositories/order_repository.py`（或任意 repository）

**任务**：
1. 解释 Repository 模式的优点
2. 如果不使用 Repository，直接在 service 中调用 SQLAlchemy，有什么问题？
3. `AsyncSessionLocal` 的生命周期是怎么管理的？

**参考答案要点**：
- 优点：隔离数据访问、便于测试 mock、支持未来 DB 迁移
- 不用 Repository 的问题：业务代码与 SQL 耦合、难以单元测试、违反单一职责
- Session 生命周期：`async with AsyncSessionLocal() as session`，自动关闭

### 3.4 练习 4：WebSocket 实时推送

**代码位置**：
- 后端：`backend/api/websocket.py`
- 前端：`frontend/src/hooks/useOrderSocket.ts`

**任务**：
1. 解释 WebSocket 连接是如何建立的
2. 如果订单完成后 WebSocket 连接断开，用户还能看到结果吗？
3. 如果要支持 1000 个并发 WebSocket 连接，需要什么改进？

**参考答案要点**：
- 后端：`WebSocketEndpoint` 接收连接，维护 `order_id → connection` 映射
- 前端：`useOrderSocket` Hook 在 `orderId` 变化时建立新连接
- 断开也能看到结果：订单已持久化到 DB，可以轮询 `/orders/{id}` fallback
- 1000 并发：需要 WebSocket 连接池、负载均衡、Redis pub/sub 跨实例同步

### 3.5 练习 5：Docker Compose 编排

**代码位置**：`docker-compose.yml`

**任务**：
1. 解释 `depends_on` 的 `condition: service_healthy` 作用
2. 如果 `postgres` 启动慢，`backend` 会怎么做？
3. 生产环境中，Docker Compose 有什么局限性？如何改进？

**参考答案要点**：
- `condition: service_healthy`：确保依赖服务真正就绪后才启动，而不是仅仅容器启动
- Postgres 启动慢：backend 会等待，因为 `depends_on` 阻塞；同时有 `restart: unless-stopped`
- 生产局限：无自动扩缩容、无服务发现、单节点部署；改进：Kubernetes / ECS + 服务网格

---

## 自测检查清单

完成 3 天面试准备后，你应该能够：

### Elevator Pitch
- [ ] 15 秒版本：流畅说完，不卡顿
- [ ] 3 分钟版本：结构清晰，有背景、架构、亮点、挑战
- [ ] 手绘架构图：60 秒内完成，每个层级一句话解释
- [ ] 针对不同岗位调整 pitch 重点

### 高频问题
- [ ] 33 道题中，能流畅回答至少 25 道（不看答案）
- [ ] 对每道答案，能应对 2-3 层追问
- [ ] 能主动提及 5 个技术亮点中的至少 3 个

### 代码走读
- [ ] 5 分钟内走读 `create_order()` 并指出改进点
- [ ] 解释 EventBus 抽象设计的优点
- [ ] 解释 Repository 模式的作用
- [ ] 解释 WebSocket 连接建立和断线处理
- [ ] 解释 Docker Compose 的服务依赖机制

### 模拟面试
- [ ] 找同学/朋友进行一次 30 分钟模拟面试
- [ ] 录制自己的回答，回放检查语速、口头禅、逻辑性
- [ ] 准备 3 个"我最自豪的技术决策"故事（带具体数字）

---

## 附录：面试心态

1. **诚实**：不会的问题直接说"这个我没深入研究过，但我可以推测..."
2. **结构化**：用"首先...其次...最后..."组织回答
3. **举例子**：抽象概念后用代码或场景举例
4. **反问**：最后准备 1-2 个反问面试官的问题（"团队的技术栈规划是什么？"）

> 🎉 祝你面试顺利！如需更多练习，可返回 [01_module_by_module.md](./01_module_by_module.md) 深入任何薄弱模块。

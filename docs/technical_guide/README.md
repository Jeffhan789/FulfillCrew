# FulfillCrew 技术原理深入文档 —— 索引

> 本文档是 FulfillCrew（智仓通）项目的技术原理教学文档集，专为项目作者设计，帮助理解每个技术选型背后的原理、代码实现细节，以及如何在架构复盘中表达。

---

## 文档结构

| # | 文档 | 内容 | 适合场景 |
|---|------|------|---------|
| 01 | [架构总览](01_architecture_overview.md) | 项目定位、v2.0 架构全景、技术选型决策矩阵、核心数据流 | 快速了解项目全貌 |
| 02 | [前端技术深入](02_frontend_deep_dive.md) | React 18 并发特性、Vite 构建原理、useOrderSocket Hook、Recharts 可视化 | 前端架构复盘准备 |
| 03 | [后端技术深入](03_backend_deep_dive.md) | FastAPI lifespan、SQLAlchemy 2.0 async、Repository 模式、Pydantic 验证、异步编程 | 后端架构复盘准备 |
| 04 | [多智能体系统](04_multi_agent_system.md) | Contract Net Protocol、6 个 Agent 详解、竞价策略公式、OrderService 编排 | 分布式系统/AI 架构复盘 |
| 05 | [机器学习模型](05_ml_models_deep_dive.md) | PyTorch MLP 架构、XGBoost + SHAP、TF-IDF + LR、合成数据生成、模型评估指标 | 机器学习架构复盘 |
| 06 | [基础设施与可观测性](06_infrastructure_observability.md) | Redis/InMemory 事件总线、structlog 结构化日志、Prometheus 指标、健康检查、WebSocket | 运维/SRE 架构复盘 |
| 07 | [Docker 与部署](07_docker_deployment.md) | 多阶段构建、Nginx 反向代理、Docker Compose 编排、环境变量管理、CI/CD 概念 | DevOps 架构复盘 |
| 08 | [架构复盘问答](08_design_review_qa.md) | 25+ 高频架构复盘题 + 参考答案 + 追问方向 + 常见陷阱 | 架构复盘冲刺阶段 |

---

## 阅读建议

### 路径一：按模块深入学习
1. 先读 [01 架构总览](01_architecture_overview.md)，建立全局认知
2. 选择你负责或最感兴趣的模块（前端/后端/ML/基础设施）深入阅读
3. 最后读 [08 架构复盘问答](08_design_review_qa.md)，检验理解程度

### 路径二：架构复盘导向速查
1. 直接跳到 [08 架构复盘问答](08_design_review_qa.md)
2. 遇到不会的题，回到对应章节深入理解
3. 重点掌握：架构图手绘、数据流讲解、技术选型理由

### 路径三：代码对照学习
1. 打开项目代码（推荐 IDE：VS Code / PyCharm）
2. 边读文档边对照源码，在代码中添加自己的注释
3. 尝试修改参数（如竞价权重、欺诈阈值），观察系统行为变化

---

## 架构复盘核心要点速查

### 项目一句话
> "FulfillCrew 是一个多智能体电商订单履约系统，用户结账后，6 个 AI Agent 协作完成欺诈检测、库存检查、仓库竞价、需求预测，支持 WebSocket 实时推送和 Docker 容器化部署。"

### 三门课程映射
| 课程 | 系统模块 | 关键技术 |
|------|---------|---------|
| COMP315 云计算 | 前端、后端 API、数据清洗、Docker 部署 | React 18, FastAPI, Nginx, Docker Compose |
| COMP310 多智能体 | 6 个 Agent 协调 | Contract Net Protocol, 仓库竞价策略 |
| ELEC320 神经网络 | 需求预测、欺诈检测、商品分类 | PyTorch MLP, XGBoost + SHAP, TF-IDF |

### 架构图（架构复盘手绘版）
```
Browser → Nginx → FastAPI → PostgreSQL (数据)
                     ↓
              ┌─────┴─────┐
            Agents     ML Models
            (6个)      (3个)
                     ↓
              Redis (事件总线)
```

### 技术亮点（架构复盘加分项）
1. **防御性编程**：Redis 不可用时自动回退到 InMemoryEventBus；structlog 不可用时回退到标准库 logging
2. **可观测性**：结构化日志 + Prometheus 指标 + 多维度健康检查
3. **可解释性**：每个仓库 bid 附带 reason 字符串；fraud 检测集成 SHAP
4. **渐进复杂度**：从同进程 Agent 到可扩展为分布式消息队列
5. **全异步**：FastAPI + SQLAlchemy 2.0 async + asyncpg，无阻塞 I/O

---

## 扩展阅读

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 迁移指南](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html)
- [React 18 并发特性](https://react.dev/blog/2022/03/29/react-v18)
- [XGBoost 论文](https://arxiv.org/abs/1603.02754)
- [SHAP 论文](https://arxiv.org/abs/1705.07874)
- [Contract Net Protocol (FIPA)](http://www.fipa.org/specs/fipa00029/SC00029H.html)
- [12-Factor App](https://12factor.net/)

---

## 反馈与迭代

如果在阅读中发现：
- 某个技术点讲得不清楚
- 架构复盘中遇到了文档没覆盖的问题
- 代码与文档不一致（项目迭代后）

请在对应文件顶部添加 TODO 注释，或在项目讨论区提出，持续迭代完善本文档集。

# FulfillCrew 架构决策记录（ADR）索引

> **Architecture Decision Records (ADR)** — 记录 FulfillCrew（智仓通）的关键架构决策、替代方案、风险与当前实现边界。

## 快速导航

| 编号 | 主题 | 状态 | 关键设计点 |
|------|------|------|-----------|
| [ADR-001](ADR-001-fastapi-async-backend.md) | FastAPI 异步后端 | ✅ v2.0 | ASGI vs WSGI；async Python 最佳实践；CPU 密集型任务 offload |
| [ADR-002](ADR-002-sqlalchemy-postgresql-persistence.md) | SQLAlchemy 2.0 + PostgreSQL | ✅ v2.0 | SA 2.0 新特性；N+1 查询；`selectinload`；`expire_on_commit` |
| [ADR-003](ADR-003-repository-pattern.md) | Repository 模式 | ✅ v2.0 | 分层架构；事务边界；为什么不写 BaseRepository 泛型 |
| [ADR-004](ADR-004-redis-inmemory-event-bus.md) | Redis/InMemory 事件总线 | ✅ v2.0 | Pub/Sub vs Streams；解耦通信；优雅降级 |
| [ADR-005](ADR-005-contract-net-protocol.md) | Contract Net Protocol 多智能体 | ✅ v2.0 | CNP 经典协议；竞价函数设计；6 智能体角色分工 |
| [ADR-006](ADR-006-react-typescript-vite-frontend.md) | React 18 + TS + Vite + Recharts | ✅ v2.0 | SPA 客户端路由；Vite vs webpack；6 个 Dashboard 组件 |
| [ADR-007](ADR-007-observability-structlog-prometheus.md) | structlog + Prometheus + /health | ✅ v2.0 | 结构化日志；Counter/Histogram/Gauge；可观测性三支柱 |
| [ADR-008](ADR-008-websocket-realtime-updates.md) | WebSocket 实时推送 | ✅ v2.0 | 全双工通信；连接管理；SSE 对比；重连策略 |
| [ADR-009](ADR-009-docker-compose-deployment.md) | Docker Compose 多服务部署 | ✅ v2.0 | 多阶段构建；healthcheck；bridge 网络；depends_on 条件 |
| [ADR-010](ADR-010-ml-model-selection.md) | ML 模型选型（MLP/XGBoost+SHAP/TF-IDF+LR） | ✅ v2.0 | PyTorch MLP 设计；XGBoost 表格数据优势；SHAP 可解释性 |

## 如何使用这些 ADR

### 作为作者（项目开发者）
1. **理解架构**：每个 ADR 详细解释了为什么做某个技术决策，而非只是"用什么"
2. **准备设计复核**：每个 ADR 包含"设计复核要点"部分，整理了高频问题和回答思路
3. **扩展项目**：在 ADR 的"权衡与风险"中预留了扩展路径（如升级到 K8s、Redis Streams、BERT 等）

### 作为维护者
可以通过 ADR 快速核对架构约束：
- 为什么选 A 而不是 B？
- 如果数据量扩大 100 倍，这个架构怎么改？
- 这个决策的风险是什么，现有缓解措施是否仍然有效？

### 作为学习者
1. 按编号顺序阅读，从后端框架到部署，形成完整的架构视图
2. 重点关注"技术细节"和"设计复核要点"部分
3. 对照代码仓库验证 ADR 中的描述是否准确

## ADR 格式说明

每个 ADR 遵循统一格式：

```
# ADR-XXX: 标题

## 状态
Draft / Proposed / Accepted / Deprecated / Superseded

## 背景
问题描述、上下文、约束条件

## 决策
选定的方案

## 考虑方案
对比表格（方案、优点、缺点、结论）

## 技术细节
代码示例、架构图、关键配置

## 权衡与风险
风险矩阵（风险、缓解措施）

## 设计复核要点
用于验证决策、实现与风险说明是否一致

## 相关文件
指向代码仓库中的具体文件

## 参考
外部文档和论文链接
```

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2024-07 | 初始 ADR 集，覆盖 v2.0 全部架构决策 |

---

> **提示**：这些 ADR 是"活文档"。当架构发生变化（如从 PostgreSQL 迁移到 MongoDB，或从 Docker Compose 升级到 Kubernetes），应创建新的 ADR 并标记旧 ADR 为 Superseded。

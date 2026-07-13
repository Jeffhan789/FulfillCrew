# FulfillCrew 教学文档制作计划

## 目标
为 FulfillCrew（智仓通）项目创建完整的教学文档体系，帮助作者理解技术原理、应对面试。

## 阶段规划

### Stage 1 — 创建教学文档目录结构
- 创建 `docs/tutorial/` 目录

### Stage 2 — 编写核心教学文档（并行）
1. **学习路径教程** (`docs/tutorial/learning_path.md`)
   - 阶段化学习路线：从入门到精通
   - 每门课程（COMP315/COMP310/ELEC320）对应的技术点映射
   - 动手实验建议

2. **面试问答手册** (`docs/tutorial/interview_qa.md`)
   - 常见技术面试问题（80+题）
   - 按模块分类：前端、后端、多智能体、ML、DevOps
   - 深度解答 + 代码示例 + 扩展讨论

3. **技术原理深度解析** (`docs/tutorial/technical_deep_dive.md`)
   - Contract Net Protocol 简化实现原理
   - SQLAlchemy 2.0 async + Repository 模式
   - WebSocket 实时推送机制
   - Event Bus (Redis/InMemory) 设计
   - Prometheus 指标 + structlog 日志
   - Docker Compose 多服务编排

4. **代码走读指南** (`docs/tutorial/code_walkthrough.md`)
   - OrderService 完整流程走读
   - 前端 Dashboard 组件数据流
   - ML 模型推理接口设计

5. **架构演进故事** (`docs/tutorial/architecture_evolution.md`)
   - v1.0 → v2.0 升级路径
   - 每个升级决策的 trade-off
   - 未来扩展方向

### Stage 3 — 验证与整合
- 检查所有文档的完整性和一致性
- 确保代码示例与项目实际代码一致

## 交付物
- 5 份 Markdown 教学文档
- 总计约 15,000-20,000 字

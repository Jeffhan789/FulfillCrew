# FulfillCrew 学习路径

这组文档面向希望理解 AI 履约系统工程实现的开发者，按“先运行、再拆模块、最后深入专题”的顺序组织。

## 路径一：快速运行

从 [`00_quickstart.md`](00_quickstart.md) 开始，完成本地启动、健康检查、下单流程和测试验证。适合第一次接触项目的读者。

## 路径二：逐模块理解

阅读 [`01_module_by_module.md`](01_module_by_module.md)，依次理解：

1. React + TypeScript 前端；
2. FastAPI 异步 API；
3. SQLAlchemy Repository；
4. 多智能体协调与仓库竞价；
5. 需求预测、欺诈检测和商品分类模型；
6. Redis、WebSocket、Prometheus 与 Docker Compose。

## 路径三：按专题深入

使用 [`03_deep_dive.md`](03_deep_dive.md) 按问题索引深入某一技术点。架构决策记录位于 [`../adr/`](../adr/)，系统设计说明见 [`../system_design.md`](../system_design.md)。

## 推荐验证顺序

```bash
ruff check backend tests ml_models
pytest -q
cd frontend && npm ci && npm test -- --run && npm run build
docker compose config
```

完成标准不是读完所有文档，而是能够运行系统、定位关键模块，并用测试或日志验证自己的理解。

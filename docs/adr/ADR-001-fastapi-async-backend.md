# FulfillCrew ADR-001：采用 FastAPI 作为异步后端框架

## 状态
Accepted — v2.0 已实施

## 背景
FulfillCrew（智仓通）是一个 Multi-Agent 电商订单履约系统，需要同时处理：
- 商品列表的同步 REST API 请求
- 订单创建的异步多智能体工作流（欺诈检测 → 库存检查 → 仓库竞价 → 需求预测）
- 实时 WebSocket 推送订单状态更新
- 高并发的仓库竞价计算

在 v1.0 中，后端使用 Flask 或简单的同步框架。v2.0 升级需要更强的异步能力来支撑多智能体并发协调。

## 决策
采用 **FastAPI**（版本 0.115.6）作为后端框架，运行在 **Uvicorn**（版本 0.34.0）ASGI 服务器上。

## 考虑方案

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| **FastAPI** | 原生 async/await；自动 OpenAPI/Swagger 文档；Pydantic 类型校验；性能接近 Go/Node.js | 生态相对 Django 较小；学习曲线比 Flask 稍陡 | ✅ 选中 |
| Django + DRF | 生态完善；ORM 成熟；admin 后台 | 同步为主；异步支持（Django 4+）仍不如 FastAPI 原生；重量级 | ❌ 过重 |
| Flask | 轻量；生态成熟；易上手 | 无原生异步；需手动集成 Swagger、验证 | ❌ 不满足并发需求 |
| Node.js/Express | 同前端语言；高并发 | 类型安全弱；Python ML 生态无法直接复用 | ❌ 与 ML 层不匹配 |
| Go/Gin | 极高性能；编译型 | 开发效率低；ML 生态缺失；学生项目学习成本高 | ❌ 不适合课程项目 |

## 技术细节

```python
# backend/main.py
app = FastAPI(
    title="Cloud Multi-Agent E-Commerce Intelligence System",
    lifespan=lifespan,  # 应用生命周期管理
)

# 自动生成的 OpenAPI 文档
# http://localhost:8000/docs  → Swagger UI
# http://localhost:8000/openapi.json → OpenAPI 3.0 schema
```

### 关键依赖版本
```
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.5
```

### 为什么 async 对多智能体系统至关重要
```python
# 在 order_service.py 中，各智能体步骤是串行但非阻塞的：
async def create_order(self, request: OrderRequest) -> OrderResponse:
    # 1. 欺诈检测（计算密集，但接口异步）
    risk_score, fraud_status = self.fraud_agent.score(...)
    # 2. 库存检查（DB 查询）
    stock_available, unavailable = self.inventory_agent.check_stock(...)
    # 3. 仓库竞价（多智能体并发）
    bids, winner = self.coordinator_agent.request_bids(...)
    # 4. 需求预测（ML 推理）
    predicted_demand = self.demand_agent.predict(...)
    # 5. 持久化到 PostgreSQL
    await self._persist_order(...)
    # 6. WebSocket 推送
    await manager.send_order_update(...)
```

FastAPI 的 `async def` 确保：
- 单个订单处理时，事件循环可以处理其他 HTTP 请求
- WebSocket 连接保持活跃的同时，后端可以执行智能体工作流
- 数据库操作通过 `asyncpg` 真正异步执行

## 权衡与风险

| 风险 | 缓解措施 |
|------|----------|
| 团队对 async Python 不熟悉 | 代码中仅在最外层（API 层、DB 层）使用 async；智能体内部保持同步 |
| 过度使用 async 导致调试困难 | 严格限制：只有 I/O 边界（HTTP、DB、WebSocket、Redis）使用 async |
| 第三方库阻塞事件循环 | 使用 `run_in_executor` 将 CPU 密集型任务（如 ML 推理） offload 到线程池 |

## 设计复核要点（供作者准备）

### Q1: 为什么选 FastAPI 而不是 Flask？
> "Flask 是同步 WSGI 框架，在高并发场景下需要 gunicorn + 多进程。FastAPI 原生基于 ASGI，支持 async/await，单进程即可处理大量并发连接。对于我们的多智能体系统，每个订单要经历 6 个智能体步骤，async 可以确保一个订单在等待 ML 推理或 DB 写入时，事件循环能处理其他请求。"

### Q2: FastAPI 的自动文档是怎么工作的？
> "FastAPI 基于 Pydantic 模型和 Python 类型注解，自动推导请求/响应的 JSON Schema，然后暴露 `/docs`（Swagger UI）和 `/openapi.json`。我们不需要写任何额外文档，这对前后端协作和 API 调试非常重要。"

### Q3: 如何处理 CPU 密集型任务（如 ML 推理）不阻塞事件循环？
> "在 Python 中，`async def` 不会 magically 让 CPU 任务并行。对于 PyTorch/XGBoost 推理，我们使用 `asyncio.get_event_loop().run_in_executor()` 将计算 offload 到线程池。或者更简单地，在 v2.0 中模型足够轻量，同步调用在毫秒级完成，对整体延迟影响可接受。"

### Q4: Uvicorn 的 `[standard]` 额外依赖包含什么？
> "包含 `uvloop`（基于 libuv 的高性能事件循环，替代默认 asyncio）、`httptools`（C 语言 HTTP 解析器）、`websockets` 库。这些让 Uvicorn 的生产性能接近 Node.js 和 Go。"

## 相关文件
- `backend/main.py` — FastAPI 应用入口
- `backend/requirements.txt` — 依赖版本锁定
- `docker-compose.yml` — Uvicorn 运行配置
- `backend/api/*.py` — 各 API Router

## 参考
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [ASGI 规范](https://asgi.readthedocs.io/)
- [Uvicorn 文档](https://www.uvicorn.org/)

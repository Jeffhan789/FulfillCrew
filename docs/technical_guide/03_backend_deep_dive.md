# 03 后端技术深入 —— FastAPI + SQLAlchemy 2.0 async + Repository 模式

---

## 1. FastAPI 生命周期管理

```python
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database.engine import init_db
from backend.infrastructure.logging import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application_startup", event="startup")
    await init_db()  # 启动时创建表（如果不存在）
    yield
    logger.info("application_shutdown", event="shutdown")

app = FastAPI(
    title="Cloud Multi-Agent E-Commerce Intelligence System",
    lifespan=lifespan,
)
```

### 1.1 为什么用 `lifespan` 而不是 `startup`/`shutdown` 事件？

FastAPI 早期使用 `@app.on_event("startup")`，但存在几个问题：
- 事件顺序不可控
- 不支持依赖注入
- 与 ASGI 规范不够对齐

`lifespan` 是 ASGI 标准的一部分，使用 `asynccontextmanager` 可以：
- 在 `yield` 前执行初始化（数据库连接、模型加载、指标注册）
- 在 `yield` 后执行清理（关闭连接池、刷新日志）
- 支持 async/await，完美配合 asyncio 生态

**面试表达**："我用 `lifespan` 管理应用生命周期，这是 FastAPI 的现代推荐方式，与 ASGI 规范对齐，支持在启动时异步初始化数据库表结构。"

### 1.2 CORS 动态配置

```python
default_origins = [
    "http://localhost:5173",  # Vite 开发服务器
    "http://localhost:8080",  # Docker 开发环境
    "http://localhost",       # 生产 Nginx
]
raw_cors = os.getenv("CORS_ORIGINS", "")
allowed_origins = [o.strip() for o in raw_cors.split(",") if o.strip()] if raw_cors else default_origins
```

**设计意图**：环境变量优先，无配置时使用安全默认值。这体现 "12-factor app" 的配置原则。

---

## 2. SQLAlchemy 2.0 async 深入

### 2.1 模型定义：Mapped 类型注解

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Float, Integer, DateTime, JSON, Boolean, ForeignKey, func

class Base(DeclarativeBase):
    pass

class ProductORM(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    
    order_items: Mapped[List["OrderItemORM"]] = relationship(
        back_populates="product", 
        lazy="selectin"  #  eager loading 策略
    )
```

**SQLAlchemy 2.0 新特性**：
- `Mapped[T]` 类型注解：IDE 和类型检查器可推断字段类型
- `mapped_column()` 替代旧版 `Column()`：语义更清晰
- `lazy="selectin"`：使用 `IN` 查询预加载关联对象，避免 N+1 问题

### 2.2 N+1 问题与解决方案

**问题**：访问 `order.items` 时，如果先查 orders 再循环查 items，会触发 N+1 次查询。

**解决**：`selectinload` 在 Repository 层主动预加载：

```python
from sqlalchemy.orm import selectinload

async def get_by_id(self, order_id: str) -> OrderORM | None:
    result = await self.session.execute(
        select(OrderORM)
        .where(OrderORM.order_id == order_id)
        .options(
            selectinload(OrderORM.items),
            selectinload(OrderORM.decisions),
            selectinload(OrderORM.bids),
        )
    )
    return result.scalar_one_or_none()
```

**原理**：`selectinload` 生成两条 SQL：
1. `SELECT ... FROM orders WHERE order_id = ?`
2. `SELECT ... FROM order_items WHERE order_id IN (?)` —— 用 IN 批量加载所有关联项

### 2.3 异步引擎与会话管理

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.database.models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/fulfillcrew")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

**关键点**：
- `postgresql+asyncpg`：使用原生 asyncpg 驱动，非 `psycopg2`（阻塞）
- `expire_on_commit=False`：提交后不使对象过期，避免后续 lazy load 失败（因为 async 会话已关闭）
- `async_sessionmaker`：工厂模式，每个请求创建独立会话

### 2.4 数据库事务边界

```python
async def _persist_order(self, order_orm, item_orms, decision_orms, bid_orms, update_stock=False, ...):
    async with AsyncSessionLocal() as session:
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        
        await order_repo.create_order(order_orm)
        await order_repo.add_items(order_orm.order_id, item_orms)
        # ... 其他持久化操作
        
        if update_stock:
            for item in request_items:
                await product_repo.update_stock(item.product_id, -item.quantity)
        
        await session.commit()  # 所有操作在一个事务中提交
```

**ACID 保证**：订单、订单项、Agent 决策、仓库竞价、库存扣减全部在同一个事务中。要么全部成功，要么全部回滚。这对电商系统至关重要。

---

## 3. Repository 模式

### 3.1 为什么不用 DAO？

| 模式 | 特点 | 适用场景 |
|------|------|---------|
| DAO (Data Access Object) | 直接映射数据库表，粒度细 | 简单 CRUD |
| Repository | 面向领域聚合，封装查询逻辑 | 复杂业务领域 |

本项目的 `OrderRepository` 聚合了订单、订单项、决策、竞价等表的操作，提供领域级的 `create_order` 方法，而非分散的 SQL。

### 3.2 Repository 实现

```python
class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_order(self, order: OrderORM) -> OrderORM:
        self.session.add(order)
        await self.session.flush()  # flush 生成主键，不提交事务
        return order

    async def get_by_id(self, order_id: str) -> OrderORM | None:
        result = await self.session.execute(
            select(OrderORM)
            .where(OrderORM.order_id == order_id)
            .options(selectinload(OrderORM.items), ...)
        )
        return result.scalar_one_or_none()
```

**面试表达**："Repository 模式将数据访问逻辑从 Service 层解耦，使 Service 只关注业务编排，不关注 SQL 细节。同时 Repository 依赖 `AsyncSession` 接口，便于单元测试时注入 mock 会话。"

---

## 4. Pydantic 验证与 FastAPI 依赖注入

### 4.1 请求模型

```python
from pydantic import BaseModel, Field

class OrderRequest(BaseModel):
    user_id: str = "guest"
    items: list[BasketItem] = Field(min_length=1)  # 至少一个商品
    shipping_distance: float = Field(default=12.0, ge=0)  # 非负
    is_new_user: bool = True
```

**Pydantic 2 特性**：
- `Field()` 约束在类型声明处直接定义，无需额外 schema
- `ge=0`（greater than or equal）等数值校验自动生成 OpenAPI 文档
- 验证失败自动返回 422 Unprocessable Entity，错误信息结构化

### 4.2 响应模型

```python
class OrderResponse(BaseModel):
    order_id: str
    order_status: str
    order_total: float
    selected_warehouse: Optional[str] = None
    risk_score: float
    fraud_status: str
    predicted_demand_next_7_days: int
    restock_recommendation: str
    bids: list[WarehouseBid]
    decision_log: list[AgentDecision]
    course_trace: list[AgentDecision]
    model_evaluations: list[ModelEvaluation]
```

**设计意图**：一个响应包含订单全链路信息，前端只需一次请求即可渲染完整状态面板。这是 BFF（Backend for Frontend）思想的简化版。

---

## 5. 异步编程要点

### 5.1 FastAPI 中的 async 路径

```python
@router.post("", response_model=OrderResponse)
async def create_order(request: OrderRequest) -> OrderResponse:
    product_service = ProductService()
    order_service = OrderService(product_service)
    return await order_service.create_order(request)
```

**为什么全链路 async？**
- `create_order` 内部调用 `await self.product_service.get_product_map()`（数据库查询）
- `await self._persist_order(...)`（数据库写入）
- `await manager.send_order_update(...)`（WebSocket 发送）

如果这些操作是同步的，worker 线程会被阻塞，无法处理其他请求。async 确保 I/O 等待时释放事件循环。

### 5.2 事件循环与 CPU 密集型任务

**注意**：Python 的 `asyncio` 不能并行执行 CPU 密集型任务。ML 模型推理（PyTorch/XGBoost）在 `OrderService` 中是同步调用的：

```python
# 在当前实现中，ML 推理是同步的
risk_score = predict_risk(features)  # 阻塞事件循环 ~ 几毫秒
```

**改进方案**（面试加分项）：
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

# 将 CPU 密集型任务丢到线程池
loop = asyncio.get_event_loop()
risk_score = await loop.run_in_executor(executor, predict_risk, features)
```

或使用 `ProcessPoolExecutor` 绕过 GIL（如果推理是 CPU 瓶颈）。

---

## 6. 测试策略

### 6.1 测试分层

```
tests/
├── test_api.py          # 集成测试：HTTP 请求 → 响应
├── test_agents.py       # 单元测试：Agent 行为验证
├── test_services.py     # 服务层测试：业务逻辑
├── test_ml_models.py    # ML 模型测试：推理正确性
└── test_data_cleaning.js # 数据清洗测试：Node.js 断言
```

### 6.2 FastAPI TestClient

```python
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client() -> TestClient:
    return TestClient(app)

def test_create_order_success(client: TestClient) -> None:
    payload = {
        "user_id": "test-user",
        "items": [{"product_id": "p-1001", "quantity": 1}],
        "shipping_distance": 10,
        "is_new_user": False,
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "order_id" in data
    assert data["order_status"] in {"created", "review_required"}
```

**TestClient 原理**：基于 `httpx` 的同步客户端，直接调用 ASGI 应用，绕过 HTTP 网络层，速度快且无需启动服务器。

---

## 7. 面试高频题

**Q: SQLAlchemy 2.0 相比 1.x 最大的改进是什么？**

> A: 原生类型注解支持（`Mapped[T]` + `mapped_column()`），全异步支持（`AsyncSession` + `async_sessionmaker`），以及 `selectinload` 等 eager loading 策略与 async 兼容。1.x 的 `Column()` 和 `query()` API 已标记为 legacy。

**Q: 为什么用 `expire_on_commit=False`？**

> A: 默认情况下，SQLAlchemy 在 commit 后会使对象过期，下次访问属性时触发 lazy load。但在 async 模式下，commit 后会话通常已关闭，lazy load 会报错。`expire_on_commit=False` 保持对象可用，直到显式刷新或关闭会话。

**Q: Repository 模式和 Active Record 的区别？**

> A: Active Record（如 Django ORM）中模型自身包含 CRUD 方法（`product.save()`）。Repository 将数据访问完全分离到独立类中，模型只承载数据。Repository 更适合复杂领域，单元测试时更容易 mock。

**Q: FastAPI 的依赖注入系统如何工作？**

> A: FastAPI 使用 Python 的类型注解和 `Depends()` 实现依赖注入。依赖可以是函数（如 `get_db` yield 一个会话），也可以是类。框架在请求到来时解析依赖图，自动注入所需对象。这减少了全局状态，使测试更容易。

**Q: 如果订单量暴增，数据库连接池会打满吗？**

> A: `asyncpg` 默认连接池大小为 10。如果并发请求超过 10，后续请求会等待。可以通过 `create_async_engine(pool_size=20, max_overflow=10)` 调整。更进一步的方案是连接池预热 + 读写分离（主库写、从库读）。

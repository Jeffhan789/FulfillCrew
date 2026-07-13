# FulfillCrew ADR-002：采用 SQLAlchemy 2.0 + PostgreSQL 替代内存存储

## 状态
Accepted — v2.0 已实施

## 背景
v1.0 使用内存字典存储产品和订单数据，优点是：
- 零配置，项目 clone 即可运行
- 没有数据库迁移问题
- 测试简单

但缺点是：
- 容器重启后数据丢失
- 无法处理并发写入（Python GIL + 字典非线程安全）
- 无法关联查询（如"查找某仓库的所有订单"）
- 无法持久化智能体决策日志（审计追踪）
- 不满足设计复核中" production-ready"的要求

v2.0 需要持久化层，同时保持 async 特性与 FastAPI 一致。

## 决策
采用 **SQLAlchemy 2.0** 的异步 ORM + **PostgreSQL 15**（通过 `asyncpg` 驱动）作为持久化方案。

## 考虑方案

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| **SQLAlchemy 2.0 + asyncpg** | 原生 async 支持；类型安全（Mapped, mapped_column）；成熟的迁移生态（Alembic）；强大的关联查询 | 学习曲线较陡；2.0 语法与 1.4 差异大 | ✅ 选中 |
| Tortoise ORM | 专为 async 设计；类似 Django ORM；轻量 | 生态较小；关联查询不如 SA 成熟；设计复核知名度低 | ❌ 生态不足 |
| Prisma Client Python | 类型安全；自动生成模型 | 额外构建步骤；相对较新；与 FastAPI 集成文档少 | ❌ 过于新 |
| SQLite (aiosqlite) | 零配置；文件级便携 | 并发写入性能差；无原生网络协议；生产不推荐 | ❌ 不满足并发需求 |
| 纯 SQL + asyncpg | 最高性能；完全控制 | 手写 SQL 维护成本高；无 ORM 抽象；设计复核需解释更多 | ❌ 开发效率低 |
| MongoDB (motor) | 文档模型灵活；schema-less | 关系型数据（订单-订单项-商品）用文档模型不自然；事务支持弱 | ❌ 数据结构不匹配 |

## 技术细节

### SQLAlchemy 2.0 新特性使用
```python
# backend/database/models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class OrderORM(Base):
    __tablename__ = "orders"
    
    order_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_status: Mapped[str] = mapped_column(String, nullable=False)
    order_total: Mapped[float] = mapped_column(Float, nullable=False)
    
    # 关系型定义 — 自动加载关联对象
    items: Mapped[List["OrderItemORM"]] = relationship(
        back_populates="order", 
        lazy="selectin",  # 避免 N+1 查询
        cascade="all, delete-orphan"
    )
    decisions: Mapped[List["AgentDecisionORM"]] = relationship(...)
    bids: Mapped[List["WarehouseBidORM"]] = relationship(...)
```

### 为什么使用 `selectinload` 策略
```python
# backend/repositories/order_repository.py
result = await self.session.execute(
    select(OrderORM)
    .where(OrderORM.order_id == order_id)
    .options(
        selectinload(OrderORM.items),      # 用第二个 SELECT IN 加载 items
        selectinload(OrderORM.decisions),  # 避免 N+1 问题
        selectinload(OrderORM.bids),
    )
)
```

`selectinload` 是 SQLAlchemy 2.0 推荐的 eager loading 策略：
- 先执行主查询获取订单
- 再执行一条 `SELECT ... WHERE id IN (...)` 加载所有关联对象
- 总共 2 条查询，无论关联多少个子对象
- 对比 `joinedload` 可能导致笛卡尔积，对比 `subqueryload` 对复杂查询不友好

### async Session 管理
```python
# backend/database/engine.py
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session  # FastAPI Depends 注入
        finally:
            await session.close()
```

`expire_on_commit=False` 是关键设置：
- 默认情况下，commit 后 session 中的对象会"过期"，下次访问触发 lazy load
- 在 async 环境中，lazy load 会导致 "GreenletSpawn" 错误（因为对象 detached 后无法发 SQL）
- 关闭 expire_on_commit 后，对象保持加载状态，直到 session 关闭

## 数据模型设计

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    products     │     │     orders      │     │   order_items   │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │◄────┤ product_id (FK) │     │ id (PK)         │
│ name            │     │ order_id (FK)   │◄────┤ order_id (FK)   │
│ price           │     │ quantity        │     │ product_id (FK) │
│ category        │     │ unit_price      │     │ quantity        │
│ type            │     │                 │     │ unit_price      │
│ quantity        │     │                 │     │                 │
│ rating          │     │                 │     │                 │
│ image_link      │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │
         │              ┌─────────────────┐     ┌─────────────────┐
         │              │ agent_decisions │     │ warehouse_bids  │
         │              ├─────────────────┤     ├─────────────────┤
         └─────────────►│ id (PK)         │     │ id (PK)         │
                        │ order_id (FK)   │◄────│ order_id (FK)   │
                        │ agent_name      │     │ warehouse_id    │
                        │ decision_type   │     │ bid_value       │
                        │ decision_data   │     │ workload        │
                        │ (JSON)          │     │ distance        │
                        │ created_at      │     │ stock_level     │
                        │                 │     │ processing_speed│
                        │                 │     │ suitability_score│
                        │                 │     │ reason          │
                        │                 │     │ is_winner       │
                        │                 │     │ created_at      │
                        └─────────────────┘     └─────────────────┘
```

## 权衡与风险

| 风险 | 缓解措施 |
|------|----------|
| SQLAlchemy 2.0 语法与 1.4 完全不同 | 团队统一使用 `Mapped[]` + `mapped_column()` 风格；不写 1.4 兼容代码 |
| async ORM 调试困难（lazy load 在 async 中失败） | 所有关联使用 `selectinload` 或 `joinedload`；禁用 lazy load |
| 数据库连接池耗尽 | 使用 `asyncpg` 内置连接池；Docker Compose 中配置合理资源限制 |
| 缺少迁移工具 | 预留 Alembic 集成路径（当前使用 `create_all()` 自动建表，适合开发） |

## 设计复核要点

### Q1: 为什么从内存存储升级到 PostgreSQL？
> "v1.0 用内存字典是为了快速演示，但生产环境需要持久化。PostgreSQL 是 ACID 数据库，能处理并发写入、支持事务、提供关系型查询。在我们的场景中，一个订单涉及多个子表（订单项、智能体决策、仓库竞价），关系型模型非常自然。"

### Q2: SQLAlchemy 2.0 相比 1.4 有什么变化？
> "最核心的变化是类型安全。2.0 引入了 `Mapped[]` 泛型和 `mapped_column()` 函数，让 ORM 模型与 Python 类型系统完全对齐。例如 `price: Mapped[float] = mapped_column(Float, nullable=False)` 既描述了数据库列，又提供了类型检查。此外 2.0 原生支持 async，通过 `create_async_engine` 和 `AsyncSession` 实现。"

### Q3: 什么是 N+1 查询问题？你们怎么解决？
> "N+1 是指：先查 1 条主记录，再对每条记录发 N 条子查询。在我们的订单查询中，如果先查订单，再循环访问 `order.items`，就是 N+1。我们使用 `selectinload` 策略，先发一条查询获取订单，再发一条 `SELECT ... IN (...)` 获取所有关联项，总共 2 条查询解决问题。"

### Q4: `expire_on_commit=False` 是做什么的？
> "默认 SQLAlchemy 在 commit 后会标记对象为'过期'，下次访问属性会触发 lazy SQL 查询。在 async 中，这会导致错误，因为对象已经 detached 了。关闭 expire_on_commit 后，对象保持加载状态，适合 FastAPI 的依赖注入模式——session 在请求结束后才关闭。"

## 相关文件
- `backend/database/models.py` — ORM 模型定义
- `backend/database/engine.py` — 引擎与 Session 管理
- `backend/repositories/*.py` — Repository 层
- `backend/services/order_service.py` — 持久化调用
- `docker-compose.yml` — PostgreSQL 服务配置

## 参考
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [asyncpg 文档](https://magicstack.github.io/asyncpg/current/)
- [SQLAlchemy 2.0 Migration Guide](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html)

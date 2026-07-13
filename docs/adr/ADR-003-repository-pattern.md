# FulfillCrew ADR-003：采用 Repository 模式封装数据访问

## 状态
Accepted — v2.0 已实施

## 背景
v1.0 中，服务层直接操作内存字典，数据访问与业务逻辑高度耦合。v2.0 引入 PostgreSQL 后，需要：
- 隔离 ORM 细节，让业务层不依赖 SQLAlchemy
- 便于单元测试（可以 mock Repository 而不需要 mock 整个 DB）
- 支持未来切换数据库（如从 PostgreSQL 到 MySQL 或 MongoDB）
- 让设计复核者能清晰解释"分层架构"

## 决策
采用 **Repository 模式** 作为数据访问层，每个领域实体对应一个 Repository 类。

## 考虑方案

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| **Repository 模式** | 解耦业务与数据访问；易测试；设计复核经典设计模式 | 增加类数量；小项目中可能显得过度设计 | ✅ 选中（教育目的） |
| 直接在 Service 中使用 Session | 代码量少；直观 | 业务与数据耦合；难以测试；SQLAlchemy 泄漏到上层 | ❌ 不满足分层要求 |
| Active Record | 简单；类似 Rails/Django ORM 默认模式 | 模型承担过多职责；难以 mock；不适合复杂查询 | ❌ 职责过重 |
| DAO (Data Access Object) | 与 Repository 类似，但偏底层 | 在 Python 社区中 Repository 更常见；概念差异细微 | ❌ 与 Repository 本质类似 |

## 技术细节

### 架构层次
```
API Layer (FastAPI Router)
    ↓ 调用
Service Layer (OrderService, ProductService)
    ↓ 调用
Repository Layer (OrderRepository, ProductRepository, ...)
    ↓ 调用
Database Layer (SQLAlchemy ORM + asyncpg + PostgreSQL)
```

### Repository 实现示例
```python
# backend/repositories/order_repository.py
class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_order(self, order: OrderORM) -> OrderORM:
        self.session.add(order)
        await self.session.flush()  # 生成 UUID，不提交
        return order

    async def get_by_id(self, order_id: str) -> OrderORM | None:
        result = await self.session.execute(
            select(OrderORM)
            .where(OrderORM.order_id == order_id)
            .options(selectinload(OrderORM.items))
        )
        return result.scalar_one_or_none()

    async def update_order_status(self, order_id: str, status: str, selected_warehouse: str | None) -> None:
        order = await self.get_by_id(order_id)
        if order is not None:
            order.order_status = status
            order.selected_warehouse = selected_warehouse
```

### 完整的 Repository 列表
```
backend/repositories/
├── __init__.py
├── order_repository.py          # 订单 CRUD + 关联加载
├── product_repository.py        # 商品查询 + 库存更新
├── warehouse_bid_repository.py  # 仓库竞价记录
└── agent_decision_repository.py # 智能体决策审计日志
```

### 为什么不用通用 BaseRepository
很多教程会写一个 `BaseRepository[T]` 用泛型做通用 CRUD。我们**刻意不这样做**，原因：
1. 每个实体的查询模式差异很大（订单需要 `selectinload`，商品不需要）
2. 通用接口会隐藏业务语义（`get_by_id` 和 `get_order_with_bids` 的意图不同）
3. Python 的类型泛型在实践中有诸多限制
4. 显式 Repository 方法能保留实体特有查询和加载策略，避免通用基类隐藏行为

### 事务边界在 Service 层
```python
# backend/services/order_service.py
async def _persist_order(self, order_orm, item_orms, decision_orms, bid_orms, ...):
    async with AsyncSessionLocal() as session:  # 事务边界
        order_repo = OrderRepository(session)
        product_repo = ProductRepository(session)
        agent_decision_repo = AgentDecisionRepository(session)
        warehouse_bid_repo = WarehouseBidRepository(session)
        
        await order_repo.create_order(order_orm)
        await order_repo.add_items(order_orm.order_id, item_orms)
        for dec in decision_orms:
            await agent_decision_repo.save(dec)
        for bid in bid_orms:
            await warehouse_bid_repo.save(bid)
        
        if update_stock:
            for item in request_items:
                await product_repo.update_stock(item.product_id, -item.quantity)
        
        await session.commit()  # 所有操作原子提交
```

**关键点：** 一个订单的所有写入（订单 + 订单项 + 决策日志 + 竞价记录 + 库存扣减）在一个事务中完成，要么全成功，要么全回滚。

## 权衡与风险

| 风险 | 缓解措施 |
|------|----------|
| Repository 层代码重复（每个 repo 都有类似的 CRUD） | 接受适度重复；设计复核中解释"显式优于隐式" |
| 过度抽象导致性能问题 | Repository 直接暴露 SQLAlchemy 的 `select()` 能力，不做额外封装 |
| 初学者理解困难 | 配合文档和设计复核 Q&A 解释分层意图 |

## 设计复核要点

### Q1: 什么是 Repository 模式？为什么不用直接在 Service 里写 SQL？
> "Repository 模式是领域驱动设计中的模式，将数据访问逻辑封装成独立的类。Service 层只调用 `order_repo.get_by_id()`，不关心数据从哪里来。这样我们未来可以从 PostgreSQL 切换到 MongoDB 时，只需要重写 Repository 实现，Service 层完全不受影响。"

### Q2: 你们为什么不写 BaseRepository 泛型基类？
> "我们考虑过，但发现每个实体的查询模式差异很大。比如 Order 需要 `selectinload(items, decisions, bids)`，而 Product 只需要简单查询。泛型基类会隐藏这些差异，导致过度抽象。在 Python 中，显式写出每个 Repository 的方法更清晰，也更容易在设计复核中解释。"

### Q3: 事务边界在哪里？为什么？
> "在 Service 层。一个订单的创建涉及多个表（orders, order_items, agent_decisions, warehouse_bids, products），这些操作必须在同一个事务中。如果 Service 层让每个 Repository 自己 commit，就可能在中间步骤失败时留下不一致的数据。所以我们在 Service 中打开 Session，所有 Repository 共享同一个 Session，最后统一 commit。"

### Q4: 如果要做分页查询，Repository 层怎么支持？
> "可以通过添加 `offset` 和 `limit` 参数实现。例如：
```python
async def list_orders(self, offset: int = 0, limit: int = 20) -> list[OrderORM]:
    result = await self.session.execute(
        select(OrderORM).offset(offset).limit(limit)
    )
    return result.scalars().all()
```
更完整的方案是引入类似 `Page[T]` 的泛型分页对象，但 v2.0 中暂不实现，保持简单。"

## 相关文件
- `backend/repositories/*.py` — 所有 Repository 实现
- `backend/services/order_service.py` — Service 层使用 Repository 的示例
- `tests/test_services.py` — Repository 层的单元测试

## 参考
- [Repository Pattern — Martin Fowler](https://martinfowler.com/eaaCatalog/repository.html)
- [Domain-Driven Design — Eric Evans](https://domainlanguage.com/ddd/)

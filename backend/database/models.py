"""SQLAlchemy 2.0 async ORM models for PostgreSQL persistence."""
from datetime import datetime, timezone
from typing import List
from sqlalchemy import String, Float, Integer, DateTime, JSON, Boolean, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import uuid


class Base(DeclarativeBase):
    pass


class ProductORM(Base):
    """Product table — cleaned data from data_cleaning pipeline."""
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    image_link: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    order_items: Mapped[List["OrderItemORM"]] = relationship(back_populates="product", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ProductORM(id={self.id}, name={self.name})>"


class OrderORM(Base):
    """Order table — persisted checkout requests."""
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, nullable=False, default="guest")
    order_status: Mapped[str] = mapped_column(String, nullable=False)  # created, review_required, rejected_out_of_stock
    order_total: Mapped[float] = mapped_column(Float, nullable=False)
    selected_warehouse: Mapped[str | None] = mapped_column(String, nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fraud_status: Mapped[str | None] = mapped_column(String, nullable=True)
    predicted_demand: Mapped[int | None] = mapped_column(Integer, nullable=True)
    restock_recommendation: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    items: Mapped[List["OrderItemORM"]] = relationship(back_populates="order", lazy="selectin", cascade="all, delete-orphan")
    decisions: Mapped[List["AgentDecisionORM"]] = relationship(back_populates="order", lazy="selectin", cascade="all, delete-orphan")
    bids: Mapped[List["WarehouseBidORM"]] = relationship(back_populates="order", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<OrderORM(id={self.order_id}, status={self.order_status})>"


class OrderItemORM(Base):
    """Order line items."""
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String, ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[str] = mapped_column(String, ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    order: Mapped["OrderORM"] = relationship(back_populates="items")
    product: Mapped["ProductORM"] = relationship(back_populates="order_items")

    def __repr__(self) -> str:
        return f"<OrderItemORM(order_id={self.order_id}, product_id={self.product_id})>"


class AgentDecisionORM(Base):
    """Audit trail of every agent step."""
    __tablename__ = "agent_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String, ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    decision_type: Mapped[str] = mapped_column(String, nullable=False)  # fraud_check, inventory_check, warehouse_bid, etc.
    decision_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    order: Mapped["OrderORM"] = relationship(back_populates="decisions")

    def __repr__(self) -> str:
        return f"<AgentDecisionORM(agent={self.agent_name}, type={self.decision_type})>"


class WarehouseBidORM(Base):
    """Record of all warehouse bids per order."""
    __tablename__ = "warehouse_bids"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String, ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)
    warehouse_id: Mapped[str] = mapped_column(String, nullable=False)
    bid_value: Mapped[float] = mapped_column(Float, nullable=False)
    workload: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance: Mapped[float | None] = mapped_column(Float, nullable=True)
    stock_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    suitability_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    is_winner: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    order: Mapped["OrderORM"] = relationship(back_populates="bids")

    def __repr__(self) -> str:
        return f"<WarehouseBidORM(warehouse={self.warehouse_id}, bid={self.bid_value}, winner={self.is_winner})>"

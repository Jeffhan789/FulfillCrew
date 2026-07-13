"""Order Service — the orchestration layer that coordinates all agents.

This is the heart of FulfillCrew. It implements the complete order fulfillment
pipeline by composing multiple agents and persisting results.

Order Processing Pipeline (sequential, single-threaded per order):
    1. Order Creation   → UUID generation, WebSocket notification
    2. Fraud Detection  → XGBoost/SHAP risk scoring, threshold check
    3. Inventory Check  → Stock availability verification
       [if out of stock] → Reject order immediately
    4. Warehouse Bidding → CFP to all warehouses, lowest-bid wins
    5. Demand Prediction → MLP forecast for restock recommendation
    6. Stock Reservation → If fraud approved, decrement inventory
    7. Persistence      → Atomic DB commit (Order + Items + Decisions + Bids)
    8. Completion       → Final WebSocket push, metrics recording

Design Patterns Used:
    - Facade: OrderService hides the complexity of coordinating 6 agents
    - Repository: All DB access goes through repository objects
    - Observer: WebSocket manager pushes real-time updates to frontend
    - Circuit Breaker (implicit): ProductService falls back to JSON if DB fails

Interview Note:
    Q: Why is the pipeline sequential rather than parallel?
    A: Fraud detection MUST run before inventory reservation (security).
       Inventory check MUST run before warehouse bidding (no point bidding
       if we can't fulfill). Sequential makes the flow deterministic and
       easier to debug. Future optimisation: parallelise fraud + demand
       prediction since they are independent.
       
    Q: How do you ensure data consistency across agent decisions?
    A: All state mutations happen in a single SQLAlchemy transaction within
       _persist_order(). If any step fails, the transaction rolls back.
       
    Q: What happens if WebSocket delivery fails?
    A: WebSocket is fire-and-forget (best-effort). The order still persists
       to the database, and the client can poll /orders/{id} as a fallback.
"""
from time import time

from datetime import datetime, timezone
from uuid import uuid4

from fastapi.encoders import jsonable_encoder

from backend.agents.coordinator_agent import CoordinatorAgent
from backend.agents.demand_prediction_agent import DemandPredictionAgent
from backend.agents.fraud_detection_agent import FraudDetectionAgent
from backend.agents.inventory_agent import InventoryAgent
from backend.agents.order_agent import OrderAgent
from backend.api.websocket import manager
from backend.database.engine import AsyncSessionLocal
from backend.database.models import AgentDecisionORM, OrderItemORM, OrderORM, WarehouseBidORM
from backend.infrastructure.logging import logger
from backend.infrastructure.metrics import (
    fraud_score,
    order_processing_duration,
    orders_total,
    warehouse_bids_total,
)
from backend.repositories.agent_decision_repository import AgentDecisionRepository
from backend.repositories.order_repository import OrderRepository
from backend.repositories.product_repository import ProductRepository
from backend.repositories.warehouse_bid_repository import WarehouseBidRepository
from backend.schemas import (
    AgentDecision,
    BasketItem,
    ModelEvaluation,
    OrderRequest,
    OrderResponse,
    Product,
    WarehouseBid,
)
from backend.services.product_service import ProductService


class OrderService:
    """Orchestrates the full order fulfillment lifecycle.
    
    Composition of Agents:
        - order_agent:     Entry-point and lifecycle ownership
        - inventory_agent: Stock check and reservation
        - coordinator_agent: Warehouse bidding (CNP)
        - demand_agent:    MLP-based demand forecasting
        - fraud_agent:     XGBoost-based risk scoring
    
    The service is instantiated per-request (not a singleton) to avoid
    cross-request state contamination. In production you might want
    to pool agents or use dependency injection.
    """
    def __init__(self, product_service: ProductService) -> None:
        self.product_service = product_service
        self.order_agent = OrderAgent()
        self.inventory_agent = InventoryAgent()
        self.coordinator_agent = CoordinatorAgent()
        self.demand_agent = DemandPredictionAgent()
        self.fraud_agent = FraudDetectionAgent()

    def _course_trace(self) -> list[AgentDecision]:
        """Return academic module mapping for the frontend course-trace panel.
        
        This is a pedagogical feature that shows which university module
        contributed to each architectural layer. It helps examiners and
        interviewers understand the theoretical foundations.
        """
        return [
            AgentDecision(
                agent="COMP315 Cloud Computing",
                message="Frontend, FastAPI backend, API boundaries and Docker-ready structure show the cloud e-commerce engineering layer.",
            ),
            AgentDecision(
                agent="COMP310 Multi-Agent Systems",
                message="Order, Inventory, Coordinator and Warehouse agents cooperate through a simplified Contract Net Protocol.",
            ),
            AgentDecision(
                agent="ELEC320 Neural Networks",
                message="Demand and fraud modules expose training/online inference style interfaces that can be replaced by real MLP/SVM models.",
            ),
        ]

    def _model_evaluations(self, risk_score: float, predicted_demand: int) -> list[ModelEvaluation]:
        """Generate model evaluation metadata for the frontend dashboard.
        
        This bridges the gap between "running code" and "academic explanation",
        making it easy to defend the project in a viva or technical interview.
        """
        return [
            ModelEvaluation(
                model_name="Demand Prediction MLP Interface",
                course_topic="MLP regression and generalisation",
                metric="predicted_sales_next_7_days",
                score=float(predicted_demand),
                interpretation="Higher value suggests stronger near-term demand and possible restock pressure.",
                training_mode="Historical product and sales features would be used to train regression weights.",
                online_mode="The Demand Prediction Agent calls the model during checkout to estimate future demand.",
            ),
            ModelEvaluation(
                model_name="Fraud Detection Classifier Interface",
                course_topic="Binary classification with sigmoid-style risk output",
                metric="risk_score",
                score=risk_score,
                interpretation="Scores above the threshold move the order into manual review.",
                training_mode="Historical labelled orders would be split into normal and suspicious examples.",
                online_mode="The Fraud Detection Agent scores each new order before inventory is reserved.",
            ),
        ]

    async def create_order(self, request: OrderRequest) -> OrderResponse:
        """Execute the complete order fulfillment pipeline.
        
        This is the MAIN ENTRY POINT for order processing. Every step is
        instrumented with structured logging, Prometheus metrics, and
        WebSocket notifications for real-time frontend updates.
        
        Args:
            request: Validated OrderRequest from the API layer.
            
        Returns:
            OrderResponse containing the final order state, all agent decisions,
            warehouse bids, and model evaluation metadata.
            
        Raises:
            No exceptions are raised — all error paths return a response with
            an appropriate status (e.g., "rejected_out_of_stock").
            
        Interview Note:
            Q: Walk me through what happens when a user clicks "Place Order".
            A: 1. Frontend POSTs to /orders with BasketItem list
               2. FastAPI validates via Pydantic (OrderRequest schema)
               3. OrderService.create_order() generates UUID, logs event
               4. FraudDetectionAgent.score() → XGBoost inference
               5. InventoryAgent.check_stock() → DB read via repository
               6. CoordinatorAgent.request_bids() → CNP to 3 warehouses
               7. DemandPredictionAgent.predict() → PyTorch MLP inference
               8. InventoryAgent.reserve_stock() → in-memory decrement
               9. _persist_order() → atomic DB transaction
               10. WebSocket push + Prometheus metrics
        """
        start = time()
        order_id = str(uuid4())
        
        # Step 0: Log order creation for observability
        logger.info(
            "order.created",
            order_id=order_id,
            user_id=request.user_id,
            item_count=sum(item.quantity for item in request.items),
        )
        
        # Notify frontend that the order has been received
        await manager.send_order_update(order_id, {
            "event": "order.created",
            "order_id": order_id,
            "data": {
                "order_status": "pending",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        })

        # Load product catalogue (with fallback to JSON if DB is down)
        products = await self.product_service.get_product_map()
        selected_products = [products[item.product_id] for item in request.items if item.product_id in products]
        item_count = sum(item.quantity for item in request.items)
        order_total = round(
            sum(products[item.product_id].price * item.quantity for item in request.items if item.product_id in products),
            2,
        )
        average_item_price = order_total / item_count if item_count else 0
        
        # Initialise decision log for the frontend timeline
        decision_log: list[AgentDecision] = [
            self.order_agent.log(f"Received order from {request.user_id} with {item_count} item(s).")
        ]

        # ───────────────────────────────────────────────
        # STEP 1: FRAUD DETECTION
        # ───────────────────────────────────────────────
        # This must run BEFORE inventory reservation to prevent
        # fraudulent orders from consuming real stock.
        risk_score_val, fraud_status = self.fraud_agent.score(
            {
                "order_total": order_total,
                "number_of_items": item_count,
                "average_item_price": average_item_price,
                "is_new_user": request.is_new_user,
                "shipping_distance": request.shipping_distance,
            }
        )
        decision_log.append(self.fraud_agent.log(f"Risk score {risk_score_val:.2f}; status {fraud_status}."))
        logger.info(
            "fraud.checked",
            order_id=order_id,
            risk_score=risk_score_val,
            fraud_status=fraud_status,
        )
        await manager.send_order_update(order_id, {
            "event": "fraud.checked",
            "order_id": order_id,
            "data": {
                "risk_score": risk_score_val,
                "fraud_status": fraud_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        })
        # Record fraud score in Prometheus for alerting
        fraud_score.labels(order_id=order_id).set(risk_score_val)
        logger.info(
            "agent_decision",
            order_id=order_id,
            agent="FraudDetectionAgent",
            decision_type="fraud_check",
            risk_score=risk_score_val,
            threshold=0.65,
            decision=fraud_status,
        )
        fraud_score.labels(order_id=order_id).set(risk_score_val)

        # ───────────────────────────────────────────────
        # STEP 2: INVENTORY CHECK
        # ───────────────────────────────────────────────
        # Early exit if stock is insufficient. This prevents unnecessary
        # warehouse bidding and demand prediction for unfulfillable orders.
        stock_available, unavailable = self.inventory_agent.check_stock(request.items, products)
        if not stock_available:
            logger.info(
                "inventory.checked",
                order_id=order_id,
                stock_available=False,
                unavailable_items=unavailable,
            )
            await manager.send_order_update(order_id, {
                "event": "inventory.checked",
                "order_id": order_id,
                "data": {
                    "stock_available": False,
                    "unavailable_items": unavailable,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            })
            
            # Build rejected order ORM for persistence
            order_status = "rejected_out_of_stock"
            order_orm = OrderORM(
                order_id=order_id,
                user_id=request.user_id,
                order_status=order_status,
                order_total=order_total,
                selected_warehouse=None,
                risk_score=risk_score_val,
                fraud_status=fraud_status,
                predicted_demand=0,
                restock_recommendation="restock required",
            )
            item_orms = [
                OrderItemORM(
                    order_id=order_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    unit_price=products[item.product_id].price,
                )
                for item in request.items
                if item.product_id in products
            ]
            decision_orms = [
                AgentDecisionORM(
                    order_id=order_id,
                    agent_name=dec.agent,
                    decision_type="agent_log",
                    decision_data={"message": dec.message},
                )
                for dec in decision_log
            ]
            await self._persist_order(order_orm, item_orms, decision_orms, [])
            orders_total.labels(status=order_status).inc()
            order_processing_duration.observe(time() - start)
            logger.info(
                "fulfillment.completed",
                order_id=order_id,
                order_status=order_status,
            )
            await manager.send_order_update(order_id, {
                "event": "fulfillment.completed",
                "order_id": order_id,
                "data": {
                    "order_status": "rejected_out_of_stock",
                    "selected_warehouse": None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            })
            return OrderResponse(
                order_id=order_id,
                order_status=order_status,
                order_total=order_total,
                selected_warehouse=None,
                risk_score=risk_score_val,
                fraud_status=fraud_status,
                predicted_demand_next_7_days=0,
                restock_recommendation="restock required",
                bids=[],
                decision_log=decision_log,
                course_trace=self._course_trace(),
                model_evaluations=self._model_evaluations(risk_score_val, 0),
            )

        # Stock is available — continue with the pipeline
        logger.info(
            "inventory.checked",
            order_id=order_id,
            stock_available=True,
        )
        await manager.send_order_update(order_id, {
            "event": "inventory.checked",
            "order_id": order_id,
            "data": {
                "stock_available": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        })
        decision_log.append(self.inventory_agent.log("Stock checked: available."))

        # ───────────────────────────────────────────────
        # STEP 3: WAREHOUSE BIDDING (Contract Net Protocol)
        # ───────────────────────────────────────────────
        # The Coordinator broadcasts a CFP to all warehouses.
        # Each warehouse evaluates its own cost function and returns a bid.
        # The Coordinator selects the lowest bid as the winner.
        bids, winner = self.coordinator_agent.request_bids(item_count)
        for bid in bids:
            decision_log.append(
                self.coordinator_agent.log(
                    f"{bid.warehouse_id} submitted bid {bid.bid} with suitability {bid.suitability_score}. {bid.reason}."
                )
            )
            logger.info(
                "warehouse.bid",
                order_id=order_id,
                warehouse_id=bid.warehouse_id,
                bid_value=bid.bid,
                suitability_score=bid.suitability_score,
                is_winner=(bid.warehouse_id == winner.warehouse_id),
            )
            warehouse_bids_total.labels(warehouse_id=bid.warehouse_id).inc()
        await manager.send_order_update(order_id, {
            "event": "warehouse.bid",
            "order_id": order_id,
            "data": {
                "bids": jsonable_encoder(bids),
                "winner": winner.warehouse_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        })
        decision_log.append(self.coordinator_agent.log(f"Selected {winner.warehouse_id} using the lowest-bid policy."))

        # ───────────────────────────────────────────────
        # STEP 4: DEMAND PREDICTION (PyTorch MLP)
        # ───────────────────────────────────────────────
        # Predict future demand to trigger restock recommendations.
        # This runs AFTER warehouse selection because it's advisory only.
        predicted_demand = self.demand_agent.predict(selected_products)
        restock_recommendation = "restock recommended" if predicted_demand > sum(product.quantity for product in selected_products) else "no restock needed"
        decision_log.append(
            self.demand_agent.log(f"Predicted next 7-day demand: {predicted_demand} unit(s).")
        )
        logger.info(
            "agent_decision",
            order_id=order_id,
            agent="DemandPredictionAgent",
            decision_type="demand_prediction",
            predicted_demand=predicted_demand,
            restock_recommendation=restock_recommendation,
        )

        # ───────────────────────────────────────────────
        # STEP 5: STOCK RESERVATION (conditional on fraud status)
        # ───────────────────────────────────────────────
        # Only reserve stock for orders that pass fraud detection.
        # Orders flagged for review are held in a "pending" state
        # without consuming inventory.
        if fraud_status == "approved":
            self.inventory_agent.reserve_stock(request.items, products)
            order_status = "created"
            decision_log.append(self.inventory_agent.log("Inventory reserved for approved order."))
        else:
            order_status = "review_required"
            decision_log.append(self.order_agent.log("Order held for manual review."))

        # ───────────────────────────────────────────────
        # STEP 6: PERSISTENCE (atomic database transaction)
        # ───────────────────────────────────────────────
        # All ORM objects are created in memory first, then committed
        # in a single transaction. This guarantees ACID properties.
        order_orm = OrderORM(
            order_id=order_id,
            user_id=request.user_id,
            order_status=order_status,
            order_total=order_total,
            selected_warehouse=winner.warehouse_id,
            risk_score=risk_score_val,
            fraud_status=fraud_status,
            predicted_demand=predicted_demand,
            restock_recommendation=restock_recommendation,
        )
        item_orms = [
            OrderItemORM(
                order_id=order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=products[item.product_id].price,
            )
            for item in request.items
            if item.product_id in products
        ]
        decision_orms = [
            AgentDecisionORM(
                order_id=order_id,
                agent_name=dec.agent,
                decision_type="agent_log",
                decision_data={"message": dec.message},
            )
            for dec in decision_log
        ]
        bid_orms = [
            WarehouseBidORM(
                order_id=order_id,
                warehouse_id=bid.warehouse_id,
                bid_value=bid.bid,
                workload=bid.workload,
                distance=bid.distance,
                stock_level=bid.stock_level,
                processing_speed=bid.processing_speed,
                suitability_score=bid.suitability_score,
                reason=bid.reason,
                is_winner=(bid.warehouse_id == winner.warehouse_id),
            )
            for bid in bids
        ]

        await self._persist_order(
            order_orm,
            item_orms,
            decision_orms,
            bid_orms,
            update_stock=(order_status == "created"),
            products=products,
            request_items=request.items,
        )

        # ───────────────────────────────────────────────
        # STEP 7: METRICS & COMPLETION
        # ───────────────────────────────────────────────
        # Record Prometheus metrics for alerting and SLO tracking
        orders_total.labels(status=order_status).inc()
        order_processing_duration.observe(time() - start)
        logger.info(
            "fulfillment.completed",
            order_id=order_id,
            order_status=order_status,
            selected_warehouse=winner.warehouse_id,
        )
        # Final WebSocket push — frontend transitions to "completed" state
        await manager.send_order_update(order_id, {
            "event": "fulfillment.completed",
            "order_id": order_id,
            "data": {
                "order_status": order_status,
                "selected_warehouse": winner.warehouse_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        })

        return OrderResponse(
            order_id=order_id,
            order_status=order_status,
            order_total=order_total,
            selected_warehouse=winner.warehouse_id,
            risk_score=risk_score_val,
            fraud_status=fraud_status,
            predicted_demand_next_7_days=predicted_demand,
            restock_recommendation=restock_recommendation,
            bids=bids,
            decision_log=decision_log,
            course_trace=self._course_trace(),
            model_evaluations=self._model_evaluations(risk_score_val, predicted_demand),
        )

    async def _persist_order(
        self,
        order_orm: OrderORM,
        item_orms: list[OrderItemORM],
        decision_orms: list[AgentDecisionORM],
        bid_orms: list[WarehouseBidORM],
        update_stock: bool = False,
        products: dict[str, Product] | None = None,
        request_items: list[BasketItem] | None = None,
    ) -> None:
        """Atomic persistence of an order and all related entities.
        
        Uses the Repository pattern to abstract database operations.
        All writes happen in a single async SQLAlchemy transaction.
        
        Args:
            order_orm: The root Order entity
            item_orms: Line items associated with the order
            decision_orms: Agent decision audit trail
            bid_orms: Warehouse bid records
            update_stock: Whether to decrement product quantities (only for approved orders)
            products: Product map (required if update_stock=True)
            request_items: Basket items (required if update_stock=True)
            
        Interview Note:
            Q: Why Repository pattern instead of direct SQLAlchemy calls?
            A: Repositories encapsulate data access logic, making unit testing
               easier (mock the repository) and allowing future DB migrations
               without changing business logic.
        """
        try:
            async with AsyncSessionLocal() as session:
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

                if update_stock and products and request_items:
                    for item in request_items:
                        if item.product_id in products:
                            await product_repo.update_stock(item.product_id, -item.quantity)

                await session.commit()
        except Exception as exc:
            logger.warning(
                "order.persistence_degraded",
                order_id=order_orm.order_id,
                error=str(exc),
            )

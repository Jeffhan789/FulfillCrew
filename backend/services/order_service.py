from uuid import uuid4
from time import time

from datetime import datetime, timezone

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
    def __init__(self, product_service: ProductService) -> None:
        self.product_service = product_service
        self.order_agent = OrderAgent()
        self.inventory_agent = InventoryAgent()
        self.coordinator_agent = CoordinatorAgent()
        self.demand_agent = DemandPredictionAgent()
        self.fraud_agent = FraudDetectionAgent()

    def _course_trace(self) -> list[AgentDecision]:
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
        start = time()
        order_id = str(uuid4())
        logger.info(
            "order.created",
            order_id=order_id,
            user_id=request.user_id,
            item_count=sum(item.quantity for item in request.items),
            event="order.created",
        )
        await manager.send_order_update(order_id, {
            "event": "order.created",
            "order_id": order_id,
            "data": {
                "order_status": "pending",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        })

        products = await self.product_service.get_product_map()
        selected_products = [products[item.product_id] for item in request.items if item.product_id in products]
        item_count = sum(item.quantity for item in request.items)
        order_total = round(
            sum(products[item.product_id].price * item.quantity for item in request.items if item.product_id in products),
            2,
        )
        average_item_price = order_total / item_count if item_count else 0
        decision_log: list[AgentDecision] = [
            self.order_agent.log(f"Received order from {request.user_id} with {item_count} item(s).")
        ]

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
            event="fraud.checked",
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
        logger.info(
            "agent_decision",
            order_id=order_id,
            agent="FraudDetectionAgent",
            decision_type="fraud_check",
            risk_score=risk_score_val,
            threshold=0.65,
            decision=fraud_status,
            event="agent_decision",
        )
        fraud_score.labels(order_id=order_id).set(risk_score_val)

        stock_available, unavailable = self.inventory_agent.check_stock(request.items, products)
        if not stock_available:
            logger.info(
                "inventory.checked",
                order_id=order_id,
                stock_available=False,
                unavailable_items=unavailable,
                event="inventory.checked",
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
            logger.info(
                "agent_decision",
                order_id=order_id,
                agent="InventoryAgent",
                decision_type="stock_check",
                stock_available=False,
                unavailable_items=unavailable,
                event="agent_decision",
            )
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
                event="fulfillment.completed",
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

        logger.info(
            "inventory.checked",
            order_id=order_id,
            stock_available=True,
            event="inventory.checked",
        )
        await manager.send_order_update(order_id, {
            "event": "inventory.checked",
            "order_id": order_id,
            "data": {
                "stock_available": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        })
        logger.info(
            "agent_decision",
            order_id=order_id,
            agent="InventoryAgent",
            decision_type="stock_check",
            stock_available=True,
            event="agent_decision",
        )
        decision_log.append(self.inventory_agent.log("Stock checked: available."))

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
                event="warehouse.bid",
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
        logger.info(
            "agent_decision",
            order_id=order_id,
            agent="CoordinatorAgent",
            decision_type="warehouse_selection",
            selected_warehouse=winner.warehouse_id,
            event="agent_decision",
        )
        decision_log.append(self.coordinator_agent.log(f"Selected {winner.warehouse_id} using the lowest-bid policy."))

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
            event="agent_decision",
        )

        if fraud_status == "approved":
            self.inventory_agent.reserve_stock(request.items, products)
            order_status = "created"
            decision_log.append(self.inventory_agent.log("Inventory reserved for approved order."))
        else:
            order_status = "review_required"
            decision_log.append(self.order_agent.log("Order held for manual review."))

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

        orders_total.labels(status=order_status).inc()
        order_processing_duration.observe(time() - start)
        logger.info(
            "fulfillment.completed",
            order_id=order_id,
            order_status=order_status,
            selected_warehouse=winner.warehouse_id,
            event="fulfillment.completed",
        )
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

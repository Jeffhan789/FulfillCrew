from uuid import uuid4

from backend.agents.coordinator_agent import CoordinatorAgent
from backend.agents.demand_prediction_agent import DemandPredictionAgent
from backend.agents.fraud_detection_agent import FraudDetectionAgent
from backend.agents.inventory_agent import InventoryAgent
from backend.agents.order_agent import OrderAgent
from backend.database.models import AgentDecision, OrderRequest, OrderResponse
from backend.services.product_service import ProductService


class OrderService:
    def __init__(self, product_service: ProductService) -> None:
        self.product_service = product_service
        self.order_agent = OrderAgent()
        self.inventory_agent = InventoryAgent()
        self.coordinator_agent = CoordinatorAgent()
        self.demand_agent = DemandPredictionAgent()
        self.fraud_agent = FraudDetectionAgent()

    def create_order(self, request: OrderRequest) -> OrderResponse:
        products = self.product_service.get_product_map()
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

        risk_score, fraud_status = self.fraud_agent.score(
            {
                "order_total": order_total,
                "number_of_items": item_count,
                "average_item_price": average_item_price,
                "is_new_user": request.is_new_user,
                "shipping_distance": request.shipping_distance,
            }
        )
        decision_log.append(self.fraud_agent.log(f"Risk score {risk_score:.2f}; status {fraud_status}."))

        stock_available, unavailable = self.inventory_agent.check_stock(request.items, products)
        if not stock_available:
            decision_log.append(self.inventory_agent.log(f"Stock unavailable for: {', '.join(unavailable)}."))
            return OrderResponse(
                order_id=str(uuid4()),
                order_status="rejected_out_of_stock",
                order_total=order_total,
                selected_warehouse=None,
                risk_score=risk_score,
                fraud_status=fraud_status,
                predicted_demand_next_7_days=0,
                restock_recommendation="restock required",
                bids=[],
                decision_log=decision_log,
            )

        decision_log.append(self.inventory_agent.log("Stock checked: available."))
        bids, winner = self.coordinator_agent.request_bids(item_count)
        for bid in bids:
            decision_log.append(self.coordinator_agent.log(f"{bid.warehouse_id} submitted bid {bid.bid}."))
        decision_log.append(self.coordinator_agent.log(f"Selected {winner.warehouse_id}."))

        predicted_demand = self.demand_agent.predict(selected_products)
        restock_recommendation = "restock recommended" if predicted_demand > sum(product.quantity for product in selected_products) else "no restock needed"
        decision_log.append(
            self.demand_agent.log(f"Predicted next 7-day demand: {predicted_demand} unit(s).")
        )

        if fraud_status == "approved":
            self.inventory_agent.reserve_stock(request.items, products)
            order_status = "created"
            decision_log.append(self.inventory_agent.log("Inventory reserved for approved order."))
        else:
            order_status = "review_required"
            decision_log.append(self.order_agent.log("Order held for manual review."))

        return OrderResponse(
            order_id=str(uuid4()),
            order_status=order_status,
            order_total=order_total,
            selected_warehouse=winner.warehouse_id,
            risk_score=risk_score,
            fraud_status=fraud_status,
            predicted_demand_next_7_days=predicted_demand,
            restock_recommendation=restock_recommendation,
            bids=bids,
            decision_log=decision_log,
        )


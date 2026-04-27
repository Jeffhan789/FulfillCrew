from backend.agents.base_agent import BaseAgent
from backend.agents.warehouse_agent import WarehouseAgent
from backend.database.models import WarehouseBid


class CoordinatorAgent(BaseAgent):
    name = "Coordinator Agent"

    def __init__(self) -> None:
        self.warehouses = [
            WarehouseAgent("Warehouse A", "London", current_workload=5, stock_level=80, processing_speed=3.0, distance=8),
            WarehouseAgent("Warehouse B", "Birmingham", current_workload=2, stock_level=55, processing_speed=2.7, distance=22),
            WarehouseAgent("Warehouse C", "Manchester", current_workload=1, stock_level=40, processing_speed=2.1, distance=35),
        ]

    def request_bids(self, item_count: int) -> tuple[list[WarehouseBid], WarehouseBid]:
        bids = [warehouse.bid(item_count) for warehouse in self.warehouses]
        winner = min(bids, key=lambda bid: bid.bid)
        return bids, winner


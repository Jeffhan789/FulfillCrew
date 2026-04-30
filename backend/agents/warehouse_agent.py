from dataclasses import dataclass

from backend.database.models import WarehouseBid


@dataclass
class WarehouseAgent:
    warehouse_id: str
    location: str
    current_workload: int
    stock_level: int
    processing_speed: float
    distance: float

    def bid(self, item_count: int) -> WarehouseBid:
        stock_penalty = max(0, item_count - self.stock_level) * 2.0
        workload_penalty = self.current_workload * 0.8
        distance_penalty = self.distance * 0.15
        speed_bonus = self.processing_speed * 1.1
        bid_value = round(5 + stock_penalty + workload_penalty + distance_penalty - speed_bonus, 2)
        suitability_score = round(100 / (1 + max(0.1, bid_value)), 1)
        reason = (
            f"workload={self.current_workload}, stock={self.stock_level}, "
            f"distance={self.distance}km, speed={self.processing_speed}; lower bid is better"
        )
        return WarehouseBid(
            warehouse_id=self.warehouse_id,
            bid=max(0.1, bid_value),
            workload=self.current_workload,
            distance=self.distance,
            stock_level=self.stock_level,
            processing_speed=self.processing_speed,
            suitability_score=suitability_score,
            reason=reason,
        )

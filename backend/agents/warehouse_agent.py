"""Warehouse Agent — implements the "Contractor" role in Contract Net Protocol (CNP).

Each warehouse evaluates a Call for Proposals (CFP) and submits a bid
based on its internal cost function. The bid is a heuristic that combines:

    bid = 5 + stock_penalty + workload_penalty + distance_penalty - speed_bonus

Where:
    stock_penalty  = max(0, item_count - stock_level) * 2.0
    workload_penalty = current_workload * 0.8
    distance_penalty = distance * 0.15
    speed_bonus    = processing_speed * 1.1

This is a classic multi-objective optimisation problem:
- Minimise: stockouts, delivery time, workload imbalance
- Maximise: processing speed

The weights (2.0, 0.8, 0.15, 1.1) are hand-tuned heuristics. In a real system
you would learn these from historical data (e.g., reinforcement learning or
genetic algorithms) to minimise actual delivery costs.

Interview Note:
    Q: Why is lower bid better?
    A: The bid represents a "cost score". Lower cost = more attractive warehouse.
    
    Q: What if all warehouses have insufficient stock?
    A: The stock_penalty makes their bids very high, but the order is still
       assigned to the "least bad" warehouse. In a production system, the
       InventoryAgent would reject the order before CNP even starts.
    
    Q: How would you make this more realistic?
    A: Add real-time shipping API (DHL, FedEx), dynamic pricing, capacity
       constraints, and historical SLA performance data.
"""

from dataclasses import dataclass

from backend.schemas import WarehouseBid


@dataclass
class WarehouseAgent:
    """Represents a single warehouse in the logistics network.
    
    Attributes are the warehouse's "private information" — in a true MAS
    each warehouse would not share its full internal state with the Coordinator.
    The bid() method is the only public interface, enforcing encapsulation.
    """
    warehouse_id: str
    location: str
    current_workload: int
    stock_level: int
    processing_speed: float
    distance: float

    def bid(self, item_count: int) -> WarehouseBid:
        """Evaluate a CFP and return a bid.
        
        The bid formula encodes multiple objectives:
        1. STOCK: Penalise if order exceeds available stock (2.0 per unit short)
        2. WORKLOAD: Busier warehouses charge more (0.8 per existing task)
        3. DISTANCE: Farther warehouses cost more (0.15 per km)
        4. SPEED: Faster warehouses offer discount (1.1 per unit speed)
        
        suitability_score = 100 / (1 + bid) — normalised to 0-100 scale
        for the frontend gauge visualisation.
        """
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

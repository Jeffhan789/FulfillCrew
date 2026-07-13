"""Coordinator Agent — implements a simplified Contract Net Protocol (CNP).

CNP is a multi-agent interaction protocol where:
1. Manager (Coordinator) broadcasts a "Call for Proposals" (CFP)
2. Contractors (Warehouses) evaluate the CFP and submit bids
3. Manager selects the best bid based on a scoring function
4. Award is granted to the winner

This is the core COMP310 Multi-Agent Systems concept demonstrated in FulfillCrew.

Interview Questions & Answers:
    Q: Why CNP instead of centralized optimisation?
    A: CNP is decentralised, fault-tolerant, and mirrors real-world logistics
       where each warehouse has private cost functions.
    
    Q: What are the limitations of this simplified CNP?
    A: No backtracking if the winner declines, no multi-round negotiation,
       and the bid function is linear/heuristic rather than learned.
"""

from backend.agents.base_agent import BaseAgent
from backend.agents.warehouse_agent import WarehouseAgent
from backend.schemas import WarehouseBid


class CoordinatorAgent(BaseAgent):
    """Manages the warehouse bidding process using a simplified Contract Net Protocol.
    
    The Coordinator acts as the "Manager" in CNP terminology:
    1. Knows all available warehouse agents (contractors)
    2. Forwards order requirements to each warehouse
    3. Collects bids and selects the winner via lowest-bid policy
    
    The bid_value formula (see warehouse_agent.py) encodes:
    - stock_penalty: penalises warehouses with insufficient stock
    - workload_penalty: prefers less-busy warehouses
    - distance_penalty: prefers closer warehouses
    - speed_bonus: rewards faster processing speeds
    """
    name = "Coordinator Agent"

    def __init__(self) -> None:
        # Three warehouses with heterogeneous capabilities.
        # In a production system these would be loaded from a database
        # or service discovery registry.
        self.warehouses = [
            WarehouseAgent("Warehouse A", "London", current_workload=5, stock_level=80, processing_speed=3.0, distance=8),
            WarehouseAgent("Warehouse B", "Birmingham", current_workload=2, stock_level=55, processing_speed=2.7, distance=22),
            WarehouseAgent("Warehouse C", "Manchester", current_workload=1, stock_level=40, processing_speed=2.1, distance=35),
        ]

    def request_bids(self, item_count: int) -> tuple[list[WarehouseBid], WarehouseBid]:
        """Execute the CFP phase and select the winning bid.
        
        Args:
            item_count: Total quantity of items in the order.
            
        Returns:
            A tuple of (all_bids, winning_bid) where the winner is selected
            by the lowest bid value (lower = better).
            
        Interview Note:
            Q: Why min() with key=lambda bid: bid.bid?
            A: This is the "award" step of CNP. The scoring function is
               encapsulated inside each WarehouseAgent.bid() call, so the
               Coordinator only needs a simple comparison.
        """
        bids = [warehouse.bid(item_count) for warehouse in self.warehouses]
        winner = min(bids, key=lambda bid: bid.bid)
        return bids, winner

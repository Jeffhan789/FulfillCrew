"""FulfillCrew Multi-Agent Order Fulfillment System

Core Architecture:
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │ OrderAgent  │    │InventoryAgent│    │FraudDetection│
    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
           │                   │                   │
           └─────────┬─────────┴─────────┬─────────┘
                     │  CoordinatorAgent │
                     └─────────┬─────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
    ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
    │Warehouse A  │    │Warehouse B  │    │Warehouse C  │
    └─────────────┘    └─────────────┘    └─────────────┘

Courses Reflected:
    - COMP315 Cloud Computing: FastAPI + Docker + async architecture
    - COMP310 Multi-Agent Systems: Contract Net Protocol (CNP) for bidding
    - ELEC320 Neural Networks: MLP/XGBoost inference integration

Design Pattern: Template Method (BaseAgent) + Strategy (bidding heuristic)
"""

from backend.schemas import AgentDecision


class BaseAgent:
    """Base class for all agents in the FulfillCrew system.
    
    Implements the Template Method pattern where each agent has a unique 'name'
    but shares the same logging/audit interface. This ensures every decision
    is traceable for debugging and academic demonstration.
    
    Engineering Note:
        Q: Why use a base class instead of plain functions?
        A: Agents need shared identity, audit trails, and extensibility.
           BaseAgent guarantees every agent produces structured AgentDecision
           logs, which is critical for the timeline visualisation in the frontend.
    """
    name = "Base Agent"

    def log(self, message: str) -> AgentDecision:
        """Produce a structured audit log entry.
        
        Each call returns an AgentDecision dataclass that can be serialised
        to JSON and sent to the frontend timeline component.
        """
        return AgentDecision(agent=self.name, message=message)

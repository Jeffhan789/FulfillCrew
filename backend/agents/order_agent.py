"""Order Agent — the entry-point agent that receives and acknowledges orders.

In a real MAS (Multi-Agent System) this agent would:
1. Parse incoming order intent (NLP or structured JSON)
2. Decompose the order into sub-tasks (fraud check, inventory check, etc.)
3. Dispatch tasks to other agents via the event bus or direct method calls

In FulfillCrew the orchestration is handled by OrderService (see
backend/services/order_service.py) for simplicity, but the OrderAgent
remains as the conceptual owner of the order lifecycle.
"""

from backend.agents.base_agent import BaseAgent


class OrderAgent(BaseAgent):
    """Represents the customer-facing order intake agent.
    
    Interview Note:
        Q: What is the difference between OrderAgent and OrderService?
        A: OrderAgent is the *agent* role in the MAS architecture (COMP310).
           OrderService is the *application service* in the layered architecture
           (COMP315). In a strict microservice design, OrderAgent would be a
           separate container communicating via message queues.
    """
    name = "Order Agent"


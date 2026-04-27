from fastapi import APIRouter

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("")
def list_agents() -> dict[str, list[str]]:
    return {
        "agents": [
            "Order Agent",
            "Inventory Agent",
            "Coordinator Agent",
            "Warehouse Agent A",
            "Warehouse Agent B",
            "Warehouse Agent C",
            "Demand Prediction Agent",
            "Fraud Detection Agent",
        ]
    }


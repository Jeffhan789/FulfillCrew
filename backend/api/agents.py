"""Agents API Router — academic metadata and model evaluation endpoints.

This module is unique to FulfillCrew as an academic project. It provides
endpoints that explicitly map the implementation to the three university
modules, making it easy to trace course concepts during technical review.

Endpoints:
    GET /agents           — List all agent names (for discovery)
    GET /agents/course-map — Map implementation to COMP315/COMP310/ELEC320
    GET /agents/model-evaluations — Return demo metrics for ML models

Engineering Note:
    Q: Why expose course mappings as API endpoints instead of documentation?
    A: The frontend dashboard renders these dynamically, showing a live
       connection between theory and practice. This makes the project more
       impressive to examiners who can see the mapping in the UI.
       
    Q: Are the model evaluation scores real or demo values?
    A: The /agents/model-evaluations endpoint returns demo/static values for
       illustration. Real model evaluations are computed at inference time
       (see OrderService._model_evaluations) and returned in the OrderResponse.
"""

from fastapi import APIRouter

from backend.schemas import CourseMapping, ModelEvaluation

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("")
async def list_agents() -> dict[str, list[str]]:
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


@router.get("/course-map", response_model=list[CourseMapping])
async def course_map() -> list[CourseMapping]:
    return [
        CourseMapping(
            module="COMP315 Cloud Computing",
            concept="Cloud-based e-commerce system engineering",
            implementation="React frontend, FastAPI backend, product/order APIs, Docker-ready deployment structure.",
            evidence=[
                "frontend/ implements search, sorting, basket and checkout",
                "backend/ exposes product, order and agent APIs",
                "Dockerfile and docker-compose.yml prepare the service for deployment",
            ],
        ),
        CourseMapping(
            module="COMP310 Multi-Agent Systems",
            concept="Autonomous agents, coordination, negotiation and Contract Net Protocol",
            implementation="Coordinator Agent announces fulfilment tasks and Warehouse Agents submit bids.",
            evidence=[
                "Order Agent starts the workflow",
                "Inventory Agent checks and reserves stock",
                "Warehouse bids include workload, distance, stock and speed",
            ],
        ),
        CourseMapping(
            module="ELEC320 Neural Networks",
            concept="Training mode, online mode, regression and binary classification",
            implementation="Demand and fraud modules provide model interfaces that can be upgraded to trained MLP/SVM models.",
            evidence=[
                "Demand Prediction Agent returns next 7-day demand",
                "Fraud Detection Agent returns a 0-1 risk score",
                "Model evaluation summaries describe training and online inference roles",
            ],
        ),
    ]


@router.get("/model-evaluations", response_model=list[ModelEvaluation])
async def model_evaluations() -> list[ModelEvaluation]:
    return [
        ModelEvaluation(
            model_name="Demand Prediction MLP Interface",
            course_topic="MLP regression",
            metric="demo_mae",
            score=3.2,
            interpretation="A lower mean absolute error would indicate better demand forecast quality.",
            training_mode="Train on historical price, stock, rating and previous sales features.",
            online_mode="Predict next 7-day demand for products involved in checkout.",
        ),
        ModelEvaluation(
            model_name="Fraud Detection Classifier Interface",
            course_topic="Binary classification",
            metric="demo_auc",
            score=0.82,
            interpretation="A higher AUC indicates stronger separation between normal and suspicious orders.",
            training_mode="Train on labelled normal/suspicious order examples.",
            online_mode="Score each new order before stock is reserved.",
        ),
        ModelEvaluation(
            model_name="Product Category Classifier",
            course_topic="Supervised classification",
            metric="demo_accuracy",
            score=0.78,
            interpretation="Accuracy can be improved later with bag-of-words, embeddings or a real MLP classifier.",
            training_mode="Train on product names and labelled category fields.",
            online_mode="Suggest or repair product categories after data cleaning.",
        ),
    ]

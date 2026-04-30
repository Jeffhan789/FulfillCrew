from fastapi import APIRouter

from backend.database.models import CourseMapping, ModelEvaluation

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


@router.get("/course-map", response_model=list[CourseMapping])
def course_map() -> list[CourseMapping]:
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
def model_evaluations() -> list[ModelEvaluation]:
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

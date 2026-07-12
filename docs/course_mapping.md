# Course Mapping

This project maps three university modules into a single running system. The mapping is exposed through the `/agents/course-map` API and visualised in the frontend Course Intelligence Dashboard.

## COMP315 Cloud Computing

**Concept:** Cloud-based e-commerce system engineering

**Implementation in the system:**
- `frontend/` implements search, sorting, basket and checkout
- `backend/` exposes product, order and agent APIs
- `Dockerfile`, `frontend/Dockerfile` and `docker-compose.yml` provide a containerised multi-service deployment with Nginx reverse proxy
- JavaScript data cleaning pipeline from CA1 becomes the product data pipeline

**Evidence:**
- `frontend/` implements search, sorting, basket and checkout
- `backend/` exposes product, order and agent APIs
- `Dockerfile` and `docker-compose.yml` prepare the service for deployment

---

## COMP310 Multi-Agent Systems

**Concept:** Autonomous agents, coordination, negotiation and Contract Net Protocol

**Implementation in the system:**
- Order Agent starts the workflow
- Inventory Agent checks and reserves stock
- Coordinator Agent announces fulfilment tasks and selects warehouse bids
- Warehouse Agents submit bids using workload, distance, stock and speed
- Demand Prediction Agent and Fraud Detection Agent connect intelligent services into the order workflow

**Evidence:**
- `backend/agents/coordinator_agent.py` implements simplified Contract Net Protocol
- `backend/agents/warehouse_agent.py` returns explainable bids
- `backend/services/order_service.py` orchestrates the full agent pipeline

---

## ELEC320 Neural Networks

**Concept:** Training mode, online mode, regression and binary classification

**Implementation in the system:**
- Demand Prediction module provides a model interface that can be upgraded to a trained MLP regression model
- Fraud Detection module provides a model interface that can be upgraded to a trained MLP or SVM binary classifier
- Product Category Classifier demonstrates supervised classification using product fields

**Evidence:**
- `ml_models/demand_prediction/` returns next 7-day demand predictions
- `ml_models/fraud_detection/` returns a 0-1 risk score
- `ml_models/product_category_classifier/` classifies product names into categories
- `/agents/model-evaluations` describes training and online inference roles

---

# 课程映射

本项目将三门大学课程映射到一个运行系统中。该映射通过 `/agents/course-map` API 暴露，并在前端课程智能仪表盘中可视化。

## COMP315 云计算（Cloud Computing）

**概念：** 基于云的电商系统工程

**在系统中的实现：**
- React 前端实现搜索、排序、购物篮和结账
- FastAPI 后端暴露商品、订单和智能体 API
- `Dockerfile`、`frontend/Dockerfile` 和 `docker-compose.yml` 提供了基于 Nginx 反向代理的容器化多服务部署
- CA1 的 JavaScript 数据清洗流水线成为商品数据流水线

**证据：**
- `frontend/` 实现搜索、排序、购物篮和结账
- `backend/` 暴露商品、订单和智能体 API
- `Dockerfile`、`frontend/Dockerfile` 和 `docker-compose.yml` 提供了基于 Nginx 反向代理的容器化多服务部署

---

## COMP310 多智能体系统（Multi-Agent Systems）

**概念：** 自主智能体、协调、协商和合同网协议

**在系统中的实现：**
- 订单智能体启动工作流
- 库存智能体检查并预留库存
- 协调智能体发布履约任务并选择仓库竞价
- 仓库智能体使用负载、距离、库存和速度提交竞价
- 需求预测智能体和欺诈检测智能体将智能服务连接到订单工作流

**证据：**
- `backend/agents/coordinator_agent.py` 实现简化的合同网协议
- `backend/agents/warehouse_agent.py` 返回可解释的竞价
- `backend/services/order_service.py` 编排完整的智能体流水线

---

## ELEC320 神经网络（Neural Networks）

**概念：** 训练模式、在线模式、回归和二分类

**在系统中的实现：**
- 需求预测模块提供模型接口，可升级为训练好的 MLP 回归模型
- 欺诈检测模块提供模型接口，可升级为训练好的 MLP 或 SVM 二分类器
- 商品品类分类器展示使用商品字段进行监督分类

**证据：**
- `ml_models/demand_prediction/` 返回未来 7 天需求预测
- `ml_models/fraud_detection/` 返回 0-1 风险分数
- `ml_models/product_category_classifier/` 将商品名称分类到品类
- `/agents/model-evaluations` 描述训练和在线推理角色

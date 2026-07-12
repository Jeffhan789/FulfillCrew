# Agents Module

This module implements the multi-agent order fulfilment workflow.

## Agent Hierarchy

```
BaseAgent (base class)
  ├── OrderAgent
  ├── InventoryAgent
  ├── CoordinatorAgent
  ├── FraudDetectionAgent
  └── DemandPredictionAgent

WarehouseAgent (standalone dataclass, used by CoordinatorAgent)
```

## Files

| File | Description |
|------|-------------|
| `base_agent.py` | Abstract base class with `name` and `log()` |
| `order_agent.py` | Entry point for checkout requests |
| `inventory_agent.py` | Stock checking and reservation |
| `coordinator_agent.py` | Contract Net Protocol orchestrator |
| `warehouse_agent.py` | Bid computation for warehouse selection |
| `fraud_detection_agent.py` | Risk scoring using ML fraud model |
| `demand_prediction_agent.py` | Demand forecasting using ML prediction model |

## Usage

Agents are instantiated and orchestrated by `OrderService` in `backend/services/order_service.py`.

---

# 智能体模块

本模块实现多智能体订单履约工作流。

## 智能体层级

```
BaseAgent（基类）
  ├── OrderAgent（订单智能体）
  ├── InventoryAgent（库存智能体）
  ├── CoordinatorAgent（协调智能体）
  ├── FraudDetectionAgent（欺诈检测智能体）
  └── DemandPredictionAgent（需求预测智能体）

WarehouseAgent（独立数据类，由 CoordinatorAgent 使用）
```

## 文件

| 文件 | 说明 |
|------|------|
| `base_agent.py` | 抽象基类，包含 `name` 和 `log()` |
| `order_agent.py` | 结账请求入口点 |
| `inventory_agent.py` | 库存检查和预留 |
| `coordinator_agent.py` | 合同网协议编排器 |
| `warehouse_agent.py` | 仓库选择竞价计算 |
| `fraud_detection_agent.py` | 使用 ML 欺诈模型进行风险评分 |
| `demand_prediction_agent.py` | 使用 ML 预测模型进行需求预测 |

## 用法

智能体由 `backend/services/order_service.py` 中的 `OrderService` 实例化并编排。

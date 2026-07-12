# Agent Design

The order workflow follows a simplified Contract Net Protocol:

1. Order Agent receives a checkout request.
2. Inventory Agent checks stock availability.
3. Fraud Detection Agent scores order risk.
4. Coordinator Agent announces the task to Warehouse Agents.
5. Warehouse Agents submit bids.
6. Coordinator Agent selects the lowest bid.
7. Inventory Agent reserves stock if the order is approved.
8. Demand Prediction Agent estimates future demand for restock guidance.

## Agent Roles

| Agent | Role | Key Action |
|-------|------|------------|
| Order Agent | Entry point | Starts the workflow and logs order receipt |
| Fraud Detection Agent | Risk assessment | Scores orders and flags suspicious ones for review |
| Inventory Agent | Stock management | Checks availability and reserves approved items |
| Coordinator Agent | Task allocation | Announces tasks and selects the best warehouse bid |
| Warehouse Agent | Fulfilment bidding | Computes bid based on workload, distance, stock and speed |
| Demand Prediction Agent | Forecasting | Predicts near-term demand from product features |

## Bid Calculation

Each warehouse computes a bid using:

```
bid = 5 + stock_penalty + workload_penalty + distance_penalty - speed_bonus
```

The coordinator selects the warehouse with the lowest bid. Every bid includes an explainable reason string for transparency.

---

# 智能体设计

订单工作流遵循简化版合同网协议（Contract Net Protocol）：

1. 订单智能体接收结账请求
2. 库存智能体检查库存可用性
3. 欺诈检测智能体为订单风险评分
4. 协调智能体向仓储智能体发布任务
5. 仓储智能体提交竞价
6. 协调智能体选择最低竞价
7. 若订单获批，库存智能体预留库存
8. 需求预测智能体估算未来需求以指导补货

## 智能体角色

| 智能体 | 角色 | 关键动作 |
|--------|------|----------|
| 订单智能体 | 入口点 | 启动工作流并记录订单接收 |
| 欺诈检测智能体 | 风险评估 | 为订单评分，将可疑订单标记为待审核 |
| 库存智能体 | 库存管理 | 检查可用性并为已审批商品预留库存 |
| 协调智能体 | 任务分配 | 发布任务并选择最优仓储竞价 |
| 仓储智能体 | 履约竞价 | 基于工作负载、距离、库存与速度计算竞价 |
| 需求预测智能体 | 预测 | 基于商品特征预测近期需求 |

## 竞价计算

每个仓库按以下公式计算竞价：

```
竞价 = 5 + 库存惩罚 + 工作负载惩罚 + 距离惩罚 - 速度加成
```

协调智能体选择竞价最低的仓库。每次竞价均包含可解释的理由字符串，确保透明度。

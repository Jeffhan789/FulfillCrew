# Services Module

This module implements the business logic layer between the API routes and the agents.

## Files

| File | Description |
|------|-------------|
| `product_service.py` | Loads cleaned product JSON into memory; provides product listing and lookup |
| `order_service.py` | Orchestrates the full multi-agent order workflow and assembles the response |

## OrderService Flow

1. Validate items against the product catalog
2. Compute order total and average item price
3. Run Fraud Detection Agent
4. Check stock with Inventory Agent
5. If out of stock, return rejection response
6. Collect warehouse bids via Coordinator Agent
7. Predict demand via Demand Prediction Agent
8. Reserve stock if fraud status is approved
9. Assemble `OrderResponse` with full logs, bids, course trace and model evaluations

---

# 服务模块

本模块实现 API 路由与智能体之间的业务逻辑层。

## 文件

| 文件 | 说明 |
|------|------|
| `product_service.py` | 将清洗后的商品 JSON 加载到内存；提供商品列表和查询 |
| `order_service.py` | 编排完整的多智能体订单工作流并组装响应 |

## OrderService 流程

1. 验证商品是否在商品目录中
2. 计算订单总额和平均单价
3. 运行欺诈检测智能体
4. 使用库存智能体检查库存
5. 如果缺货，返回拒绝响应
6. 通过协调智能体收集仓库竞价
7. 通过需求预测智能体预测需求
8. 如果欺诈状态为通过，则预留库存
9. 组装包含完整日志、竞价、课程追踪和模型评估的 `OrderResponse`

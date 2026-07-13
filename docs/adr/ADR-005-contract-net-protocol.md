# FulfillCrew ADR-005：采用简化 Contract Net Protocol 协调多智能体

## 状态
Accepted — v2.0 已实施（v1.0 已使用）

## 背景
FulfillCrew 的核心卖点是"多智能体订单履约系统"。需要一种协调机制让多个自主智能体（订单、欺诈检测、库存、协调、仓库、需求预测）合作完成一个订单。

COMP310 Multi-Agent Systems 课程教授了多种协调协议：
- Contract Net Protocol（合同网协议）— 任务拍卖模式
- Blackboard System（黑板系统）— 共享工作空间
- Hierarchical Control（层级控制）— 主从模式

## 决策
采用**简化版 Contract Net Protocol（CNP）** 作为多智能体协调机制，具体用于仓库竞价场景。

## 考虑方案

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| **Contract Net Protocol** | 经典 MAS 协议；架构复盘易解释；仓库竞价场景天然匹配 | 需要设计竞价函数；比简单函数调用复杂 | ✅ 选中 |
| 黑板系统 | 共享知识；适合复杂推理 | 实现复杂；需要黑板管理器；不适合简单任务分配 | ❌ 过重 |
| 层级控制（主从） | 简单；命令链清晰 | 不体现"自治"；协调器负担过重；与 MAS 理念冲突 | ❌ 非 MAS |
| 简单顺序函数调用 | 最简单；易调试 | 不体现多智能体特性；架构复盘难以展开 | ❌ 无 MAS 价值 |
| BDI（Belief-Desire-Intention） | 强智能体模型；适合复杂决策 | 需要 BDI 框架（如 Jason）；对 Python 项目过重 | ❌ 过重 |

## 技术细节

### Contract Net Protocol 标准流程
```
Initiator（协调智能体）        Participants（仓库智能体）
    |                                 |
    |  1. Call for Proposals (CFP)   |
    | ─────────────────────────────► |
    |                                 |
    |  2. Bid (proposal)             |
    | ◄───────────────────────────── |
    |                                 |
    |  3. Award (contract)           |
    | ─────────────────────────────► |
    |                                 |
    |  4. Result (fulfillment)       |
    | ◄───────────────────────────── |
```

### 我们的简化实现
```python
# backend/agents/coordinator_agent.py
class CoordinatorAgent:
    def request_bids(self, item_count: int) -> tuple[list[WarehouseBid], WarehouseBid]:
        bids = []
        for warehouse in self.warehouses:
            bid = warehouse.compute_bid(item_count)
            bids.append(bid)
        
        # 最低竞价策略（lowest-bid policy）
        winner = min(bids, key=lambda b: b.bid)
        return bids, winner
```

### 竞价函数设计
```python
# backend/agents/warehouse_agent.py
bid = 5 + stock_penalty + workload_penalty + distance_penalty - speed_bonus

# 具体因素：
# - stock_penalty: 库存不足时惩罚（缺货 → 高 bid → 不选）
# - workload_penalty: 当前工作负载（越忙 → 高 bid）
# - distance_penalty: 距离客户越远越高
# - speed_bonus: 处理速度越快，bid 越低（负值优惠）
```

### 为什么设计这个公式？
1. **基值 5**：确保 bid 为正，避免除零或负数问题
2. **惩罚项（+）**：因素对履约不利时增加 bid（越高越不选）
3. **奖励项（-）**：因素对履约有优势时降低 bid
4. **可解释性**：每个 bid 附带 `reason` 字符串，说明为什么是这个值

### 6 个智能体的角色分工
```
Order Agent          — 入口点，接收订单，启动工作流
Fraud Detection Agent — 风险评分，决定是否人工审核
Inventory Agent      — 检查库存，预留库存
Coordinator Agent    — 发布任务，收集竞价，选择最佳仓库
Warehouse Agent x3   — 自主计算 bid，基于本地状态
Demand Prediction Agent — 预测未来需求，提供补货建议
```

### 工作流时序
```
User 提交订单
    ↓
Order Agent — 记录订单接收
    ↓
Fraud Detection Agent — 评分（0-1）
    ↓（如果 fraud_status == "review_required"）
    → 订单进入人工审核，不执行后续步骤
    ↓（如果 fraud_status == "approved"）
Inventory Agent — 检查库存
    ↓（如果缺货）
    → 订单拒绝，状态 = rejected_out_of_stock
    ↓（如果库存充足）
Coordinator Agent — 发布 CFP 给 3 个 Warehouse Agents
    ↓
Warehouse Agents — 各自计算 bid 并返回
    ↓
Coordinator Agent — 选择最低 bid 的仓库
    ↓
Inventory Agent — 预留库存
    ↓
Demand Prediction Agent — 预测未来 7 天需求
    ↓
持久化到 PostgreSQL + WebSocket 推送
```

## 权衡与风险

| 风险 | 缓解措施 |
|------|----------|
| 竞价公式过于简单 | 设计上就有意保持简单；架构复盘时强调"可解释性"而非"最优性" |
| 仓库智能体不是真正的独立进程 | 在课程项目中这是可接受的；真实系统可以用 Celery/独立服务 |
| 没有考虑多仓库协同（如分仓发货） | 当前是单仓库胜出；未来可扩展为组合优化 |
| 协调器是单点 | 真实系统需高可用协调器；当前用 Python 类实现 |

## 架构复盘要点

### Q1: 什么是 Contract Net Protocol？
> "Contract Net Protocol 是 Smith 在 1980 年提出的多智能体协商协议。核心思想是：一个 Initiator（管理者）发布任务招标（Call for Proposals），多个 Participant（承包商）提交报价（Bid），管理者选择最佳报价并授予合同。在我们的系统中，协调智能体是 Initiator，仓库智能体是 Participants。"

### Q2: 你们的竞价函数是怎么设计的？为什么这样设计？
> "bid = 5 + stock_penalty + workload_penalty + distance_penalty - speed_bonus。基值 5 保证结果为正。惩罚项越高表示该仓库不适合履约——库存少、工作负载高、距离远。speed_bonus 是负值，处理速度快的仓库 bid 更低。这个设计的核心优势是可解释性：每个 bid 都附带一个 reason 字符串，说明为什么是这个值。"

### Q3: 如果两个仓库 bid 相同怎么办？
> "当前实现用 Python 的 `min()` 函数，如果有相同最小值，会选择列表中第一个。在真实系统中，可以添加次级排序规则：比如优先选择库存更高的、距离更近的。或者引入随机化避免总是偏向同一个仓库。"

### Q4: 你们的多智能体是并发运行的吗？
> "在 v2.0 中，仓库竞价是串行的（在 Python 中循环调用），但因为计算足够快，延迟可接受。真实系统可以让每个 Warehouse Agent 作为独立进程/微服务，通过消息队列并发处理。我们保留了这种扩展路径：仓库智能体是独立类，未来可以轻易提取为独立服务。"

### Q5: 这 6 个智能体是微服务吗？
> "当前不是，它们是 Python 类，运行在同一个进程中。但从架构上，每个智能体有清晰的职责边界和接口契约，符合微服务的设计思想。未来可以将 Fraud Detection Agent 和 Demand Prediction Agent 提取为独立的 ML 推理服务，通过 HTTP/gRPC 调用。"

## 相关文件
- `backend/agents/base_agent.py` — 智能体基类
- `backend/agents/coordinator_agent.py` — 协调智能体
- `backend/agents/warehouse_agent.py` — 仓库智能体
- `backend/agents/order_agent.py` — 订单智能体
- `backend/agents/inventory_agent.py` — 库存智能体
- `backend/agents/fraud_detection_agent.py` — 欺诈检测智能体
- `backend/agents/demand_prediction_agent.py` — 需求预测智能体
- `backend/services/order_service.py` — 完整工作流编排

## 参考
- [Smith, R. G. (1980). The Contract Net Protocol: High-Level Communication and Control in a Distributed Problem Solver](https://www.sciencedirect.com/science/article/pii/0004370280900333)
- [Multi-Agent Systems: Algorithmic, Game-Theoretic, and Logical Foundations — Yoav Shoham & Kevin Leyton-Brown](http://www.masfoundations.org/)
- [COMP310 课程讲义 — Contract Net Protocol](https://www.liverpool.ac.uk/computer-science/)

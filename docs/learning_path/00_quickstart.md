# 快速上手：30 分钟跑通 FulfillCrew

> **预计时间**：30 分钟  
> **前置知识**：已安装 Docker Desktop（或 Docker + Docker Compose）、了解基本的浏览器操作  
> **目标**：从 `git clone` 到完成第一个订单，建立对系统的直观认知

---

## 目录

1. [步骤 1：克隆项目并启动](#步骤-1克隆项目并启动--5-分钟)
2. [步骤 2：添加商品到购物车并结账](#步骤-2添加商品到购物车并结账--5-分钟)
3. [步骤 3：观察 WebSocket 实时推送](#步骤-3观察-websocket-实时推送--5-分钟)
4. [步骤 4：浏览 Swagger UI 理解 API](#步骤-4浏览-swagger-ui-理解-api--10-分钟)
5. [步骤 5：查看前端 Dashboard](#步骤-5查看前端-dashboard--5-分钟)
6. [自测检查清单](#自测检查清单)

---

## 步骤 1：克隆项目并启动（5 分钟）

### 1.1 克隆代码

```bash
git clone <项目仓库地址>
cd FulfillCrew
```

> 💡 如果没有 git，可以直接下载 ZIP 并解压到本地目录。

### 1.2 检查环境

确保 Docker Desktop 正在运行：

```bash
docker --version
docker compose --version
```

预期输出：
```
Docker version 24.x.x, build xxxxx
docker compose version v2.x.x
```

### 1.3 启动所有服务

```bash
docker compose up --build
```

> ⏱️ 首次构建约需 2-5 分钟（取决于网络速度），会下载 Python、Node、PostgreSQL、Redis 镜像并编译前端。

预期输出（最后几行）：
```
fulfillcrew-backend  | INFO     application_startup event=startup
fulfillcrew-backend  | INFO     database.initialized
fulfillcrew-postgres | ... database system is ready to accept connections
fulfillcrew-redis    | ... Ready to accept connections
fulfillcrew-backend  | INFO     Uvicorn running on http://0.0.0.0:8000
fulfillcrew-frontend | ... nginx started
```

### 1.4 验证服务状态

打开浏览器访问以下地址，确认全部可达：

| 服务 | 地址 | 预期结果 |
|------|------|----------|
| 前端页面 | `http://localhost` | 看到商品列表页面 |
| Swagger API 文档 | `http://localhost:8000/docs` | 看到 FastAPI 自动生成的 API 文档 |
| 健康检查 | `http://localhost:8000/health` | JSON 返回 `{"status": "healthy"}` |
| Prometheus 指标 | `http://localhost:8000/metrics` | 看到原始指标文本 |

---

## 步骤 2：添加商品到购物车并结账（5 分钟）

### 2.1 浏览商品

在前端页面中：
- 看到商品卡片（名称、价格、评分、库存数量）
- 使用搜索框搜索商品名称
- 使用排序下拉菜单按价格/评分排序
- 勾选 "In stock" 仅显示有库存商品

### 2.2 添加商品到购物车

点击任意商品卡片上的 **"Add"** 按钮：
- 右侧 Basket 面板会增加商品行
- 多次点击同一商品会增加数量
- 点击 "-" 减少数量，"+" 增加数量

### 2.3 结账（Checkout）

点击 Basket 面板底部的 **"Checkout"** 按钮：

**预期行为**：
1. 按钮变为加载状态（短暂）
2. 页面下方出现订单结果面板
3. 订单状态从 `pending` → 经过 `fraud.checked` → `inventory.checked` → `warehouse.bid` → `fulfillment.completed`

---

## 步骤 3：观察 WebSocket 实时推送（5 分钟）

### 3.1 查看 WebSocket 状态

在订单结果面板顶部，可以看到一行状态：

```
● Live    Latest: fraud.checked — approved
```

- `● Live` = WebSocket 连接正常，实时接收订单状态更新
- `○ Offline` = WebSocket 连接断开，系统回退到轮询

### 3.2 理解推送流程

每次订单状态变化，后端都会通过 WebSocket 向前端推送事件：

| 顺序 | 事件 | 含义 | 对应 Agent |
|------|------|------|------------|
| 1 | `order.created` | 订单已创建 | OrderAgent |
| 2 | `fraud.checked` | 欺诈检测完成 | FraudDetectionAgent |
| 3 | `inventory.checked` | 库存检查完成 | InventoryAgent |
| 4 | `warehouse.bid` | 仓库竞价完成 | CoordinatorAgent |
| 5 | `fulfillment.completed` | 订单履约完成 | OrderAgent |

> 💡 代码对应：
> - 后端推送：`backend/api/websocket.py` → `manager.send_order_update()`
> - 前端接收：`frontend/src/hooks/useOrderSocket.ts` → `WebSocket` 连接

---

## 步骤 4：浏览 Swagger UI 理解 API（10 分钟）

### 4.1 打开 Swagger 文档

访问 `http://localhost:8000/docs`，你将看到 FastAPI 自动生成的交互式 API 文档：

### 4.2 核心 API 速览

| API 端点 | 方法 | 功能 | 对应前端功能 |
|----------|------|------|------------|
| `/products` | GET | 获取所有商品 | 商品列表页 |
| `/orders` | POST | 创建订单 | Checkout 按钮 |
| `/orders/{id}` | GET | 查询订单详情 | 订单状态追踪 |
| `/agents/course-map` | GET | 课程映射信息 | Course Dashboard |
| `/agents/model-evaluations` | GET | 模型评估数据 | ML Model Evaluations 面板 |
| `/health` | GET | 系统健康检查 | System Health 面板 |
| `/metrics` | GET | Prometheus 指标 | 可观测性监控 |

### 4.3 亲手调用一次 API

在 Swagger UI 中：

1. 找到 `/orders` → `POST` 端点
2. 点击 **"Try it out"**
3. 在 Request Body 中填入：

```json
{
  "user_id": "demo-user",
  "shipping_distance": 18,
  "is_new_user": true,
  "items": [
    { "product_id": "prod-001", "quantity": 2 }
  ]
}
```

4. 点击 **"Execute"**
5. 观察 Response Body 中的完整订单结果：

```json
{
  "order_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "order_status": "created",
  "order_total": 45.98,
  "selected_warehouse": "warehouse_0",
  "risk_score": 0.32,
  "fraud_status": "approved",
  "predicted_demand_next_7_days": 156,
  "restock_recommendation": "restock recommended",
  "bids": [...],
  "decision_log": [...],
  "course_trace": [...],
  "model_evaluations": [...]
}
```

---

## 步骤 5：查看前端 Dashboard（5 分钟）

### 5.1 六大可视化组件

结账成功后，页面下方会出现一个 Dashboard 网格，包含 4 个可视化组件：

| 组件 | 功能 | 数据来源 |
|------|------|----------|
| **Risk Score Gauge** | 欺诈风险仪表盘 | `fraud_status` + `risk_score` |
| **Warehouse Bid Chart** | 仓库竞价对比图 | `bids` 数组 |
| **Demand Prediction Chart** | 需求预测柱状图 | `predicted_demand_next_7_days` |
| **Order Status Timeline** | 决策日志时间线 | `decision_log` 数组 |
| **System Health Panel** | 系统健康状态 | `/health` API |
| **Model Evaluation Panel** | 模型评估详情 | `model_evaluations` 数组 |

### 5.2 Course Dashboard

在商品列表上方，还有一个 "Course Intelligence Dashboard"，展示三门课程如何映射到系统实现：

- **COMP315 Cloud Computing** → 前端、后端、Docker
- **COMP310 Multi-Agent Systems** → Agent 协作、Contract Net Protocol
- **ELEC320 Neural Networks** → MLP、XGBoost、分类器

> 对应代码：`backend/services/order_service.py` → `_course_trace()` 方法

---

## 自测检查清单

完成本章节后，你应该能够回答以下问题：

- [ ] 我能否成功用 Docker Compose 启动所有服务？
- [ ] 我能否在前端完成一次完整的结账流程？
- [ ] 我能否说出订单从创建到完成的 5 个状态变化？
- [ ] 我能否在 Swagger UI 中手动调用 `/orders` API 并理解返回字段？
- [ ] 我能否指出 Dashboard 中每个可视化组件对应的数据来源？
- [ ] 我能否解释 WebSocket `● Live` 状态的含义？

---

## 下一步

恭喜！你已经完成了 30 分钟快速上手。现在可以选择：

1. **逐模块理解** → 前往 [`01_module_by_module.md`](./01_module_by_module.md) 阅读核心实现
2. **按专题深入** → 前往 [`03_deep_dive.md`](./03_deep_dive.md) 定位具体技术主题

---

## 附录：常用命令速查

```bash
# 启动所有服务（前台模式，适合首次运行观察日志）
docker compose up --build

# 启动所有服务（后台模式）
docker compose up -d --build

# 查看日志
docker compose logs -f backend

# 停止所有服务
docker compose down

# 停止并删除数据卷（彻底重置）
docker compose down -v

# 只启动后端（开发调试）
docker compose up postgres redis -d
cd backend && uvicorn backend.main:app --reload --port 8000

# 只启动前端（开发调试）
cd frontend && npm run dev
```

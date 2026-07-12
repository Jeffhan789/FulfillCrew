# System Design

```text
React Frontend
  -> FastAPI Backend
    -> Multi-Agent System
      -> Demand and Fraud ML Modules
    -> Cleaned Product Data
```

The first implementation keeps data in memory so that the portfolio demo remains easy to run. The next natural upgrade is to replace the in-memory product store with SQLite or PostgreSQL.

## Components

- **Frontend (React + Vite)**: Single-page application with product browsing, basket management, checkout and order result display.
- **Backend (FastAPI)**: REST API layer handling products, orders and agent metadata.
- **Multi-Agent System**: Autonomous agents coordinating order fulfilment via a simplified Contract Net Protocol.
- **ML Modules**: Lightweight deterministic models with stable inference contracts, ready to be upgraded to trained models.
- **Data Pipeline**: JavaScript cleaning pipeline that transforms noisy raw product JSON into validated records.

## Testing

The system includes comprehensive tests at every layer:

- Unit tests for ML models
- Integration tests for agent workflows
- API endpoint tests with FastAPI TestClient
- Service layer tests with shared fixtures

---

# 系统设计

```text
React 前端
  -> FastAPI 后端
    -> 多智能体系统
      -> 需求预测与欺诈检测 ML 模块
    -> 清洗后的商品数据
```

第一版实现将数据保留在内存中，确保作品集演示易于运行。下一步自然升级是将内存中的商品存储替换为 SQLite 或 PostgreSQL。

## 组件

- **前端（React + Vite）**：单页应用，支持商品浏览、购物篮管理、结账与订单结果展示
- **后端（FastAPI）**：REST API 层，处理商品、订单与智能体元数据
- **多智能体系统**：自主智能体通过简化版合同网协议协调订单履约
- **ML 模块**：轻量级确定性模型，具备稳定的推理接口，可随时升级为训练好的模型
- **数据管道**：JavaScript 清洗管道，将含噪声的原始商品 JSON 转换为已验证的记录

## 测试

系统在每一层都包含全面的测试：

- ML 模型单元测试
- 智能体工作流集成测试
- 使用 FastAPI TestClient 的 API 端点测试
- 使用共享 fixture 的服务层测试

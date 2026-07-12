# Frontend

This folder contains the React + Vite frontend for the FulfillCrew order intelligence system.

## Tech Stack

- **React 18** with TypeScript
- **Vite** as the build tool and dev server
- **Lucide React** for icons
- Vanilla CSS for styling (no UI framework)

## Features

- Product catalog with search, sort and in-stock filter
- Basket management with add/remove/quantity controls
- Checkout that sends orders to the FastAPI backend
- Order result display with warehouse bids, risk scores, demand predictions and decision logs
- Course Intelligence Dashboard showing how COMP315, COMP310 and ELEC320 map into the system

## Development

```bash
cd frontend
npm install
npm run dev
```

The dev server runs on `http://127.0.0.1:5173` by default.

## Build

```bash
npm run build
```

The production build is output to `frontend/dist/`.

## API Base URL

The frontend expects the backend at `http://127.0.0.1:8000`. Update `API_BASE` in `src/main.tsx` if your backend runs on a different host or port.

---

# 前端

本文件夹包含 FulfillCrew 订单智能系统的 React + Vite 前端。

## 技术栈

- **React 18** + TypeScript
- **Vite** 作为构建工具和开发服务器
- **Lucide React** 用于图标
- 原生 CSS 样式（无 UI 框架）

## 功能

- 商品目录，支持搜索、排序和库存筛选
- 购物篮管理，支持添加/移除/数量控制
- 结账功能，将订单发送到 FastAPI 后端
- 订单结果展示，包括仓库竞价、风险分数、需求预测和决策日志
- 课程智能仪表盘，展示 COMP315、COMP310 和 ELEC320 如何映射到系统中

## 开发

```bash
cd frontend
npm install
npm run dev
```

开发服务器默认运行在 `http://127.0.0.1:5173`。

## 构建

```bash
npm run build
```

生产构建输出到 `frontend/dist/`。

## API 基础 URL

前端期望后端在 `http://127.0.0.1:8000`。如果你的后端运行在不同的主机或端口上，请更新 `src/main.tsx` 中的 `API_BASE`。

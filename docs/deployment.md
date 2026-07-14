# Deployment Guide

## Deployment Overview

FulfillCrew is containerised as a multi-service Docker Compose stack. The architecture consists of:

- **Backend** -- FastAPI application served by Uvicorn (`Dockerfile`)
- **Frontend** -- React SPA built with Vite and served by Nginx (`frontend/Dockerfile`)
- **Nginx reverse proxy** -- Routes `/api/*`, `/health`, `/docs` and `/openapi.json` to the backend; serves static assets directly (`frontend/nginx.conf`)
- **Shared Docker network** -- `fulfillcrew-network` bridges frontend and backend communication

Two Compose files are provided:

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Production -- optimised multi-stage builds, health checks, auto-restart |
| `docker-compose.dev.yml` | Development -- mounts source code for hot reload, maps frontend to port 8080 |

## Prerequisites

- Docker Engine >= 24.0
- Docker Compose >= 2.20

## Quick Start -- Production

```bash
# 1. Navigate to the project root
cd FulfillCrew

# 2. (Optional) create environment file from template
cp .env.example .env

# 3. Build and start all services in detached mode
docker compose up --build -d

# 4. Verify containers are healthy
docker compose ps

# 5. Open the frontend
open http://localhost        # macOS
xdg-open http://localhost    # Linux
```

Services will be available at:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost | React SPA via Nginx |
| Backend API | http://localhost:8000 | FastAPI application |
| API Docs | http://localhost:8000/docs | Swagger UI (auto-generated) |
| OpenAPI | http://localhost:8000/openapi.json | OpenAPI 3.0 schema |

### Stop Production Stack

```bash
# Graceful stop (preserves volumes)
docker compose down

# Full cleanup -- removes containers, networks and built images
docker compose down --volumes --rmi all
```

## Quick Start -- Development

The development Compose file mounts backend source code as read-only volumes and enables Uvicorn hot reload. The frontend is mapped to port 8080 to avoid conflicts with any local Nginx.

```bash
docker compose -f docker-compose.dev.yml up --build -d
```

| Service | URL | Notes |
|---------|-----|-------|
| Frontend | http://localhost:8080 | Nginx serving built SPA |
| Backend | http://localhost:8000 | Hot reload enabled (`--reload`) |

To view backend logs with hot reload feedback:

```bash
docker logs -f fulfillcrew-backend-dev
```

## Architecture Detail

### Backend Dockerfile

- **Builder stage** (`python:3.12-slim`)
  - Installs build dependencies (`gcc`)
  - Installs Python requirements into `/root/.local`
- **Runtime stage** (`python:3.12-slim`)
  - Copies Python packages from builder
  - Copies `backend/`, `ml_models/` and cleaned product data
  - Sets `PYTHONPATH=/app`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`
  - Exposes port 8000
  - Declares Docker `HEALTHCHECK` on `/health`
  - Runs `uvicorn backend.main:app --host 0.0.0.0 --port 8000`

### Frontend Dockerfile

- **Builder stage** (`node:20-alpine`)
  - Runs `npm ci` for reproducible installs
  - Sets `VITE_API_BASE=/api` so the built SPA uses relative API paths
  - Runs `npm run build` to produce `dist/`
- **Runtime stage** (`nginx:alpine`)
  - Copies `dist/` to Nginx document root
  - Copies `nginx.conf` to `/etc/nginx/conf.d/default.conf`
  - Enables gzip compression for static assets
  - Declares Docker `HEALTHCHECK` on `/`
  - Exposes port 80

### Nginx Configuration (`frontend/nginx.conf`)

- Serves React SPA with `try_files` fallback for client-side routing
- Proxies `/api/` -> `http://backend:8000/` (strips `/api` prefix)
- Proxies `/health`, `/docs`, `/openapi.json` -> backend directly
- Applies gzip compression and 1-year cache headers for static assets

### CORS Configuration

The backend reads allowed origins from the `CORS_ORIGINS` environment variable (comma-separated). If not set, it falls back to a sensible default covering common local development URLs:

```
http://localhost:5173   # Vite dev server
http://127.0.0.1:5173   # Vite dev server (IP)
http://localhost        # Nginx (production)
http://127.0.0.1        # Nginx (IP)
http://localhost:8080   # Nginx (dev)
```

For production deployment, set `CORS_ORIGINS` to your deployed frontend domain:

```bash
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

## Environment Variables

Copy `.env.example` to `.env` and adjust values:

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_LOG_LEVEL` | FastAPI / Uvicorn log level | `info` |
| `BACKEND_PORT` | Port inside the backend container | `8000` |
| `FRONTEND_PORT` | Host port mapped to Nginx | `80` |
| `API_BASE_URL` | Frontend dev API base (local non-Docker) | `http://127.0.0.1:8000` |
| `CORS_ORIGINS` | Comma-separated allowed origins | See `.env.example` |

## Manual Development (Without Docker)

If you prefer running services directly on your host machine:

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite's dev server proxies `/api` and `/health` to `http://127.0.0.1:8000` automatically. Open http://localhost:5173.

### Data Cleaning

```bash
node data_cleaning/data_processing.js \
  data_cleaning/raw_products/products.json \
  data_cleaning/cleaned_products/products.json
```

## Shared-deployment checklist

- [x] Provide `.env.example` for local configuration
- [x] Run PostgreSQL and Redis through Docker Compose
- [x] Persist orders and products through SQLAlchemy repositories
- [x] Run tests, frontend build, dependency audit, data-cleaning verification, and image build in CI
- [x] Emit structured application logs and Prometheus metrics
- [ ] Add TLS termination (Let's Encrypt, Cloudflare, or cloud load balancer)
- [ ] Configure `CORS_ORIGINS` for the shared domain
- [ ] Add versioned database migrations (Alembic or similar)
- [ ] Add an authenticated image-publishing and deployment pipeline
- [ ] Add a log aggregation backend
- [ ] Add rate limiting on the order creation endpoint
- [ ] Connect metrics to Prometheus + Grafana or a cloud-native monitor
- [ ] Add automated backups for persistent data volumes

## Docker Health Checks

All four services declare Docker health checks:

| Container | Check Interval | Command |
|-----------|---------------|---------|
| `fulfillcrew-postgres` | 10s | `pg_isready -U postgres` |
| `fulfillcrew-redis` | 10s | `redis-cli ping` |
| `fulfillcrew-backend` | 30s | `urllib.request.urlopen('http://localhost:8000/health')` |
| `fulfillcrew-frontend` | 30s | `wget --spider http://localhost/` |

Inspect health status:

```bash
docker compose ps
docker inspect --format='{{.State.Health.Status}}' fulfillcrew-backend
docker inspect --format='{{.State.Health.Status}}' fulfillcrew-frontend
```

## Troubleshooting

### Frontend cannot reach backend

- Check that both containers are on the same Docker network: `docker network inspect fulfillcrew-network`
- Verify the backend is healthy: `docker compose ps`
- Check backend logs: `docker logs fulfillcrew-backend`
- Ensure `CORS_ORIGINS` includes your frontend origin

### Port 80 is already in use

- Change the host port mapping in `docker-compose.yml`: `ports: ["8080:80"]`
- Or use the dev Compose file which maps to port 8080 by default

### Hot reload not working in dev mode

- Ensure volumes in `docker-compose.dev.yml` point to the correct paths
- Check that `backend/main.py` is being mounted correctly: `docker exec fulfillcrew-backend-dev ls -la /app/backend`

---

# 部署指南

## 部署概览

FulfillCrew 已容器化为多服务 Docker Compose 栈。架构由以下部分组成：

- **后端** -- FastAPI 应用，由 Uvicorn 提供服务（`Dockerfile`）
- **前端** -- React SPA，Vite 构建，Nginx 提供服务（`frontend/Dockerfile`）
- **Nginx 反向代理** -- 将 `/api/*`、`/health`、`/docs` 和 `/openapi.json` 路由到后端；直接提供静态资源（`frontend/nginx.conf`）
- **共享 Docker 网络** -- `fulfillcrew-network` 桥接前端与后端通信

提供两份 Compose 文件：

| 文件 | 用途 |
|------|------|
| `docker-compose.yml` | 本地/单主机 -- 多阶段构建、健康检查、自动重启 |
| `docker-compose.dev.yml` | 开发环境 -- 挂载源码实现热重载，前端映射到 8080 端口 |

## 前置条件

- Docker Engine >= 24.0
- Docker Compose >= 2.20

## 快速启动 -- 本地/单主机

```bash
# 1. 进入项目根目录
cd FulfillCrew

# 2. （可选）从模板创建环境变量文件
cp .env.example .env

# 3. 构建并以 detached 模式启动所有服务
docker compose up --build -d

# 4. 验证容器健康状态
docker compose ps

# 5. 打开前端
open http://localhost        # macOS
xdg-open http://localhost    # Linux
```

服务将可用：

| 服务 | URL | 说明 |
|------|-----|------|
| 前端 | http://localhost | Nginx 提供的 React SPA |
| 后端 API | http://localhost:8000 | FastAPI 应用 |
| API 文档 | http://localhost:8000/docs | Swagger UI（自动生成） |
| OpenAPI | http://localhost:8000/openapi.json | OpenAPI 3.0 模式 |

### 停止生产栈

```bash
# 优雅停止（保留卷）
docker compose down

# 完全清理 -- 移除容器、网络和构建的镜像
docker compose down --volumes --rmi all
```

## 快速启动 -- 开发环境

开发版 Compose 文件将后端源码以只读卷挂载，并启用 Uvicorn 热重载。前端映射到 8080 端口，避免与本地 Nginx 冲突。

```bash
docker compose -f docker-compose.dev.yml up --build -d
```

| 服务 | URL | 说明 |
|------|-----|------|
| 前端 | http://localhost:8080 | Nginx 提供构建后的 SPA |
| 后端 | http://localhost:8000 | 启用热重载（`--reload`） |

查看后端日志并观察热重载反馈：

```bash
docker logs -f fulfillcrew-backend-dev
```

## 架构详情

### 后端 Dockerfile

- **构建阶段**（`python:3.12-slim`）
  - 安装构建依赖（`gcc`）
  - 将 Python 依赖安装到 `/root/.local`
- **运行阶段**（`python:3.12-slim`）
  - 从构建阶段复制 Python 包
  - 复制 `backend/`、`ml_models/` 和清洗后的商品数据
  - 设置 `PYTHONPATH=/app`、`PYTHONDONTWRITEBYTECODE=1`、`PYTHONUNBUFFERED=1`
  - 暴露端口 8000
  - 声明 Docker `HEALTHCHECK` 在 `/health`
  - 运行 `uvicorn backend.main:app --host 0.0.0.0 --port 8000`

### 前端 Dockerfile

- **构建阶段**（`node:20-alpine`）
  - 运行 `npm ci` 确保可复现安装
  - 设置 `VITE_API_BASE=/api`，使构建后的 SPA 使用相对 API 路径
  - 运行 `npm run build` 生成 `dist/`
- **运行阶段**（`nginx:alpine`）
  - 将 `dist/` 复制到 Nginx 文档根目录
  - 将 `nginx.conf` 复制到 `/etc/nginx/conf.d/default.conf`
  - 为静态资源启用 gzip 压缩
  - 声明 Docker `HEALTHCHECK` 在 `/`
  - 暴露端口 80

### Nginx 配置（`frontend/nginx.conf`）

- 通过 `try_files` 回退提供 React SPA，支持客户端路由
- 代理 `/api/` -> `http://backend:8000/`（去掉 `/api` 前缀）
- 直接代理 `/health`、`/docs`、`/openapi.json` -> 后端
- 对静态资源应用 gzip 压缩和 1 年缓存头

### CORS 配置

后端从环境变量 `CORS_ORIGINS`（逗号分隔）读取允许来源。如未设置，则回退到覆盖常见本地开发 URL 的默认值：

```
http://localhost:5173   # Vite 开发服务器
http://127.0.0.1:5173   # Vite 开发服务器（IP）
http://localhost        # Nginx（生产）
http://127.0.0.1        # Nginx（IP）
http://localhost:8080   # Nginx（开发）
```

生产部署时，将 `CORS_ORIGINS` 设置为部署后的前端域名：

```bash
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

## 环境变量

复制 `.env.example` 为 `.env` 并调整数值：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `BACKEND_LOG_LEVEL` | FastAPI / Uvicorn 日志级别 | `info` |
| `BACKEND_PORT` | 后端容器内部端口 | `8000` |
| `FRONTEND_PORT` | 映射到 Nginx 的主机端口 | `80` |
| `API_BASE_URL` | 前端开发 API 基础 URL（本地非 Docker） | `http://127.0.0.1:8000` |
| `CORS_ORIGINS` | 逗号分隔的允许来源 | 见 `.env.example` |

## 手动开发（不借助 Docker）

如果你倾向于直接在主机上运行服务：

### 后端

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

Vite 开发服务器会自动将 `/api` 和 `/health` 请求代理到 `http://127.0.0.1:8000`。打开 http://localhost:5173 即可。

### 数据清洗

```bash
node data_cleaning/data_processing.js \
  data_cleaning/raw_products/products.json \
  data_cleaning/cleaned_products/products.json
```

## 共享部署检查清单

- [x] 提供 `.env.example` 作为本地配置模板
- [x] 通过 Docker Compose 运行 PostgreSQL 与 Redis
- [x] 通过 SQLAlchemy Repository 持久化订单与商品
- [x] CI 执行测试、前端构建、依赖审计、数据清洗校验与镜像构建
- [x] 输出结构化日志与 Prometheus 指标
- [ ] 添加 TLS 终止（Let's Encrypt、Cloudflare 或云负载均衡器）
- [ ] 为共享域名配置 `CORS_ORIGINS`
- [ ] 添加版本化数据库迁移（Alembic 或类似工具）
- [ ] 添加经过认证的镜像发布与部署流水线
- [ ] 接入日志聚合后端
- [ ] 在订单创建端点添加速率限制
- [ ] 将指标接入 Prometheus + Grafana 或云原生监控
- [ ] 为持久数据卷设置自动备份

## Docker 健康检查

四个服务均声明了 Docker 健康检查：

| 容器 | 检查间隔 | 命令 |
|------|---------|------|
| `fulfillcrew-postgres` | 10s | `pg_isready -U postgres` |
| `fulfillcrew-redis` | 10s | `redis-cli ping` |
| `fulfillcrew-backend` | 30s | `urllib.request.urlopen('http://localhost:8000/health')` |
| `fulfillcrew-frontend` | 30s | `wget --spider http://localhost/` |

查看健康状态：

```bash
docker compose ps
docker inspect --format='{{.State.Health.Status}}' fulfillcrew-backend
docker inspect --format='{{.State.Health.Status}}' fulfillcrew-frontend
```

## 故障排查

### 前端无法访问后端

- 检查两个容器是否在同一 Docker 网络：`docker network inspect fulfillcrew-network`
- 验证后端是否健康：`docker compose ps`
- 查看后端日志：`docker logs fulfillcrew-backend`
- 确保 `CORS_ORIGINS` 包含你的前端来源

### 端口 80 已被占用

- 在 `docker-compose.yml` 中更改主机端口映射：`ports: ["8080:80"]`
- 或使用默认映射到 8080 端口的开发版 Compose 文件

### 开发模式下热重载不生效

- 确保 `docker-compose.dev.yml` 中的卷指向正确路径
- 检查 `backend/main.py` 是否正确挂载：`docker exec fulfillcrew-backend-dev ls -la /app/backend`

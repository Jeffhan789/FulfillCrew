# FulfillCrew ADR-009：采用 Docker Compose 多服务容器化部署

## 状态
Accepted — v2.0 已实施（v1.0 已使用 Docker）

## 背景
项目需要展示"云计算"能力，要求：
- 一键启动完整系统（前端 + 后端 + 数据库 + 缓存）
- 开发环境支持热重载
- 生产环境支持健康检查、自动重启
- 面试中能解释容器化、网络、反向代理等概念

## 决策
采用 **Docker Compose** 编排多服务容器，包含：
- PostgreSQL 15（持久化）
- Redis 7（缓存/事件总线）
- FastAPI 后端（Uvicorn）
- Nginx 前端（React SPA + 反向代理）

提供两个 Compose 文件：`docker-compose.yml`（生产）和 `docker-compose.dev.yml`（开发）。

## 考虑方案

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| **Docker Compose** | 简单；学习曲线低；适合开发和小型部署；面试标准答案 | 单主机；无自动扩缩容；不是生产编排工具 | ✅ 选中（课程项目） |
| Kubernetes | 云原生标准；自动扩缩容；自愈 | 学习曲线极陡；需要 K8s 集群；对学生过重 | ❌ 过重 |
| Docker Swarm | 原生 Docker 编排；比 K8s 简单 | 生态衰退；被 Compose 和 K8s 挤压 | ❌ 生态衰退 |
| 裸机部署 | 无容器开销；直接控制 | 环境不一致；依赖冲突；无法一键复现 | ❌ 不满足云计算要求 |
| 云厂商 PaaS | 托管；自动运维 | 锁定厂商；面试中无法展示底层理解 | ❌ 无法展示技能 |

## 技术细节

### 生产编排 (`docker-compose.yml`)
```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: fulfillcrew-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: fulfillcrew
    ports: ["5432:5432"]
    volumes: [postgres-data:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: fulfillcrew-redis
    ports: ["6379:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  backend:
    build: {context: ., dockerfile: Dockerfile}
    container_name: fulfillcrew-backend
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/fulfillcrew
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres: {condition: service_healthy}
      redis: {condition: service_healthy}
    healthcheck:
      test: ["CMD", "python", "-c", "urllib.request.urlopen('http://localhost:8000/health')"]
    restart: unless-stopped

  frontend:
    build: {context: ./frontend, dockerfile: Dockerfile}
    container_name: fulfillcrew-frontend
    ports: ["80:80"]
    depends_on:
      backend: {condition: service_healthy}
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost/"]
    restart: unless-stopped

volumes: postgres-data:
networks: fulfillcrew-network: {driver: bridge}
```

### 为什么用 `depends_on` + `condition: service_healthy`

默认的 `depends_on` 只等待容器启动，不等待服务就绪。如果后端在 PostgreSQL 还没准备好时就启动，会导致连接失败。

```yaml
# 错误：只等待容器启动
depends_on: [postgres]

# 正确：等待 PostgreSQL 健康检查通过
depends_on:
  postgres:
    condition: service_healthy
```

### 为什么用 Bridge 网络
```yaml
networks:
  fulfillcrew-network:
    driver: bridge
```

- **bridge**：Docker 默认网络驱动，容器间通过 DNS 名通信（如 `backend:8000`、`postgres:5432`）
- **host**：容器共享宿主机网络，简单但端口冲突
- **overlay**：跨主机网络，用于 Swarm/K8s

对于单机 Compose，bridge 是最自然的选择。

### 后端 Dockerfile 多阶段构建
```dockerfile
# backend/Dockerfile
# 阶段 1：构建依赖
FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y gcc
COPY backend/requirements.txt .
RUN pip install --user -r requirements.txt

# 阶段 2：运行环境
FROM python:3.12-slim
COPY --from=builder /root/.local /root/.local
COPY backend/ /app/backend/
COPY ml_models/ /app/ml_models/
ENV PYTHONPATH=/app PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 多阶段构建的优势
1. **减小镜像体积**：构建工具（gcc）不在最终镜像中
2. **安全性**：编译工具不暴露在运行时环境
3. **缓存优化**：requirements.txt 不变时，依赖层直接命中缓存

### 前端 Dockerfile 多阶段构建
```dockerfile
# frontend/Dockerfile
# 阶段 1：构建 React 应用
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json .
RUN npm ci
ENV VITE_API_BASE=/api
COPY . .
RUN npm run build

# 阶段 2：Nginx 服务静态文件
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK CMD wget --spider http://localhost/
```

### 开发编排 (`docker-compose.dev.yml`)
```yaml
backend:
  volumes:
    - ./backend:/app/backend:ro      # 只读挂载，热重载
    - ./ml_models:/app/ml_models:ro
    - ./data_cleaning/cleaned_products:/app/data_cleaning/cleaned_products:ro
  command: uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

开发环境的关键差异：
- 挂载源码卷，代码修改无需重建镜像
- `--reload` 启用 Uvicorn 热重载
- 前端映射到 8080 端口避免与本地 Nginx 冲突

## 权衡与风险

| 风险 | 缓解措施 |
|------|----------|
| Docker Compose 不适合生产级多主机部署 | 面试中明确说明"这是课程项目的容器化展示，生产环境需 K8s 或云托管" |
| 密码硬编码在 Compose 文件中 | 开发环境可接受；生产环境应使用 Docker Secrets 或环境变量注入 |
| 卷数据在容器删除时可能丢失 | `postgres-data` 使用命名卷，数据持久化到宿主机 |
| 前端 `try_files` 配置不当导致 404 | 已配置 `try_files $uri $uri/ /index.html` 支持 React Router |

## 面试要点

### Q1: Docker 和 Docker Compose 有什么区别？
> "Docker 是容器运行时，管理单个容器。Docker Compose 是编排工具，用一个 YAML 文件定义多个服务、网络、卷，一键启动整个系统。比如我们的项目有 4 个服务（frontend, backend, postgres, redis），用 `docker compose up` 可以一次性启动，并自动配置网络连接。"

### Q2: 多阶段构建（Multi-stage）的好处是什么？
> "多阶段构建将编译环境和运行环境分离。比如后端需要 gcc 编译某些 Python 包，但运行时不需 gcc。通过多阶段构建，最终镜像只有运行所需的内容，体积更小、攻击面更小。我们的后端镜像从约 500MB 缩减到约 200MB。"

### Q3: `depends_on` 的 `condition: service_healthy` 是做什么的？
> "默认的 `depends_on` 只等待容器进程启动，但此时服务可能还没准备好（比如 PostgreSQL 正在初始化）。`condition: service_healthy` 会等待容器的 HEALTHCHECK 通过，确保依赖真正就绪。在我们的编排中，backend 会等待 postgres 和 redis 都健康后才启动。"

### Q4: 为什么用 Nginx 而不是直接暴露前端？
> "Nginx 有三个作用：1) 提供静态文件服务（React 构建产物）；2) 反向代理 API 请求到后端容器；3) 启用 gzip 压缩和缓存头。如果没有 Nginx，前端需要知道后端的具体地址，且无法处理客户端路由（SPA 刷新页面会 404）。"

### Q5: 开发环境为什么用只读挂载（:ro）？
> "`:ro` 表示只读（read-only），防止容器内意外修改源码。同时 Uvicorn 的 `--reload` 会监控文件变化，宿主机修改后容器内自动感知。这样既保证开发效率，又避免容器内外的文件不一致。"

### Q6: 如果要做 CI/CD，流水线怎么设计？
> "可以设计一个 GitHub Actions 流水线：
1. `test` 阶段：运行 pytest 和 Node.js 测试
2. `build` 阶段：构建前后端 Docker 镜像，推送到 Docker Hub
3. `deploy` 阶段：在目标服务器上 `docker compose pull && docker compose up -d`
面试中展示对完整 DevOps 流程的理解。"

## 相关文件
- `docker-compose.yml` — 生产编排
- `docker-compose.dev.yml` — 开发编排
- `Dockerfile` — 后端多阶段构建
- `frontend/Dockerfile` — 前端多阶段构建
- `frontend/nginx.conf` — Nginx 反向代理配置
- `.env.example` — 环境变量模板

## 参考
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Docker 多阶段构建](https://docs.docker.com/build/building/multi-stage/)
- [Docker Healthcheck](https://docs.docker.com/reference/dockerfile/#healthcheck)
- [Nginx 反向代理配置](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)

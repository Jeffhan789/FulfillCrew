# 07 Docker 与部署 —— 容器化、编排、反向代理

---

## 1. Docker 多阶段构建

### 1.1 后端 Dockerfile

```dockerfile
# 阶段 1: 构建环境
FROM python:3.12-slim AS builder
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 阶段 2: 运行环境
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY backend/ ./backend/
COPY ml_models/ ./ml_models/
COPY data_cleaning/cleaned_products/ ./data_cleaning/cleaned_products/
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**多阶段构建的优势**：
- **减小镜像体积**：builder 阶段的编译工具（如 gcc）不进入最终镜像
- **提升安全性**：最终镜像只含运行所需文件，攻击面更小
- **加速构建**：阶段缓存，未变更的层不用重新构建

### 1.2 前端 Dockerfile

```dockerfile
# 阶段 1: 构建
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# 阶段 2: 运行（Nginx）
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

**关键点**：
- `npm ci` 比 `npm install` 更快（直接读取 package-lock.json，不解析依赖树）
- Vite 构建产物在 `dist/` 目录，是纯静态文件
- Nginx 直接服务静态文件，无需 Node.js 运行时

---

## 2. Nginx 反向代理

### 2.1 nginx.conf

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # 前端静态资源
    location / {
        try_files $uri $uri/ /index.html;  # SPA 路由回退
    }

    # API 代理到后端
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket 代理
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 健康检查、文档代理
    location /health { proxy_pass http://backend:8000; }
    location /docs { proxy_pass http://backend:8000; }
    location /openapi.json { proxy_pass http://backend:8000; }
}
```

### 2.2 关键配置解析

| 配置 | 作用 |
|------|------|
| `try_files $uri $uri/ /index.html` | SPA 路由：用户刷新 `/orders/123` 时，Nginx 返回 `index.html`，React Router 接管客户端路由 |
| `proxy_set_header Upgrade $http_upgrade` | WebSocket 协议升级：HTTP → WebSocket 的握手需要这个头 |
| `proxy_http_version 1.1` | HTTP/1.1 支持 keep-alive 和 Upgrade 头 |

### 2.3 为什么需要反向代理？

```text
无反向代理：
  Browser → FastAPI:8000 (API)
  Browser → Vite:5173 (前端开发) / Nginx:80 (前端生产)
  问题：跨域、端口分散、无法统一管理 SSL

有反向代理：
  Browser → Nginx:80
    ├── /api/* → FastAPI:8000
    ├── /ws/* → FastAPI:8000 (WebSocket)
    ├── /health → FastAPI:8000
    └── / → 静态文件
  优势：统一入口、CORS 由 Nginx 处理、SSL 在 Nginx 终止
```

**架构复盘表达**："Nginx 作为反向代理统一了前端入口，所有请求走 80 端口。API 和 WebSocket 通过 `proxy_pass` 转发到后端容器。生产环境中 SSL 证书也配置在 Nginx 层（`listen 443 ssl`），后端保持纯 HTTP，简化部署。"

---

## 3. Docker Compose 编排

### 3.1 生产配置

```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: fulfillcrew-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: fulfillcrew
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - fulfillcrew-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: fulfillcrew-redis
    ports:
      - "6379:6379"
    networks:
      - fulfillcrew-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: fulfillcrew-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/fulfillcrew
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - fulfillcrew-network
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: fulfillcrew-frontend
    ports:
      - "80:80"
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - fulfillcrew-network
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/"]

volumes:
  postgres-data:

networks:
  fulfillcrew-network:
    driver: bridge
```

### 3.2 配置要点

| 配置 | 含义 |
|------|------|
| `condition: service_healthy` | 等依赖服务健康后才启动，避免启动时依赖未就绪报错 |
| `restart: unless-stopped` | 容器崩溃后自动重启，除非手动停止 |
| `volumes: postgres-data` | 命名卷持久化数据库数据，容器删除后数据保留 |
| `driver: bridge` | 默认网络驱动，容器间通过 DNS 名称通信（如 `postgres` 解析到数据库容器 IP） |

### 3.3 开发环境差异

`docker-compose.dev.yml` 与生产版的主要区别：
- 挂载源代码卷（`./backend:/app/backend:ro`），实现热重载
- 前端端口映射到 8080 而非 80
- 可能不启动 Nginx，直接用 Vite 开发服务器

---

## 4. 环境变量管理

### 4.1 .env.example

```
BACKEND_LOG_LEVEL=info
BACKEND_PORT=8000
FRONTEND_PORT=80
API_BASE_URL=http://127.0.0.1:8000
CORS_ORIGINS=http://localhost:5173,http://localhost:8080,http://localhost
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fulfillcrew
REDIS_URL=redis://localhost:6379/0
```

### 4.2 12-Factor App 配置原则

本项目遵循 [12-Factor App](https://12factor.net/config) 的配置原则：

1. **配置与代码分离**：敏感信息（密码）不提交到 Git
2. **环境变量优先**：`os.getenv("VAR", "default")` 模式
3. **无分组环境**：没有 `production.py` / `development.py`，只有环境变量差异

---

## 5. 扩展：CI/CD 流水线

虽然本项目目前未实现完整 CI/CD，但架构复盘中应能描述：

```yaml
# .github/workflows/ci.yml 概念设计
name: CI/CD
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r backend/requirements.txt
      - run: pytest tests/ -v

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t fulfillcrew-backend:latest .
      - run: docker build -t fulfillcrew-frontend:latest ./frontend
      # 推送到 Docker Hub / GHCR

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: ssh user@server "docker compose pull && docker compose up -d"
```

---

## 6. 架构复盘高频题

**Q: Docker 镜像和容器的区别？**

> A: 镜像是只读模板（类似类），包含应用代码、运行时、库等层级。容器是镜像的运行实例（类似对象），有独立的进程空间和可写层。同一镜像可启动多个容器。

**Q: 为什么用 Alpine 镜像？**

> A: Alpine Linux 基于 musl libc 和 busybox，基础镜像仅 ~5MB，相比 Ubuntu (~80MB) 大幅减小攻击面和传输时间。缺点是某些 Python 包（如 pandas）需要编译，可能缺少工具链，需额外安装 `build-base`。

**Q: `depends_on` 能保证服务启动顺序吗？**

> A: 默认只能保证启动顺序，不能保证服务就绪。比如 PostgreSQL 容器启动了，但数据库还在初始化。Docker Compose v2.1+ 支持 `condition: service_healthy`，配合 healthcheck 才能确保服务真正可用后再启动依赖。

**Q: 容器内如何访问另一个容器？**

> A: 同一 Docker 网络的容器通过服务名 DNS 解析。如 backend 容器内 `postgres` 解析为数据库容器 IP，`redis:6379` 直接连接 Redis。这是 Docker 内置的 DNS 服务实现的。

**Q: 为什么 WebSocket 需要 `proxy_set_header Upgrade`？**

> A: WebSocket 握手是 HTTP Upgrade 请求：客户端发送 `Upgrade: websocket` 和 `Connection: Upgrade`，服务器回复 101 Switching Protocols。Nginx 作为反向代理必须透传这些头，否则后端收不到 Upgrade 请求，无法建立 WebSocket 连接。

**Q: 生产环境数据库密码怎么管理？**

> A: 绝对不要写在代码或 Docker Compose 中。正确做法：
> 1. Docker Secrets（Docker Swarm/Kubernetes）
> 2. 环境变量注入（CI/CD 或 orchestrator 注入）
> 3. 云厂商 Secrets Manager（AWS Secrets Manager、Azure Key Vault）
> 4. 运行时挂载（如 Kubernetes Secret 挂载为文件）

# 常见问题排查指南

> **预计时间**：按需（每个问题 5-30 分钟）  
> **前置知识**：已完成 [00_quickstart.md](./00_quickstart.md)  
> **目标**：独立诊断和解决常见问题

---

## 目录

- [Docker 启动失败](#一docker-启动失败)
- [数据库连接问题](#二数据库连接问题)
- [模型加载失败](#三模型加载失败)
- [WebSocket 连接不上](#四websocket-连接不上)
- [前端构建失败](#五前端构建失败)
- [其他问题](#六其他问题)
- [求助渠道](#七求助渠道)

---

## 一、Docker 启动失败

### 症状

```bash
docker compose up --build
# 报错：Error response from daemon:... 
# 或：某个容器反复重启（Restarting）
```

### 诊断步骤

#### 步骤 1：检查 Docker 是否运行

```bash
docker info
```

**预期输出**：`Server Version: 24.x.x`
**如果报错**：`Cannot connect to the Docker daemon` → 启动 Docker Desktop

#### 步骤 2：查看各容器日志

```bash
# 查看所有服务日志
docker compose logs

# 只看后端日志（最可能出问题）
docker compose logs -f backend

# 只看最后 50 行
docker compose logs --tail=50 backend
```

#### 步骤 3：逐个检查服务状态

```bash
# 查看容器状态
docker compose ps

# 预期：所有容器都是 Up (healthy)
# 如果某个是 Restarting 或 Exit(1)，重点排查该服务
```

### 常见错误及解决方案

#### 错误 1：端口被占用

```
Error: Bind for 0.0.0.0:5432 failed: port is already allocated
```

**原因**：PostgreSQL 的 5432 端口被其他程序占用

**解决方案**：

```bash
# 找到占用 5432 的进程
lsof -i :5432
# 或 macOS
sudo lsof -i :5432

# 解决方案 A：停止占用进程
kill -9 <PID>

# 解决方案 B：修改 docker-compose.yml 中的端口映射
# 将 "5432:5432" 改为 "5433:5432"
```

#### 错误 2：镜像拉取失败 / 网络超时

```
Error: failed to solve: rpc error: code = Unknown desc = failed to pull image
```

**原因**：网络连接 Docker Hub 超时（国内常见）

**解决方案**：

```bash
# 解决方案 A：配置 Docker 镜像加速（推荐）
# 在 Docker Desktop → Settings → Docker Engine 中添加：
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}

# 解决方案 B：手动拉取镜像
docker pull postgres:15-alpine
docker pull redis:7-alpine
# 然后再运行 docker compose up --build
```

#### 错误 3：后端健康检查失败（反复重启）

```
fulfillcrew-backend  | Restarting (1) 5 seconds ago
```

**诊断**：

```bash
# 查看后端详细日志
docker compose logs --tail=100 backend

# 常见原因：
# 1. 数据库还没准备好，后端就尝试连接
# 2. Python 依赖安装失败
# 3. 代码语法错误
```

**解决方案**：

```bash
# 步骤 1：确保 postgres 和 redis 完全启动
docker compose up postgres redis -d

# 步骤 2：等待 10 秒，确认 postgres 健康
docker compose ps
# 应该看到 postgres 状态是 Up (healthy)

# 步骤 3：单独启动后端
docker compose up backend

# 如果仍然失败，检查 Python 依赖
# 进入后端容器内部排查
docker compose exec backend bash
# 在容器内运行：python -c "import backend.main"
# 看是否有 ImportError
```

#### 错误 4：构建缓存导致的问题

```bash
# 清理 Docker 构建缓存
docker compose down -v
docker system prune -f
# 然后重新构建
docker compose up --build
```

⚠️ **警告**：`docker system prune` 会删除所有未使用的容器、网络和镜像。确认没有重要数据后再执行。

---

## 二、数据库连接问题

### 症状

- 前端能加载，但商品列表为空
- Swagger UI 中调用 `/products` 返回 500
- 后端日志中出现 `sqlalchemy.exc.OperationalError` 或 `Connection refused`

### 诊断步骤

#### 步骤 1：检查数据库容器是否运行

```bash
docker compose ps
# 检查 postgres 状态是否为 Up (healthy)
```

#### 步骤 2：检查数据库连接字符串

```bash
# 查看后端环境变量
docker compose exec backend env | grep DATABASE

# 预期：DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/fulfillcrew
```

#### 步骤 3：从后端容器内部测试连接

```bash
docker compose exec backend bash
# 在容器内部：
python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
async def test():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@postgres:5432/fulfillcrew')
    async with engine.connect() as conn:
        result = await conn.execute('SELECT 1')
        print(result.scalar())
asyncio.run(test())
"
```

**预期输出**：`1`  
**如果报错**：看具体错误信息

### 常见错误及解决方案

#### 错误 1：数据库表未初始化

```
sqlalchemy.exc.ProgrammingError: relation "products" does not exist
```

**原因**：数据库已启动，但表结构没有创建

**解决方案**：

```bash
# 检查后端是否成功执行了 init_db
docker compose logs backend | grep "database.initialized"

# 如果没有，手动重启后端
docker compose restart backend

# 或手动进入后端容器执行初始化
docker compose exec backend python -c "
import asyncio
from backend.database.engine import init_db
asyncio.run(init_db())
"
```

#### 错误 2：数据库连接池耗尽

```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached
```

**原因**：并发请求过多，连接池耗尽

**解决方案**：

```python
# backend/database/engine.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,        # 增加连接池大小
    max_overflow=20,     # 增加溢出连接数
    pool_recycle=3600,   # 连接回收时间
)
```

#### 错误 3：数据库数据丢失（重置后）

```bash
# 彻底重置数据库（删除卷，重新初始化）
docker compose down -v  # -v 删除数据卷
docker compose up --build

# 或只重新初始化表（保留数据）
docker compose exec backend python -c "
import asyncio
from backend.database.init_db import init_db
asyncio.run(init_db())
"
```

---

## 三、模型加载失败

### 症状

- 结账时后端返回 500
- 后端日志中出现 `ModuleNotFoundError: No module named 'torch'` 或 `xgboost`
- 欺诈检测或需求预测返回默认值

### 诊断步骤

#### 步骤 1：检查 Python 依赖

```bash
# 进入后端容器
docker compose exec backend bash

# 检查 PyTorch 是否安装
python -c "import torch; print(torch.__version__)"

# 检查 XGBoost
python -c "import xgboost; print(xgboost.__version__)"

# 检查 scikit-learn
python -c "import sklearn; print(sklearn.__version__)"
```

#### 步骤 2：检查模型文件是否存在

```bash
# 在 backend 容器内
ls -la /app/ml_models/
# 检查模型文件（.pkl, .pt, .json）是否存在
```

### 常见错误及解决方案

#### 错误 1：ML 依赖未安装

**原因**：`requirements.txt` 中可能缺少 ML 库，或者镜像构建时未安装

**解决方案**：

```bash
# 进入后端容器安装
docker compose exec backend pip install torch xgboost scikit-learn shap

# 或修改 requirements.txt，添加：
# torch>=2.0
# xgboost>=1.7
# scikit-learn>=1.3
# shap>=0.42
# 然后重新构建
docker compose up --build backend
```

#### 错误 2：模型文件路径错误

```python
# 检查模型加载代码中的路径
import os
model_path = os.path.join(os.path.dirname(__file__), "model.pkl")
print(f"Loading model from: {model_path}")
# 确认路径存在
```

#### 错误 3：模型版本不兼容（最常见）

```
xgboost.core.XGBoostError: Check failed: header == serialisation_header
```

**原因**：用 XGBoost 1.7 保存的模型，用 2.0 加载

**解决方案**：

```bash
# 确保训练和推理使用的库版本一致
pip install xgboost==1.7.6  # 与保存模型时的版本一致

# 或重新训练模型
python ml_models/fraud_detection/train.py
```

### Fallback 机制说明

系统设计了**防御性 fallback**，当 ML 模型不可用时：

| 模型 | 正常情况 | Fallback |
|------|----------|----------|
| 需求预测 MLP | PyTorch 推理返回预测值 | 返回基于历史均值的简单估计 |
| 欺诈检测 XGBoost | XGBoost 推理返回 risk_score | 返回基于规则的简单评分（如订单金额阈值） |
| 商品分类 TF-IDF+LR | sklearn 推理返回品类 | 返回基于关键词匹配的分类 |

**Fallback 代码位置**：各 Agent 的 `score()` / `predict()` / `classify()` 方法中的 `try/except` 块

```python
# backend/agents/fraud_detection_agent.py（示意）
def score(self, features):
    try:
        # 尝试使用 XGBoost 模型
        risk_score = self.model.predict(features)
        return risk_score, "approved" if risk_score < 0.65 else "review"
    except Exception:
        # Fallback：基于规则的简单评分
        if features["order_total"] > 1000:
            return 0.8, "review"
        return 0.3, "approved"
```

---

## 四、WebSocket 连接不上

### 症状

- 前端结账后，状态栏显示 `○ Offline` 而不是 `● Live`
- 订单状态不会实时更新，需要刷新页面才能看到结果
- 浏览器控制台出现 `WebSocket connection failed`

### 诊断步骤

#### 步骤 1：检查浏览器控制台

```
# 打开浏览器开发者工具（F12）→ Console
grep: WebSocket connection to 'ws://localhost/ws/orders/xxx' failed
```

#### 步骤 2：检查 WebSocket 端点是否可达

```bash
# 使用 curl 测试（WebSocket 需要特殊工具）
# 或直接在浏览器控制台：
# new WebSocket('ws://localhost/ws/orders/test')
```

#### 步骤 3：检查 Nginx 反向代理配置

```bash
# 查看 nginx 配置（在 frontend 容器内）
docker compose exec frontend cat /etc/nginx/nginx.conf
# 或查看项目中的 nginx 配置
```

### 常见错误及解决方案

#### 错误 1：Nginx 未正确代理 WebSocket

**原因**：Nginx 默认只代理 HTTP，需要额外配置 WebSocket 支持

**解决方案**：

```nginx
# nginx 配置中需要添加：
location /ws/ {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

#### 错误 2：后端 WebSocket 路由未注册

**检查**：`backend/main.py` 中是否包含：

```python
app.include_router(websocket_router.router)  # /ws/orders/{order_id}
```

#### 错误 3：前端连接地址错误

**检查**：`frontend/src/hooks/useOrderSocket.ts` 中的 WebSocket URL：

```typescript
// 开发环境
const wsUrl = `ws://localhost:8000/ws/orders/${orderId}`;

// 生产环境（通过 Nginx 代理）
const wsUrl = `ws://localhost/ws/orders/${orderId}`;
```

**问题**：如果前端通过 Nginx 访问（端口 80），但 WebSocket 直接连接后端（端口 8000），可能会因为 CORS 或防火墙问题失败。

**解决方案**：确保 WebSocket 也走 Nginx 代理，使用 `ws://localhost/ws/orders/${orderId}`

#### 错误 4：WebSocket 连接数限制

```bash
# 检查后端日志中是否有 "too many connections" 错误
docker compose logs backend | grep -i websocket
```

---

## 五、前端构建失败

### 症状

```bash
docker compose up --build frontend
# 报错：npm ERR! code ELIFECYCLE
# 或：npm ERR! build failed
```

### 诊断步骤

#### 步骤 1：单独构建前端

```bash
cd frontend
npm install
npm run build
```

#### 步骤 2：检查 Node.js 版本

```bash
node --version
# 预期：v18+（package.json 中 engines 字段要求）
```

#### 步骤 3：检查 TypeScript 错误

```bash
cd frontend
npx tsc --noEmit
# 看是否有类型错误
```

### 常见错误及解决方案

#### 错误 1：npm 依赖安装失败

```bash
# 清理缓存
rm -rf node_modules package-lock.json
npm install

# 或使用国内镜像加速
npm install --registry=https://registry.npmmirror.com
```

#### 错误 2：TypeScript 类型错误

```
Type error: Property 'xxx' does not exist on type 'yyy'
```

**解决方案**：

```bash
# 检查 tsconfig.json 配置
# 确保 @types/node 和 @types/react 已安装
npm install --save-dev @types/react @types/react-dom

# 如果是自定义类型缺失，添加 .d.ts 文件
```

#### 错误 3：Vite 构建错误

```bash
# 检查 vite.config.ts
# 确保代理配置正确
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': 'ws://localhost:8000',
    }
  }
})
```

#### 错误 4：Recharts 或其他第三方库报错

```bash
# 检查是否安装了对应的类型定义
npm install --save-dev @types/recharts
# 或确认 recharts 版本兼容
```

---

## 六、其他问题

### 问题 1：前端能访问但后端 404

**诊断**：

```bash
# 检查 Nginx 反向代理配置
docker compose exec frontend cat /etc/nginx/conf.d/default.conf

# 确保有以下配置：
location /api/ {
    proxy_pass http://backend:8000/;
}
location /docs {
    proxy_pass http://backend:8000/docs;
}
```

### 问题 2：CORS 错误

```
Access to fetch at 'http://localhost:8000/products' from origin 'http://localhost' has been blocked by CORS policy
```

**解决方案**：

```bash
# 检查 backend 的 CORS 配置
docker compose exec backend env | grep CORS

# 确保 CORS_ORIGINS 包含前端地址
# 在 .env 或 docker-compose.yml 中设置：
CORS_ORIGINS=http://localhost,http://localhost:80

# 或修改 backend/main.py 中的 default_origins
```

### 问题 3：系统时间不同步导致 JWT 或日志时间异常

**解决方案**：

```bash
# 同步 Docker 容器时间
docker compose exec backend date
# 如果与主机时间不一致，重启 Docker Desktop
```

### 问题 4：磁盘空间不足导致构建失败

```bash
# 检查 Docker 磁盘使用
docker system df

# 清理未使用的资源
docker system prune -a --volumes
# ⚠️ 这会删除所有未使用的容器、镜像、卷
```

---

## 七、求助渠道

如果按照上述步骤仍无法解决问题，请按以下方式求助：

### 1. 收集信息

在提问前，准备以下信息：

```bash
# 操作系统和版本
uname -a

# Docker 版本
docker --version
docker compose --version

# 容器状态
docker compose ps

# 后端日志（最后 100 行）
docker compose logs --tail=100 backend > backend_logs.txt

# 前端日志（如果前端失败）
docker compose logs --tail=50 frontend > frontend_logs.txt
```

### 2. 提问模板

```
【环境】
- OS: macOS 14.x / Ubuntu 22.04 / Windows 11
- Docker: 24.x.x
- 项目版本: commit hash 或最新 main

【问题描述】
简要描述遇到的问题和症状

【已尝试的解决方案】
1. 已尝试 xxx，结果...
2. 已尝试 yyy，结果...

【相关日志】
贴出关键错误日志（脱敏后）
```

### 3. 自查清单

在提问前，先确认以下基础项：

- [ ] Docker Desktop 已启动
- [ ] 网络连接正常（能访问 Docker Hub）
- [ ] 端口未被占用（5432, 6379, 8000, 80）
- [ ] 已尝试 `docker compose down -v` 后重新 `up --build`
- [ ] 已查看对应服务的日志
- [ ] 已检查 `.env` 或环境变量配置

---

## 常用命令速查表

| 命令 | 作用 |
|------|------|
| `docker compose up --build` | 构建并启动所有服务 |
| `docker compose up -d` | 后台启动 |
| `docker compose down` | 停止所有服务 |
| `docker compose down -v` | 停止并删除数据卷 |
| `docker compose logs -f backend` | 实时查看后端日志 |
| `docker compose ps` | 查看容器状态 |
| `docker compose exec backend bash` | 进入后端容器 |
| `docker compose restart backend` | 重启后端服务 |
| `docker system prune -f` | 清理未使用资源 |
| `lsof -i :5432` | 查看占用 5432 端口的进程 |

---

> 💡 **最后建议**：遇到问题时，**先看日志**。日志通常包含了最直接的错误信息。养成阅读日志的习惯，是独立排查问题的第一步。

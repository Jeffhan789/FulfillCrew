# FulfillCrew ADR-006：采用 React 18 + TypeScript + Vite + Recharts 前端技术栈

## 状态
Accepted — v2.0 已实施（v1.0 已使用 React + Vite）

## 背景
FulfillCrew 的前端需要展示：
- 商品浏览（搜索、排序、过滤）
- 购物篮管理
- 订单结果展示（包含 6 个 Dashboard 组件的可视化）
- 实时 WebSocket 订单状态更新
- 课程智能仪表盘（将三门课程映射到系统实现）

v1.0 使用 React 17 + JavaScript + Vite。v2.0 升级了 TypeScript 和 Recharts 可视化。

## 决策
采用 **React 18** + **TypeScript 5.7** + **Vite** + **Recharts** 作为前端技术栈，辅以 **Lucide React** 图标库。

## 考虑方案

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| **React 18 + TS + Vite** | 生态最成熟；Vite 构建极快；TypeScript 类型安全；面试认可度最高 | 需要学 JSX/Hook； bundle 体积比 Vue 稍大 | ✅ 选中 |
| Vue 3 + Vite | 学习曲线平缓；模板语法直观；性能优秀 | 面试中 React 更常见；学生项目通常用 React | ❌ 非最优选择（面试角度） |
| Svelte | 编译型；无虚拟 DOM；性能最好 | 生态较小；面试讨论度低；对学生不友好 | ❌ 生态不足 |
| Next.js | SSR/SSG；SEO 友好；全栈能力 | 对 SPA 项目过重；引入服务器端复杂度；课程项目不需要 SSR | ❌ 过重 |
| Angular | 企业级；TypeScript 原生；完整框架 | 学习曲线极陡；概念过多（RxJS、DI、Module）；对课程项目过重 | ❌ 过重 |
| 纯 Vanilla JS | 无依赖；完全控制 | 组件化困难；状态管理复杂；面试认可度低 | ❌ 无框架价值 |

## 技术细节

### 为什么 TypeScript 是 v2.0 的升级重点
```typescript
// frontend/src/main.tsx
interface OrderResponse {
  order_id: string;
  order_status: string;
  order_total: number;
  selected_warehouse: string | null;
  risk_score: number;
  fraud_status: string;
  predicted_demand_next_7_days: number;
  restock_recommendation: string;
  bids: WarehouseBid[];
  decision_log: { agent: string; message: string }[];
  course_trace: { agent: string; message: string }[];
  model_evaluations: ModelEvaluation[];
}
```

TypeScript 的价值：
1. **API 契约自动校验**：后端 Pydantic 模型和前端 TypeScript 接口可以 1:1 对应
2. **重构安全**：改名、改接口时编译器会报错，而不是运行时崩溃
3. **IDE 智能提示**：VS Code 中自动补全 API 字段，减少文档查阅
4. **面试加分**：TypeScript 是 2024 年前端标配，不用 TS 会被质疑"代码质量"

### 为什么用 Vite 而不是 Create React App
```javascript
// frontend/vite.config.ts
export default defineConfig({
  // Vite 基于 esbuild，冷启动 < 100ms
  // CRA 基于 webpack，冷启动 5-30s
});
```

| 特性 | Vite | Create React App |
|------|------|------------------|
| 冷启动 | ~100ms | 5-30s |
| HMR 更新 | 即时 | 2-5s |
| 构建工具 | esbuild + Rollup | webpack |
| 配置复杂度 | 极简 | 隐藏但复杂 |
| 未来维护 | 活跃（Vue 团队） | 官方已推荐迁移 |

### 6 个 Dashboard 组件
```
frontend/src/components/
├── WarehouseBidChart.tsx        — 柱状图展示仓库竞价对比
├── DemandPredictionChart.tsx    — 折线图/指标卡展示需求预测
├── RiskScoreGauge.tsx           — 仪表盘/进度条展示风险评分
├── OrderStatusTimeline.tsx      — 时间线展示智能体决策步骤
├── SystemHealthPanel.tsx        — 系统健康状态面板（调用 /health）
└── ModelEvaluationPanel.tsx     — ML 模型评估指标展示
```

### Recharts 选择理由
```typescript
// frontend/src/components/WarehouseBidChart.tsx
import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

<BarChart data={bids}>
  <CartesianGrid strokeDasharray="3 3" />
  <XAxis dataKey="warehouse_id" />
  <YAxis />
  <Tooltip />
  <Bar dataKey="bid" fill="#3b82f6" />
</BarChart>
```

- **声明式**：类似 React 的 JSX 语法，学习成本低
- **轻量**：比 D3.js 易用得多，不需要手动操作 SVG
- **响应式**：自动适配容器大小
- **面试友好**：Recharts 是 React 图表库的"默认选择"

### WebSocket 实时通信
```typescript
// frontend/src/hooks/useOrderSocket.ts
export function useOrderSocket(orderId: string | null) {
  const [status, setStatus] = useState<SocketMessage | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!orderId) return;
    const ws = new WebSocket(`${WS_BASE}/ws/orders/${orderId}`);
    ws.onopen = () => setConnected(true);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStatus(data);
    };
    return () => ws.close();
  }, [orderId]);

  return { status, connected };
}
```

这是一个自定义 Hook，封装了 WebSocket 连接逻辑：
- 只有 `orderId` 存在时才连接（避免无意义的连接）
- 组件卸载时自动关闭连接（cleanup）
- 返回 `connected` 状态用于 UI 指示器
- 返回 `status` 用于展示最新事件

### Nginx 部署配置
```nginx
# frontend/nginx.conf
server {
    listen 80;
    root /usr/share/nginx/html;
    
    # 1. 提供 React SPA 静态资源
    location / {
        try_files $uri $uri/ /index.html;  # 支持客户端路由
    }
    
    # 2. 反向代理 API 请求到后端
    location /api/ {
        proxy_pass http://backend:8000/;
    }
    
    # 3. 健康检查和文档代理
    location /health { proxy_pass http://backend:8000/health; }
    location /docs { proxy_pass http://backend:8000/docs; }
    
    # 4. gzip 压缩和缓存
    gzip on;
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## 权衡与风险

| 风险 | 缓解措施 |
|------|----------|
| 学生不熟悉 TypeScript 类型体操 | 项目中只使用基础类型和接口，不涉及泛型、条件类型等高级特性 |
| Recharts 定制能力不如 D3 | 当前需求是标准图表，不需要自定义 SVG；Recharts 足够 |
| 前端 bundle 体积 | Vite 的 tree-shaking 和 code-splitting 自动优化；React 18 体积可控 |
| 实时数据通过 WebSocket 但重连逻辑简单 | 当前是演示场景，不需要企业级重连；如需可用 `reconnecting-websocket` 库 |

## 面试要点

### Q1: 为什么用 React 而不是 Vue？
> "React 的生态系统更大，面试中出现频率更高。对于我们这个需要数据可视化的仪表盘项目，React + Recharts 的组合非常成熟。另外，TypeScript 和 React 的集成比 Vue 更自然（JSX 本身就是 TypeScript 友好的）。"

### Q2: Vite 和 webpack 有什么区别？
> "Vite 在开发时使用原生 ES Modules，不需要打包，冷启动几乎是即时的。webpack 需要分析整个依赖图才能启动。Vite 生产构建用 Rollup，tree-shaking 效果更好。对于这个项目，Vite 让开发体验提升了一个数量级。"

### Q3: WebSocket 连接是每订单一个还是全局一个？
> "每订单一个。当用户点击 checkout 后，创建订单并获取 order_id，然后建立 WebSocket 连接 `/ws/orders/{order_id}`。这样后端可以只推送与该订单相关的事件，前端也只需要监听一个频道。订单完成后或用户离开页面，连接自动关闭。"

### Q4: 你们的前端状态管理怎么设计的？
> "当前使用 React 内置的 `useState` 和 `useEffect`，没有引入 Redux 或 Zustand。原因是：
1. 状态相对简单（商品列表、购物篮、当前订单）
2. 不需要跨组件共享复杂状态
3. 面试中展示'用最少工具解决问题'的能力
如果未来状态变复杂，可以引入 Zustand（轻量）或 Redux Toolkit（规范）。"

### Q5: Nginx 的 `try_files` 是做什么的？
> "React 是单页应用（SPA），路由由客户端 JavaScript 处理（如 React Router）。当用户直接访问 `/orders/123` 时，服务器需要返回 `index.html`，让 React 接管路由。`try_files $uri $uri/ /index.html` 的意思是：先尝试找文件，找不到就返回 index.html。"

## 相关文件
- `frontend/src/main.tsx` — 主应用组件
- `frontend/src/hooks/useOrderSocket.ts` — WebSocket Hook
- `frontend/src/components/*.tsx` — 6 个 Dashboard 组件
- `frontend/vite.config.ts` — Vite 配置
- `frontend/nginx.conf` — Nginx 配置
- `frontend/Dockerfile` — 多阶段构建

## 参考
- [React 官方文档](https://react.dev/)
- [Vite 官方文档](https://vitejs.dev/)
- [TypeScript 手册](https://www.typescriptlang.org/docs/)
- [Recharts 文档](https://recharts.org/)
- [Lucide React](https://lucide.dev/guide/packages/lucide-react)

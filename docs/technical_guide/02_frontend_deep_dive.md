# 02 前端技术深入 —— React 18 + TypeScript + Vite + Recharts + WebSocket

---

## 1. 为什么选 React 18 + TypeScript？

### 1.1 React 18 的关键特性

React 18 引入了 **Concurrent Features**（并发特性），核心改进包括：

- **Automatic Batching**：多个 state 更新自动合并为一次重渲染
  ```tsx
  // React 18 之前：两次 setState 触发两次渲染
  // React 18：自动 batch，只渲染一次
  setCount(c => c + 1);
  setFlag(f => !f);
  ```
- **Suspense 改进**：支持数据获取场景（配合 `use` hook 或框架级数据流）
- **Transitions**：区分紧急更新（如输入）和非紧急更新（如搜索列表）

**在本项目中的体现**：`useOrderSocket`  hook 持续接收 WebSocket 消息更新状态，React 18 的自动 batch 确保高频消息不会触发不必要的重渲染。

### 1.2 TypeScript 的价值

```tsx
// 定义精确的类型边界，防止运行时错误
type OrderResponse = {
  order_id: string;
  order_status: string;
  selected_warehouse: string | null;  // null 是显式类型的一部分
  risk_score: number;
  fraud_status: string;
  predicted_demand_next_7_days: number;
  restock_recommendation: string;
  bids: WarehouseBid[];
  decision_log: { agent: string; message: string }[];
  course_trace: { agent: string; message: string }[];
  model_evaluations: ModelEvaluation[];
};
```

TypeScript 的**类型收窄**（Type Narrowing）在条件渲染中特别有用：
```tsx
{order ? (
  <section className="order-band">
    <span>Warehouse: {order.selected_warehouse || "none"}</span>
  </section>
) : null}
// TypeScript 知道 order 存在时 selected_warehouse 是 string | null
```

---

## 2. Vite 构建原理

### 2.1 为什么不用 Create React App？

| 维度 | CRA (webpack) | Vite (esbuild + Rollup) |
|------|--------------|------------------------|
| 冷启动 | 数秒到数十秒 | 毫秒级（< 300ms） |
| HMR | 全量更新，慢 | 模块级精确更新，即时 |
| 生产构建 | webpack 打包 | Rollup 优化打包，tree-shaking 更彻底 |
| 配置复杂度 | 需要 eject | 开箱即用，配置极简 |

### 2.2 Vite 的核心机制

```text
开发阶段：
  1. 浏览器请求 index.html
  2. Vite 拦截 <script type="module"> 请求
  3. 将源码通过 esbuild 转译（ESM → 浏览器可执行 JS）
  4. 按需加载：只有浏览器请求的模块才会被转译

生产阶段：
  1. Rollup 预构建所有依赖（bundling）
  2. Tree-shaking 移除未使用代码
  3. Code splitting 按路由/动态导入拆分 chunk
  4. 生成优化后的静态资源
```

**面试考点**：Vite 的「按需编译」与 webpack 的「全量打包」的根本区别。webpack 在开发阶段也需要构建完整的依赖图，而 Vite 利用浏览器原生 ESM 支持，将"构建"延迟到请求发生时。

---

## 3. React Hooks 深入：useOrderSocket

```ts
import { useEffect, useState } from "react";

interface SocketMessage {
  event: string;
  order_id: string;
  data: Record<string, any>;
}

const WS_BASE = import.meta.env.VITE_WS_BASE_URL || "ws://127.0.0.1:8000";

export function useOrderSocket(orderId: string | null) {
  const [status, setStatus] = useState<SocketMessage | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!orderId) return;  // 防御性：无 orderId 时不建立连接

    const ws = new WebSocket(`${WS_BASE}/ws/orders/${orderId}`);

    ws.onopen = () => setConnected(true);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStatus(data);     // 触发 React 重渲染，更新订单状态面板
    };
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    return () => ws.close();  // 清理函数：组件卸载或 orderId 变化时关闭连接
  }, [orderId]);  // 依赖数组：只有 orderId 变化时才重建连接

  return { status, connected };
}
```

### 3.1 设计要点

1. **条件连接**：`if (!orderId) return` 避免无效连接
2. **依赖数组精确**：`[orderId]` 确保每个订单有独立 WebSocket，切换订单时旧连接关闭、新连接建立
3. **清理函数**：`return () => ws.close()` 防止内存泄漏，这是 React 18 StrictMode 双重挂载/卸载的安全保障
4. **状态外显**：`connected` 状态用于 UI 显示 "● Live / ○ Offline"

### 3.2 面试追问：如果每秒接收 100 条消息，会卡顿吗？

**答案**：React 18 的 Automatic Batching 会合并同一事件循环中的多次 `setStatus`，但如果消息频率极高，仍需要：
- 使用 `useRef` 保存最新状态，配合 `requestAnimationFrame` 节流渲染
- 或在前端做消息队列，每 100ms 批量更新一次 UI

---

## 4. Recharts 数据可视化

### 4.1 WarehouseBidChart：双轴组合图

```tsx
<ComposedChart data={data}>
  <Bar yAxisId="left" dataKey="bid" fill="#256d57" />      {/* 柱状图：竞价数值 */}
  <Line yAxisId="right" dataKey="suitability_score" />     {/* 折线图：适配度 */}
</ComposedChart>
```

**技术点**：
- **双 Y 轴**：`yAxisId="left"` / `yAxisId="right"`，解决量纲不同（bid 可能 10-50，suitability 是 0-1）
- **CustomTooltip**：自定义悬浮提示，避免默认 tooltip 信息过载
- **ResponsiveContainer**：`width="100%" height={200}`，CSS 容器查询式自适应

### 4.2 DemandPredictionChart：带参考线的柱状图

```tsx
<BarChart data={data}>
  <ReferenceLine x="Today" stroke="#256d57" strokeDasharray="4 4" />
  <Bar dataKey="demand">
    {data.map((entry, index) => (
      <Cell key={index} fill={entry.isCurrent ? "#256d57" : "#b7d9c2"} />
    ))}
  </Bar>
</BarChart>
```

**技术点**：
- `ReferenceLine`：标记当前时间点，提供时间上下文
- 条件颜色：`Cell` 组件动态填充，当前日期用深色突出
- 数据合成：`buildDemandData()` 将单一预测值扩展为 7 天历史/预测序列，让图表有"走势"而非一个孤点

---

## 5. 组件架构：单一职责

| 组件 | 职责 | 输入 props | 面试亮点 |
|------|------|-----------|---------|
| `App` | 数据获取、状态管理、布局编排 | 无 | 使用 `useMemo` 优化商品列表过滤排序 |
| `WarehouseBidChart` | 仓库竞价可视化 | `bids: WarehouseBid[]` | 双轴 ComposedChart，自定义 Tooltip |
| `DemandPredictionChart` | 需求预测可视化 | `predictedDemand, recommendation` | 数据合成让单点数据变成趋势图 |
| `RiskScoreGauge` | 风险分数仪表盘 | `riskScore, fraudStatus` | 阈值颜色映射（绿/黄/红） |
| `OrderStatusTimeline` | 决策时间线 | `logs: AgentDecision[]` | 按步骤渲染，可扩展为步骤条 |
| `SystemHealthPanel` | 系统健康检查 | 无 | 定时轮询 `/health`，展示多维度状态 |
| `ModelEvaluationPanel` | 模型评估面板 | `evaluations: ModelEvaluation[]` | 表格/卡片混合展示，信息密度高 |

---

## 6. 性能优化点

### 6.1 useMemo 缓存过滤结果

```tsx
const visibleProducts = useMemo(() => {
  return products
    .filter((product) => product.name.toLowerCase().includes(query.toLowerCase()))
    .filter((product) => !inStockOnly || product.quantity > 0)
    .sort((a, b) => { ... });
}, [products, query, sortBy, inStockOnly]);
```

**为什么需要**：搜索、排序、过滤是 O(n log n) 操作，如果每次渲染都执行，在商品列表增大时会卡顿。`useMemo` 确保依赖未变化时返回缓存结果。

### 6.2 图片懒加载（可扩展）

当前代码中 `img` 直接加载 `?auto=format&fit=crop&w=600&q=80`，生产环境中应替换为：
```tsx
<img loading="lazy" src={...} alt={...} />
```

或使用 `IntersectionObserver` 实现真正的懒加载。

---

## 7. 面试高频题

**Q: 为什么用 React 的函数组件而不是 Class 组件？**

> A: 函数组件 + Hooks 是 React 官方推荐方向。Hooks 让状态逻辑复用更简单（如 `useOrderSocket` 可在任何组件复用），且没有 `this` 绑定问题。React 18 的并发特性也是为函数组件设计的。

**Q: Vite 的 HMR 为什么比 webpack 快？**

> A: Vite 开发阶段不做打包，而是让浏览器直接请求 ESM 模块。当文件修改时，Vite 只需重新转译该模块并通过 WebSocket 通知浏览器更新，而 webpack 需要重新构建整个依赖图。

**Q: useEffect 的依赖数组为空 `[]` 和有依赖 `[orderId]` 的区别？**

> A: `[]` 只在组件挂载时执行一次，适合初始化数据获取。`[orderId]` 在 orderId 变化时重新执行，同时清理函数会先关闭旧连接，这是 WebSocket 连接管理的正确模式。

**Q: 如果后端推送 10MB 的 JSON，前端会卡吗？怎么处理？**

> A: 会卡。处理方式：1) 后端做分页/增量更新；2) 前端用 Web Worker 解析 JSON；3) 虚拟滚动（Virtual List）只渲染可视区域。本项目目前订单数据量小，暂未引入这些优化，但面试中应提及扩展方案。

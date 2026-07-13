# FulfillCrew ADR-008：采用 WebSocket 实现订单状态实时推送

## 状态
Accepted — v2.0 已实施

## 背景
订单履约流程涉及多个智能体步骤（欺诈检测 → 库存检查 → 仓库竞价 → 需求预测），每个步骤需要数秒完成。用户提交订单后，如果等待所有步骤完成才返回，HTTP 请求会超时。需要一种机制：
- 先快速返回订单创建确认
- 实时推送每个智能体步骤的完成状态
- 前端展示动态进度和决策日志

## 决策
采用 **WebSocket** 实现订单状态的实时推送，每个订单拥有独立的 WebSocket 连接。

## 考虑方案

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| **WebSocket** | 全双工；低延迟；服务器可主动推送；HTTP 升级兼容 | 需要维持长连接；有状态；需要连接管理 | ✅ 选中 |
| Server-Sent Events (SSE) | 简单；单向推送；自动重连；HTTP 兼容 | 单向（服务器→客户端）；部分代理不支持 | ❌ 单向限制 |
| 长轮询（Long Polling） | 兼容性好；无需额外协议 | 延迟高；服务器资源消耗大；非实时 | ❌ 过时方案 |
| 纯 HTTP 轮询 | 最简单 | 延迟不可控；服务器压力大；非实时 | ❌ 不满足体验需求 |
| gRPC Streaming | 高性能；强类型；双向流 | 需要 HTTP/2；浏览器支持弱；需要 .proto | ❌ 前端兼容性差 |

## 技术细节

### 连接管理器
```python
# backend/api/websocket.py
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, order_id: str):
        await websocket.accept()
        self.active_connections[order_id] = websocket
    
    def disconnect(self, order_id: str):
        self.active_connections.pop(order_id, None)
    
    async def send_order_update(self, order_id: str, data: dict):
        if order_id in self.active_connections:
            await self.active_connections[order_id].send_json(data)

manager = ConnectionManager()  # 单例，模块级共享
```

### 为什么用字典而不是列表？
- 字典以 `order_id` 为键，O(1) 查找特定订单的连接
- 列表需要遍历，O(n) 且可能找不到
- 每个订单只有一个 WebSocket 连接，键值对模型天然匹配

### 端点设计
```python
@router.websocket("/ws/orders/{order_id}")
async def websocket_endpoint(websocket: WebSocket, order_id: str):
    await manager.connect(websocket, order_id)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"event": "pong", "order_id": order_id})
    except WebSocketDisconnect:
        manager.disconnect(order_id)
```

### 事件推送流程
```python
# backend/services/order_service.py
async def create_order(self, request):
    order_id = str(uuid4())
    
    # 1. 订单创建 → 推送
    await manager.send_order_update(order_id, {
        "event": "order.created",
        "order_id": order_id,
        "data": {"order_status": "pending", "timestamp": "..."}
    })
    
    # 2. 欺诈检测完成 → 推送
    risk_score, fraud_status = self.fraud_agent.score(...)
    await manager.send_order_update(order_id, {
        "event": "fraud.checked",
        "data": {"risk_score": risk_score, "fraud_status": fraud_status}
    })
    
    # 3. 库存检查完成 → 推送
    await manager.send_order_update(order_id, {
        "event": "inventory.checked",
        "data": {"stock_available": True}
    })
    
    # 4. 仓库竞价完成 → 推送
    await manager.send_order_update(order_id, {
        "event": "warehouse.bid",
        "data": {"bids": [...], "winner": "warehouse_1"}
    })
    
    # 5. 履约完成 → 推送
    await manager.send_order_update(order_id, {
        "event": "fulfillment.completed",
        "data": {"order_status": "created", "selected_warehouse": "warehouse_1"}
    })
```

### 前端 Hook 封装
```typescript
// frontend/src/hooks/useOrderSocket.ts
export function useOrderSocket(orderId: string | null) {
  const [status, setStatus] = useState<SocketMessage | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!orderId) return;  // 无订单时不连接
    const ws = new WebSocket(`${WS_BASE}/ws/orders/${orderId}`);
    ws.onopen = () => setConnected(true);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStatus(data);  // 触发 React 重新渲染
    };
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    return () => ws.close();  // cleanup：组件卸载时关闭
  }, [orderId]);  // orderId 变化时重建连接

  return { status, connected };
}
```

### 前端状态指示器
```tsx
// frontend/src/main.tsx 中的 WebSocket 状态条
<section className="websocket-panel">
  <div className="ws-status">
    <span className={connected ? "connected" : "disconnected"}>
      {connected ? "● Live" : "○ Offline"}
    </span>
    {wsStatus ? (
      <span>Latest: {wsStatus.event} — {wsStatus.data?.fraud_status || "..."}</span>
    ) : null}
  </div>
</section>
```

## 权衡与风险

| 风险 | 缓解措施 |
|------|----------|
| WebSocket 连接在服务器重启时断开 | 前端可自动重连（当前未实现，可用 `reconnecting-websocket` 库） |
| 单服务器的连接数上限（内存中的字典） | 当前是演示场景；生产环境可用 Redis 做连接状态共享，支持多实例 |
| 没有心跳检测，NAT/防火墙可能断开空闲连接 | 客户端发送 ping 消息，服务器回 pong；当前已实现 basic ping/pong |
| 连接泄漏（未正确关闭） | 使用 `try/finally` 确保 disconnect；前端 useEffect cleanup 关闭连接 |

## 设计复核要点

### Q1: 为什么用 WebSocket 而不是 SSE？
> "SSE 是单向的（服务器→客户端），基于 HTTP，自动重连简单。WebSocket 是全双工的，虽然我们需要的主要也是服务器推送，但 WebSocket 的握手升级后就是纯 TCP 帧，延迟更低。另外，如果未来需要客户端向服务器发送消息（如取消订单），WebSocket 天然支持。"

### Q2: 如果服务器重启，已建立的 WebSocket 连接会怎样？
> "连接会断开。前端会收到 `onclose` 事件，显示 'Offline' 状态。生产环境需要实现自动重连逻辑，比如指数退避重试。当前版本是演示目的，暂未实现，但架构上支持。"

### Q3: 每个订单一个 WebSocket 连接，如果用户同时下 100 个订单怎么办？
> "浏览器对同一域的并发连接数有限制（通常是 6-8 个），所以 100 个订单同时连接不现实。更好的设计可能是：一个全局连接接收所有订单的更新，通过消息中的 `order_id` 字段路由到正确的 UI 组件。当前采用每订单一个连接是为了演示清晰，设计复核中可以讨论这种权衡。"

### Q4: WebSocket 和 HTTP 请求有什么区别？
> "HTTP 是请求-响应模式，客户端必须主动发起，服务器才能返回。WebSocket 通过 HTTP 升级握手建立 TCP 长连接，之后双方可以任意时刻发送消息。在我们的场景中，服务器需要在欺诈检测、库存检查等步骤完成后主动推送，HTTP 做不到这一点（除非长轮询，但效率低）。"

### Q5: 你们的连接管理器是线程安全的吗？
> "在 Python async 环境中，事件循环是单线程的，所以字典操作天然是线程安全的（没有多线程竞争）。但如果未来水平扩展（多个后端实例），需要用 Redis 或共享内存来同步连接状态。当前是单进程演示，足够。"

## 相关文件
- `backend/api/websocket.py` — WebSocket 连接管理器
- `frontend/src/hooks/useOrderSocket.ts` — 前端 WebSocket Hook
- `backend/services/order_service.py` — 事件推送逻辑
- `frontend/src/main.tsx` — 状态指示器 UI

## 参考
- [FastAPI WebSocket 文档](https://fastapi.tiangolo.com/advanced/websockets/)
- [WebSocket RFC 6455](https://tools.ietf.org/html/rfc6455)
- [MDN WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

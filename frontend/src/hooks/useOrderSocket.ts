/**
 * useOrderSocket.ts
 * Custom React Hook for WebSocket-driven real-time order updates.
 *
 * This hook encapsulates the WebSocket lifecycle management:
 *   - Connection establishment when orderId changes
 *   - Message parsing and React state updates
 *   - Automatic cleanup (disconnect) on unmount or orderId change
 *
 * Architecture Pattern: Custom Hook (React composition pattern)
 * Benefits:
 *   - Reusable across any component that needs order status
 *   - Isolates side effects (WebSocket I/O) from UI rendering
 *   - Handles connection state for UX (loading spinner, disconnect warning)
 *
 * WebSocket Flow:
 *   1. Component mounts with orderId → hook opens ws://.../ws/orders/{id}
 *   2. Server pushes events: { event: "fraud.checked", data: {...} }
 *   3. Hook parses JSON → updates React state → triggers re-render
 *   4. Component unmounts → hook closes connection
 *
 * Engineering Note:
 *   Q: Why a custom hook instead of putting WebSocket logic in the component?
 *   A: Separation of concerns. The component renders UI; the hook manages
 *      side effects and state. This makes both easier to test and reuse.
 *
 *   Q: What happens if the WebSocket server restarts?
 *   A: The connection drops, onclose fires, and the component shows "Disconnected".
 *      In production you'd add automatic reconnection with exponential backoff.
 *
 *   Q: How does useEffect dependency array work here?
 *   A: [orderId] means the effect re-runs whenever orderId changes. The cleanup
 *      function (return () => ws.close()) runs before each re-run and on unmount,
 *      preventing memory leaks and stale connections.
 */

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
    if (!orderId) return;
    const ws = new WebSocket(`${WS_BASE}/ws/orders/${orderId}`);
    ws.onopen = () => setConnected(true);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStatus(data);
    };
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    return () => ws.close();
  }, [orderId]);

  return { status, connected };
}

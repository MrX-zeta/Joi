import { useEffect, useRef, useState, useCallback } from "react";

type Status = "connecting" | "open" | "closed";

export function useJoiSocket(url = "ws://localhost:8000/ws") {
  const [status, setStatus] = useState<Status>("connecting");
  const [lastMessage, setLastMessage] = useState<string>("");
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setStatus("open");
    ws.onclose = () => setStatus("closed");
    ws.onerror = () => setStatus("closed");
    ws.onmessage = (e) => setLastMessage(e.data);

    return () => ws.close();
  }, [url]);

  const send = useCallback((msg: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(msg);
    }
  }, []);

  return { status, lastMessage, send };
}
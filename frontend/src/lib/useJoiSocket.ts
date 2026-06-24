import { useEffect, useRef, useState, useCallback } from "react";

type Status = "connecting" | "open" | "closed";

export function useJoiSocket(
  onToken: (token: string) => void,
  url = "ws://localhost:8000/ws"
) {
  const [status, setStatus] = useState<Status>("connecting");
  const wsRef = useRef<WebSocket | null>(null);
  const onTokenRef = useRef(onToken);
  onTokenRef.current = onToken;

  useEffect(() => {
    let closed = false;
    let retry: ReturnType<typeof setTimeout>;

    const connect = () => {
      const ws = new WebSocket(url);
      wsRef.current = ws;
      setStatus("connecting");

      ws.onopen = () => setStatus("open");
      ws.onmessage = (e) => onTokenRef.current(e.data);
      ws.onerror = () => ws.close();
      ws.onclose = () => {
        setStatus("closed");
        if (!closed) retry = setTimeout(connect, 1000); // reintenta cada 1s
      };
    };

    connect();
    return () => {
      closed = true;
      clearTimeout(retry);
      wsRef.current?.close();
    };
  }, [url]);

  const send = useCallback((msg: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) wsRef.current.send(msg);
  }, []);

  return { status, send };
}
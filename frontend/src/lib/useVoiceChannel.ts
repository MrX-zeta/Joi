import { useEffect, useRef, useState } from "react";

type Status = "connecting" | "open" | "closed";

type VoiceHandlers = {
  onTranscript?: (text: string) => void;
  onToken?: (text: string) => void;
  onEnd?: () => void;
  onSpeakingChange?: (speaking: boolean) => void;
};

export function useVoiceChannel(
  handlers: VoiceHandlers,
  url = "ws://localhost:8000/voice"
) {
  const [status, setStatus] = useState<Status>("connecting");
  const wsRef = useRef<WebSocket | null>(null);
  const h = useRef(handlers);
  h.current = handlers;

  const queue = useRef<string[]>([]);
  const playing = useRef(false);

  const playNext = () => {
    if (playing.current) return;
    const next = queue.current.shift();
    if (!next) return;
    playing.current = true;
    h.current.onSpeakingChange?.(true);
    const audio = new Audio(next);
    const done = () => {
      URL.revokeObjectURL(next);
      playing.current = false;
      if (queue.current.length) playNext();
      else h.current.onSpeakingChange?.(false);
    };
    audio.onended = done;
    audio.onerror = done;
    audio.play().catch(done);
  };

  useEffect(() => {
    let closed = false;
    let retry: ReturnType<typeof setTimeout>;

    const connect = () => {
      const ws = new WebSocket(url);
      ws.binaryType = "arraybuffer";
      wsRef.current = ws;
      setStatus("connecting");

      ws.onopen = () => setStatus("open");
      ws.onerror = () => ws.close();
      ws.onclose = () => {
        setStatus("closed");
        if (!closed) retry = setTimeout(connect, 1000);
      };
      ws.onmessage = (e) => {
        if (typeof e.data === "string") {
          const msg = JSON.parse(e.data);
          if (msg.type === "transcript") h.current.onTranscript?.(msg.text);
          else if (msg.type === "token") h.current.onToken?.(msg.text);
          else if (msg.type === "end") h.current.onEnd?.();
        } else {
          const blobUrl = URL.createObjectURL(
            new Blob([e.data], { type: "audio/mpeg" })
          );
          queue.current.push(blobUrl);
          playNext();
        }
      };
    };

    connect();
    return () => {
      closed = true;
      clearTimeout(retry);
      wsRef.current?.close();
    };
  }, [url]);

  const sendAudio = (samples: Float32Array) => {
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN) ws.send(samples);
  };

  const sendText = (text: string) => {
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN)
      ws.send(JSON.stringify({ type: "text", content: text }));
  };

  const sendConfig = (speak: boolean) => {
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN)
      ws.send(JSON.stringify({ type: "config", speak }));
  };

  return { status, sendAudio, sendText, sendConfig };
}
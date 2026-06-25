import { useEffect, useRef, useState } from "react";

type Status = "connecting" | "open" | "closed";

type ConfirmRequest = {
  id: string;
  tool: string;
  args: Record<string, unknown>;
  label: string;
};

type VoiceHandlers = {
  onTranscript?: (text: string) => void;
  onToken?: (text: string) => void;
  onEnd?: () => void;
  onSpeakingChange?: (speaking: boolean) => void;
  onHistory?: (messages: { role: string; content: string }[]) => void;
  onConfirmRequest?: (req: ConfirmRequest) => void;
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
    if (!next) {
      h.current.onSpeakingChange?.(false);
      return;
    }
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
          if (msg.type === "history") h.current.onHistory?.(msg.messages);
          else if (msg.type === "transcript") h.current.onTranscript?.(msg.text);
          else if (msg.type === "token") h.current.onToken?.(msg.text);
          else if (msg.type === "confirm_request")
            h.current.onConfirmRequest?.({
              id: msg.id,
              tool: msg.tool,
              args: msg.args,
              label: msg.label,
            });
          else if (msg.type === "end") h.current.onEnd?.();
          // audio_start / audio_end se ignoran: el control de "hablando"
          // lo maneja la cola de reproducción (playNext)
        } else {
          const blobUrl = URL.createObjectURL(
            new Blob([e.data], { type: "audio/wav" })
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

  const sendConfirm = (id: string, approved: boolean) => {
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN)
      ws.send(JSON.stringify({ type: "confirm_response", id, approved }));
  };

  return { status, sendAudio, sendText, sendConfig, sendConfirm };
}
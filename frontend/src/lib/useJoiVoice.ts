import { useEffect, useRef } from "react";
import { listen } from "@tauri-apps/api/event";
import { invoke } from "@tauri-apps/api/core";

type Handlers = {
  onListening?: () => void;
  onSpeechEnd?: () => void;
  onUtterance?: (samples: Float32Array) => void;
};

export function useJoiVoice(handlers: Handlers) {
  const ref = useRef(handlers);
  ref.current = handlers;

  const lastUtterance = useRef(0);

  useEffect(() => {
    const unlisteners = [
      listen("joi://listening", () => ref.current.onListening?.()),
      listen("joi://speech-end", () => ref.current.onSpeechEnd?.()),
      listen<number[]>("joi://utterance", (e) => {
        // Anti-duplicado: ignora utterances que llegan pegadas (StrictMode / VAD doble)
        const now = Date.now();
        if (now - lastUtterance.current < 600) return;
        lastUtterance.current = now;
        ref.current.onUtterance?.(Float32Array.from(e.payload));
      }),
    ];
    return () => {
      unlisteners.forEach((p) => p.then((fn) => fn()));
    };
  }, []);
}

export const startListening = () => invoke("start_listening");
export const stopListening = () => invoke("stop_listening");
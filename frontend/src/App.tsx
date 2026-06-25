import { useEffect, useRef, useState } from "react";
import { useJoiSocket } from "./lib/useJoiSocket";
import { useJoiVoice, startListening, stopListening } from "./lib/useJoiVoice";
import { useVoiceChannel } from "./lib/useVoiceChannel";
import Aurora, { type AuroraState } from "./components/Aurora";
import Sidebar, { type Message } from "./components/Sidebar";
import Dock from "./components/Dock";

const STATE_LABEL: Record<AuroraState, string> = {
  idle: "en reposo",
  listening: "te escucho",
  thinking: "pensando",
  speaking: "hablando",
};

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [streaming, setStreaming] = useState("");
  const [thinking, setThinking] = useState(false);
  const [muted, setMuted] = useState(false);
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [historyOpen, setHistoryOpen] = useState(false);

  const streamingRef = useRef("");
  const speakingRef = useRef(false);
  const mutedRef = useRef(false);

  const appendToken = (t: string) => {
    streamingRef.current += t;
    setStreaming(streamingRef.current);
    setThinking(false);
  };
  const commitAssistant = () => {
    const full = streamingRef.current;
    streamingRef.current = "";
    if (full) setMessages((m) => [...m, { role: "joi", content: full }]);
    setStreaming("");
    setThinking(false);
  };
  const commitUser = (t: string) => setMessages((m) => [...m, { role: "user", content: t }]);

  const { status, send } = useJoiSocket((token) => {
    if (token === "[[END]]") return commitAssistant();
    appendToken(token);
  });

  const { status: voiceStatus, sendAudio, sendText, sendConfig } = useVoiceChannel({
    onHistory: (hist) => {
      setMessages(
        hist.map((m) => ({
          role: m.role === "assistant" ? "joi" : "user",
          content: m.content,
        })) as Message[]
      );
    },
    onTranscript: (t) => commitUser(t),
    onToken: (t) => appendToken(t),
    onEnd: () => commitAssistant(),
    onSpeakingChange: (s) => {
      speakingRef.current = s;
      setSpeaking(s);
    },
  });

  useEffect(() => {
    if (voiceStatus === "open") sendConfig(voiceEnabled);
  }, [voiceEnabled, voiceStatus]);

  useJoiVoice({
    onListening: () => setListening(true),
    onSpeechEnd: () => setListening(false),
    onUtterance: (samples) => {
      if (speakingRef.current || mutedRef.current) return;
      setStreaming("");
      setThinking(true);
      sendAudio(samples);
    },
  });

  useEffect(() => {
    startListening();
    return () => {
      stopListening();
    };
  }, []);

  const toggleMute = async () => {
    if (muted) {
      await startListening();
      mutedRef.current = false;
      setMuted(false);
    } else {
      await stopListening();
      mutedRef.current = true;
      setMuted(true);
      setListening(false);
    }
  };

  const ready = voiceEnabled ? voiceStatus === "open" : status === "open";

  const handleSend = (text: string) => {
    if (!ready) return;
    commitUser(text);
    setStreaming("");
    setThinking(true);
    if (voiceEnabled) sendText(text);
    else send(text);
  };

  const auroraState: AuroraState =
    listening && !muted ? "listening" : speaking || streaming ? "speaking" : thinking ? "thinking" : "idle";

  const online = (voiceEnabled ? voiceStatus : status) === "open";

  return (
    <main className="fixed inset-0 overflow-hidden bg-[#0c0f10] text-zinc-100">
      <div aria-hidden className="pointer-events-none absolute inset-0" style={{ background: "radial-gradient(ellipse at 50% 92%, #14302e 0%, #0e1816 38%, #0a0d0e 70%)" }} />
      <div aria-hidden className="pointer-events-none absolute inset-0 opacity-60" style={{ background: "radial-gradient(circle at 50% 100%, #fcd34d14 0%, transparent 46%), radial-gradient(circle at 80% 12%, #8b5cf610 0%, transparent 44%)" }} />
      <div aria-hidden className="pointer-events-none absolute inset-0" style={{ backgroundImage: "linear-gradient(#ffffff03 1px, transparent 1px)", backgroundSize: "100% 3px" }} />

      {/* Estado (esquina fija) */}
      <div className="absolute left-6 top-5 z-40 flex items-center gap-2.5 font-mono text-[13px] font-medium tracking-[0.35em] text-teal-200/90">
        <span className={"h-1.5 w-1.5 rounded-full " + (online ? "bg-teal-300 shadow-[0_0_10px_#5eead4]" : "bg-rose-500")} />
        JOI
      </div>

      {/* Aurora: SIEMPRE centrada. Nada la mueve. */}
      <div className="pointer-events-none absolute left-1/2 top-1/2 z-10 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center">
        <Aurora state={auroraState} />
        <p className="mt-1 font-mono text-[13px] font-medium tracking-[0.4em] text-teal-100/70">{STATE_LABEL[auroraState]}</p>
      </div>

      {/* Dock: SIEMPRE centrado abajo. */}
      <div className="absolute bottom-8 left-1/2 z-30 -translate-x-1/2">
        <Dock
          onSend={handleSend}
          disabled={!ready}
          onToggleMute={toggleMute}
          muted={muted}
          listening={listening}
          voiceEnabled={voiceEnabled}
          onToggleVoice={() => setVoiceEnabled((v) => !v)}
        />
      </div>

      {/* Botón historial (esquina fija) */}
      <button
        onClick={() => setHistoryOpen(true)}
        aria-label="Abrir historial"
        className="absolute right-5 top-4 z-40 flex h-9 w-9 items-center justify-center rounded-[10px] border border-white/10 bg-[#0c0f10] text-teal-100/70 transition-colors duration-300 hover:bg-white/10"
      >
        <SidebarIcon />
      </button>

      {/* Historial: overlay flotante */}
      <Sidebar
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        messages={messages}
        streaming={streaming}
        thinking={thinking}
      />
    </main>
  );
}

function SidebarIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <line x1="15" y1="4" x2="15" y2="20" />
    </svg>
  );
}
import { useState } from "react";

export default function InputBar({
  onSend,
  disabled,
  onToggleMute,
  muted,
  listening,
}: {
  onSend: (text: string) => void;
  disabled: boolean;
  onToggleMute: () => void;
  muted: boolean;
  listening: boolean;
}) {
  const [value, setValue] = useState("");

  const submit = () => {
    const t = value.trim();
    if (!t || disabled) return;
    onSend(t);
    setValue("");
  };

  const micClass = muted
    ? "border-rose-500/50 bg-rose-500/10 text-rose-400"
    : listening
    ? "border-cyan-400/70 bg-cyan-400/20 text-cyan-300 shadow-[0_0_18px_-2px_rgba(34,211,238,0.6)]"
    : "border-cyan-400/30 bg-cyan-400/5 text-cyan-400/80 hover:bg-cyan-400/15";

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={onToggleMute}
        aria-label={muted ? "Activar micrófono" : "Silenciar micrófono"}
        className={
          "relative flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border transition-all duration-200 " +
          micClass +
          (listening && !muted ? " animate-pulse" : "")
        }
      >
        <MicIcon muted={muted} />
      </button>

      <div className="flex flex-1 items-center rounded-2xl border border-zinc-800/80 bg-zinc-900/50 pr-1.5 transition focus-within:border-purple-500/50 focus-within:bg-zinc-900/80">
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder={muted ? "Micrófono en silencio — escribe aquí…" : "Habla o escribe…"}
          className="h-11 flex-1 bg-transparent px-4 text-sm text-zinc-100 outline-none placeholder:text-zinc-600"
        />
        <button
          onClick={submit}
          disabled={disabled || !value.trim()}
          aria-label="Enviar"
          className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-[#ff8a5b] via-[#ff6b9d] to-[#9b5cd6] text-white transition hover:brightness-110 disabled:opacity-30 disabled:saturate-0"
        >
          <SendIcon />
        </button>
      </div>
    </div>
  );
}

function MicIcon({ muted }: { muted: boolean }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
      <path d="M19 10v1a7 7 0 0 1-14 0v-1M12 18v4" />
      {muted && <line x1="3" y1="3" x2="21" y2="21" stroke="currentColor" />}
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 19V5M5 12l7-7 7 7" />
    </svg>
  );
}
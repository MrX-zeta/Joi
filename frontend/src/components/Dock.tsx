import { useState } from "react";

export default function Dock({
  onSend,
  disabled,
  onToggleMute,
  muted,
  listening,
  voiceEnabled,
  onToggleVoice,
}: {
  onSend: (text: string) => void;
  disabled: boolean;
  onToggleMute: () => void;
  muted: boolean;
  listening: boolean;
  voiceEnabled: boolean;
  onToggleVoice: () => void;
}) {
  const [value, setValue] = useState("");
  const [focused, setFocused] = useState(false);

  const submit = () => {
    const t = value.trim();
    if (!t || disabled) return;
    onSend(t);
    setValue("");
  };

  const micColor = muted
    ? "border-rose-500/40 bg-rose-500/10 text-rose-400"
    : listening
    ? "border-teal-300/60 bg-teal-400/15 text-teal-200"
    : "border-teal-300/30 bg-teal-400/[0.07] text-teal-200/80 hover:bg-teal-400/15";

  const voiceColor = voiceEnabled
    ? "border-amber-300/40 bg-amber-300/12 text-amber-200/90"
    : "border-zinc-700 bg-zinc-800/40 text-zinc-500 hover:text-zinc-300";

  return (
    <div
      className="flex items-center gap-3 rounded-full border py-3 pl-4 pr-3"
      style={{
        width: "min(760px, 92vw)",
        background: "rgba(0,0,0,0.32)",
        borderColor: focused ? "rgba(94,234,212,0.45)" : "rgba(94,234,212,0.14)",
        boxShadow: focused
          ? "inset 0 1px 12px rgba(0,0,0,0.5), 0 0 0 1px rgba(94,234,212,0.25), 0 0 30px rgba(94,234,212,0.18)"
          : "inset 0 1px 12px rgba(0,0,0,0.55), 0 0 26px rgba(94,234,212,0.05)",
        transition: "border-color .4s ease, box-shadow .4s ease",
      }}
    >
      <button
        onClick={onToggleMute}
        aria-label={muted ? "Activar micrófono" : "Silenciar micrófono"}
        className={
          "flex h-12 w-12 shrink-0 items-center justify-center rounded-full border transition-all duration-500 " +
          micColor +
          (listening && !muted ? " animate-pulse" : "")
        }
      >
        <MicIcon muted={muted} />
      </button>

      <button
        onClick={onToggleVoice}
        aria-label={voiceEnabled ? "Desactivar voz de Joi" : "Activar voz de Joi"}
        className={"flex h-12 w-12 shrink-0 items-center justify-center rounded-full border transition-all duration-500 " + voiceColor}
      >
        <SpeakerIcon on={voiceEnabled} />
      </button>

      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        onKeyDown={(e) => e.key === "Enter" && submit()}
        placeholder={muted ? "Micrófono en silencio — escribe…" : "Habla o escribe…"}
        className="h-11 min-w-0 flex-1 bg-transparent px-2 text-[15px] tracking-[0.3px] text-teal-50/90 outline-none placeholder:text-[#5a6f69]"
      />

      <button
        onClick={submit}
        disabled={disabled || !value.trim()}
        aria-label="Enviar"
        className="ml-1 flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-teal-300/25 bg-teal-400/[0.06] text-teal-200/80 transition-all duration-300 hover:bg-teal-400/15 disabled:border-transparent disabled:bg-transparent disabled:text-teal-200/20"
      >
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 19V5M5 12l7-7 7 7" />
        </svg>
      </button>
    </div>
  );
}

function MicIcon({ muted }: { muted: boolean }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
      <path d="M19 10v1a7 7 0 0 1-14 0v-1M12 18v4" />
      {muted && <line x1="3" y1="3" x2="21" y2="21" />}
    </svg>
  );
}

function SpeakerIcon({ on }: { on: boolean }) {
  return (
    <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 5 6 9H2v6h4l5 4V5z" />
      {on ? (
        <>
          <path d="M15.5 8.5a5 5 0 0 1 0 7" />
          <path d="M18.5 5.5a9 9 0 0 1 0 13" />
        </>
      ) : (
        <line x1="22" y1="9" x2="16" y2="15" />
      )}
    </svg>
  );
}
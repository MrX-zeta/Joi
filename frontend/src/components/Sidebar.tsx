import { useEffect, useRef } from "react";

export type Message = { role: "user" | "joi"; content: string };

export default function Sidebar({
  open,
  onClose,
  messages,
  streaming,
  thinking,
}: {
  open: boolean;
  onClose: () => void;
  messages: Message[];
  streaming: string;
  thinking: boolean;
}) {
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (open) endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming, thinking, open]);

  const today = new Date()
    .toLocaleDateString("es-MX", { day: "2-digit", month: "long" })
    .toUpperCase();

  // Cerrado = no se renderiza. Imposible que aparezca solo o se quede pegado.
  if (!open) return null;

  return (
    <div className="absolute inset-0 z-50 flex justify-end" style={{ animation: "joiFade .3s ease" }}>
      <style>{`@keyframes joiFade{from{opacity:0}to{opacity:1}}`}</style>

      {/* Fondo oscurecido: clic para cerrar */}
      <div onClick={onClose} className="absolute inset-0 bg-black/40" />

      {/* Panel del historial: solo aparece (opacidad), NO se desliza */}
      <aside
        className="relative flex h-full w-[360px] flex-col border-l border-teal-300/15 bg-[#0a100f]"
        style={{ boxShadow: "-30px 0 60px rgba(0,0,0,0.5)" }}
      >

        <div className="flex items-center justify-between px-6 pb-3 pt-6">
          <span className="font-mono text-[12px] font-medium tracking-[0.3em] text-teal-200/80">HOY · {today}</span>
          <button
            onClick={onClose}
            aria-label="Cerrar historial"
            className="flex h-7 w-7 items-center justify-center rounded-md border border-white/10 text-teal-100/60 transition-colors hover:bg-white/10"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

       <div
          className="flex flex-1 flex-col gap-3 overflow-y-auto overscroll-contain px-4 pb-4"
          style={{ scrollbarGutter: "stable" }}
        >
          {messages.length === 0 && !streaming && !thinking && (
            <p className="mt-8 px-2 text-center text-sm text-teal-100/25">Aún no han conversado hoy.</p>
          )}

          {messages.map((m, i) => (
            <Bubble key={i} role={m.role}>
              {m.content}
            </Bubble>
          ))}

          {streaming && <Bubble role="joi">{streaming}</Bubble>}

          {thinking && !streaming && (
            <div className="self-start rounded-[18px_18px_18px_5px] border border-teal-300/20 bg-teal-400/10 px-4 py-3">
              <span className="flex gap-1">
                <Dot d="0s" /> <Dot d=".15s" /> <Dot d=".3s" />
              </span>
            </div>
          )}
          <div ref={endRef} />
        </div>
      </aside>
    </div>
  );
}

function Bubble({ role, children }: { role: "user" | "joi"; children: React.ReactNode }) {
  const isUser = role === "user";
  return (
    <div
      className={
        "max-w-[88%] whitespace-pre-wrap px-4 py-2.5 text-[13px] leading-relaxed tracking-[0.2px] " +
        (isUser
          ? "self-end rounded-[18px_18px_5px_18px] border border-white/[0.06] bg-white/[0.04] text-slate-400"
          : "self-start rounded-[18px_18px_18px_5px] border border-teal-300/20 bg-teal-400/[0.1] text-[#cdeee6] shadow-[0_0_18px_rgba(94,234,212,0.06)]")
      }
    >
      {children}
    </div>
  );
}

function Dot({ d }: { d: string }) {
  return <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal-300/60" style={{ animationDelay: d }} />;
}
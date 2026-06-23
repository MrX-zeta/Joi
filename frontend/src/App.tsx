import { useState } from "react";
import { useJoiSocket } from "./lib/useJoiSocket";

export default function App() {
  const { status, lastMessage, send } = useJoiSocket();
  const [input, setInput] = useState("Hola");

  const dotColor =
    status === "open"
      ? "bg-emerald-400"
      : status === "connecting"
      ? "bg-amber-400"
      : "bg-rose-500";

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-zinc-950 text-zinc-100 font-mono">
      <div className="w-full max-w-md rounded-2xl border border-zinc-800 bg-zinc-900/60 p-8 shadow-[0_0_40px_-10px_rgba(56,189,248,0.3)] backdrop-blur">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-semibold tracking-widest text-cyan-300">JOI</h1>
          <span className="flex items-center gap-2 text-xs uppercase tracking-wider text-zinc-400">
            <span className={`h-2 w-2 rounded-full ${dotColor} animate-pulse`} />
            {status}
          </span>
        </div>

        <div className="mb-4 h-20 rounded-lg border border-zinc-800 bg-black/40 p-4 text-cyan-200">
          <span className="text-xs text-zinc-500">echo →</span>
          <p className="mt-1 truncate text-lg">{lastMessage || "..."}</p>
        </div>

        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send(input)}
            className="flex-1 rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2 text-sm outline-none transition focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
            placeholder="Escribe un mensaje..."
          />
          <button
            onClick={() => send(input)}
            disabled={status !== "open"}
            className="rounded-lg bg-cyan-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-cyan-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Enviar
          </button>
        </div>
      </div>
    </main>
  );
}
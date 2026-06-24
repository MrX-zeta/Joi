import { useEffect, useRef } from "react";

export type Message = { role: "user" | "joi"; content: string };

export default function ChatLog({
  messages,
  streaming,
  thinking,
}: {
  messages: Message[];
  streaming: string;
  thinking: boolean;
}) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming, thinking]);

  return (
    <div className="flex flex-1 flex-col gap-2 overflow-y-auto pr-1">
      {messages.map((m, i) => (
        <Bubble key={i} role={m.role}>
          {m.content}
        </Bubble>
      ))}

      {streaming && <Bubble role="joi">{streaming}</Bubble>}

      {thinking && !streaming && (
        <div className="self-start rounded-xl rounded-bl-sm border border-purple-400/20 bg-purple-400/10 px-3 py-2">
          <span className="flex gap-1">
            <Dot delay="0s" />
            <Dot delay="0.15s" />
            <Dot delay="0.3s" />
          </span>
        </div>
      )}

      <div ref={endRef} />
    </div>
  );
}

function Bubble({
  role,
  children,
}: {
  role: "user" | "joi";
  children: React.ReactNode;
}) {
  const isUser = role === "user";
  return (
    <div
      className={
        "max-w-[86%] whitespace-pre-wrap rounded-xl px-3 py-2 text-sm leading-relaxed " +
        (isUser
          ? "self-end rounded-br-sm bg-zinc-800 text-zinc-200"
          : "self-start rounded-bl-sm border border-purple-400/25 bg-purple-400/10 text-purple-100")
      }
    >
      {children}
    </div>
  );
}

function Dot({ delay }: { delay: string }) {
  return (
    <span
      className="h-1.5 w-1.5 animate-bounce rounded-full bg-purple-300"
      style={{ animationDelay: delay }}
    />
  );
}
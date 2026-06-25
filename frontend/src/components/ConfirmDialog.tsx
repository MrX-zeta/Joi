type ConfirmRequest = {
  id: string;
  label: string;
};

type Props = {
  request: ConfirmRequest | null;
  onRespond: (id: string, approved: boolean) => void;
};

export default function ConfirmDialog({ request, onRespond }: Props) {
  if (!request) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      style={{ animation: "joiFade 0.2s ease-out" }}
    >
      <div className="mx-4 w-full max-w-sm rounded-2xl border border-teal-400/20 bg-[#0e1816] p-6 shadow-2xl">
        <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-teal-300/60">
          Confirmación
        </p>
        <p className="mb-6 text-lg text-teal-50">{request.label}</p>
        <div className="flex gap-3">
          <button
            onClick={() => onRespond(request.id, false)}
            className="flex-1 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-teal-100/70 transition hover:bg-white/10"
          >
            Cancelar
          </button>
          <button
            onClick={() => onRespond(request.id, true)}
            className="flex-1 rounded-xl border border-teal-400/30 bg-teal-400/15 px-4 py-2.5 text-sm font-medium text-teal-100 transition hover:bg-teal-400/25"
          >
            Aceptar
          </button>
        </div>
      </div>
    </div>
  );
}
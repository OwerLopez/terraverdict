import { X } from "lucide-react";
import { useEffect, useRef, type ReactNode } from "react";
import { t } from "../lib/i18n";

/** Diálogo modal accesible basado en <dialog> nativo (foco atrapado y Escape). */
export function Dialogo({
  abierto,
  alCerrar,
  titulo,
  children,
}: {
  abierto: boolean;
  alCerrar: () => void;
  titulo: string;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (abierto && !d.open) d.showModal?.();
    if (!abierto && d.open) d.close?.();
  }, [abierto]);

  return (
    <dialog
      ref={ref}
      onClose={alCerrar}
      onClick={(e) => e.target === ref.current && alCerrar()}
      className="w-[min(92vw,420px)] rounded-2xl border border-line bg-surface p-0 text-ink shadow-flotante backdrop:bg-black/40 backdrop:backdrop-blur-sm"
      aria-label={titulo}
    >
      <div className="flex items-center justify-between border-b border-line px-5 py-3.5">
        <h2 className="font-semibold">{titulo}</h2>
        <button type="button" onClick={alCerrar} className="rounded-md p-1 text-ink-3 hover:bg-surface-2 hover:text-ink" aria-label={t("Cerrar", "Close")}>
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="p-5">{children}</div>
    </dialog>
  );
}

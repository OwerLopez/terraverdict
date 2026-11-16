import { X } from "lucide-react";
import { useEffect, useRef, type ReactNode } from "react";
import { t } from "../lib/i18n";

/** Panel que se desliza desde la derecha (diálogo nativo: foco atrapado, Escape y clic fuera cierran). */
export function PanelLateral({
  abierto,
  alCerrar,
  titulo,
  children,
}: {
  abierto: boolean;
  alCerrar: () => void;
  titulo: ReactNode;
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
      className="panel-lateral fixed inset-y-0 right-0 left-auto m-0 h-full max-h-none w-[min(94vw,480px)] border-0 border-l border-line bg-surface-solida p-0 text-ink shadow-flotante backdrop:bg-black/30 backdrop:backdrop-blur-[2px]"
    >
      <div className="flex h-full flex-col">
        <div className="flex items-center justify-between gap-3 border-b border-line px-5 py-4">
          <h2 className="text-[15px] font-semibold tracking-tight">{titulo}</h2>
          <button type="button" onClick={alCerrar} className="rounded-md p-1.5 text-ink-3 hover:bg-surface-2 hover:text-ink" aria-label={t("Cerrar", "Close")}>
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="flex-1 space-y-4 overflow-y-auto px-5 py-5 text-[14px] leading-relaxed text-ink-2">{children}</div>
      </div>
    </dialog>
  );
}

/** Primera oración de un texto (para resumir sin cortar a mitad de frase). */
export function primeraOracion(texto: string): { inicio: string; resto: string } {
  const m = texto.match(/^(.+?[.!?])(\s+)(.+)$/s);
  if (!m || m[1] === undefined || m[3] === undefined || m[1].length < 40) return { inicio: texto, resto: "" };
  return { inicio: m[1], resto: m[3] };
}

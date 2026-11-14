/** Componentes base del sistema de diseño de TerraVerdict. */
import { clsx } from "clsx";
import {
  AlertTriangle,
  Ban,
  Calculator,
  CheckCircle2,
  CircleDashed,
  Clock,
  Equal,
  FlaskConical,
  HelpCircle,
  Loader2,
  Minus,
  ShieldAlert,
  ShieldCheck,
  XCircle,
  type LucideIcon,
} from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { ErrorApi } from "../api/cliente";

export type Tono = "neutral" | "accent" | "good" | "warning" | "serious" | "critical";

const COLOR_TONO: Record<Tono, string> = {
  neutral: "var(--ink-3)",
  accent: "var(--accent)",
  good: "var(--good)",
  warning: "var(--warning)",
  serious: "var(--serious)",
  critical: "var(--critical)",
};

export function Tarjeta({
  titulo,
  subtitulo,
  acciones,
  pie,
  children,
  className,
  sinPadding,
}: {
  titulo?: ReactNode;
  subtitulo?: ReactNode;
  acciones?: ReactNode;
  pie?: ReactNode;
  children: ReactNode;
  className?: string;
  sinPadding?: boolean;
}) {
  return (
    <section className={clsx("rounded-2xl border border-line bg-surface shadow-tarjeta animate-aparecer", className)}>
      {(titulo || acciones) && (
        <header className="flex items-start justify-between gap-4 px-5 pt-4">
          <div className="min-w-0">
            {titulo && <h2 className="text-[15px] font-semibold tracking-tight text-ink">{titulo}</h2>}
            {subtitulo && <p className="mt-0.5 text-[13px] leading-snug text-ink-2">{subtitulo}</p>}
          </div>
          {acciones && <div className="flex shrink-0 items-center gap-2">{acciones}</div>}
        </header>
      )}
      <div className={clsx(!sinPadding && "px-5 py-4")}>{children}</div>
      {pie && <footer className="border-t border-line px-5 py-2.5 text-[12px] text-ink-3">{pie}</footer>}
    </section>
  );
}

export function Insignia({ tono = "neutral", icono: Icono, children, className }: {
  tono?: Tono;
  icono?: LucideIcon;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border border-line bg-surface-2 px-2 py-0.5 text-[12px] font-medium text-ink-2",
        className,
      )}
    >
      {Icono ? (
        <Icono aria-hidden className={clsx("h-3.5 w-3.5", Icono === Loader2 && "animate-spin")} style={{ color: COLOR_TONO[tono] }} />
      ) : (
        <span aria-hidden className="h-1.5 w-1.5 rounded-full" style={{ background: COLOR_TONO[tono] }} />
      )}
      {children}
    </span>
  );
}

type Def = { tono: Tono; icono: LucideIcon; texto: string };

export const ESTADOS_VERIFICACION: Record<string, Def> = {
  verificado: { tono: "good", icono: CheckCircle2, texto: "Verificado" },
  parcial: { tono: "warning", icono: AlertTriangle, texto: "Parcial" },
  no_verificado: { tono: "critical", icono: XCircle, texto: "No verificado" },
  sin_evidencia: { tono: "neutral", icono: CircleDashed, texto: "Sin evidencia" },
};

export const ESTADOS_PRUEBA: Record<string, Def> = {
  aprobada: { tono: "good", icono: CheckCircle2, texto: "Aprobada" },
  fallida: { tono: "critical", icono: XCircle, texto: "Fallida" },
  calculada: { tono: "accent", icono: Calculator, texto: "Calculada" },
  pendiente: { tono: "neutral", icono: Clock, texto: "Pendiente" },
  no_aplica: { tono: "neutral", icono: Minus, texto: "No aplica" },
};

export const VEREDICTOS: Record<string, Def> = {
  robusta: { tono: "good", icono: ShieldCheck, texto: "Robusta" },
  fragil: { tono: "serious", icono: ShieldAlert, texto: "Frágil" },
  no_decidible: { tono: "neutral", icono: HelpCircle, texto: "No decidible" },
  sin_tendencia: { tono: "accent", icono: Equal, texto: "Sin tendencia" },
  preliminar: { tono: "warning", icono: FlaskConical, texto: "Preliminar" },
};

export const NOMBRES_PRUEBA: Record<string, string> = {
  ventanas: "Ventanas",
  enso: "Filtro El Niño",
  sensor: "Cambio de sensor",
  independencia: "Independencia",
  detectabilidad: "Detectabilidad",
};

export const ESTADOS_PROCESO: Record<string, Def> = {
  pendiente: { tono: "neutral", icono: Clock, texto: "Pendiente" },
  en_curso: { tono: "accent", icono: Loader2, texto: "En curso" },
  completado: { tono: "good", icono: CheckCircle2, texto: "Completado" },
  fallido: { tono: "critical", icono: XCircle, texto: "Fallido" },
  cancelado: { tono: "neutral", icono: Ban, texto: "Cancelado" },
};

export function ChipEstado({ mapa, valor }: { mapa: Record<string, Def>; valor: string | null | undefined }) {
  const def = (valor && mapa[valor]) || { tono: "neutral" as Tono, icono: HelpCircle, texto: valor ?? "—" };
  return (
    <Insignia tono={def.tono} icono={def.icono}>
      {def.texto}
    </Insignia>
  );
}

export function Boton({
  variante = "secundario",
  tamano = "md",
  icono: Icono,
  className,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variante?: "primario" | "secundario" | "fantasma";
  tamano?: "sm" | "md";
  icono?: LucideIcon;
}) {
  return (
    <button
      type="button"
      {...props}
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        tamano === "sm" ? "h-8 px-2.5 text-[13px]" : "h-9 px-3.5 text-sm",
        variante === "primario" && "bg-accent text-white hover:brightness-110",
        variante === "secundario" && "border border-line bg-surface text-ink hover:bg-surface-2",
        variante === "fantasma" && "text-ink-2 hover:bg-surface-2 hover:text-ink",
        className,
      )}
    >
      {Icono && <Icono aria-hidden className="h-4 w-4" />}
      {children}
    </button>
  );
}

export function EstadoVacio({
  icono: Icono = CircleDashed,
  titulo,
  children,
  acciones,
  className,
}: {
  icono?: LucideIcon;
  titulo: string;
  children?: ReactNode;
  acciones?: ReactNode;
  className?: string;
}) {
  return (
    <div className={clsx("rayado flex flex-col items-center justify-center rounded-xl border border-dashed border-line-strong px-6 py-10 text-center", className)}>
      <div className="mb-3 grid h-10 w-10 place-items-center rounded-full border border-line bg-surface">
        <Icono aria-hidden className="h-5 w-5 text-ink-3" />
      </div>
      <p className="font-semibold text-ink">{titulo}</p>
      {children && <div className="mt-1 max-w-md text-[13px] leading-relaxed text-ink-2">{children}</div>}
      {acciones && <div className="mt-4 flex gap-2">{acciones}</div>}
    </div>
  );
}

export function Esqueleto({ className }: { className?: string }) {
  return <div aria-hidden className={clsx("animate-pulso rounded-lg bg-surface-3", className)} />;
}

export function ErrorCarga({ error, className }: { error: unknown; className?: string }) {
  const e = error instanceof ErrorApi ? error : null;
  return (
    <div role="alert" className={clsx("rounded-xl border border-line bg-surface-2 p-4 text-sm", className)}>
      <p className="flex items-center gap-2 font-semibold text-ink">
        <XCircle aria-hidden className="h-4 w-4" style={{ color: "var(--critical)" }} />
        {e?.codigo === "sin_conexion" ? "No hay conexión con la API" : (e?.problema?.title ?? "No se pudo cargar")}
      </p>
      <p className="mt-1 text-ink-2">{e?.message ?? String(error)}</p>
      {e?.problema?.request_id && <p className="mt-2 font-mono text-[11px] text-ink-3">request_id: {e.problema.request_id}</p>}
    </div>
  );
}

export function Encabezado({
  eyebrow,
  titulo,
  descripcion,
  acciones,
}: {
  eyebrow?: string;
  titulo: string;
  descripcion?: ReactNode;
  acciones?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div className="max-w-3xl">
        {eyebrow && <p className="etiqueta mb-1.5">{eyebrow}</p>}
        <h1 className="text-[26px] font-semibold leading-tight tracking-tight text-ink md:text-[30px]">{titulo}</h1>
        {descripcion && <p className="mt-2 text-[15px] leading-relaxed text-ink-2">{descripcion}</p>}
      </div>
      {acciones && <div className="flex shrink-0 gap-2">{acciones}</div>}
    </div>
  );
}

export function Segmentado<T extends string>({
  opciones,
  valor,
  alCambiar,
  etiqueta,
}: {
  opciones: { valor: T; texto: ReactNode; titulo?: string }[];
  valor: T;
  alCambiar: (v: T) => void;
  etiqueta: string;
}) {
  return (
    <div role="radiogroup" aria-label={etiqueta} className="inline-flex rounded-lg border border-line bg-surface-2 p-0.5">
      {opciones.map((o) => (
        <button
          key={o.valor}
          type="button"
          role="radio"
          aria-checked={valor === o.valor}
          title={o.titulo}
          onClick={() => alCambiar(o.valor)}
          className={clsx(
            "inline-flex h-7 items-center gap-1.5 rounded-md px-2.5 text-[12.5px] font-medium transition-colors",
            valor === o.valor ? "bg-surface text-ink shadow-tarjeta" : "text-ink-2 hover:text-ink",
          )}
        >
          {o.texto}
        </button>
      ))}
    </div>
  );
}

export function Dato({
  etiqueta,
  valor,
  unidad,
  nota,
  icono: Icono,
  tono = "accent",
}: {
  etiqueta: string;
  valor: ReactNode;
  unidad?: string;
  nota?: ReactNode;
  icono?: LucideIcon;
  tono?: Tono;
}) {
  return (
    <div className="flex h-full flex-col rounded-2xl border border-line bg-surface p-4 shadow-tarjeta animate-aparecer">
      <div className="flex items-center justify-between">
        <p className="etiqueta">{etiqueta}</p>
        {Icono && <Icono aria-hidden className="h-4 w-4" style={{ color: COLOR_TONO[tono] }} />}
      </div>
      <p className="mt-2 text-[28px] font-semibold leading-none tracking-tight text-ink">
        {valor}
        {unidad && <span className="ml-1 text-[15px] font-medium text-ink-2">{unidad}</span>}
      </p>
      {nota && <p className="mt-auto pt-2 text-[12px] leading-snug text-ink-3">{nota}</p>}
    </div>
  );
}

export function NotaFuente({ children }: { children: ReactNode }) {
  return <p className="text-[12px] leading-snug text-ink-3">{children}</p>;
}

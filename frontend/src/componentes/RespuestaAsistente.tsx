/** Respuesta del asistente: citas enlazadas a cada expediente y sello de verificación numérica. */
import { CheckCircle2, XCircle } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import type { Esquemas } from "../api/cliente";
import { numero } from "../lib/formato";
import { t } from "../lib/i18n";
import { traducirTitulo } from "../lib/titulos";
import { Insignia } from "./ui";

type Respuesta = Esquemas["RespuestaAsistenteSalida"];

const PATRON_CITA = /\[((?:TV-[A-Z]{2,4}-[0-9A-F]{12})(?:\s*,\s*TV-[A-Z]{2,4}-[0-9A-F]{12})*)\]/g;

/** Negritas (**x**) dentro de un tramo de texto plano. */
function conNegritas(texto: string, clave: string): ReactNode[] {
  return texto.split(/\*\*(.+?)\*\*/g).map((parte, i) => (i % 2 ? <strong key={`${clave}-${i}`} className="font-semibold text-ink">{parte}</strong> : parte));
}

/** Limpia restos de notación (LaTeX, viñetas con asterisco) que el modelo pudiera emitir. */
export function limpiarTexto(texto: string): string {
  return texto
    .replace(/\$([^$]{1,40})\$/g, "$1")
    .replace(/\\(?:ge|geq)\b/g, "≥")
    .replace(/\\(?:le|leq)\b/g, "≤")
    .replace(/\\[a-zA-Z]+\s?/g, "")
    .replace(/^\s*[*-]\s+/gm, "• ");
}

/**
 * Texto con las citas [TV-…] convertidas en chips numerados que enlazan al expediente que respalda
 * cada cifra (el ID completo queda en la descripción emergente y en la lista de fuentes).
 */
export function TextoConCitas({ texto, orden }: { texto: string; orden?: string[] }) {
  const limpio = limpiarTexto(texto);
  const indices = new Map<string, number>((orden ?? []).map((id, i) => [id, i + 1]));
  const partes: ReactNode[] = [];
  let ultimo = 0;
  for (const m of limpio.matchAll(PATRON_CITA)) {
    partes.push(...conNegritas(limpio.slice(ultimo, m.index), `t${ultimo}`));
    const ids = (m[1] ?? "").split(/\s*,\s*/);
    partes.push(
      <span key={`${m.index}`} className="whitespace-nowrap">
        {ids.map((id) => {
          if (!indices.has(id)) indices.set(id, indices.size + 1);
          return (
            <Link
              key={id}
              to={`/expedientes/${id}`}
              title={id}
              aria-label={`${t("Expediente", "Case file")} ${id}`}
              className="mx-0.5 inline-grid h-[18px] min-w-[18px] place-items-center rounded-full bg-accent-soft px-1 align-text-top text-[10.5px] font-semibold text-accent-ink hover:brightness-95"
            >
              {indices.get(id)}
            </Link>
          );
        })}
      </span>,
    );
    ultimo = (m.index ?? 0) + m[0].length;
  }
  partes.push(...conNegritas(limpio.slice(ultimo), `t${ultimo}`));
  return <span className="whitespace-pre-line">{partes}</span>;
}

export function SelloRespuesta({ r }: { r: Respuesta }) {
  const v = r.verificacion;
  const total = v.cifras.length;
  const trazables = v.cifras.filter((c) => c.trazable).length;
  return (
    <div className="mt-2 space-y-1.5 border-t border-line pt-2 text-[11.5px] text-ink-2">
      <div className="flex flex-wrap items-center gap-1.5">
        <Insignia tono={v.aprobado ? "good" : "critical"} icono={v.aprobado ? CheckCircle2 : XCircle}>
          {v.aprobado
            ? t(`Verificado: ${trazables}/${total} cifras respaldadas`, `Verified: ${trazables}/${total} figures backed`)
            : t(`Sin respaldo: ${v.no_trazables.join(", ")}`, `Unbacked: ${v.no_trazables.join(", ")}`)}
        </Insignia>
        {(v.coincidencias_debiles ?? []).length > 0 && (
          <Insignia tono="warning">{t(`Coincidencia débil: ${(v.coincidencias_debiles ?? []).join(", ")}`, `Weak match: ${(v.coincidencias_debiles ?? []).join(", ")}`)}</Insignia>
        )}
        <span className="text-ink-3">
          {r.modelo} · {numero(r.latencia_s, 1)} s{r.intentos > 1 ? t(" · reescrita 1 vez", " · rewritten once") : ""}
        </span>
      </div>
      {r.expedientes_consultados.length > 0 && (
        <p className="text-ink-3">
          {t("Contexto: ", "Context: ")}
          {r.expedientes_consultados.map((e, i) => (
            <span key={e.id}>
              {i > 0 && " · "}
              <Link to={`/expedientes/${e.id}`} className="hover:text-ink hover:underline">{traducirTitulo(e.titulo)}</Link>
            </span>
          ))}
        </p>
      )}
    </div>
  );
}


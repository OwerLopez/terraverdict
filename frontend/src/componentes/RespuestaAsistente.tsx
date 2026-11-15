/** Respuesta del asistente: citas enlazadas a cada expediente y sello de verificación numérica. */
import { CheckCircle2, XCircle } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import type { Esquemas } from "../api/cliente";
import { numero } from "../lib/formato";
import { t } from "../lib/i18n";
import { Insignia } from "./ui";

type Respuesta = Esquemas["RespuestaAsistenteSalida"];

const PATRON_CITA = /\[((?:TV-[A-Z]{2,4}-[0-9A-F]{12})(?:\s*,\s*TV-[A-Z]{2,4}-[0-9A-F]{12})*)\]/g;

/** Texto con las citas [TV-…] convertidas en enlaces al expediente que respalda cada cifra. */
export function TextoConCitas({ texto }: { texto: string }) {
  const partes: ReactNode[] = [];
  let ultimo = 0;
  for (const m of texto.matchAll(PATRON_CITA)) {
    partes.push(texto.slice(ultimo, m.index));
    const ids = (m[1] ?? "").split(/\s*,\s*/);
    partes.push(
      <span key={`${m.index}`} className="whitespace-nowrap">
        [
        {ids.map((id, i) => (
          <span key={id}>
            {i > 0 && ", "}
            <Link to={`/expedientes/${id}`} className="font-mono text-[11.5px] text-accent underline-offset-2 hover:underline">{id}</Link>
          </span>
        ))}
        ]
      </span>,
    );
    ultimo = (m.index ?? 0) + m[0].length;
  }
  partes.push(texto.slice(ultimo));
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
              <Link to={`/expedientes/${e.id}`} className="hover:text-ink hover:underline">{e.titulo}</Link>
            </span>
          ))}
        </p>
      )}
    </div>
  );
}


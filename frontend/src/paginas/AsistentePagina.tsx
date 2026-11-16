import { CheckCircle2, ShieldCheck, XCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { type Esquemas } from "../api/cliente";
import { useExpediente, useExpedientes, useVerificarTexto } from "../api/consultas";
import { Boton, Encabezado, Insignia, Tarjeta } from "../componentes/ui";
import { numero, numeroEs } from "../lib/formato";
import { t } from "../lib/i18n";

function marcarCifras(texto: string, cifras: Esquemas["CifraDetectada"][]) {
  const partes: { texto: string; cifra?: Esquemas["CifraDetectada"] }[] = [];
  let resto = texto;
  for (const c of cifras) {
    const i = resto.indexOf(c.texto);
    if (i < 0) continue;
    partes.push({ texto: resto.slice(0, i) }, { texto: c.texto, cifra: c });
    resto = resto.slice(i + c.texto.length);
  }
  partes.push({ texto: resto });
  return partes;
}

function Verificador() {
  const expedientes = useExpedientes();
  const lista = useMemo(() => expedientes.data?.items ?? [], [expedientes.data]);
  const [seleccion, setSeleccion] = useState<string[]>([]);
  // El texto de ejemplo cita un expediente de tendencia; se verifica solo contra ese por defecto.
  // Respaldar con todos a la vez debilita el verificador: con decenas de miles de valores (series y
  // métricas de los modelos), casi cualquier cifra coincide por azar dentro de la tolerancia.
  const base = useMemo(() => lista.find((e) => e.tipo === "tendencia") ?? lista[0], [lista]);
  const primero = useExpediente(base?.id);
  const [texto, setTexto] = useState("");
  const verificar = useVerificarTexto();

  useEffect(() => {
    if (base && seleccion.length === 0) setSeleccion([base.id]);
  }, [base, seleccion.length]);

  useEffect(() => {
    const r = primero.data?.resultado;
    if (!texto && r?.tipo === "tendencia") {
      const p = r.pendiente;
      setTexto(
        `${primero.data?.titulo}: la pendiente de Sen es ${numeroEs(p.valor, 2, { signo: true })} por década, con un intervalo de ${numeroEs(p.intervalo.lo, 2)} a ${numeroEs(p.intervalo.hi, 2)}.`,
      );
    }
  }, [primero.data, texto]);

  const partes = useMemo(() => (verificar.data ? marcarCifras(texto, verificar.data.cifras) : null), [verificar.data, texto]);

  return (
    <Tarjeta
      titulo={<span className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-accent" /> {t("Verificador numérico", "Numeric verifier")}</span>}
      subtitulo={t("Activo hoy. Comprueba que cada cifra de un texto esté respaldada, con su redondeo, por los expedientes seleccionados. Pruebe cambiar un número.", "Active today. It checks that every figure in a text is backed, with its rounding, by the selected case files. Try changing a number. Figures use the Spanish format (decimal comma).")}
    >
      <label className="block text-[12px] text-ink-2">
        {t("Texto a verificar", "Text to verify")}
        <textarea
          value={texto}
          onChange={(e) => {
            setTexto(e.target.value);
            verificar.reset();
          }}
          rows={4}
          className="mt-1 w-full rounded-lg border border-line bg-surface-2 p-3 text-[13.5px] leading-relaxed text-ink"
        />
      </label>
      <fieldset className="mt-3">
        <legend className="etiqueta mb-1.5">{t("Expedientes de respaldo", "Backing case files")}</legend>
        <div className="flex flex-wrap gap-2">
          {lista.map((e) => (
            <label key={e.id} className="inline-flex items-center gap-1.5 rounded-lg border border-line px-2.5 py-1 text-[12px] text-ink-2">
              <input
                type="checkbox"
                checked={seleccion.includes(e.id)}
                onChange={(ev) => setSeleccion((s) => (ev.target.checked ? [...s, e.id] : s.filter((x) => x !== e.id)))}
                className="accent-[var(--accent)]"
              />
              <span className="font-mono">{e.id}</span>
            </label>
          ))}
        </div>
      </fieldset>
      <Boton
        variante="primario"
        className="mt-3"
        icono={ShieldCheck}
        disabled={!texto.trim() || seleccion.length === 0 || verificar.isPending}
        onClick={() => verificar.mutate({ texto, expediente_ids: seleccion })}
      >
        {t("Verificar cifras", "Verify figures")}
      </Boton>

      {verificar.error && <p className="mt-3 text-[13px]" style={{ color: "var(--critical)" }}>{verificar.error.message}</p>}
      {verificar.data && partes && (
        <div className="mt-4 space-y-3" aria-live="polite">
          <Insignia tono={verificar.data.aprobado ? "good" : "critical"} icono={verificar.data.aprobado ? CheckCircle2 : XCircle}>
            {verificar.data.aprobado ? t("Todas las cifras están respaldadas", "All figures are backed") : t(`${verificar.data.no_trazables.length} cifra(s) sin respaldo`, `${verificar.data.no_trazables.length} unbacked figure(s)`)}
          </Insignia>
          <p className="rounded-xl border border-line bg-surface-2 p-3 text-[13.5px] leading-relaxed text-ink">
            {partes.map((p, i) =>
              p.cifra ? (
                <mark
                  key={i}
                  title={
                    p.cifra.trazable
                      ? t(
                          `Coincide con ${p.cifra.coincide_con}; probabilidad de coincidir por azar ${numero(p.cifra.probabilidad_azar, 3)}`,
                          `Matches ${p.cifra.coincide_con}; chance-match probability ${numero(p.cifra.probabilidad_azar, 3)}`,
                        )
                      : t("Sin respaldo en los expedientes", "Not backed by the case files")
                  }
                  className="rounded px-0.5 font-semibold"
                  style={{
                    background: "transparent",
                    color: "inherit",
                    boxShadow: `inset 0 -2px 0 ${p.cifra.trazable ? "var(--good)" : "var(--critical)"}`,
                  }}
                >
                  {p.texto}
                </mark>
              ) : (
                <span key={i}>{p.texto}</span>
              ),
            )}
          </p>
          <p className="text-[12px] text-ink-3">
            {t("Subrayado verde: cifra respaldada. Subrayado rojo: cifra sin respaldo. Valores permitidos evaluados:", "Green underline: backed figure. Red underline: unbacked figure. Allowed values evaluated:")} {verificar.data.valores_permitidos}.
          </p>
          {(verificar.data.coincidencias_debiles ?? []).length > 0 && (
            <p role="alert" className="text-[12px]" style={{ color: "var(--warning)" }}>
              {t(
                `Coincidencias débiles (${(verificar.data.coincidencias_debiles ?? []).join(", ")}): una cifra inventada con el mismo formato coincidiría por azar con probabilidad mayor que ${numero(verificar.data.alfa_coincidencia, 2)}. Verifique contra el expediente que cita el texto.`,
                `Weak matches (${(verificar.data.coincidencias_debiles ?? []).join(", ")}): an invented figure with the same format would match by chance with probability above ${numero(verificar.data.alfa_coincidencia, 2)}. Verify against the case file the text cites.`,
              )}
            </p>
          )}
        </div>
      )}
    </Tarjeta>
  );
}

export function AsistentePagina() {
  return (
    <div className="space-y-6">
      <Encabezado
        eyebrow={t("IA con garantías", "AI with guarantees")}
        titulo={t("Verificador numérico", "Numeric verifier")}
        descripcion={t(
          "Comprueba que cada cifra de un texto esté respaldada por los expedientes publicados. Es la misma garantía que aplica Terra, el asistente flotante (abajo a la derecha): Google Gemini conversa pero no calcula, responde solo con los expedientes más pertinentes, cita cada uno y cada cifra pasa por este verificador antes de mostrarse; si alguna no tiene respaldo, se pide una reescritura y el resultado se muestra tal cual.",
          "Checks that every figure in a text is backed by published case files. It is the same guarantee Terra, the floating assistant (bottom right), applies: Google Gemini converses but does not compute, answers only from the most relevant case files, cites each one, and every figure passes through this verifier before being shown; if any is unbacked, a rewrite is requested and the outcome is shown as is.",
        )}
        ayuda={
          <ul className="list-disc space-y-1.5 pl-5">
            <li>{t("Cada cifra debe coincidir, con su redondeo, con un valor del expediente citado.", "Every figure must match, with its rounding, a value in the cited case file.")}</li>
            <li>{t("Se informa la probabilidad de que una cifra inventada coincida por azar (coincidencia débil si supera 0,05).", "The probability that an invented figure would match by chance is reported (weak match above 0.05).")}</li>
            <li>{t("Los años se omiten: son metadatos del periodo, no resultados.", "Years are skipped: they are period metadata, not results.")}</li>
          </ul>
        }
      />
      <Verificador />
    </div>
  );
}

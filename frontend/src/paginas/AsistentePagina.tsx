import { clsx } from "clsx";
import { Bot, CheckCircle2, PlugZap, Send, ShieldCheck, XCircle } from "lucide-react";
import { useEffect, useMemo, useState, type FormEvent } from "react";
import { ErrorApi, type Esquemas } from "../api/cliente";
import { useConsultarAsistente, useExpediente, useExpedientes, useVerificarTexto } from "../api/consultas";
import { Boton, Encabezado, Insignia, Tarjeta } from "../componentes/ui";
import { numeroEs } from "../lib/formato";
import { t } from "../lib/i18n";

type Mensaje = { rol: "persona" | "sistema"; texto: string; tono?: "neutral" | "critical" };

const SUGERENCIAS: [string, string][] = [
  ["¿Llueve menos en la cabecera del Chili?", "Is it raining less in the Chili headwaters?"],
  ["¿Qué tan confiable es la tendencia de temperatura?", "How reliable is the temperature trend?"],
  ["¿Qué variables importan para las lluvias extremas?", "Which variables matter for extreme rain?"],
];

function Conversacion() {
  const consultar = useConsultarAsistente();
  const [mensajes, setMensajes] = useState<Mensaje[]>([]);
  const [texto, setTexto] = useState("");

  const enviar = (pregunta: string) => {
    if (!pregunta.trim()) return;
    setMensajes((m) => [...m, { rol: "persona", texto: pregunta }]);
    setTexto("");
    consultar.mutate(
      { pregunta, expediente_ids: [] },
      {
        onSuccess: (r) => setMensajes((m) => [...m, { rol: "sistema", texto: r.texto }]),
        onError: (e) =>
          setMensajes((m) => [
            ...m,
            {
              rol: "sistema",
              tono: "critical",
              texto:
                e instanceof ErrorApi && e.status === 503
                  ? t("El asistente todavía no está conectado. Cuando lo esté, responderá solo con herramientas del sistema y cada cifra pasará por el verificador numérico. No se genera ninguna respuesta de relleno.", "The assistant is not connected yet. When it is, it will answer only with system tools and every figure will pass the numeric verifier. No filler answer is generated.")
                  : e.message,
            },
          ]),
      },
    );
  };

  return (
    <Tarjeta
      titulo={<span className="flex items-center gap-2"><Bot className="h-4 w-4 text-accent" /> {t("Conversación", "Conversation")}</span>}
      acciones={<Insignia icono={PlugZap}>{t("No conectado", "Not connected")}</Insignia>}
      sinPadding
    >
      <div className="flex h-[440px] flex-col">
        <div className="flex-1 space-y-3 overflow-y-auto px-5 py-4" aria-live="polite">
          {mensajes.length === 0 && (
            <div className="grid h-full place-items-center text-center">
              <div>
                <p className="font-semibold text-ink">{t("Pregunte sobre el agua de Arequipa", "Ask about Arequipa's water")}</p>
                <p className="mt-1 text-[13px] text-ink-2">{t("La respuesta solo podrá citar expedientes publicados.", "The answer can only cite published case files.")}</p>
                <div className="mt-4 flex flex-wrap justify-center gap-2">
                  {SUGERENCIAS.map(([es, en]) => (
                    <button key={es} type="button" onClick={() => enviar(t(es, en))} className="rounded-full border border-line px-3 py-1.5 text-[12.5px] text-ink-2 hover:bg-surface-2 hover:text-ink">
                      {t(es, en)}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
          {mensajes.map((m, i) => (
            <div key={i} className={clsx("flex", m.rol === "persona" ? "justify-end" : "justify-start")}>
              <p
                className={clsx(
                  "max-w-[85%] rounded-2xl px-3.5 py-2.5 text-[13.5px] leading-relaxed",
                  m.rol === "persona" ? "bg-accent text-white" : "border border-line bg-surface-2 text-ink",
                )}
              >
                {m.tono === "critical" && <PlugZap aria-hidden className="mb-0.5 mr-1.5 inline h-3.5 w-3.5 text-ink-3" />}
                {m.texto}
              </p>
            </div>
          ))}
          {consultar.isPending && <p className="animate-pulso text-[13px] text-ink-3">{t("Consultando…", "Querying…")}</p>}
        </div>
        <form
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            enviar(texto);
          }}
          className="flex gap-2 border-t border-line p-3"
        >
          <label className="sr-only" htmlFor="pregunta">{t("Pregunta", "Question")}</label>
          <input id="pregunta" value={texto} onChange={(e) => setTexto(e.target.value)} placeholder={t("Escriba su pregunta…", "Type your question…")} className="h-10 flex-1 rounded-lg border border-line bg-surface-2 px-3 text-sm text-ink" />
          <Boton type="submit" variante="primario" icono={Send} disabled={!texto.trim() || consultar.isPending}>{t("Enviar", "Send")}</Boton>
        </form>
      </div>
    </Tarjeta>
  );
}

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

/** Con más valores que esto, la tolerancia relativa (0,5 %) cubre buena parte de cualquier rango y una
 *  coincidencia deja de ser evidencia de respaldo. Un expediente de tendencia aporta decenas de valores. */
const VALORES_RESPALDO_MAXIMOS = 1000;

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
        onClick={() => verificar.mutate({ texto, expediente_ids: seleccion, tolerancia_relativa: 0.005 })}
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
                  title={p.cifra.trazable ? t(`Coincide con ${p.cifra.coincide_con}`, `Matches ${p.cifra.coincide_con}`) : t("Sin respaldo en los expedientes", "Not backed by the case files")}
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
          {verificar.data.valores_permitidos > VALORES_RESPALDO_MAXIMOS && (
            <p role="alert" className="text-[12px]" style={{ color: "var(--warning)" }}>
              {t(
                "Con tantos valores de respaldo, una coincidencia puede ser azar. Verifique contra el expediente que cita el texto.",
                "With this many backing values a match may be chance. Verify against the case file the text cites.",
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
        titulo={t("Asistente", "Assistant")}
        descripcion={t("La IA conversa, pero no calcula: cada número que diga debe estar en un expediente. El verificador que impone esa regla ya funciona; el modelo de lenguaje se conectará sin cambiar el contrato.", "The AI converses but does not compute: every number it says must be in a case file. The verifier that enforces that rule already works; the language model will plug in without changing the contract.")}
      />
      <div className="grid gap-6 xl:grid-cols-2">
        <Conversacion />
        <Verificador />
      </div>
    </div>
  );
}

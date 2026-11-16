/**
 * Asistente flotante (Google Gemini) disponible en todas las páginas.
 *
 * - Botón con el avatar del proyecto abajo a la derecha; abre un panel (pantalla completa en móvil).
 * - Sugerencias según la página: en un expediente ofrece explicarlo usando solo ese expediente.
 * - Cada respuesta muestra sus citas enlazadas y el sello de verificación numérica (plegable).
 * - La conversación se conserva al navegar (sessionStorage, con try/catch: puede no estar disponible).
 */
import { clsx } from "clsx";
import { ChevronDown, Maximize2, Minimize2, RotateCcw, Send, ShieldCheck, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { Link, useLocation } from "react-router-dom";
import { ErrorApi, type Esquemas } from "../api/cliente";
import { useConsultarAsistente, useResumen } from "../api/consultas";
import { t, useIdioma } from "../lib/i18n";
import { SelloRespuesta, TextoConCitas } from "./RespuestaAsistente";
import { traducirTitulo } from "../lib/titulos";

type Respuesta = Esquemas["RespuestaAsistenteSalida"];
type Mensaje = { rol: "persona" | "bot"; texto: string; error?: boolean; respuesta?: Respuesta };

const CLAVE = "tv-chat";
const EVENTO_ABRIR = "terra:abrir";

/** Abre el asistente desde cualquier parte de la interfaz; con `pregunta`, la deja escrita lista para enviar. */
export function abrirTerra(pregunta?: string): void {
  window.dispatchEvent(new CustomEvent<string | undefined>(EVENTO_ABRIR, { detail: pregunta }));
}
const PATRON_EXPEDIENTE = /^\/expedientes\/(TV-[A-Z]{2,4}-[0-9A-F]{12})/;

/** Avatar de "Terra", el detective del proyecto: un satélite-detective con órbita y antena. */
export function AvatarBot({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" className={className} aria-hidden>
      <circle cx="24" cy="25" r="17" fill="#0d366b" />
      <ellipse cx="24" cy="25" rx="21" ry="6.5" fill="none" stroke="#86b6ef" strokeWidth="1.6" transform="rotate(-18 24 25)" opacity="0.85" />
      <rect x="14" y="19" width="20" height="12" rx="6" fill="#e8f1fc" />
      <circle cx="19.5" cy="25" r="2.3" fill="#0d366b" />
      <circle cx="28.5" cy="25" r="2.3" fill="#0d366b" />
      <circle cx="20.2" cy="24.2" r="0.7" fill="#fff" />
      <circle cx="29.2" cy="24.2" r="0.7" fill="#fff" />
      <path d="M24 8v-3" stroke="#86b6ef" strokeWidth="1.8" strokeLinecap="round" />
      <circle cx="24" cy="4.5" r="2.6" fill="#eb6834" />
      <path d="M20 34.5c2.4 1.4 5.6 1.4 8 0" fill="none" stroke="#86b6ef" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

function sugerencias(ruta: string): [string, string][] {
  const tema: Record<string, [string, string][]> = {
    "/sismos": [["¿Hubo más sismos cerca de Arequipa con los años?", "Have earthquakes near Arequipa increased over the years?"], ["¿Se puede pronosticar el número de sismos por mes?", "Can the monthly number of earthquakes be forecast?"]],
    "/volcanes": [["¿Qué volcán del sur del Perú es el más activo?", "Which volcano in southern Peru is the most active?"]],
    "/caos": [["¿La lluvia de la cabecera muestra caos?", "Does headwater rainfall show chaos?"]],
    "/peru": [["¿Qué departamentos tienen tendencias de temperatura confirmadas?", "Which regions have confirmed temperature trends?"]],
    "/relevancia": [["¿Qué variables importan para la lluvia extrema?", "Which variables matter for extreme rain?"]],
    "/metricas": [["¿Qué tan bien se pronostica la sequía a 1 y 3 meses?", "How well is drought forecast at 1 and 3 months?"]],
    "/modelos": [["¿Qué modelo pronostica mejor la sequía?", "Which model forecasts drought best?"]],
  };
  return [...(Object.entries(tema).find(([r]) => ruta.startsWith(r))?.[1] ?? []), ...PREGUNTAS_RAPIDAS].slice(0, 4);
}

/**
 * Preguntas rápidas para quien evalúa: cada premisa está documentada (Aguada Blanca 43 → 22 hm³ en la
 * crónica de eventos; ONI ASO 2026 = +2,46 de NOAA CPC). Al hacer clic se envía la consulta real.
 */
export const PREGUNTAS_RAPIDAS: [string, string][] = [
  ["¿Por qué la represa Aguada Blanca perdió cerca de la mitad de su capacidad?", "Why has Aguada Blanca reservoir lost about half of its storage capacity?"],
  ["¿Puede el ML predecir la lluvia extrema de mañana en los Andes?", "Can ML predict tomorrow's extreme rainfall in the Andes?"],
  ["¿Cómo afecta El Niño (ONI +2,46) al riesgo de sequía esta temporada?", "How does El Niño (ONI +2.46) affect drought risk this season?"],
  ["Muéstrame el intervalo de confianza del 90 % del modelo SPI-3.", "Show me the 90% confidence interval of the SPI-3 model."],
];

function leer(): Mensaje[] {
  try {
    return JSON.parse(sessionStorage.getItem(CLAVE) ?? "[]") as Mensaje[];
  } catch {
    return [];
  }
}

function MensajeBot({ m }: { m: Mensaje }) {
  const [detalle, setDetalle] = useState(false);
  return (
    <div className="flex gap-2">
      <AvatarBot className="mt-0.5 h-7 w-7 shrink-0" />
      <div className={clsx("min-w-0 max-w-[88%] rounded-2xl rounded-tl-md border px-3.5 py-2.5 text-[13.5px] leading-relaxed", m.error ? "border-line bg-surface-2 text-ink-2" : "border-line bg-surface-solida text-ink")}>
        <TextoConCitas texto={m.texto} orden={m.respuesta?.expedientes_citados} />
        {m.respuesta && m.respuesta.expedientes_citados.length > 0 && (
          <ol className="mt-2 space-y-0.5 border-t border-line pt-2 text-[11.5px] text-ink-3">
            {m.respuesta.expedientes_citados.map((id, i) => (
              <li key={id} className="flex gap-1.5">
                <span className="inline-grid h-4 min-w-4 place-items-center rounded-full bg-accent-soft px-1 text-[10px] font-semibold text-accent-ink">{i + 1}</span>
                <Link to={`/expedientes/${id}`} className="truncate hover:text-ink hover:underline">
                  {traducirTitulo(m.respuesta?.expedientes_consultados.find((e) => e.id === id)?.titulo ?? id)}
                </Link>
              </li>
            ))}
          </ol>
        )}
        {m.respuesta && (
          <div className="mt-2">
            <button type="button" onClick={() => setDetalle((d) => !d)} aria-expanded={detalle} className="inline-flex items-center gap-1 text-[12px] font-medium text-accent-ink hover:underline">
              <ShieldCheck aria-hidden className="h-3.5 w-3.5" />
              {m.respuesta.verificacion.aprobado
                ? t(`${m.respuesta.verificacion.cifras.filter((c) => c.trazable).length} cifras verificadas`, `${m.respuesta.verificacion.cifras.filter((c) => c.trazable).length} figures verified`)
                : t("Revisar verificación", "Review verification")}
              <ChevronDown aria-hidden className={clsx("h-3.5 w-3.5 transition-transform", detalle && "rotate-180")} />
            </button>
            {detalle && <SelloRespuesta r={m.respuesta} />}
          </div>
        )}
      </div>
    </div>
  );
}

export function ChatFlotante() {
  useIdioma(); // re-render al cambiar de idioma
  const { pathname } = useLocation();
  const resumen = useResumen();
  const conectado = resumen.data?.asistente_conectado;
  const consultar = useConsultarAsistente();
  const [abierto, setAbierto] = useState(false);
  const [grande, setGrande] = useState(false);
  const [mensajes, setMensajes] = useState<Mensaje[]>(leer);
  const [texto, setTexto] = useState("");
  const fin = useRef<HTMLDivElement>(null);
  const entrada = useRef<HTMLInputElement>(null);
  const expediente = useMemo(() => pathname.match(PATRON_EXPEDIENTE)?.[1], [pathname]);

  useEffect(() => {
    try {
      sessionStorage.setItem(CLAVE, JSON.stringify(mensajes.slice(-30)));
    } catch {
      /* sin almacenamiento: la conversación vive solo en memoria */
    }
    fin.current?.scrollIntoView({ block: "end" });
  }, [mensajes, abierto]);

  useEffect(() => {
    const abrir = (e: Event) => {
      const pregunta = (e as CustomEvent<string | undefined>).detail;
      setAbierto(true);
      if (pregunta) setTexto(pregunta);
    };
    window.addEventListener(EVENTO_ABRIR, abrir);
    return () => window.removeEventListener(EVENTO_ABRIR, abrir);
  }, []);

  useEffect(() => {
    if (abierto) entrada.current?.focus();
    const tecla = (e: KeyboardEvent) => e.key === "Escape" && setAbierto(false);
    window.addEventListener("keydown", tecla);
    return () => window.removeEventListener("keydown", tecla);
  }, [abierto]);

  const enviar = (pregunta: string, ids: string[] = []) => {
    if (!pregunta.trim() || consultar.isPending) return;
    setMensajes((m) => [...m, { rol: "persona", texto: pregunta }]);
    setTexto("");
    consultar.mutate(
      { pregunta, expediente_ids: ids },
      {
        onSuccess: (r) => setMensajes((m) => [...m, { rol: "bot", texto: r.texto, respuesta: r }]),
        onError: (e) =>
          setMensajes((m) => [
            ...m,
            {
              rol: "bot",
              error: true,
              texto:
                e instanceof ErrorApi && e.status === 429
                  ? t("Muchas preguntas seguidas. Espera un minuto y vuelve a intentarlo.", "Too many questions in a row. Wait a minute and try again.")
                  : e instanceof ErrorApi && e.status === 503
                    ? t("El proveedor de IA no respondió a tiempo. No invento respuestas: inténtalo de nuevo en unos segundos.", "The AI provider did not respond in time. I never make answers up: please try again in a few seconds.")
                    : e.message,
            },
          ]),
      },
    );
  };

  const explicarExpediente = () =>
    expediente &&
    enviar(
      t("Explícame este expediente en lenguaje claro: qué muestra, qué tan confiable es y qué no permite concluir.", "Explain this case file in plain language: what it shows, how reliable it is and what it does not allow to conclude."),
      [expediente],
    );

  return (
    <>
      {abierto && (
        <section
          role="dialog"
          aria-label={t("Asistente TerraVerdict", "TerraVerdict assistant")}
          className={clsx(
            "chat-flotante-entrada fixed z-50 flex flex-col overflow-hidden border border-line bg-surface-solida shadow-flotante",
            "inset-0 sm:inset-auto sm:bottom-24 sm:right-5 sm:rounded-2xl",
            grande ? "sm:h-[min(86vh,820px)] sm:w-[min(92vw,720px)]" : "sm:h-[min(78vh,620px)] sm:w-[400px]",
          )}
        >
          <header className="flex items-center gap-3 border-b border-line bg-gradient-to-r from-[#0d366b] to-[#1d5aa6] px-4 py-3 text-white">
            <AvatarBot className="h-9 w-9 shrink-0 rounded-full bg-white/10 p-0.5" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-[14px] font-semibold">Terra · {t("detective de datos", "data detective")}</p>
              <p className="flex items-center gap-1.5 text-[11.5px] text-white/80">
                <span className={clsx("h-1.5 w-1.5 rounded-full", conectado ? "bg-emerald-300" : "bg-amber-300")} />
                {conectado ? t("Gemini · cada cifra verificada", "Gemini · every figure verified") : t("IA no configurada en este despliegue", "AI not configured in this deployment")}
              </p>
            </div>
            {mensajes.length > 0 && (
              <button type="button" onClick={() => setMensajes([])} className="rounded-md p-1.5 text-white/80 hover:bg-white/10 hover:text-white" aria-label={t("Nueva conversación", "New conversation")} title={t("Nueva conversación", "New conversation")}>
                <RotateCcw className="h-4 w-4" />
              </button>
            )}
            <button type="button" onClick={() => setGrande((g) => !g)} className="hidden rounded-md p-1.5 text-white/80 hover:bg-white/10 hover:text-white sm:block" aria-label={grande ? t("Reducir", "Shrink") : t("Ampliar", "Expand")}>
              {grande ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </button>
            <button type="button" onClick={() => setAbierto(false)} className="rounded-md p-1.5 text-white/80 hover:bg-white/10 hover:text-white" aria-label={t("Cerrar asistente", "Close assistant")}>
              <X className="h-4 w-4" />
            </button>
          </header>

          <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4" aria-live="polite">
            {mensajes.length === 0 && (
              <div className="space-y-3">
                <div className="flex gap-2">
                  <AvatarBot className="mt-0.5 h-7 w-7 shrink-0" />
                  <div className="rounded-2xl rounded-tl-md border border-line bg-surface-2 px-3.5 py-2.5 text-[13.5px] leading-relaxed text-ink">
                    {t(
                      "¡Hola! Soy Terra. Respondo sobre lluvia, sequía, sismos, volcanes y deslizamientos en Arequipa y el Perú usando solo los resultados publicados. Cito cada fuente y verifico cada número.",
                      "Hi! I'm Terra. I answer about rain, drought, earthquakes, volcanoes and landslides in Arequipa and Peru using only published results. I cite every source and verify every number.",
                    )}
                    {conectado === false && (
                      <p className="mt-2 text-[12.5px] text-ink-2">
                        {t("En este despliegue falta la clave del proveedor de IA. Mientras tanto, el ", "This deployment is missing the AI provider key. Meanwhile, the ")}
                        <Link to="/asistente" onClick={() => setAbierto(false)} className="font-medium text-accent-ink hover:underline">{t("verificador numérico", "numeric verifier")}</Link>
                        {t(" funciona.", " works.")}
                      </p>
                    )}
                  </div>
                </div>
                {expediente && (
                  <button type="button" onClick={explicarExpediente} disabled={!conectado} className="w-full rounded-xl border border-line bg-accent-soft px-3 py-2 text-left text-[13px] font-medium text-accent-ink hover:brightness-95 disabled:opacity-50">
                    ✨ {t("Explícame este expediente en lenguaje claro", "Explain this case file in plain language")}
                  </button>
                )}
                <div className="flex flex-wrap gap-2">
                  {sugerencias(pathname).map(([es, en]) => (
                    <button key={es} type="button" disabled={!conectado} onClick={() => enviar(t(es, en))} className="rounded-full border border-line px-3 py-1.5 text-left text-[12.5px] text-ink-2 hover:bg-surface-2 hover:text-ink disabled:opacity-50">
                      {t(es, en)}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {mensajes.map((m, i) =>
              m.rol === "persona" ? (
                <div key={i} className="flex justify-end">
                  <p className="max-w-[85%] rounded-2xl rounded-tr-md bg-accent px-3.5 py-2.5 text-[13.5px] leading-relaxed text-white">{m.texto}</p>
                </div>
              ) : (
                <MensajeBot key={i} m={m} />
              ),
            )}
            {consultar.isPending && (
              <div className="flex items-center gap-2 text-[12.5px] text-ink-3">
                <AvatarBot className="h-7 w-7 animate-pulso" />
                {t("Buscando expedientes y verificando cifras…", "Searching case files and verifying figures…")}
              </div>
            )}
            <div ref={fin} />
          </div>

          <form
            onSubmit={(e: FormEvent) => {
              e.preventDefault();
              enviar(texto);
            }}
            className="flex gap-2 border-t border-line p-3"
          >
            <label className="sr-only" htmlFor="chat-pregunta">{t("Pregunta", "Question")}</label>
            <input
              id="chat-pregunta"
              ref={entrada}
              maxLength={2000}
              value={texto}
              disabled={!conectado}
              onChange={(e) => setTexto(e.target.value)}
              placeholder={conectado ? t("Pregunta en español o en inglés…", "Ask in English or Spanish…") : t("Asistente no disponible", "Assistant unavailable")}
              className="h-10 min-w-0 flex-1 rounded-xl border border-line bg-surface-2 px-3 text-sm text-ink disabled:opacity-60"
            />
            <button type="submit" disabled={!texto.trim() || consultar.isPending || !conectado} className="grid h-10 w-10 place-items-center rounded-xl bg-accent text-white disabled:opacity-40" aria-label={t("Enviar", "Send")}>
              <Send className="h-4 w-4" />
            </button>
          </form>
        </section>
      )}

      <button
        type="button"
        onClick={() => setAbierto((a) => !a)}
        aria-expanded={abierto}
        aria-label={abierto ? t("Cerrar asistente", "Close assistant") : t("Abrir asistente Terra", "Open Terra assistant")}
        className={clsx(
          "fixed bottom-5 right-5 z-50 grid h-16 w-16 place-items-center rounded-full bg-surface-solida shadow-flotante ring-2 ring-[#86b6ef]/60 transition-transform hover:scale-105 focus-visible:outline-none focus-visible:ring-4",
          abierto ? "max-sm:hidden" : "bot-flotante",
        )}
      >
        {abierto ? <X className="h-6 w-6 text-ink" /> : <AvatarBot className="h-12 w-12" />}
        {!abierto && conectado && <span className="absolute -right-0.5 -top-0.5 rounded-full bg-[#eb6834] px-1.5 py-0.5 text-[10px] font-bold text-white shadow">IA</span>}
      </button>
    </>
  );
}

/**
 * Recorrido guiado por todo el sistema: resalta cada función real (spotlight), explica en dos frases qué
 * muestra y por qué importa, y navega solo entre páginas. No inventa nada: cada paso apunta a un elemento
 * que existe en la interfaz; si aún no está en pantalla (datos cargando), la tarjeta se muestra centrada.
 * Teclado: ← → para moverse, Esc para salir.
 */
import { clsx } from "clsx";
import { ArrowLeft, ArrowRight, BrainCircuit, Compass, Gauge, Globe2, MapPinned, MessageSquareText, ShieldCheck, Sparkles, Table2, X, type LucideIcon } from "lucide-react";
import { useCallback, useEffect, useLayoutEffect, useRef, useState, type CSSProperties } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { t } from "../lib/i18n";
import { abrirTerra } from "./ChatFlotante";

const EVENTO = "terraverdict:recorrido";
const CLAVE_INVITACION = "terraverdict.recorrido.invitacion";

export function abrirRecorrido(): void {
  window.dispatchEvent(new Event(EVENTO));
}

type Paso = {
  ruta: string;
  selector: string;
  icono: LucideIcon;
  color: string;
  titulo: [string, string];
  texto: [string, string];
};

const PASOS: Paso[] = [
  {
    ruta: "/",
    selector: '[data-tour="hero"]',
    icono: Sparkles,
    color: "from-[#1d63c8] to-[#0ea5b7]",
    titulo: ["Qué resuelve TerraVerdict", "What TerraVerdict solves"],
    texto: [
      "Arequipa pierde agua por sequía y por lluvias extremas. TerraVerdict convierte datos abiertos de NASA en veredictos probados: qué cambia de verdad, qué se puede anticipar y dónde actuar.",
      "Arequipa loses water to drought and to extreme rain. TerraVerdict turns NASA open data into tested verdicts: what is really changing, what can be anticipated, and where to act.",
    ],
  },
  {
    ruta: "/",
    selector: '[data-tour="estado"]',
    icono: Gauge,
    color: "from-[#0ea5b7] to-[#10b981]",
    titulo: ["Cómo estamos hoy", "Where things stand today"],
    texto: [
      "Represas, El Niño y sequía en la cabecera con la fecha de su último dato real. Si una cifra no está al día, la tarjeta lo dice.",
      "Reservoirs, El Niño and headwater drought, each with the date of its latest real observation. If a figure is not current, the card says so.",
    ],
  },
  {
    ruta: "/",
    selector: '[data-tour="veredictos"]',
    icono: Table2,
    color: "from-[#6250d6] to-[#1d63c8]",
    titulo: ["Cinco amenazas, un veredicto cada una", "Five hazards, one verdict each"],
    texto: [
      "Lluvia extrema, sequía, sismos, volcanes y deslizamientos: tendencia, si se puede anticipar y el veredicto. Cuando la evidencia no alcanza, el sistema se abstiene.",
      "Extreme rain, drought, earthquakes, volcanoes and landslides: trend, whether it can be anticipated, and the verdict. When the evidence is insufficient, the system abstains.",
    ],
  },
  {
    ruta: "/mapa",
    selector: '[data-tour="mapa"]',
    icono: Globe2,
    color: "from-[#0d366b] to-[#1d63c8]",
    titulo: ["Mapa satelital 3D de la cuenca", "3D satellite map of the basin"],
    texto: [
      "Capas reales de NASA GIBS (MODIS, SMAP) e imágenes HLS de 30 m, relieve 3D, cortina entre dos fechas y time-lapse mensual del embalse Aguada Blanca.",
      "Real NASA GIBS layers (MODIS, SMAP) and 30 m HLS imagery, 3D terrain, a two-date swipe and a monthly time-lapse of Aguada Blanca reservoir.",
    ],
  },
  {
    ruta: "/modelos",
    selector: '[data-tour="prediccion"]',
    icono: BrainCircuit,
    color: "from-[#eb6834] to-[#e34948]",
    titulo: ["Pronóstico frente a realidad", "Forecast vs reality"],
    texto: [
      "Lo observado (negro), lo pronosticado (azul) y el cono conformal del 90 %, en años que el modelo nunca vio. Así se ve si el pronóstico de sequía sirve de verdad.",
      "Observed (black), forecast (blue) and the 90 % conformal cone, on years the model never saw. This is how you can see whether the drought forecast really works.",
    ],
  },
  {
    ruta: "/peru",
    selector: '[data-tour="peru"]',
    icono: MapPinned,
    color: "from-[#1baf7a] to-[#0ea5b7]",
    titulo: ["El mismo motor para todo el Perú", "The same engine for all of Peru"],
    texto: [
      "Los 25 departamentos con las mismas reglas que Arequipa: tendencias con Sello de Confianza, sequía (SPI) y sismicidad. Agregar una región es configuración, no código nuevo.",
      "All 25 departments under the same rules as Arequipa: trends with a Confidence Seal, drought (SPI) and seismicity. Adding a region is configuration, not new code.",
    ],
  },
  {
    ruta: "/procesos",
    selector: "main h1",
    icono: ShieldCheck,
    color: "from-[#008300] to-[#1baf7a]",
    titulo: ["Auditoría: cada cifra tiene procedencia", "Audit: every number has provenance"],
    texto: [
      "Cada descarga de NASA lleva su hash SHA-256 y cada resultado su commit de código. Cualquiera puede reproducir las cifras.",
      "Every NASA download carries its SHA-256 hash and every result its code commit. Anyone can reproduce the numbers.",
    ],
  },
  {
    ruta: "/",
    selector: '[data-tour="terra"]',
    icono: MessageSquareText,
    color: "from-[#e87ba4] to-[#6250d6]",
    titulo: ["Pregúntele a Terra, la IA verificada", "Ask Terra, the verified AI"],
    texto: [
      "Terra (Google Gemini) responde solo con resultados publicados, cita cada expediente y un verificador comprueba cada cifra y su fuente antes de mostrarla.",
      "Terra (Google Gemini) answers only from published results, cites each case file, and a verifier checks every figure and its source before showing it.",
    ],
  },
];

type Caja = { top: number; left: number; width: number; height: number } | null;
const MARGEN = 8;

function medir(selector: string): Caja {
  const el = document.querySelector(selector);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  if (r.width === 0 && r.height === 0) return null;
  // Elementos más altos que la pantalla (el mapa): se resalta la parte visible.
  const top = Math.max(r.top, 0);
  const bottom = Math.min(r.bottom, window.innerHeight);
  if (bottom <= 0 || top >= window.innerHeight) return null; // fuera de pantalla: tarjeta centrada
  return { top: top - MARGEN, left: r.left - MARGEN, width: r.width + 2 * MARGEN, height: Math.max(bottom - top, 40) + 2 * MARGEN };
}

export function Recorrido() {
  const [indice, setIndice] = useState<number | null>(null);
  const [caja, setCaja] = useState<Caja>(null);
  const navegar = useNavigate();
  const { pathname } = useLocation();
  const siguienteRef = useRef<HTMLButtonElement>(null);
  const paso = indice === null ? null : PASOS[indice];

  const cerrar = useCallback(() => {
    setIndice(null);
    setCaja(null);
  }, []);

  useEffect(() => {
    const abrir = () => setIndice(0);
    window.addEventListener(EVENTO, abrir);
    return () => window.removeEventListener(EVENTO, abrir);
  }, []);

  // Cada paso lleva a su página y espera a que su elemento exista (los datos pueden tardar en llegar).
  useEffect(() => {
    if (!paso) return;
    if (pathname !== paso.ruta) {
      window.scrollTo({ top: 0, behavior: "auto" });
      navegar(paso.ruta);
      return;
    }
    let vivo = true;
    let intentos = 0;
    const buscar = () => {
      if (!vivo) return;
      const el = document.querySelector(paso.selector);
      if (el) {
        const r = el.getBoundingClientRect();
        // Desplazamiento instantáneo: el suave depende de cuadros de animación que el navegador puede pausar.
        const fijo = getComputedStyle(el).position === "fixed";
        if (!fijo && (r.top < 70 || r.bottom > window.innerHeight - 220)) {
          const destino = r.height > window.innerHeight * 0.6 ? r.top + window.scrollY - 80 : r.top + window.scrollY - (window.innerHeight - r.height) / 2 + 100;
          window.scrollTo({ top: Math.max(0, destino), behavior: "auto" });
        }
        window.setTimeout(() => vivo && setCaja(medir(paso.selector)), 120);
      } else if (intentos++ < 40) {
        window.setTimeout(buscar, 150);
      } else {
        setCaja(null);
      }
    };
    setCaja(null);
    buscar();
    return () => {
      vivo = false;
    };
  }, [paso, pathname, navegar]);

  useEffect(() => {
    if (!paso) return;
    const actualizar = () => setCaja(medir(paso.selector));
    window.addEventListener("resize", actualizar);
    window.addEventListener("scroll", actualizar, true);
    return () => {
      window.removeEventListener("resize", actualizar);
      window.removeEventListener("scroll", actualizar, true);
    };
  }, [paso]);

  useEffect(() => {
    if (indice === null) return;
    const tecla = (e: KeyboardEvent) => {
      if (e.key === "Escape") cerrar();
      if (e.key === "ArrowRight") setIndice((i) => (i !== null && i < PASOS.length - 1 ? i + 1 : i));
      if (e.key === "ArrowLeft") setIndice((i) => (i !== null && i > 0 ? i - 1 : i));
    };
    window.addEventListener("keydown", tecla);
    return () => window.removeEventListener("keydown", tecla);
  }, [indice, cerrar]);

  useLayoutEffect(() => {
    if (indice !== null) siguienteRef.current?.focus({ preventScroll: true });
  }, [indice]);

  if (!paso || indice === null) return null;
  const Icono = paso.icono;
  const ultimo = indice === PASOS.length - 1;
  const ancho = Math.min(380, window.innerWidth - 32);
  // La tarjeta va debajo del elemento si cabe; si no, encima; si no hay elemento, al centro.
  let estilo: CSSProperties = { left: "50%", top: "50%", transform: "translate(-50%, -50%)", width: ancho };
  if (caja) {
    const izquierda = Math.min(Math.max(caja.left, 16), window.innerWidth - ancho - 16);
    const abajo = caja.top + caja.height + 12;
    if (abajo + 240 < window.innerHeight) estilo = { left: izquierda, top: abajo, width: ancho };
    else if (caja.top - 252 > 0) estilo = { left: izquierda, top: caja.top - 252, width: ancho };
    else estilo = { left: Math.max(16, window.innerWidth - ancho - 24), bottom: 24, width: ancho };
  }

  return (
    <div className="fixed inset-0 z-[70]" aria-live="polite">
      {/* Fondo atenuado con un hueco sobre el elemento resaltado. */}
      {caja ? (
        <div
          aria-hidden
          className="recorrido-foco pointer-events-none fixed rounded-2xl ring-2 ring-[#86b6ef] transition-all duration-300"
          style={{ top: caja.top, left: caja.left, width: caja.width, height: caja.height, boxShadow: "0 0 0 9999px rgba(3, 10, 25, 0.62)" }}
        />
      ) : (
        <div aria-hidden className="fixed inset-0 bg-[rgba(3,10,25,0.62)]" />
      )}
      <div className="fixed inset-0" onClick={cerrar} aria-hidden />
      <div role="dialog" aria-modal="true" aria-labelledby="recorrido-titulo" className="fixed overflow-hidden rounded-2xl border border-white/15 bg-surface-solida shadow-flotante" style={estilo}>
        <div className={clsx("flex items-center justify-between gap-3 bg-gradient-to-r px-4 py-3 text-white", paso.color)}>
          <span className="flex items-center gap-2 text-[12px] font-semibold uppercase tracking-wider">
            <Icono className="h-4 w-4" aria-hidden /> {t(`Recorrido · paso ${indice + 1} de ${PASOS.length}`, `Guided tour · step ${indice + 1} of ${PASOS.length}`)}
          </span>
          <button type="button" onClick={cerrar} className="rounded-md p-1 text-white/85 hover:bg-white/15 hover:text-white" aria-label={t("Salir del recorrido", "Exit the tour")}>
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="px-4 pb-4 pt-3">
          <h2 id="recorrido-titulo" className="text-[16.5px] font-semibold leading-snug text-ink">{t(...paso.titulo)}</h2>
          <p className="mt-1.5 text-[13.5px] leading-relaxed text-ink-2">{t(...paso.texto)}</p>
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
            <div className="flex gap-1.5" aria-hidden>
              {PASOS.map((_, i) => (
                <span key={i} className={clsx("h-1.5 rounded-full transition-all", i === indice ? "w-5 bg-accent" : i < indice ? "w-1.5 bg-accent/60" : "w-1.5 bg-ink-3/30")} />
              ))}
            </div>
            <div className="ml-auto flex gap-2 whitespace-nowrap">
              {indice > 0 && (
                <button type="button" onClick={() => setIndice(indice - 1)} className="inline-flex items-center gap-1 rounded-lg border border-line px-3 py-1.5 text-[13px] font-medium text-ink-2 hover:bg-surface-2">
                  <ArrowLeft className="h-3.5 w-3.5" aria-hidden /> {t("Atrás", "Back")}
                </button>
              )}
              {ultimo && (
                <button type="button" onClick={cerrar} className="rounded-lg border border-line px-3 py-1.5 text-[13px] font-medium text-ink-2 hover:bg-surface-2">
                  {t("Terminar", "Finish")}
                </button>
              )}
              <button
                ref={siguienteRef}
                type="button"
                onClick={() => {
                  if (!ultimo) return setIndice(indice + 1);
                  cerrar();
                  abrirTerra();
                }}
                className={clsx("inline-flex items-center gap-1 rounded-lg bg-gradient-to-r px-3.5 py-1.5 text-[13px] font-semibold text-white shadow hover:brightness-110", paso.color)}
              >
                {ultimo ? t("Preguntar a Terra", "Ask Terra now") : t("Siguiente", "Next")} <ArrowRight className="h-3.5 w-3.5" aria-hidden />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Invitación discreta en la primera visita (no bloquea nada): se cierra con un clic y no vuelve a salir.
 */
export function InvitacionRecorrido() {
  const [visible, setVisible] = useState(() => {
    try {
      return localStorage.getItem(CLAVE_INVITACION) !== "vista";
    } catch {
      return true;
    }
  });
  const descartar = () => {
    setVisible(false);
    try {
      localStorage.setItem(CLAVE_INVITACION, "vista");
    } catch {
      /* sin almacenamiento: solo se oculta en esta visita */
    }
  };
  useEffect(() => {
    window.addEventListener(EVENTO, descartar);
    return () => window.removeEventListener(EVENTO, descartar);
  }, []);
  if (!visible) return null;
  return (
    <div className="fixed bottom-24 left-4 z-[60] w-[min(92vw,340px)] lg:bottom-5 overflow-hidden rounded-2xl border border-white/15 bg-surface-solida shadow-flotante animate-aparecer lg:left-[296px]">
      <div className="h-1 bg-gradient-to-r from-[#1d63c8] via-[#0ea5b7] to-[#eb6834]" />
      <div className="flex gap-3 p-4">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-[#1d63c8] to-[#0ea5b7] text-white"><Compass className="h-5 w-5" aria-hidden /></span>
        <div className="min-w-0 flex-1">
          <p className="text-[14px] font-semibold text-ink">{t("¿Primera vez aquí?", "First time here?")}</p>
          <p className="mt-0.5 text-[12.5px] leading-relaxed text-ink-2">{t("Un recorrido de 8 pasos por las funciones clave, en unos 90 segundos.", "An 8-step tour of the key features, in about 90 seconds.")}</p>
          <div className="mt-3 flex gap-2">
            <button type="button" onClick={() => { descartar(); abrirRecorrido(); }} className="rounded-lg bg-gradient-to-r from-[#1d63c8] to-[#0ea5b7] px-3 py-1.5 text-[13px] font-semibold text-white shadow hover:brightness-110">
              {t("Iniciar recorrido", "Start the tour")}
            </button>
            <button type="button" onClick={descartar} className="rounded-lg px-3 py-1.5 text-[13px] font-medium text-ink-2 hover:bg-surface-2">{t("Ahora no", "Not now")}</button>
          </div>
        </div>
      </div>
    </div>
  );
}

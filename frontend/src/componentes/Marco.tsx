import { clsx } from "clsx";
import { Activity, BookOpenText, Bot, BrainCircuit, CalendarClock, ChartColumnBig, FileCheck2, Globe2, Grid3x3, Info, Layers3, LayoutDashboard, LineChart, LogIn, LogOut, MapPinned, Menu, Monitor, Moon, Mountain, Orbit, Satellite, Sun, Workflow, X, type LucideIcon } from "lucide-react";
import { useState, type FormEvent, type ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { ErrorApi } from "../api/cliente";
import { useResumen, useSalud } from "../api/consultas";
import { useSesion } from "../lib/sesion";
import { t, useIdioma, type Idioma } from "../lib/i18n";
import { useTema, type Tema } from "../lib/tema";
import { Dialogo } from "./Dialogo";
import { Boton, Insignia, Segmentado } from "./ui";

const NAVEGACION: { grupo: [string, string]; items: { a: string; texto: [string, string]; icono: LucideIcon }[] }[] = [
  {
    grupo: ["Explorar", "Explore"],
    items: [
      { a: "/", texto: ["Panel", "Dashboard"], icono: LayoutDashboard },
      { a: "/mapa", texto: ["Mapa satelital", "Satellite map"], icono: Globe2 },
      { a: "/series", texto: ["Series", "Time series"], icono: LineChart },
      { a: "/expedientes", texto: ["Expedientes", "Case files"], icono: FileCheck2 },
    ],
  },
  {
    grupo: ["Fenómenos naturales", "Natural hazards"],
    items: [
      { a: "/peru", texto: ["Perú: escala nacional", "Peru: national scale"], icono: MapPinned },
      { a: "/fenomenos", texto: ["Catálogo de fenómenos", "Hazard catalog"], icono: Layers3 },
      { a: "/sismos", texto: ["Sismos", "Earthquakes"], icono: Activity },
      { a: "/volcanes", texto: ["Volcanes", "Volcanoes"], icono: Mountain },
      { a: "/caos", texto: ["Dinámica y caos", "Dynamics & chaos"], icono: Orbit },
      { a: "/modelos", texto: ["Modelos", "Models"], icono: BrainCircuit },
      { a: "/metricas", texto: ["Métricas e historial", "Metrics & history"], icono: ChartColumnBig },
    ],
  },
  {
    grupo: ["Ciencia de datos", "Data science"],
    items: [
      { a: "/relevancia", texto: ["Matriz de relevancia", "Relevance matrix"], icono: Grid3x3 },
      { a: "/procesos", texto: ["Procesos", "Pipeline jobs"], icono: Workflow },
    ],
  },
  {
    grupo: ["Evidencia", "Evidence"],
    items: [
      { a: "/fuentes", texto: ["Fuentes verificadas", "Verified sources"], icono: Satellite },
      { a: "/eventos", texto: ["Crónica de eventos", "Event chronicle"], icono: CalendarClock },
      { a: "/asistente", texto: ["Asistente", "Assistant"], icono: Bot },
    ],
  },
];

function Marca() {
  return (
    <div className="flex items-center gap-2.5">
      <svg viewBox="0 0 32 32" className="h-8 w-8 shrink-0" aria-hidden>
        <rect width="32" height="32" rx="9" fill="#0d366b" />
        <circle cx="16" cy="17" r="7.5" fill="none" stroke="#86b6ef" strokeWidth="2" />
        <path d="M8.5 17c3-2.6 12-2.6 15 0" fill="none" stroke="#86b6ef" strokeWidth="1.6" />
        <circle cx="23.5" cy="8.5" r="2.5" fill="#eb6834" />
      </svg>
      <div className="leading-tight">
        <p className="text-[15px] font-semibold tracking-tight text-ink">TerraVerdict</p>
        <p className="text-[11px] text-ink-3">{t("Arequipa → Perú · amenazas naturales", "Arequipa → Peru · natural hazards")}</p>
      </div>
    </div>
  );
}

function EstadoApi() {
  const salud = useSalud();
  const resumen = useResumen();
  const enLinea = salud.isSuccess;
  return (
    <div className="flex items-center justify-between rounded-lg border border-line bg-surface-2 px-3 py-2 text-[12px]">
      <span className="flex items-center gap-2 text-ink-2">
        <span className="relative flex h-2 w-2">
          {enLinea && <span className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-40" style={{ background: "var(--good)" }} />}
          <span className="relative inline-flex h-2 w-2 rounded-full" style={{ background: enLinea ? "var(--good)" : "var(--critical)" }} />
        </span>
        {salud.isLoading ? t("Conectando…", "Connecting…") : enLinea ? t("API en línea", "API online") : t("API sin conexión", "API offline")}
      </span>
      <span className="font-mono text-ink-3">v{resumen.data?.version_api ?? "—"}</span>
    </div>
  );
}

function SelectorIdioma() {
  const { idioma, cambiar } = useIdioma();
  return (
    <Segmentado<Idioma>
      etiqueta={t("Idioma", "Language")}
      valor={idioma}
      alCambiar={cambiar}
      opciones={[
        { valor: "es", texto: "ES", titulo: "Español" },
        { valor: "en", texto: "EN", titulo: "English" },
      ]}
    />
  );
}

function SelectorTema() {
  const { tema, cambiar } = useTema();
  return (
    <Segmentado<Tema>
      etiqueta={t("Tema de color", "Color theme")}
      valor={tema}
      alCambiar={cambiar}
      opciones={[
        { valor: "light", texto: <Sun className="h-3.5 w-3.5" />, titulo: t("Claro", "Light") },
        { valor: "sistema", texto: <Monitor className="h-3.5 w-3.5" />, titulo: t("Sistema", "System") },
        { valor: "dark", texto: <Moon className="h-3.5 w-3.5" />, titulo: t("Oscuro", "Dark") },
      ]}
    />
  );
}

function Acceso() {
  const { identidad, iniciar, cerrar } = useSesion();
  const [abierto, setAbierto] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const enviar = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const datos = new FormData(e.currentTarget);
    setEnviando(true);
    setError(null);
    try {
      await iniciar(String(datos.get("email")), String(datos.get("contrasena")));
      setAbierto(false);
    } catch (err) {
      setError(err instanceof ErrorApi ? err.message : t("No se pudo iniciar sesión.", "Sign-in failed."));
    } finally {
      setEnviando(false);
    }
  };

  if (identidad) {
    return (
      <div className="flex items-center justify-between gap-2 rounded-lg border border-line px-3 py-2">
        <div className="min-w-0">
          <p className="truncate text-[12.5px] font-medium text-ink">{identidad.nombre}</p>
          <p className="text-[11px] capitalize text-ink-3">{identidad.rol ?? identidad.tipo}</p>
        </div>
        <button type="button" onClick={cerrar} className="rounded-md p-1.5 text-ink-3 hover:bg-surface-2 hover:text-ink" aria-label={t("Cerrar sesión", "Sign out")} title={t("Cerrar sesión", "Sign out")}>
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    );
  }
  return (
    <>
      <Boton icono={LogIn} className="w-full" onClick={() => setAbierto(true)}>
        {t("Iniciar sesión", "Sign in")}
      </Boton>
      <Dialogo abierto={abierto} alCerrar={() => setAbierto(false)} titulo={t("Iniciar sesión", "Sign in")}>
        <form onSubmit={enviar} className="space-y-3">
          <p className="text-[13px] text-ink-2">
            {t("La lectura es pública. Inicie sesión para solicitar procesos (rol analista) o administrar el sistema.", "Reading is public. Sign in to request pipeline jobs (analyst role) or administer the system.")}
          </p>
          <label className="block text-[13px] font-medium">
            {t("Correo", "Email")}
            <input name="email" type="email" required autoComplete="username" className="mt-1 h-10 w-full rounded-lg border border-line bg-surface-2 px-3 text-sm outline-none focus:border-accent" />
          </label>
          <label className="block text-[13px] font-medium">
            {t("Contraseña", "Password")}
            <input name="contrasena" type="password" required autoComplete="current-password" className="mt-1 h-10 w-full rounded-lg border border-line bg-surface-2 px-3 text-sm outline-none focus:border-accent" />
          </label>
          {error && <p role="alert" className="text-[13px]" style={{ color: "var(--critical)" }}>{error}</p>}
          <Boton type="submit" variante="primario" className="w-full" disabled={enviando}>
            {enviando ? t("Verificando…", "Verifying…") : t("Entrar", "Sign in")}
          </Boton>
        </form>
      </Dialogo>
    </>
  );
}

function Navegacion({ alNavegar }: { alNavegar?: () => void }) {
  return (
    <nav aria-label={t("Principal", "Main")} className="space-y-5">
      {NAVEGACION.map((g) => (
        <div key={g.grupo[0]}>
          <p className="etiqueta mb-1.5 px-3">{t(...g.grupo)}</p>
          <ul className="space-y-0.5">
            {g.items.map((i) => (
              <li key={i.a}>
                <NavLink
                  to={i.a}
                  end={i.a === "/"}
                  onClick={alNavegar}
                  className={({ isActive }) =>
                    clsx(
                      "flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13.5px] font-medium transition-colors",
                      isActive ? "bg-accent-soft text-accent-ink" : "text-ink-2 hover:bg-surface-2 hover:text-ink",
                    )
                  }
                >
                  <i.icono aria-hidden className="h-4 w-4" />
                  {t(...i.texto)}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  );
}

function PieLateral() {
  return (
    <div className="space-y-2.5">
      <EstadoApi />
      <div className="flex items-center justify-between">
        <SelectorTema />
        <SelectorIdioma />
        <a href="/api/docs" target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[12px] font-medium text-ink-2 hover:bg-surface-2 hover:text-ink">
          <BookOpenText className="h-3.5 w-3.5" /> API
        </a>
      </div>
      <Acceso />
    </div>
  );
}

export function Marco({ children }: { children: ReactNode }) {
  const [menu, setMenu] = useState(false);
  const { pathname } = useLocation();
  const esMapa = pathname.startsWith("/mapa");
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[264px_1fr]">
      <aside className="panel-vidrio sticky top-0 hidden h-screen flex-col justify-between !border-y-0 !border-l-0 px-3 py-4 lg:flex">
        <div className="space-y-6 overflow-y-auto">
          <div className="px-2"><Marca /></div>
          <Navegacion />
        </div>
        <PieLateral />
      </aside>

      <header className="vidrio sticky top-0 z-30 flex items-center justify-between border-b border-line px-4 py-3 lg:hidden">
        <Marca />
        <button type="button" onClick={() => setMenu(true)} className="rounded-lg p-2 text-ink-2 hover:bg-surface-2" aria-label={t("Abrir menú", "Open menu")}>
          <Menu className="h-5 w-5" />
        </button>
      </header>
      {menu && (
        <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true" aria-label={t("Menú", "Menu")}>
          <div className="absolute inset-0 bg-black/40" onClick={() => setMenu(false)} />
          <div className="absolute inset-y-0 left-0 flex w-[280px] flex-col justify-between overflow-y-auto bg-surface-solida p-4 shadow-flotante">
            <div className="space-y-6">
              <div className="flex items-center justify-between"><Marca />
                <button type="button" onClick={() => setMenu(false)} className="rounded-lg p-2 text-ink-2 hover:bg-surface-2" aria-label={t("Cerrar menú", "Close menu")}><X className="h-5 w-5" /></button>
              </div>
              <Navegacion alNavegar={() => setMenu(false)} />
            </div>
            <PieLateral />
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-col">
        <AvisoNoOficial />
        <main className={clsx(esMapa ? "h-[calc(100vh-57px-36px)] lg:h-[calc(100vh-36px)]" : "mx-auto w-full max-w-[1280px] px-4 py-6 md:px-8 md:py-10")}>
          {children}
        </main>
      </div>
    </div>
  );
}

/** Aviso permanente en todas las vistas: nada de lo que muestra el sistema es una alerta oficial. */
export function AvisoNoOficial() {
  return (
    <p
      role="note"
      className="vidrio flex min-h-9 items-center justify-center gap-2 border-b border-line px-4 py-1.5 text-center text-[12.5px] font-medium text-ink-2"
    >
      <Info aria-hidden className="h-3.5 w-3.5 shrink-0 text-accent" />
      {t("Resultados experimentales. No son alertas oficiales (SENAMHI, IGP, INGEMMET, INDECI).", "Experimental results. Not official warnings (SENAMHI, IGP, INGEMMET, INDECI).")}
    </p>
  );
}

export function AvisoDatosReales({ children }: { children?: ReactNode }) {
  return (
    <Insignia tono="good" className="!rounded-md">
      {children ?? t("Solo datos reales verificados", "Verified real data only")}
    </Insignia>
  );
}

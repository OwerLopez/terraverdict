import { clsx } from "clsx";
import {
  BookOpenText,
  Bot,
  CalendarClock,
  FileCheck2,
  Globe2,
  Grid3x3,
  LayoutDashboard,
  LineChart,
  LogIn,
  LogOut,
  Menu,
  Monitor,
  Moon,
  Satellite,
  Sun,
  Workflow,
  X,
  type LucideIcon,
} from "lucide-react";
import { useState, type FormEvent, type ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { ErrorApi } from "../api/cliente";
import { useResumen, useSalud } from "../api/consultas";
import { useSesion } from "../lib/sesion";
import { useTema, type Tema } from "../lib/tema";
import { Dialogo } from "./Dialogo";
import { Boton, Insignia, Segmentado } from "./ui";

const NAVEGACION: { grupo: string; items: { a: string; texto: string; icono: LucideIcon }[] }[] = [
  {
    grupo: "Explorar",
    items: [
      { a: "/", texto: "Panel", icono: LayoutDashboard },
      { a: "/mapa", texto: "Mapa satelital", icono: Globe2 },
      { a: "/series", texto: "Series", icono: LineChart },
      { a: "/expedientes", texto: "Expedientes", icono: FileCheck2 },
    ],
  },
  {
    grupo: "Ciencia de datos",
    items: [
      { a: "/relevancia", texto: "Matriz de relevancia", icono: Grid3x3 },
      { a: "/procesos", texto: "Procesos", icono: Workflow },
    ],
  },
  {
    grupo: "Evidencia",
    items: [
      { a: "/fuentes", texto: "Fuentes verificadas", icono: Satellite },
      { a: "/eventos", texto: "Crónica de eventos", icono: CalendarClock },
      { a: "/asistente", texto: "Asistente", icono: Bot },
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
        <p className="text-[11px] text-ink-3">Cuenca del Chili · Arequipa</p>
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
        {salud.isLoading ? "Conectando…" : enLinea ? "API en línea" : "API sin conexión"}
      </span>
      <span className="font-mono text-ink-3">v{resumen.data?.version_api ?? "—"}</span>
    </div>
  );
}

function SelectorTema() {
  const { tema, cambiar } = useTema();
  return (
    <Segmentado<Tema>
      etiqueta="Tema de color"
      valor={tema}
      alCambiar={cambiar}
      opciones={[
        { valor: "light", texto: <Sun className="h-3.5 w-3.5" />, titulo: "Claro" },
        { valor: "sistema", texto: <Monitor className="h-3.5 w-3.5" />, titulo: "Sistema" },
        { valor: "dark", texto: <Moon className="h-3.5 w-3.5" />, titulo: "Oscuro" },
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
      setError(err instanceof ErrorApi ? err.message : "No se pudo iniciar sesión.");
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
        <button type="button" onClick={cerrar} className="rounded-md p-1.5 text-ink-3 hover:bg-surface-2 hover:text-ink" aria-label="Cerrar sesión" title="Cerrar sesión">
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    );
  }
  return (
    <>
      <Boton icono={LogIn} className="w-full" onClick={() => setAbierto(true)}>
        Iniciar sesión
      </Boton>
      <Dialogo abierto={abierto} alCerrar={() => setAbierto(false)} titulo="Iniciar sesión">
        <form onSubmit={enviar} className="space-y-3">
          <p className="text-[13px] text-ink-2">
            La lectura es pública. Inicie sesión para solicitar procesos (rol analista) o administrar el sistema.
          </p>
          <label className="block text-[13px] font-medium">
            Correo
            <input name="email" type="email" required autoComplete="username" className="mt-1 h-10 w-full rounded-lg border border-line bg-surface-2 px-3 text-sm outline-none focus:border-accent" />
          </label>
          <label className="block text-[13px] font-medium">
            Contraseña
            <input name="contrasena" type="password" required autoComplete="current-password" className="mt-1 h-10 w-full rounded-lg border border-line bg-surface-2 px-3 text-sm outline-none focus:border-accent" />
          </label>
          {error && <p role="alert" className="text-[13px]" style={{ color: "var(--critical)" }}>{error}</p>}
          <Boton type="submit" variante="primario" className="w-full" disabled={enviando}>
            {enviando ? "Verificando…" : "Entrar"}
          </Boton>
        </form>
      </Dialogo>
    </>
  );
}

function Navegacion({ alNavegar }: { alNavegar?: () => void }) {
  return (
    <nav aria-label="Principal" className="space-y-5">
      {NAVEGACION.map((g) => (
        <div key={g.grupo}>
          <p className="etiqueta mb-1.5 px-3">{g.grupo}</p>
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
                  {i.texto}
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
      <aside className="sticky top-0 hidden h-screen flex-col justify-between border-r border-line bg-surface px-3 py-4 lg:flex">
        <div className="space-y-6 overflow-y-auto">
          <div className="px-2"><Marca /></div>
          <Navegacion />
        </div>
        <PieLateral />
      </aside>

      <header className="vidrio sticky top-0 z-30 flex items-center justify-between border-b border-line px-4 py-3 lg:hidden">
        <Marca />
        <button type="button" onClick={() => setMenu(true)} className="rounded-lg p-2 text-ink-2 hover:bg-surface-2" aria-label="Abrir menú">
          <Menu className="h-5 w-5" />
        </button>
      </header>
      {menu && (
        <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true" aria-label="Menú">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMenu(false)} />
          <div className="absolute inset-y-0 left-0 flex w-[280px] flex-col justify-between overflow-y-auto bg-surface p-4 shadow-flotante">
            <div className="space-y-6">
              <div className="flex items-center justify-between"><Marca />
                <button type="button" onClick={() => setMenu(false)} className="rounded-lg p-2 text-ink-2 hover:bg-surface-2" aria-label="Cerrar menú"><X className="h-5 w-5" /></button>
              </div>
              <Navegacion alNavegar={() => setMenu(false)} />
            </div>
            <PieLateral />
          </div>
        </div>
      )}

      <main className={clsx(esMapa ? "h-[calc(100vh-57px)] lg:h-screen" : "mx-auto w-full max-w-[1280px] px-4 py-6 md:px-8 md:py-10")}>
        {children}
      </main>
    </div>
  );
}

export function AvisoDatosReales({ children }: { children?: ReactNode }) {
  return (
    <Insignia tono="good" className="!rounded-md">
      {children ?? "Solo datos reales verificados"}
    </Insignia>
  );
}

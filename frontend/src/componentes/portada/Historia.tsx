/**
 * Modo historia: el corte de agua de febrero de 2025 en tres actos, solo con evidencia citada o calculada.
 *
 * - Acto 1: la crisis (crónica de eventos con sus fuentes).
 * - Acto 2: lo que muestran los datos (imágenes HLS reales del embalse y desempeño del modelo de lluvia en
 *   ese mes, calculado por el pipeline).
 * - Acto 3: la decisión: qué respalda la evidencia y qué falta (sin inventar quebradas ni causas).
 */
import { ArrowLeft, ArrowRight, Clapperboard, ExternalLink } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { useEventos } from "../../api/consultas";
import { cifraCitada, numero } from "../../lib/formato";
import type { EventoLluvia } from "../../lib/indicadores";
import { t } from "../../lib/i18n";
import { imagenDelMes } from "../../lib/timelapse";
import { Dialogo } from "../Dialogo";
import { Boton } from "../ui";

function Imagen({ mes, pie }: { mes: string; pie: string }) {
  const img = imagenDelMes(mes);
  if (!img) return <div className="grid aspect-square place-items-center rounded-xl bg-surface-2 text-[12px] text-ink-3">{t("Sin imagen válida ese mes", "No valid image that month")}</div>;
  return (
    <figure>
      <img src={img.url} alt={`Aguada Blanca · ${img.sensor} · ${img.fecha}`} className="aspect-square w-full rounded-xl object-cover" loading="lazy" />
      <figcaption className="mt-1 text-[11.5px] text-ink-3">{pie} · {img.sensor} · {img.fecha}</figcaption>
    </figure>
  );
}

export function ModoHistoria({ lluvia }: { lluvia: EventoLluvia[] }) {
  const [abierto, setAbierto] = useState(false);
  const [acto, setActo] = useState(0);
  const eventos = useEventos();
  const porId = new Map((eventos.data ?? []).map((e) => [e.id, e]));
  const corte = porId.get("2025-02-corte-turbidez");
  const segundo = porId.get("2025-02-segundo-episodio");
  const merese = porId.get("2024-04-merese-sedapar");
  const colmatacion = porId.get("2024-03-colmatacion-aguada-blanca");
  const feb = lluvia.find((e) => e.evento === "2025-02-corte-turbidez");

  const actos = [
    {
      titulo: t("Acto 1 · La crisis", "Act 1 · The crisis"),
      cuerpo: corte && (
        <div className="space-y-3">
          <p className="cifra text-[40px] font-semibold leading-none text-ink">{cifraCitada(corte.cifras[0]!)}</p>
          <p className="text-[14px] text-ink">{t(corte.titulo, corte.titulo_en ?? corte.titulo)}</p>
          <p className="text-[13px] leading-relaxed text-ink-2">{t(corte.descripcion, corte.descripcion_en ?? corte.descripcion)}</p>
          {segundo && <p className="text-[13px] text-ink-2">{t(segundo.titulo, segundo.titulo_en ?? segundo.titulo)} ({segundo.fecha}).</p>}
          <div className="flex flex-wrap gap-3 text-[12px]">
            {corte.fuentes.map((f) => (
              <a key={f.url} href={f.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-accent-ink hover:underline"><ExternalLink className="h-3 w-3" /> {f.medio ?? f.titulo}</a>
            ))}
          </div>
        </div>
      ),
    },
    {
      titulo: t("Acto 2 · Lo que muestran los datos de NASA", "Act 2 · What the NASA data show"),
      cuerpo: (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Imagen mes="2023-11" pie={t("Almacenamiento bajo", "Low storage")} />
            <Imagen mes="2025-02" pie={t("Episodio de turbidez", "Turbidity episode")} />
          </div>
          <p className="text-[12.5px] leading-relaxed text-ink-2">
            {t(
              "Imágenes HLS de 30 m (NASA; Sentinel-2 de ESA/Copernicus y Landsat). En feb-2025 el embalse se ve pardo claro, compatible con agua cargada de sedimentos; en nov-2023, verde azulado. Es color de superficie, no una medición de turbidez.",
              "30 m HLS imagery (NASA; ESA/Copernicus Sentinel-2 and Landsat). In Feb 2025 the reservoir looks light brown, consistent with sediment-laden water; in Nov 2023, blue-green. This is surface colour, not a turbidity measurement.",
            )}
          </p>
          {feb && (
            <p className="rounded-xl bg-surface-2 p-3 text-[13px] leading-relaxed text-ink">
              {t(
                `Lluvia en la cabecera (NASA POWER): ${feb.dias_lluvia_fuerte_observados} días de lluvia fuerte en feb-2025. En esos días el modelo daba en promedio ${numero((feb.probabilidad_media_modelo_en_dias_fuertes ?? 0) * 100, 0)} % de probabilidad, frente a ${numero((feb.probabilidad_media_climatologia_en_dias_fuertes ?? 0) * 100, 0)} % de la climatología y ${numero((feb.probabilidad_media_modelo_resto ?? 0) * 100, 0)} % en los demás días del mes.`,
                `Headwater rain (NASA POWER): ${feb.dias_lluvia_fuerte_observados} heavy-rain days in Feb 2025. On those days the model gave on average ${numero((feb.probabilidad_media_modelo_en_dias_fuertes ?? 0) * 100, 0)} % probability, vs ${numero((feb.probabilidad_media_climatologia_en_dias_fuertes ?? 0) * 100, 0)} % for climatology and ${numero((feb.probabilidad_media_modelo_resto ?? 0) * 100, 0)} % on the other days of the month.`,
              )}
              <span className="mt-1 block text-[11.5px] text-ink-3">{t("Evaluación fuera de muestra (prueba 2021–2026). IMERG se usa en la Matriz de Relevancia (M1), no en este modelo.", "Out-of-sample evaluation (2021–2026 test). IMERG is used in the Relevance Matrix (M1), not in this model.")}</span>
            </p>
          )}
        </div>
      ),
    },
    {
      titulo: t("Acto 3 · La decisión", "Act 3 · The decision"),
      cuerpo: (
        <div className="space-y-3 text-[13px] leading-relaxed text-ink-2">
          <p className="text-ink">
            {t(
              "Lo que la evidencia respalda: los cortes coinciden con días de lluvia fuerte en la cabecera que el modelo marcó con probabilidad muy por encima de la climatología, y el embalse cambió de color de forma visible.",
              "What the evidence supports: the outages coincide with heavy-rain days in the headwaters that the model flagged with probability well above climatology, and the reservoir visibly changed colour.",
            )}
          </p>
          {colmatacion && (
            <p>
              {t("Contexto citado:", "Cited context:")} {t(colmatacion.titulo, colmatacion.titulo_en ?? colmatacion.titulo)} ({colmatacion.cifras.map((c) => cifraCitada(c)).join(" → ")}).
            </p>
          )}
          {merese && <p>{t("Instrumento de inversión:", "Investment instrument:")} {t(merese.titulo, merese.titulo_en ?? merese.titulo)}.</p>}
          <p className="rounded-xl border border-dashed border-line-strong p-3">
            {t(
              "Lo que todavía no se puede afirmar: qué quebrada concreta aportó más sedimento. Eso exige erosión RUSLE y datos locales de sedimento (módulo M5), que aún no están implementados; TerraVerdict no señala una quebrada sin esa evidencia.",
              "What cannot be claimed yet: which specific gully contributed the most sediment. That requires RUSLE erosion and local sediment data (module M5), not yet implemented; TerraVerdict does not point to a gully without that evidence.",
            )}
          </p>
          <div className="flex flex-wrap gap-2">
            <Link to="/mapa" onClick={() => setAbierto(false)}><Boton tamano="sm">{t("Ver la cortina en el mapa", "See the swipe on the map")}</Boton></Link>
            <Link to="/relevancia" onClick={() => setAbierto(false)}><Boton tamano="sm">{t("Variables que importan (M1)", "Variables that matter (M1)")}</Boton></Link>
          </div>
        </div>
      ),
    },
  ];

  return (
    <>
      <button
        type="button"
        onClick={() => {
          setActo(0);
          setAbierto(true);
        }}
        className="flex w-full items-center gap-4 rounded-3xl border border-line bg-gradient-to-r from-[#eb6834]/10 to-transparent p-5 text-left shadow-tarjeta transition-transform hover:-translate-y-0.5"
      >
        <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-[#eb6834] text-white"><Clapperboard className="h-6 w-6" aria-hidden /></span>
        <span>
          <span className="block text-[17px] font-semibold tracking-tight text-ink">{t("Caso de estudio: el corte de agua de febrero de 2025 en 60 segundos", "Case study: the February 2025 water cutoff in 60 seconds")}</span>
          <span className="mt-0.5 block text-[12.5px] text-ink-2">{t("Tres actos: la crisis, lo que muestran los datos y qué decisión respaldan.", "Three acts: the crisis, what the data show and which decision they support.")}</span>
        </span>
        <ArrowRight className="ml-auto h-5 w-5 shrink-0 text-ink-3" aria-hidden />
      </button>
      <Dialogo abierto={abierto} alCerrar={() => setAbierto(false)} titulo={actos[acto]!.titulo} ancho="w-[min(94vw,720px)]">
        <ol className="mb-4 flex gap-1.5" aria-label={t("Progreso", "Progress")}>
          {actos.map((a, i) => (
            <li key={a.titulo} className="h-1.5 flex-1 rounded-full" style={{ background: i <= acto ? "var(--accent)" : "var(--surface-3)" }} aria-current={i === acto ? "step" : undefined} />
          ))}
        </ol>
        <div className="min-h-[300px]">{actos[acto]!.cuerpo}</div>
        <div className="mt-4 flex justify-between">
          <Boton tamano="sm" icono={ArrowLeft} disabled={acto === 0} onClick={() => setActo((a) => a - 1)}>{t("Anterior", "Back")}</Boton>
          {acto < actos.length - 1 ? (
            <Boton tamano="sm" variante="primario" icono={ArrowRight} onClick={() => setActo((a) => a + 1)}>{t("Siguiente", "Next")}</Boton>
          ) : (
            <Boton tamano="sm" variante="primario" onClick={() => setAbierto(false)}>{t("Cerrar", "Close")}</Boton>
          )}
        </div>
      </Dialogo>
    </>
  );
}

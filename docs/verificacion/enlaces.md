# Revisión de todos los enlaces del reto y de la guía

> **Fecha:** 14 de noviembre de 2026.
> **Método:** cada enlace se abrió con una consulta real desde el entorno del proyecto ([`scripts/revisar_enlaces.py`](../../scripts/revisar_enlaces.py) → [`enlaces.json`](enlaces.json)). En las fuentes con datos se consultó además qué hay sobre la cuenca del Chili; parte de esas consultas está en [`evidencia.json`](evidencia.json).
> **Resultado:** 40 enlaces únicos (Giovanni y AppEEARS aparecen dos veces en las tablas), revisados en tres corridas automáticas con reintento ante fallos de red. **35 respondieron HTTP 200** en al menos una corrida; la red del entorno corta conexiones de forma intermitente, por eso cada enlace guarda su historial en [`enlaces.json`](enlaces.json). **2 respondieron 403** porque bloquean consultas automáticas (Medium y GitHub); su contenido se revisó por otra vía. **3 no se pudieron abrir** desde el entorno: el certificado SSL de las dos páginas de spaceappschallenge.org y del portal RCM de la CSA no se pudo validar a través del proxy de red. No se desactivó la verificación de seguridad para forzarlos.

## Leyenda

- **¿Se usa?** ✅ se descargan datos de esta fuente · 🔧 herramienta de validación o de apoyo (no aporta datos nuevos) · 📖 referencia metodológica · ❌ no se usa (con motivo)
- **Revisión:** ✅ abrió con consulta real · 🔁 abrió solo en algunas corridas o al reintentar · ⚠️ no abrió desde el entorno (se indica cómo se verificó)

## 1. Recursos oficiales del reto

| Recurso | Revisión | Qué datos ofrece (comprobado) | ¿Se usa? | Qué se descarga y para qué |
|---|---|---|---|---|
| [Página del reto](https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/) | ⚠️ certificado SSL no validable desde el proxy | Enunciado y lista de recursos (texto oficial entregado por el equipo) | 📖 | Requisitos del reto |
| [Giovanni](https://giovanni.gsfc.nasa.gov/) | ✅ HTTP 200 | Series de área de IMERG, MERRA-2 y GLDAS. Requiere sesión de Earthdata y es interactivo | 🔧 | **Validar** que nuestras series coinciden con las de NASA. Los mismos productos se descargan por CMR (verificados) |
| [Hydrology Time Series](https://disc.gsfc.nasa.gov/information/tools?title=Hydrology%20Time%20Series) | ✅ página 200; el servicio *data rods* cortó la conexión | Series por punto de GLDAS | ✅ si responde | Humedad del suelo y escorrentía por punto. Respaldo: GLDAS por CMR (verificado) |
| [AppEEARS](https://appeears.earthdatacloud.nasa.gov/) | ✅ 200; API con 193 productos | MODIS, VIIRS, SMAP, HLS, NASADEM, ECOSTRESS, recortados por polígono | ✅ | **Fuente principal** de NDVI, LST, ET, nieve, SMAP, HLS y NASADEM sobre la cuenca |
| [Climate Data Online](https://www.ncei.noaa.gov/cdo-web/) | ✅ 200 | GHCN-Daily: estación PE000084752 Arequipa (lluvia 1973–2025, temperatura 1948–2025) | ✅ | Validación puntual. Solo 14 años de lluvia completos y ninguno desde 2010: no sirve para tendencias |
| [Artículo SeaWiFS](https://ntrs.nasa.gov/api/citations/20090042747/downloads/20090042747.pdf) (Acker et al., 2009) | ✅ PDF leído (~28 páginas) | Método: series de Giovanni, regresión lineal, pruebas de significancia y anomalías. No usa Mann-Kendall ni corrección por autocorrelación | 📖 | Precedente de NASA. Nosotros agregamos Mann-Kendall, la corrección por autocorrelación y las otras pruebas del sello |
| [KNMI Climate Explorer](https://climexp.knmi.nl/) | ✅ 200; serie descargada | Niño3.4 (ERSST v5), estaciones, correlaciones, CMIP6 | ✅ | Niño3.4 para el filtro de El Niño (último valor: septiembre de 2026, +2,86); escenarios CMIP6 |
| [Artículo de pruebas de tendencia (Medium)](https://medium.com/@snp.kriss/statistical-test-methods-to-detect-trends-in-time-series-data-b361a0ec530b) | ⚠️ Medium devolvió 403 (bloquea consultas automáticas) | Artículo de divulgación sobre pruebas de tendencia | 📖 | Referencia general. Nuestro motor sigue la literatura primaria (Mann, Kendall, Sen, Hamed-Rao) |
| [Guía de significancia (Statsig)](https://www.statsig.com/perspectives/a-comprehensive-guide-to-statistical-significance) | ✅ 200; contenido leído | Valor p, comparaciones múltiples, potencia estadística | 📖 | Respaldo de la corrección FDR y de la prueba de detectabilidad |
| [RCM (CSA)](https://donnees-data.asc-csa.gc.ca/en/dataset/rcm) | ⚠️ certificado SSL no validable; verificado por documentación | Radar con licencia abierta de Canadá; productos de archivo de 16 m o más gruesos | ❌ por ahora | La cobertura sobre Perú no está confirmada. Para radar se usa **Sentinel-1**: 6573 productos sobre la cuenca en ASF, desde 2015 |
| [Geo.ca](https://geo.ca/) | ✅ 200 | Datos geoespaciales de Canadá | ❌ | No cubre Perú. Útil solo si se replica en Canadá |
| [SWOT (CSA)](https://www.asc-csa.gc.ca/eng/satellites/swot/) | ✅ 200 | Información de la misión. Los datos están en PO.DAAC: 1361 gránulos LakeSP sobre la cuenca desde 2022-12 | ✅ | **Cambio de almacenamiento de las represas** (por PO.DAAC) |
| [Ecosistemas desde el espacio (CSA)](https://www.asc-csa.gc.ca/eng/satellites/everyday-lives/monitoring-and-protecting-our-ecosystems-from-space.asp) | ✅ 200 | Contexto de monitoreo de humedales | 📖 | Marco para bofedales y para el pitch |
| [Tutorial SAR (CSA)](https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial) | ⚠️ 403 a la descarga automática; contenido revisado antes | Cuaderno Python (GDAL, cartopy) y guía de QGIS para graficar radar | 🔧 | Base para procesar y mostrar Sentinel-1 (le agregamos la detección de agua) |

## 2. Guía de la sede

### 2.1 Portales generales

| Recurso | Revisión | Qué ofrece (comprobado) | ¿Se usa? | Motivo |
|---|---|---|---|---|
| [data.nasa.gov](https://data.nasa.gov) | ✅ 200; su API devolvió 31 conjuntos para "IMERG precipitation" | Catálogo general de NASA | 🔧 | Solo búsqueda. Los datos se descargan de los archivos originales (CMR, DAAC) |
| [api.nasa.gov](https://api.nasa.gov) | ✅ 200; APOD con clave de prueba: 429 (límite de uso) | APIs de astronomía, asteroides, rovers | ❌ | No tiene datos de la cuenca |
| [Earthdata](https://earthdata.nasa.gov) | ✅ 200 | Portal y documentación | 🔧 | Documentación y políticas de datos |
| [Cuenta Earthdata (URS)](https://urs.earthdata.nasa.gov) | 🔁 200 en una de tres corridas (las otras cortaron la conexión) | Inicio de sesión | ✅ obligatorio | Necesaria para descargar de GES DISC, LP DAAC, NSIDC y PO.DAAC |
| [Earthdata Search](https://search.earthdata.nasa.gov) | ✅ 200 | Buscador sobre CMR | ✅ (vía CMR) | 29 colecciones verificadas por la API de CMR |
| [Worldview](https://worldview.earthdata.nasa.gov) | ✅ 200; GIBS con 1330 capas | Imágenes diarias | ✅ visual | Fondo del mapa 3D e imágenes de los días de los eventos |
| [images.nasa.gov](https://images.nasa.gov) | ✅ 200; 6 resultados para "Arequipa" (cañones, volcán Ubinas, fotos desde la Estación Espacial) | Fotos y videos | ✅ solo pitch | Material visual; no se usa para cálculos |
| [Retos 2026](https://www.spaceappschallenge.org/2026/challenges/) | ⚠️ certificado SSL | Lista de retos | 📖 | — |

### 2.2 Retos de la Tierra

| Recurso | Revisión | Qué ofrece (comprobado) | ¿Se usa? | Motivo |
|---|---|---|---|---|
| R01 [Giovanni](https://giovanni.gsfc.nasa.gov) | ✅ 200 | Ver la sección 1 | 🔧 | Validación |
| R02 [ASF Search](https://search.asf.alaska.edu) | ✅ 200; API consultada | **NISAR: 666 productos sobre la cuenca, del 30-10-2025 al 01-11-2026** (incluye 93 de humedad del suelo, SME2). Sentinel-1: 6573 productos desde 2015 | ✅ Sentinel-1; NISAR solo para monitoreo actual | NISAR tiene apenas un año de historia: **no sirve para tendencias**, sí para ver el estado actual de bofedales y suelo |
| R02 [NISAR (JPL)](https://nisar.jpl.nasa.gov) | 🔁 200 (redirige a science.nasa.gov) | Información de la misión | 📖 | — |
| R03 [NASA POWER](https://power.larc.nasa.gov) | ✅ 200; serie 1981–2024 descargada | T2M, lluvia, radiación, humedad y viento por punto (MERRA-2, CERES) | ✅ | **Ya usado** en el primer análisis real |
| R03 [SMAP (JPL)](https://smap.jpl.nasa.gov) | ✅ 200 | Información. Los datos están en NSIDC: SPL3SMP_E con 4167 gránulos sobre la cuenca; SPL4SMGP | ✅ | Humedad del suelo desde 2015 |
| R03/R04 [AppEEARS](https://appeears.earthdatacloud.nasa.gov) | ✅ 200 | Ver la sección 1 | ✅ | Fuente principal de extracción |
| R04 [FIRMS](https://firms.modaps.eosdis.nasa.gov) | ✅ 200 (la API necesita una clave gratuita) | Fuegos activos MODIS y VIIRS | ✅ | Quemas que degradan bofedales. Respaldo: VNP14IMG y MCD64A1 por CMR (verificados) |
| R05 [Sonificación (Chandra)](https://chandra.si.edu/sound/) | ✅ 200 | Datos astronómicos convertidos en sonido | ❌ datos / 💡 idea | Idea opcional de accesibilidad: "escuchar" la serie de lluvia |

### 2.3 Luna y Marte

| Recurso | Revisión | ¿Se usa? | Motivo |
|---|---|---|---|
| [Moon/Mars Trek](https://trek.nasa.gov) | ✅ 200 | ❌ | Datos de la Luna y Marte |
| [Planetary Data System](https://pds.nasa.gov) | ✅ 200 | ❌ | Datos planetarios |
| [HiRISE](https://hirise.lpl.arizona.edu) | ✅ 200 | ❌ | Imágenes de Marte |
| [NSSDC](https://nssdc.gsfc.nasa.gov) | ✅ 200 | ❌ | Catálogo histórico de misiones |
| [EarthExplorer (USGS)](https://earthexplorer.usgs.gov) | ✅ 200 | ✅ | **Landsat 1984–2012** para la historia larga de represas y bofedales (requiere cuenta USGS) |

### 2.4 Ciencia, tripulación y cielo

| Recurso | Revisión | ¿Se usa? | Motivo |
|---|---|---|---|
| R12 [PSI](https://psi.nasa.gov) | 🔁 200 (science.nasa.gov) | ❌ | Experimentos de física en la Estación Espacial |
| R13 [OSDR](https://osdr.nasa.gov) | 🔁 200 (science.nasa.gov) | ❌ | Biología espacial |
| R13 [Human Research Program](https://www.nasa.gov/hrp) | ✅ 200 | ❌ | Salud de astronautas |
| R14 [IRSA / SPHEREx](https://irsa.ipac.caltech.edu) | ✅ 200 | ❌ | Astronomía infrarroja |

### 2.5 Agencias aliadas

| Recurso | Revisión | Qué ofrece (comprobado) | ¿Se usa? | Para qué |
|---|---|---|---|---|
| [Copernicus Data Space](https://dataspace.copernicus.eu) | ✅ 200; catálogo consultado | Sentinel-1 (S1C, 11-11-2026) y Sentinel-2 (S2B, 09-11-2026) sobre la cabecera | ✅ | Agua bajo nubes (radar), bofedales y turbidez (óptico, 10 m) |
| [JAXA G-Portal](https://gportal.jaxa.jp) | ✅ 200 | GSMaP (lluvia), entre otros. Requiere registro | ⏳ opcional | Cuarta familia de lluvia para la prueba de independencia, si alcanza el tiempo |
| [CSA](https://www.asc-csa.gc.ca) | ✅ 200 | Portal de la agencia | 📖 | Ver RCM y SWOT en la sección 1 |

## 3. Resumen: qué se descarga

| Fuente | Productos que se descargan |
|---|---|
| **NASA Earthdata (CMR + DAAC)** | IMERG (Final, Early, Late), MERRA-2, GLDAS, FLDAS, MODIS (LST, NDVI, ET, nieve, área quemada), VIIRS, SMAP, NASADEM, HLS, ICESat-2, SWOT |
| **AppEEARS** | Los mismos productos MODIS, VIIRS, SMAP, HLS y NASADEM, recortados por polígono |
| **NASA POWER** | Temperatura, lluvia, radiación, humedad y viento por punto |
| **ASF** | Sentinel-1 (y NISAR para el estado actual) |
| **Copernicus** | Sentinel-1 y Sentinel-2 |
| **EarthExplorer** | Landsat 1984–2012 |
| **NOAA** | ONI y RONI (CPC); GHCN (CDO) |
| **KNMI** | Niño3.4 y CMIP6 |
| **FIRMS** | Fuegos activos (o VNP14IMG por CMR) |
| **Fuentes locales** | Reportes de AUTODEMA |

**No se usan para datos** (fuera del tema del reto): api.nasa.gov, Moon/Mars Trek, PDS, HiRISE, NSSDC, PSI, OSDR, HRP, IRSA, Geo.ca y la sonificación de Chandra (esta última queda como idea de accesibilidad).

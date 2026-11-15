# Licencias y atribuciones

> Actualizado: 15-11-2026. Regla: aquí solo se escriben términos **comprobados en la fuente oficial** o en un catálogo público que la cita. Lo no comprobado se marca **⚠️ verificar**.

## 1. Código

- **Licencia:** MIT. Ver [`LICENSE`](../LICENSE). Cubre el paquete científico (`src/`), el backend (`backend/`), el frontend (`frontend/`), los scripts y la documentación.
- **Dependencias de terceros:** el inventario está en [`licencias-terceros.md`](licencias-terceros.md). Se genera con `scripts/inventario_licencias.py` a partir de los metadatos que declara cada paquete instalado.
  - Todas las licencias son permisivas (MIT, BSD, ISC, Apache-2.0, PSF).
  - Única excepción: `certifi`, con MPL-2.0. Su copyleft es por archivo; lo usamos sin modificar, como dependencia de `requests`, y eso es compatible con distribuir el proyecto bajo MIT.

## 2. Datos

### Qué hay en este repositorio
- **Crudos:** no se redistribuyen en git (`.gitignore`). Solo se versiona su `data/raw/<fuente>/manifiesto.json`, con la URL, la fecha de descarga y el SHA-256 de cada archivo, para que cualquiera los vuelva a bajar de la fuente oficial.
- **Derivados:** `resultados/*.json` y `resultados/contrato/expedientes.json` contienen estadísticos calculados. Siguen sujetos a la atribución de la fuente de la que provienen.
- **Excepción:** `tests/fixtures/` guarda recortes pequeños de datos reales para las pruebas reproducibles; también se atribuyen aquí.

### Fuentes que usa el sistema

| Fuente | Dónde se usa | Términos | Cita o atribución obligatoria | Estado |
|---|---|---|---|---|
| **NASA POWER** (LaRC), API diaria | Temperatura y lluvia en Arequipa y en los 25 departamentos; caos | Política de datos abiertos de NASA: uso sin restricciones | Nombre del servicio, versión y fecha de acceso. Plantilla oficial: *"The data was obtained from the POWER Project's Daily 2.x.x version on YYYY/MM/DD."* La versión y la fecha exactas están en el manifiesto | ✅ [Referencing](https://power.larc.nasa.gov/docs/referencing/) · [Data use policy](https://www.earthdata.nasa.gov/earth-observation-data/data-use-policy) |
| **GPM IMERG Final V07 diaria** (GES DISC) | Contraste de lluvia (descarga parcial, ver `pendientes.md`) | Política de datos abiertos de NASA. Requiere cuenta Earthdata | Huffman, G.J., Stocker, E.F., Bolvin, D.T., Nelkin, E.J. y Tan, J. (2023). *GPM IMERG Final Precipitation L3 1 day 0.1° × 0.1° V07.* GES DISC. doi:[10.5067/GPM/IMERGDF/DAY/07](https://doi.org/10.5067/GPM/IMERGDF/DAY/07) | ✅ |
| **NASA GIBS** (teselas del mapa) | Fondo satelital del mapa | Política de datos abiertos de NASA | En el mapa: *"Imágenes: NASA GIBS / ESDIS"*. En textos: *"We acknowledge the use of imagery provided by services from NASA's Global Imagery Browse Services (GIBS), part of NASA's Earth Science Data and Information System (ESDIS)."* | ✅ [GIBS](https://www.earthdata.nasa.gov/gibs) |
| **NASA Global Landslide Catalog** (exportación de data.nasa.gov) | Deslizamientos | Catálogo público de NASA. El registro de data.gov no declara licencia y la trata como obra del Gobierno de EE. UU. | Kirschbaum et al. (2010), *Natural Hazards* 52(3):561–575, doi:[10.1007/s11069-009-9401-4](https://doi.org/10.1007/s11069-009-9401-4); y Kirschbaum, Stanley y Zhou (2015), *Geomorphology* 249:4–15, doi:[10.1016/j.geomorph.2015.03.016](https://doi.org/10.1016/j.geomorph.2015.03.016) | ✅ [GPM: Citing the data](https://gpm.nasa.gov/landslides/data.html) · [data.gov](https://catalog.data.gov/dataset/global-landslide-catalog-export) |
| **USGS ComCat** (ANSS) | Sismos en Arequipa y en todo el Perú | Datos producidos por USGS: dominio público de EE. UU., uso libre citando a USGS | U.S. Geological Survey, Earthquake Hazards Program (2017). *Advanced National Seismic System (ANSS) Comprehensive Catalog of Earthquake Events and Products.* doi:[10.5066/F7MS3QZH](https://doi.org/10.5066/F7MS3QZH) | ✅ [USGS FAQ](https://www.usgs.gov/faqs/what-usgs-policy-release-scientific-data-are-any-usgs-products-restricted) · [ComCat references](https://earthquake.usgs.gov/data/comcat/references.php) |
| **Smithsonian GVP**, *Volcanoes of the World* | Volcanes: historia eruptiva y recurrencia | Términos de uso del Smithsonian: uso personal, educativo y **no comercial** con cita. El uso comercial requiere permiso escrito | Global Volcanism Program (2025). *Volcanoes of the World* (v. 5.3.0; 17 Jul 2025). Smithsonian Institution, comp. Venzke, E. doi:[10.5479/si.GVP.VOTW5-2025.5.3](https://doi.org/10.5479/si.GVP.VOTW5-2025.5.3). Indicar la versión y la fecha de descarga del manifiesto | ✅ [Cómo citar](https://volcano.si.edu/gvp_cite.cfm) · [Términos](https://volcano.si.edu/gvp_termsofuse.cfm) |
| **NOAA CPC ONI** | ENSO: prueba ENSO-HAC del Sello y covariable | Obra del Gobierno de EE. UU., uso libre | NOAA Climate Prediction Center, *Oceanic Niño Index* (`oni.ascii.txt`), con la fecha de acceso | ✅ (política de NOAA; ver [`verificacion/README.md`](verificacion/README.md) §3) |
| **NOAA NCEI GHCN-Daily** | Estación de Arequipa (validación puntual) | Obra del Gobierno de EE. UU., uso libre | Menne, M.J. et al. (2012), *J. Atmos. Oceanic Technol.* 29:897–910, doi:[10.1175/JTECH-D-11-00103.1](https://doi.org/10.1175/JTECH-D-11-00103.1); y el conjunto GHCN-Daily v3, doi:[10.7289/V5D21VHZ](https://doi.org/10.7289/V5D21VHZ), indicando la estación PE000084752 | ✅ [NCEI](https://www.ncei.noaa.gov/metadata/geoportal/rest/metadata/item/gov.noaa.ncdc:C00861/html) |
| **CHIRPS** (por ClimateSERV) | Contraste de lluvia y sequía | Dominio público (renuncia de derechos) y CC BY 4.0 | Funk, C. et al. (2015), *Scientific Data* 2:150066, doi:[10.1038/sdata.2015.66](https://doi.org/10.1038/sdata.2015.66). Para v3: doi 10.15780/G2JQ0P | ✅ (ver [`verificacion/README.md`](verificacion/README.md) §3). En este entorno ClimateSERV estuvo bloqueado: solo hay manifiesto |
| **Mapzen Terrain Tiles** (Registry of Open Data on AWS) | Relieve 3D del mapa (solo visual) | Atribución obligatoria para análisis o visualización (`attribution.md` de tilezen/joerd) | En el mapa: *"Relieve: Mapzen Terrain Tiles · 3DEP, SRTM, GMTED2010 (USGS), ETOPO1 (NOAA)"* | ⚠️ verificar el texto vigente en [tilezen/joerd attribution.md](https://github.com/tilezen/joerd/blob/master/docs/attribution.md) ([registro AWS](https://registry.opendata.aws/terrain-tiles)); la lista de fuentes se tomó de una copia secundaria |
| **IGP** (último sismo) | Previsto; no usado (host bloqueado, solo manifiesto vacío) | El IGP publica catálogos en la Plataforma Nacional de Datos Abiertos, pero no se encontró la licencia | Citar al Instituto Geofísico del Perú y el conjunto con su fecha | ⚠️ verificar en [datosabiertos.gob.pe](https://www.datosabiertos.gob.pe) antes de usarlo |
| **MODIS LST** (ORNL DAAC) | Previsto, solo control de calidad (ORNL respondía 502) | Política de datos abiertos de NASA | Citar el producto MODIS y su DOI | ⏳ no se usa todavía |
| **Reportes de AUTODEMA** | Validación cualitativa de eventos | Documentos públicos sin licencia explícita | Citar el documento y su fecha | ⚠️ verificar ([`verificacion/README.md`](verificacion/README.md) §3) |

### Fuentes descartadas por su licencia
- **PISCOp V2.1 (SENAMHI):** CC BY-NC-ND. No permite distribuir derivados, así que no se publica ningún resultado derivado de PISCOp.

## 3. Consecuencias para el uso del sistema

1. **Uso académico y de investigación** (el de la Space Apps Challenge): permitido por todas las fuentes usadas, siempre que se citen como arriba.
2. **Uso comercial:**
   - el código es MIT;
   - los resultados de volcanes derivan del Smithsonian GVP, que exige permiso escrito para uso comercial. Un despliegue comercial debe pedir ese permiso o retirar el módulo de volcanes.
3. **Avisos visibles:** la interfaz muestra la atribución de cada capa del mapa y el aviso permanente *"Resultados experimentales. No son alertas oficiales (SENAMHI, IGP, INGEMMET, INDECI)."*

## 4. Cómo mantener este documento

```bash
.venv/bin/python scripts/inventario_licencias.py python "terraverdict[ml]" > /tmp/ciencia.md
backend/.venv/bin/python scripts/inventario_licencias.py python terraverdict-backend > /tmp/backend.md
python scripts/inventario_licencias.py npm frontend > /tmp/frontend.md
```

Con esas tres salidas se rehace `licencias-terceros.md`. Cada fuente de datos nueva entra en la tabla de la §2 con su licencia comprobada **antes** de que se publique un resultado derivado de ella.

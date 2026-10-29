# BG Riesgo Macro

Seguimiento macroeconómico del Ecuador organizado en cuatro sectores (real, financiero, fiscal y externo) más una página de resumen. Construido con [Observable Framework](https://observablehq.com/framework/) y [Highcharts Stock](https://www.highcharts.com/products/stock/).

## Desarrollo local

Requiere Node.js 20 o superior.

```sh
npm install
npm run dev      # vista previa en http://127.0.0.1:3000 con recarga automática
npm run build    # genera el sitio estático en dist/
```

## Estructura

```
src/
  index.md            Resumen: mensajes clave, KPI por sector, gráficos y tablero
  real.md             Sector real
  financiero.md       Sector monetario y financiero
  fiscal.md           Sector fiscal
  externo.md          Sector externo
  internacional.md    Economía internacional (mercados)
  data/               Datos generados por scripts/procesar_datos.py
  components/
    base.js           Carga las series macro una sola vez para todas las páginas
    mercados.js       Carga las series de mercados (solo en las páginas que las usan)
    datos.js          Transformaciones (sumas móviles, variaciones) y formatos
    graficos.js       Envoltorio de Highcharts con el estilo del sitio
    ui.js             Tarjetas KPI, paneles y cabeceras
  style.css           Tipografía, colores (incluye modo oscuro) y diseño
observablehq.config.js
scripts/descargar_datos.py  internet → data_raw/ (mercados y previsiones del FMI y Banco Mundial)
scripts/catalogo_mercados.py  series de mercados: fuente, código y ficha
scripts/procesar_datos.py   data_raw/ → src/data/
```

## Datos

Los archivos fuente van en `data_raw/`. Esa carpeta no se sube a git: los archivos son pesados y algunos tienen licencias de uso restringido. Para regenerar los datos del sitio, ejecuta [uv](https://docs.astral.sh/uv/) desde la raíz del repositorio:

```sh
uv run scripts/descargar_datos.py   # mercados y previsiones del FMI y Banco Mundial (requiere internet)
uv run scripts/procesar_datos.py
```

`descargar_datos.py` baja las series de mercados de Yahoo Finance (bolsas, monedas, materias primas), FRED (tasas de la Fed y del BCE, SOFR, curva del Tesoro), Banco de Inglaterra, Deutsche Bundesbank, Ministerio de Finanzas de Japón y Banco de Japón; del BCE, los precios de los bonos globales de Ecuador y el riesgo país; y las previsiones de crecimiento del FMI (WEO) y del Banco Mundial (GEP). Si una fuente falla, no sobrescribe `data_raw/mercados.csv`.

Sistema de bancos privados: `data_raw/sb/indicadores_banco*.xlsx` (compilación interna con datos de la Superintendencia de Bancos; se usa el más reciente y, de su hoja `Sheet1`, el total del segmento `BANCOS PRIVADOS`). La liquidez oficial (fondos disponibles / depósitos a corto plazo) sale de `data_raw/sb/SERIES SUBSISTEMA BANCA PRIVADA AAAA_MM.xlsx`, las series mensuales que publica la Superintendencia de Bancos (se usa la del último mes según el nombre).

Previsiones de crecimiento (`data_raw/previsiones/`):

| Archivo | Institución |
|---|---|
| `PrevEconAAMM.xlsx` | BCE, Previsiones macroeconómicas (se usa el más reciente) |
| `*Resumen-de-las-proyecciones*.xlsx` | MEF, Programación macroeconómica |
| `fmi.csv`, `bm.csv` | FMI y Banco Mundial (los escribe `descargar_datos.py`) |
| `otras.csv` | A mano: CEPAL u otras instituciones (`institucion, informe, fecha, anio, valor`) |

El script lee `data_raw/` y escribe en `src/data/`:

| Archivo | Contenido |
|---|---|
| `series.csv` + `catalogo.json` | Series macro en formato largo (`id, fecha, valor`) y su ficha |
| `mercados.csv` + `mercados.json` | Series diarias de mercados internacionales (formato ancho) |
| `previsiones.csv` | Previsiones de crecimiento del PIB por institución |
| `exportaciones.csv` + `.json` | Exportaciones mensuales por producto (clasificación BCE) |
| `importaciones.csv` + `.json` | Importaciones mensuales por CUODE |
| `ventas_sector.csv` | Ventas locales SRI por sección CIIU (y división en comercio) |
| `ipc_incidencias.csv` | Incidencia por división del IPC (último mes; IPC del BCE con ponderaciones del INEC) |
| `spnf.csv` | Operaciones mensuales del SPNF por partida (MEF) |
| `vencimientos.csv` | Perfil de vencimientos de la deuda pública (MEF) |

- **Fechas:** inicio del período (`2026-04-01` = T2 2026; `2025-01-01` = año 2025).
- **Frecuencias:** `D` diaria, `S` semanal, `M` mensual, `T` trimestral, `A` anual.

## Publicación

Cada push a `main` compila y publica el sitio con GitHub Actions (`.github/workflows/deploy.yml`). En el repositorio, en *Settings → Pages → Build and deployment*, el origen debe ser **GitHub Actions**.

## Licencias

Highcharts requiere licencia comercial para uso dentro de una empresa. Consulta https://www.highcharts.com/license.

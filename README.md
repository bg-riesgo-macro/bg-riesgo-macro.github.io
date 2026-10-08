# BG Riesgo Macro

Seguimiento macroeconómico del Ecuador organizado en cuatro sectores (real, financiero, fiscal y externo) más una página de resumen. Construido con [Observable Framework](https://observablehq.com/framework/) y [Highcharts Stock](https://www.highcharts.com/products/stock/).

> **Estado:** versión preliminar.

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
  internacional.md    Economía internacional (Bloomberg)
  data/               Datos generados por scripts/procesar_datos.py
  components/
    base.js           Carga las series macro una sola vez para todas las páginas
    mercados.js       Carga las series de Bloomberg (solo en las páginas que las usan)
    datos.js          Transformaciones (sumas móviles, variaciones) y formatos
    graficos.js       Envoltorio de Highcharts con el estilo del sitio
    ui.js             Tarjetas KPI, paneles y cabeceras
  style.css           Tipografía, colores (incluye modo oscuro) y diseño
observablehq.config.js
scripts/procesar_datos.py   data_raw/ → src/data/
```

## Datos

Los archivos fuente van en `data_raw/`. Esa carpeta no se sube a git: los archivos son pesados y algunos tienen licencias de uso restringido. Para regenerar los datos del sitio, ejecuta [uv](https://docs.astral.sh/uv/) desde la raíz del repositorio:

```sh
uv run scripts/procesar_datos.py
```

El script lee `data_raw/` y escribe en `src/data/`:

| Archivo | Contenido |
|---|---|
| `series.csv` + `catalogo.json` | Series macro en formato largo (`id, fecha, valor`) y su ficha |
| `mercados.csv` + `mercados.json` | Series diarias de Bloomberg (formato ancho) |
| `exportaciones.csv` + `.json` | Exportaciones mensuales por producto (clasificación BCE) |
| `importaciones.csv` + `.json` | Importaciones mensuales por CUODE |
| `ventas_sector.csv` | Ventas SRI por sección CIIU |
| `ipc_incidencias.csv` | Incidencia por división del IPC (último mes) |
| `spnf.csv` | Operaciones mensuales del SPNF por partida (MEF) |
| `vencimientos.csv` | Perfil de vencimientos de la deuda pública (MEF) |

- **Fechas:** inicio del período (`2026-04-01` = T2 2026; `2025-01-01` = año 2025).
- **Frecuencias:** `D` diaria, `S` semanal, `M` mensual, `T` trimestral, `A` anual.

## Publicación

Cada push a `main` compila y publica el sitio con GitHub Actions (`.github/workflows/deploy.yml`). En el repositorio, en *Settings → Pages → Build and deployment*, el origen debe ser **GitHub Actions**.

## Licencias

Highcharts requiere licencia comercial para uso dentro de una empresa. Consulta https://www.highcharts.com/license.

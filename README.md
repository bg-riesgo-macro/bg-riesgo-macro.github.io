# BG Riesgo Macro

Seguimiento macroeconómico del Ecuador organizado en cuatro sectores (real, financiero, fiscal y externo) más una página de resumen. Construido con [Observable Framework](https://observablehq.com/framework/) y [Highcharts Stock](https://www.highcharts.com/products/stock/).

> **Estado:** maqueta con datos ilustrativos (no oficiales).

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
  data/
    series.csv        Series en formato largo: id, fecha, valor
    catalogo.json     Metadatos de cada serie (nombre, sector, unidad, frecuencia, fuente)
  components/
    base.js           Carga los datos una sola vez para todas las páginas
    datos.js          Transformaciones (sumas móviles, variaciones) y formatos
    graficos.js       Envoltorio de Highcharts con el estilo del sitio
    ui.js             Tarjetas KPI, paneles y cabeceras
  style.css           Tipografía, colores (incluye modo oscuro) y diseño
observablehq.config.js
```

## Datos

Cada serie se identifica por un `id` que aparece en `series.csv` y en `catalogo.json`.

- **Fechas:** inicio del período (`2026-04-01` = T2 2026; `2025-01-01` = año 2025).
- **Frecuencias:** `D` diaria, `M` mensual, `T` trimestral, `A` anual.

Para agregar un indicador: añade sus filas a `series.csv`, su ficha a `catalogo.json` y úsalo en la página que corresponda con `db.serie("id")`.

## Publicación

Cada push a `main` compila y publica el sitio con GitHub Actions (`.github/workflows/deploy.yml`). En el repositorio, en *Settings → Pages → Build and deployment*, el origen debe ser **GitHub Actions**.

## Licencias

Highcharts requiere licencia comercial para uso dentro de una empresa. Consulta https://www.highcharts.com/license.

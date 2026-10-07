---
title: Sector fiscal
---

```js
import {db} from "./components/base.js";
import {sumaMovil, combinar} from "./components/datos.js";
import {grafico} from "./components/graficos.js";
import {kpiSerie, panel, cabecera} from "./components/ui.js";

const fuente = (id) => db.meta(id).fuente;
const ingresos12 = sumaMovil(db.serie("ingresos_spnf"), 12);
const gastos12 = sumaMovil(db.serie("gastos_spnf"), 12);
const recaudacion12 = sumaMovil(db.serie("recaudacion"), 12);
const deudaTotal = combinar(db.serie("deuda_externa"), db.serie("deuda_interna"), (a, b) => a + b);
```

```js
display(cabecera({
  antetitulo: "Sector fiscal",
  titulo: "Finanzas públicas y deuda",
  bajada: "Ingresos, gastos y resultado del Sector Público No Financiero, recaudación tributaria y endeudamiento público.",
  corte: db.corte()
}));

display(html`<div class="kpis">
  ${kpiSerie(db, "resultado_global_pib", {cambio: null})}
  ${kpiSerie(db, "deuda_pib")}
  ${kpiSerie(db, "deuda_externa", {titulo: "Deuda pública total", datos: deudaTotal})}
  ${kpiSerie(db, "recaudacion", {titulo: "Recaudación, 12 meses", datos: recaudacion12})}
</div>`);
```

## Resultado fiscal

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Resultado global y primario del SPNF",
    subtitulo: "% del PIB, anual",
    fuente: fuente("resultado_global_pib"),
    contenido: grafico({
      series: [
        {nombre: "Resultado global", datos: db.serie("resultado_global_pib")},
        {nombre: "Resultado primario", datos: db.serie("resultado_primario_pib")}
      ],
      frecuencia: "A", unidad: "% PIB", decimales: 1, tipo: "column", cero: true
    })
  })}
  ${panel({
    titulo: "Ingresos y gastos del SPNF",
    subtitulo: "USD millones, suma móvil de 12 meses",
    fuente: fuente("ingresos_spnf"),
    contenido: grafico({
      series: [
        {nombre: "Ingresos", datos: ingresos12},
        {nombre: "Gastos", datos: gastos12}
      ],
      frecuencia: "M", unidad: "USD mm", decimales: 0
    })
  })}
</div>`);
```

## Recaudación tributaria

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Recaudación tributaria mensual",
    subtitulo: "USD millones",
    fuente: fuente("recaudacion"),
    ancho: true,
    contenido: grafico({
      series: [{nombre: "Recaudación", datos: db.serie("recaudacion")}],
      frecuencia: "M", unidad: "USD mm", decimales: 0, tipo: "column", navegador: true, rango: "3a"
    })
  })}
</div>`);
```

## Deuda pública

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Saldo de la deuda pública",
    subtitulo: "USD millones, por tipo de acreedor",
    fuente: fuente("deuda_externa"),
    contenido: grafico({
      series: [
        {nombre: "Externa", datos: db.serie("deuda_externa")},
        {nombre: "Interna", datos: db.serie("deuda_interna")}
      ],
      frecuencia: "M", unidad: "USD mm", decimales: 0, tipo: "area", apilado: true
    })
  })}
  ${panel({
    titulo: "Deuda pública total",
    subtitulo: "% del PIB, mensual",
    fuente: fuente("deuda_pib"),
    contenido: grafico({
      series: [{nombre: "Deuda pública", datos: db.serie("deuda_pib")}],
      frecuencia: "M", unidad: "% PIB", decimales: 1
    })
  })}
</div>`);
```

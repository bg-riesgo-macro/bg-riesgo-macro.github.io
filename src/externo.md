---
title: Sector externo
---

```js
import {db} from "./components/base.js";
import {sumaMovil, combinar} from "./components/datos.js";
import {grafico} from "./components/graficos.js";
import {kpiSerie, panel, cabecera} from "./components/ui.js";

const fuente = (id) => db.meta(id).fuente;
const suma = (a, b) => a + b;
const exportaciones = combinar(db.serie("x_petroleras"), db.serie("x_no_petroleras"), suma);
const exportaciones12 = sumaMovil(exportaciones, 12);
const importaciones12 = sumaMovil(db.serie("importaciones"), 12);
const balanza = combinar(exportaciones, db.serie("importaciones"), (x, m) => x - m);
const balanza12 = sumaMovil(balanza, 12);
const noPetroleras12 = sumaMovil(db.serie("x_no_petroleras"), 12);
const remesas4 = sumaMovil(db.serie("remesas"), 4);
const productos = ["x_camaron", "x_banano", "x_mineria", "x_cacao"];
```

```js
display(cabecera({
  antetitulo: "Sector externo",
  titulo: "Comercio, petróleo y balanza de pagos",
  bajada: "Exportaciones e importaciones, principales productos de exportación, precios del crudo, cuenta corriente y remesas.",
  corte: db.corte()
}));

display(html`<div class="kpis">
  ${kpiSerie(db, "importaciones", {titulo: "Balanza comercial, 12 meses", datos: balanza12, cambio: null})}
  ${kpiSerie(db, "x_no_petroleras", {titulo: "X no petroleras, 12 meses", datos: noPetroleras12})}
  ${kpiSerie(db, "crudo_oriente")}
  ${kpiSerie(db, "remesas", {titulo: "Remesas, 4 trimestres", datos: remesas4})}
</div>`);
```

## Comercio exterior

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Exportaciones e importaciones",
    subtitulo: "USD millones FOB, suma móvil de 12 meses",
    fuente: fuente("importaciones"),
    contenido: grafico({
      series: [
        {nombre: "Exportaciones", datos: exportaciones12},
        {nombre: "Importaciones", datos: importaciones12}
      ],
      frecuencia: "M", unidad: "USD mm", decimales: 0
    })
  })}
  ${panel({
    titulo: "Balanza comercial mensual",
    subtitulo: "Exportaciones menos importaciones, USD millones FOB",
    fuente: fuente("importaciones"),
    contenido: grafico({
      series: [{nombre: "Balanza comercial", datos: balanza.slice(-48)}],
      frecuencia: "M", unidad: "USD mm", decimales: 0, tipo: "column", cero: true
    })
  })}
</div>`);
```

## Exportaciones no petroleras

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Principales productos de exportación no petrolera",
    subtitulo: "USD millones FOB, suma móvil de 12 meses",
    fuente: fuente("x_camaron"),
    ancho: true,
    contenido: grafico({
      series: productos.map((id) => ({nombre: db.meta(id).corto, datos: sumaMovil(db.serie(id), 12)})),
      frecuencia: "M", unidad: "USD mm", decimales: 0, altura: 340
    })
  })}
</div>`);
```

## Precios del petróleo

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Precio del crudo",
    subtitulo: "USD por barril, diario",
    fuente: `${fuente("wti")}; ${fuente("crudo_oriente")}`,
    ancho: true,
    contenido: grafico({
      series: [
        {nombre: "WTI", datos: db.serie("wti")},
        {nombre: "Crudo Oriente", datos: db.serie("crudo_oriente")}
      ],
      frecuencia: "D", unidad: "USD/bl", decimales: 2, navegador: true, rango: "3a", altura: 420
    })
  })}
</div>`);
```

## Balanza de pagos

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Cuenta corriente",
    subtitulo: "Saldo, % del PIB, anual",
    fuente: fuente("cuenta_corriente_pib"),
    contenido: grafico({
      series: [{nombre: "Cuenta corriente", datos: db.serie("cuenta_corriente_pib")}],
      frecuencia: "A", unidad: "% PIB", decimales: 1, tipo: "column", cero: true
    })
  })}
  ${panel({
    titulo: "Remesas recibidas",
    subtitulo: "USD millones, trimestral",
    fuente: fuente("remesas"),
    contenido: grafico({
      series: [{nombre: "Remesas", datos: db.serie("remesas")}],
      frecuencia: "T", unidad: "USD mm", decimales: 0, tipo: "column"
    })
  })}
</div>`);
```

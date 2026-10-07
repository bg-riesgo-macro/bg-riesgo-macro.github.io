---
title: Sector financiero
---

```js
import {db} from "./components/base.js";
import {variacion} from "./components/datos.js";
import {grafico} from "./components/graficos.js";
import {kpiSerie, panel, cabecera} from "./components/ui.js";

const fuente = (id) => db.meta(id).fuente;
```

```js
display(cabecera({
  antetitulo: "Sector monetario y financiero",
  titulo: "Riesgo soberano, liquidez y crédito",
  bajada: "Percepción de riesgo de los mercados, reservas internacionales, depósitos, crédito y tasas de interés.",
  corte: db.corte()
}));

display(html`<div class="kpis">
  ${kpiSerie(db, "embi")}
  ${kpiSerie(db, "reservas")}
  ${kpiSerie(db, "depositos")}
  ${kpiSerie(db, "morosidad")}
</div>`);
```

## Riesgo país

El EMBI mide el diferencial de rendimiento de los bonos soberanos de Ecuador frente a los del Tesoro de EE.&nbsp;UU. Usa el navegador inferior o los botones para cambiar el período.

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Riesgo país (EMBI Ecuador)",
    subtitulo: "Puntos básicos, diario",
    fuente: fuente("embi"),
    ancho: true,
    contenido: grafico({
      series: [{nombre: "EMBI Ecuador", datos: db.serie("embi")}],
      frecuencia: "D", unidad: "pb", decimales: 0, navegador: true, rango: "3a", altura: 420
    })
  })}
</div>`);
```

## Depósitos y crédito

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Depósitos y crédito",
    subtitulo: "Saldos, USD millones, bancos privados",
    fuente: fuente("depositos"),
    contenido: grafico({
      series: [
        {nombre: "Depósitos", datos: db.serie("depositos")},
        {nombre: "Crédito", datos: db.serie("credito")}
      ],
      frecuencia: "M", unidad: "USD mm", decimales: 0
    })
  })}
  ${panel({
    titulo: "Crecimiento de depósitos y crédito",
    subtitulo: "Variación anual, %",
    fuente: fuente("depositos"),
    contenido: grafico({
      series: [
        {nombre: "Depósitos", datos: variacion(db.serie("depositos"), 12)},
        {nombre: "Crédito", datos: variacion(db.serie("credito"), 12)}
      ],
      frecuencia: "M", unidad: "%", decimales: 1, cero: true
    })
  })}
</div>`);
```

## Tasas de interés y calidad de cartera

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Tasas de interés referenciales",
    subtitulo: "Tasas efectivas, %, mensual",
    fuente: fuente("tasa_activa"),
    contenido: grafico({
      series: [
        {nombre: "Activa", datos: db.serie("tasa_activa")},
        {nombre: "Pasiva", datos: db.serie("tasa_pasiva")}
      ],
      frecuencia: "M", unidad: "%", decimales: 2
    })
  })}
  ${panel({
    titulo: "Morosidad de la cartera",
    subtitulo: "% de la cartera bruta, bancos privados",
    fuente: fuente("morosidad"),
    contenido: grafico({
      series: [{nombre: "Morosidad", datos: db.serie("morosidad")}],
      frecuencia: "M", unidad: "%", decimales: 2
    })
  })}
</div>`);
```

## Reservas internacionales

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Reservas internacionales",
    subtitulo: "USD millones, fin de mes",
    fuente: fuente("reservas"),
    ancho: true,
    contenido: grafico({
      series: [{nombre: "Reservas internacionales", datos: db.serie("reservas")}],
      frecuencia: "M", unidad: "USD mm", decimales: 0, tipo: "area", navegador: true, rango: "Todo"
    })
  })}
</div>`);
```

---
title: Sector real
---

```js
import {db} from "./components/base.js";
import {grafico} from "./components/graficos.js";
import {kpiSerie, panel, cabecera} from "./components/ui.js";

const fuente = (id) => db.meta(id).fuente;
```

```js
display(cabecera({
  antetitulo: "Sector real",
  titulo: "Actividad, precios y empleo",
  bajada: "Evolución de la producción, la inflación, el mercado laboral y la actividad petrolera.",
  corte: db.corte()
}));

display(html`<div class="kpis">
  ${kpiSerie(db, "pib_real_aa", {cambio: null})}
  ${kpiSerie(db, "inflacion_aa")}
  ${kpiSerie(db, "desempleo")}
  ${kpiSerie(db, "prod_petrolera")}
</div>`);
```

## Actividad económica

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "PIB real",
    subtitulo: "Variación anual, %, trimestral",
    fuente: fuente("pib_real_aa"),
    contenido: grafico({
      series: [{nombre: "PIB real", datos: db.serie("pib_real_aa")}],
      frecuencia: "T", unidad: "%", decimales: 1, tipo: "column", cero: true
    })
  })}
  ${panel({
    titulo: "Índice de Actividad Económica Coyuntural",
    subtitulo: "Índice 2007 = 100, mensual",
    fuente: fuente("ideac"),
    contenido: grafico({
      series: [{nombre: "IDEAC", datos: db.serie("ideac")}],
      frecuencia: "M", unidad: "", decimales: 1
    })
  })}
</div>`);
```

## Precios

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Inflación anual",
    subtitulo: "Variación anual del IPC, %, mensual",
    fuente: fuente("inflacion_aa"),
    contenido: grafico({
      series: [{nombre: "Inflación anual", datos: db.serie("inflacion_aa")}],
      frecuencia: "M", unidad: "%", decimales: 2, cero: true
    })
  })}
  ${panel({
    titulo: "Inflación mensual",
    subtitulo: "Variación mensual del IPC, %",
    fuente: fuente("inflacion_mm"),
    contenido: grafico({
      series: [{nombre: "Inflación mensual", datos: db.serie("inflacion_mm").slice(-36)}],
      frecuencia: "M", unidad: "%", decimales: 2, tipo: "column", cero: true
    })
  })}
</div>`);
```

## Mercado laboral

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Tasa de desempleo",
    subtitulo: "% de la población económicamente activa, mensual",
    fuente: fuente("desempleo"),
    contenido: grafico({
      series: [{nombre: "Desempleo", datos: db.serie("desempleo")}],
      frecuencia: "M", unidad: "%", decimales: 1
    })
  })}
  ${panel({
    titulo: "Tasa de empleo adecuado",
    subtitulo: "% de la población económicamente activa, mensual",
    fuente: fuente("empleo_adecuado"),
    contenido: grafico({
      series: [{nombre: "Empleo adecuado", datos: db.serie("empleo_adecuado")}],
      frecuencia: "M", unidad: "%", decimales: 1
    })
  })}
</div>`);
```

## Petróleo

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Producción nacional de petróleo",
    subtitulo: "Miles de barriles diarios, promedio mensual",
    fuente: fuente("prod_petrolera"),
    ancho: true,
    contenido: grafico({
      series: [{nombre: "Producción", datos: db.serie("prod_petrolera")}],
      frecuencia: "M", unidad: "miles bpd", decimales: 0, navegador: true, rango: "Todo"
    })
  })}
</div>`);
```

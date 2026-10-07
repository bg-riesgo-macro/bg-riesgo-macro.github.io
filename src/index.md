---
title: Resumen
toc: false
---

```js
import {db} from "./components/base.js";
import {sumaMovil, combinar, cambioAnual, haceUnAno, formatoNumero, formatoCambio, formatoPeriodo} from "./components/datos.js";
import {grafico} from "./components/graficos.js";
import {kpiSerie, panel, cabecera} from "./components/ui.js";
```

```js
// Transformaciones usadas en el resumen
const exportaciones12 = sumaMovil(combinar(db.serie("x_petroleras"), db.serie("x_no_petroleras"), (a, b) => a + b), 12);
const importaciones12 = sumaMovil(db.serie("importaciones"), 12);
const balanza12 = combinar(exportaciones12, importaciones12, (x, m) => x - m);
```

```js
display(cabecera({
  antetitulo: "Panorama macroeconómico",
  titulo: "Ecuador en cuatro sectores",
  bajada: "Lo esencial de la economía real, el sistema financiero, las finanzas públicas y el sector externo, con la última información disponible.",
  corte: db.corte()
}));
```

```js
// Mensajes clave: frases construidas a partir de los últimos datos.
const [tPib, pib] = db.ultimo("pib_real_aa");
const [tInf, inf] = db.ultimo("inflacion_aa");
const [tEmbi, embi] = db.ultimo("embi");
const embiAnt = haceUnAno(db.serie("embi"))[1];
const dep = cambioAnual(db.serie("depositos"), "USD mm").valor;
const [tRes, res] = db.ultimo("resultado_global_pib");
const [, deuda] = db.ultimo("deuda_pib");
const [tBal, bal] = balanza12[balanza12.length - 1];
const [, oriente] = db.ultimo("crudo_oriente");

const mensajes = [
  {
    sector: "Real",
    texto: `La economía ${pib >= 0 ? "creció" : "se contrajo"} ${formatoNumero(Math.abs(pib), 1)}% anual en el ${formatoPeriodo(tPib, "T")}. La inflación anual fue ${formatoNumero(inf, 2)}% en ${formatoPeriodo(tInf, "M")}.`
  },
  {
    sector: "Financiero",
    texto: `El riesgo país se ubicó en ${formatoNumero(embi, 0)} pb, ${formatoNumero(Math.abs(embi - embiAnt), 0)} pb ${embi < embiAnt ? "menos" : "más"} que hace un año. Los depósitos crecen ${formatoNumero(dep, 1)}% anual.`
  },
  {
    sector: "Fiscal",
    texto: `El SPNF registró un ${res < 0 ? "déficit" : "superávit"} global de ${formatoNumero(Math.abs(res), 1)}% del PIB en ${formatoPeriodo(tRes, "A")}. La deuda pública equivale a ${formatoNumero(deuda, 1)}% del PIB.`
  },
  {
    sector: "Externo",
    texto: `La balanza comercial acumula un ${bal >= 0 ? "superávit" : "déficit"} de USD ${formatoNumero(Math.abs(bal), 0)} millones en 12 meses a ${formatoPeriodo(tBal, "M")}. El crudo Oriente cotiza en USD ${formatoNumero(oriente, 2)} por barril.`
  }
];

display(html`<div class="mensajes">${mensajes.map((m) => html`<div class="mensaje"><h3>${m.sector}</h3><p>${m.texto}</p></div>`)}</div>`);
```

```js
display(html`<div class="kpis-sectores">
  <div class="kpi-columna">
    <h3><a href="./real">Sector real</a></h3>
    ${kpiSerie(db, "pib_real_aa", {cambio: null})}
    ${kpiSerie(db, "inflacion_aa")}
  </div>
  <div class="kpi-columna">
    <h3><a href="./financiero">Sector financiero</a></h3>
    ${kpiSerie(db, "embi")}
    ${kpiSerie(db, "reservas")}
  </div>
  <div class="kpi-columna">
    <h3><a href="./fiscal">Sector fiscal</a></h3>
    ${kpiSerie(db, "resultado_global_pib", {cambio: null})}
    ${kpiSerie(db, "deuda_pib")}
  </div>
  <div class="kpi-columna">
    <h3><a href="./externo">Sector externo</a></h3>
    ${kpiSerie(db, "importaciones", {titulo: "Balanza comercial, 12 meses", datos: balanza12, cambio: null})}
    ${kpiSerie(db, "crudo_oriente")}
  </div>
</div>`);
```

## Indicadores clave por sector

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Crecimiento del PIB real",
    subtitulo: "Variación anual, %, trimestral",
    fuente: db.meta("pib_real_aa").fuente,
    enlace: {href: "./real", texto: "Sector real"},
    contenido: grafico({
      series: [{nombre: "PIB real", datos: db.serie("pib_real_aa")}],
      frecuencia: "T", unidad: "%", decimales: 1, tipo: "column", cero: true
    })
  })}
  ${panel({
    titulo: "Riesgo país (EMBI)",
    subtitulo: "Puntos básicos, diario",
    fuente: db.meta("embi").fuente,
    enlace: {href: "./financiero", texto: "Sector financiero"},
    contenido: grafico({
      series: [{nombre: "EMBI Ecuador", datos: db.serie("embi")}],
      frecuencia: "D", unidad: "pb", decimales: 0
    })
  })}
  ${panel({
    titulo: "Resultado del Sector Público No Financiero",
    subtitulo: "% del PIB, anual",
    fuente: db.meta("resultado_global_pib").fuente,
    enlace: {href: "./fiscal", texto: "Sector fiscal"},
    contenido: grafico({
      series: [
        {nombre: "Resultado global", datos: db.serie("resultado_global_pib")},
        {nombre: "Resultado primario", datos: db.serie("resultado_primario_pib")}
      ],
      frecuencia: "A", unidad: "% PIB", decimales: 1, tipo: "column", cero: true
    })
  })}
  ${panel({
    titulo: "Comercio exterior",
    subtitulo: "USD millones, suma móvil de 12 meses",
    fuente: db.meta("importaciones").fuente,
    enlace: {href: "./externo", texto: "Sector externo"},
    contenido: grafico({
      series: [
        {nombre: "Exportaciones", datos: exportaciones12},
        {nombre: "Importaciones", datos: importaciones12}
      ],
      frecuencia: "M", unidad: "USD mm", decimales: 0
    })
  })}
</div>`);
```

## Tablero de indicadores

Último dato disponible de cada indicador y su comparación con el mismo período del año anterior.

```js
const grupos = [
  ["Sector real", ["pib_real_aa", "ideac", "inflacion_aa", "desempleo", "empleo_adecuado", "prod_petrolera"]],
  ["Sector financiero", ["embi", "reservas", "depositos", "credito", "tasa_activa", "tasa_pasiva", "morosidad"]],
  ["Sector fiscal", ["resultado_global_pib", "resultado_primario_pib", "deuda_pib", "deuda_externa", "deuda_interna"]],
  ["Sector externo", ["crudo_oriente", "wti", "cuenta_corriente_pib", "remesas"]]
];

function fila(id) {
  const m = db.meta(id);
  const s = db.serie(id);
  const [t, v] = s[s.length - 1];
  const ant = haceUnAno(s);
  const c = cambioAnual(s, m.unidad);
  return html`<tr>
    <td>${m.nombre}</td>
    <td class="unidad-celda">${m.unidad}</td>
    <td>${formatoPeriodo(t, m.frecuencia)}</td>
    <td><b>${formatoNumero(v, m.decimales)}</b></td>
    <td>${ant ? formatoNumero(ant[1], m.decimales) : "–"}</td>
    <td>${c ? formatoCambio(c.valor, c.decimales ?? 1, c.unidad) : "–"}</td>
  </tr>`;
}

display(html`<div class="tabla-wrap"><table class="tablero">
  <thead><tr><th>Indicador</th><th>Unidad</th><th>Período</th><th>Último</th><th>Hace un año</th><th>Cambio</th></tr></thead>
  <tbody>${grupos.flatMap(([g, ids]) => [
    html`<tr class="grupo"><td colspan="6">${g}</td></tr>`,
    ...ids.map(fila)
  ])}</tbody>
</table></div>`);
```

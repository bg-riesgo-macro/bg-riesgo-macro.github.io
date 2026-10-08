---
title: Resumen
toc: false
---

```js
import {db} from "./components/base.js";
import {mercados} from "./components/mercados.js";
import {acumuladoAnual, etiquetaAcumulado, mesUltimo, variacion, cambioAnual, haceUnAno, formatoNumero, formatoCambio, formatoPeriodo} from "./components/datos.js";
import {grafico} from "./components/graficos.js";
import {kpiSerie, panel, cabecera, kpiAcumulado as kpiAcumuladoBase} from "./components/ui.js";

const desde = (serie, anio) => serie.filter(([t]) => t >= Date.UTC(anio, 0, 1));
```

```js
// Comercio exterior acumulado de enero al último mes disponible.
const mes = mesUltimo(db.serie("x_total"));
const acum = (id) => desde(acumuladoAnual(db.serie(id), mes), 2018);
const anioComercio = new Date(db.ultimo("x_total")[0]).getUTCFullYear();
const etiqueta = (t) => etiquetaAcumulado(mes, new Date(t).getUTCFullYear());
const ultimoYPrevio = (serie) => [serie[serie.length - 1][1], serie[serie.length - 2][1]];

const kpiAcumulado = (titulo, datos, opciones = {}) => kpiAcumuladoBase({titulo, datos, mes, ...opciones});
```

```js
display(cabecera({
  antetitulo: "Panorama macroeconómico",
  titulo: "Ecuador en cuatro sectores",
  bajada: "Lo esencial de la economía real, el sistema financiero, las finanzas públicas, el sector externo y el entorno internacional, con la última información disponible.",
  corte: mercados.corte(),
  frecuencia: "D"
}));
```

```js
// Mensajes clave: frases construidas a partir de los últimos datos.
const [tPib, pib] = db.ultimo("pib_real_aa");
const [tImae, imae] = db.ultimo("imaec_aa");
const [tInf, inf] = db.ultimo("inflacion_aa");
const dep = cambioAnual(db.serie("depositos_bp"), "USD mm").valor;
const car = cambioAnual(db.serie("cartera_bp"), "USD mm").valor;
const [, mora] = db.ultimo("morosidad_sf");
const [tRi, ri] = db.ultimo("reservas");
const [tEmbi, embi] = db.ultimo("embi");
const [x, xAnt] = ultimoYPrevio(acum("x_total"));
const [xnp, xnpAnt] = ultimoYPrevio(acum("x_no_pet"));
const [bal] = ultimoYPrevio(acum("bc_total"));
const [, ust10] = mercados.ultimo("us_10a");
const [, fed] = mercados.ultimo("fed");
const [, wti] = mercados.ultimo("wti");
const [, cacao] = mercados.ultimo("cacao");

// Sector fiscal: acumulado del SPNF a su propio mes de corte.
const mesFiscal = mesUltimo(db.serie("spnf_resultado_global"));
const acumFiscal = (id) => desde(acumuladoAnual(db.serie(id), mesFiscal), 2018);
const anioFiscal = new Date(db.ultimo("spnf_resultado_global")[0]).getUTCFullYear();
const [rg, rgAnt] = ultimoYPrevio(acumFiscal("spnf_resultado_global"));
const [tDeuda, deudaPib] = db.ultimo("deuda_pib");
const saldo = (v) => `${v >= 0 ? "superávit" : "déficit"} de USD ${formatoNumero(Math.abs(v), 0)} millones`;
const pct = (a, b) => formatoCambio((a / b - 1) * 100, 1, "%");
const periodoComercio = `enero y ${etiquetaAcumulado(mes).replace("ene–", "")} de ${anioComercio}`;

const mensajes = [
  {
    sector: "Real",
    texto: `El PIB ${pib >= 0 ? "creció" : "se contrajo"} ${formatoNumero(Math.abs(pib), 1)}% anual en el ${formatoPeriodo(tPib, "T")}. El IMAEc varió ${formatoCambio(imae, 1, "%")} en ${formatoPeriodo(tImae, "M")} y la inflación anual fue ${formatoNumero(inf, 2)}% en ${formatoPeriodo(tInf, "M")}.`
  },
  {
    sector: "Financiero",
    texto: `Las reservas internacionales suman USD ${formatoNumero(ri, 0)} millones (${formatoPeriodo(tRi, "D")}) y el riesgo país se ubicó en ${formatoNumero(embi, 0)} pb (${formatoPeriodo(tEmbi, "D")}). Los depósitos de los bancos privados crecen ${formatoNumero(dep, 1)}% anual y la cartera ${formatoNumero(car, 1)}%.`
  },
  {
    sector: "Fiscal",
    texto: `Entre enero y ${etiquetaAcumulado(mesFiscal).replace("ene–", "")} de ${anioFiscal}, el SPNF registró un ${saldo(rg)}, frente a un ${saldo(rgAnt)} en el mismo período de ${anioFiscal - 1}. La deuda pública equivale a ${formatoNumero(deudaPib, 1)}% del PIB (${formatoPeriodo(tDeuda, "M")}).`
  },
  {
    sector: "Externo",
    texto: `Entre ${periodoComercio}, las exportaciones sumaron USD ${formatoNumero(x, 0)} millones (${pct(x, xAnt)}); las no petroleras, USD ${formatoNumero(xnp, 0)} millones (${pct(xnp, xnpAnt)}). La balanza comercial acumula un ${bal >= 0 ? "superávit" : "déficit"} de USD ${formatoNumero(Math.abs(bal), 0)} millones.`
  },
  {
    sector: "Internacional",
    texto: `El Tesoro de EE. UU. a 10 años rinde ${formatoNumero(ust10, 2)}% y la Fed mantiene su tasa en ${formatoNumero(fed, 2)}%. El WTI cotiza en USD ${formatoNumero(wti, 2)} por barril y el cacao en USD ${formatoNumero(cacao, 0)} por tonelada.`
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
    ${kpiAcumuladoBase({titulo: "Resultado global del SPNF", datos: acumFiscal("spnf_resultado_global"), mes: mesFiscal, nivel: false})}
    ${kpiSerie(db, "deuda_pib")}
  </div>
  <div class="kpi-columna">
    <h3><a href="./externo">Sector externo</a></h3>
    ${kpiAcumulado("Exportaciones", acum("x_total"))}
    ${kpiAcumulado("Balanza comercial", acum("bc_total"), {nivel: false})}
  </div>
</div>`);
```

## Indicadores clave por sector

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Crecimiento del PIB real",
    subtitulo: "Variación anual, %, trimestral (serie desestacionalizada)",
    fuente: db.meta("pib_real_aa").fuente,
    enlace: {href: "./real", texto: "Sector real"},
    contenido: grafico({
      series: [{nombre: "PIB real", datos: desde(db.serie("pib_real_aa"), 2015)}],
      frecuencia: "T", unidad: "%", decimales: 1, tipo: "column", cero: true
    })
  })}
  ${panel({
    titulo: "Crecimiento de depósitos y cartera",
    subtitulo: "Variación anual, %, bancos privados",
    fuente: db.meta("depositos_bp").fuente,
    enlace: {href: "./financiero", texto: "Sector financiero"},
    contenido: grafico({
      series: [
        {nombre: "Depósitos", datos: desde(variacion(db.serie("depositos_bp"), 12), 2015)},
        {nombre: "Cartera", datos: desde(variacion(db.serie("cartera_bp"), 12), 2015)}
      ],
      frecuencia: "M", unidad: "%", decimales: 1, cero: true
    })
  })}
  ${panel({
    titulo: "Exportaciones",
    subtitulo: `USD millones FOB, acumulado ${etiquetaAcumulado(mes)}`,
    fuente: db.meta("x_total").fuente,
    enlace: {href: "./externo", texto: "Sector externo"},
    contenido: grafico({
      series: [
        {nombre: "Petroleras", datos: acum("x_pet")},
        {nombre: "No petroleras", datos: acum("x_no_pet")}
      ],
      frecuencia: "A", unidad: "USD mm", decimales: 0, tipo: "column", apilado: true, periodo: etiqueta
    })
  })}
  ${panel({
    titulo: "Riesgo país (EMBI Ecuador)",
    subtitulo: "Puntos básicos, diario",
    fuente: db.meta("embi").fuente,
    enlace: {href: "./financiero", texto: "Sector financiero"},
    contenido: grafico({
      series: [{nombre: "EMBI Ecuador", datos: desde(db.serie("embi"), 2018)}],
      frecuencia: "D", unidad: "pb", decimales: 0
    })
  })}
</div>`);
```

## Tablero de indicadores

Último dato disponible de cada indicador y su comparación con el mismo período del año anterior.

```js
const grupos = [
  ["Sector real", db, ["pib_real_aa", "imaec_aa", "inflacion_aa", "desempleo", "empleo_adecuado", "subempleo"]],
  ["Sector financiero", db, ["embi", "reservas", "depositos_bp", "cartera_bp", "ltd_bp", "morosidad_sf", "liquidez_bp", "solvencia_sf", "tpr"]],
  ["Sector fiscal", db, ["resultado_global_pib", "resultado_primario_pib", "deuda_total", "deuda_pib"]],
  ["Sector externo", db, ["terminos_intercambio", "remesas_recibidas", "ied", "cuenta_corriente_pib"]],
  ["Economía internacional", mercados, ["fed", "us_2a", "us_10a", "dxy", "wti", "cacao", "oro"]]
];

function fila(base, id) {
  const m = base.meta(id);
  const s = base.serie(id);
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
  <tbody>${grupos.flatMap(([g, base, ids]) => [
    html`<tr class="grupo"><td colspan="6">${g}</td></tr>`,
    ...ids.map((id) => fila(base, id))
  ])}</tbody>
</table></div>`);
```

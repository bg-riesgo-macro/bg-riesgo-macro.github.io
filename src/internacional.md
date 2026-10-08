---
title: Economía internacional
---

```js
import {mercados, curvas} from "./components/mercados.js";
import {combinar, valorEn, formatoNumero, formatoCambio, formatoPeriodo} from "./components/datos.js";
import {grafico, graficoCategorias} from "./components/graficos.js";
import {kpiSerie, panel, cabecera} from "./components/ui.js";

const corte = +mercados.corte();
const DIA = 864e5;
const anio = new Date(corte).getUTCFullYear();
const referencias = [
  {etiqueta: "1 mes", t: corte - 30 * DIA},
  {etiqueta: "En el año", t: Date.UTC(anio - 1, 11, 31)},
  {etiqueta: "12 meses", t: Date.UTC(anio - 1, new Date(corte).getUTCMonth(), new Date(corte).getUTCDate())}
];
const desde = (id, t) => mercados.serie(id).filter(([x]) => x >= t);

// Cambio desde una fecha: % para precios e índices, puntos básicos para tasas.
function cambio(id, t) {
  const s = mercados.serie(id);
  const actual = s[s.length - 1][1];
  const ref = valorEn(s, t);
  if (ref == null) return "–";
  return mercados.meta(id).unidad === "%"
    ? formatoCambio((actual - ref) * 100, 0, "pb")
    : formatoCambio((actual / ref - 1) * 100, 1, "%");
}

/** Tabla de desempeño: grupos de series con último valor y cambios. */
function tablaDesempeno(grupos, {unidad = true} = {}) {
  return html`<div class="tabla-wrap"><table class="tablero cuadro">
    <thead><tr>
      <th></th>${unidad ? html`<th>Unidad</th>` : null}<th>Último</th>
      ${referencias.map((r) => html`<th>${r.etiqueta}</th>`)}
    </tr></thead>
    <tbody>${grupos.flatMap(([grupo, ids]) => [
      grupo ? html`<tr class="fila-grupo nivel-0"><td colspan=${unidad ? 6 : 5}>${grupo}</td></tr>` : null,
      ...ids.map((id) => {
        const m = mercados.meta(id);
        return html`<tr class="fila-item nivel-0">
          <td>${m.corto}</td>
          ${unidad ? html`<td class="unidad-celda">${m.unidad}</td>` : null}
          <td><b>${formatoNumero(mercados.ultimo(id)[1], m.decimales)}</b></td>
          ${referencias.map((r) => html`<td>${cambio(id, r.t)}</td>`)}
        </tr>`;
      })
    ])}</tbody>
  </table></div>`;
}

// Índice base 100 en la fecha t.
const base100 = (id, t) => {
  const s = desde(id, t);
  return s.map(([x, v]) => [x, (v / s[0][1]) * 100]);
};
```

```js
display(cabecera({
  antetitulo: "Economía internacional",
  titulo: "Mercados, tasas y materias primas",
  bajada: "Bolsas, política monetaria y curvas de rendimiento de las principales economías, monedas y precios de las materias primas más relevantes para Ecuador.",
  corte,
  frecuencia: "D"
}));

display(html`<div class="kpis">
  ${kpiSerie(mercados, "spx")}
  ${kpiSerie(mercados, "us_10a", {titulo: "Tesoro EE. UU. 10 años", cambio: {valor: (mercados.ultimo("us_10a")[1] - valorEn(mercados.serie("us_10a"), referencias[2].t)) * 100, unidad: "pb", decimales: 0, etiqueta: "a/a"}})}
  ${kpiSerie(mercados, "dxy")}
  ${kpiSerie(mercados, "wti", {titulo: "Petróleo WTI"})}
</div>`);
```

## Bolsas

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Principales índices bursátiles",
    ancho: true,
    subtitulo: `Variación, % · al ${formatoPeriodo(corte, "D")}`,
    fuente: "Bloomberg",
    contenido: tablaDesempeno([
      ["Estados Unidos", ["spx", "nasdaq", "dow"]],
      ["Europa", ["stoxx50", "dax", "ftse", "cac", "ibex"]],
      ["Asia", ["nikkei", "hangseng", "shanghai"]],
      ["América Latina", ["bovespa"]]
    ], {unidad: false})
  })}
  ${panel({
    titulo: "Desempeño de las bolsas en los últimos 12 meses",
    ancho: true,
    subtitulo: "Índice, base 100 hace 12 meses",
    fuente: "Bloomberg",
    contenido: grafico({
      series: [
        {nombre: "S&P 500", datos: base100("spx", referencias[2].t)},
        {nombre: "Euro Stoxx 50", datos: base100("stoxx50", referencias[2].t)},
        {nombre: "Nikkei 225", datos: base100("nikkei", referencias[2].t)},
        {nombre: "Bovespa", datos: base100("bovespa", referencias[2].t)}
      ],
      frecuencia: "D", soloImagen: true, unidad: "", decimales: 1, referencia: 100, altura: 400
    })
  })}
</div>`);
```

## Tasas de interés

```js
const politica = ["fed", "bce_tasa", "boe", "boj"];
const plazosUS = curvas.find((c) => c.id === "us").plazos;
const curvaEn = (pref, plazos, t) => plazos.map((p) => valorEn(mercados.serie(`${pref}_${p.toLowerCase()}`), t) ?? null);
const todosPlazos = ["3M", "1A", "2A", "3A", "5A", "7A", "10A", "15A", "20A", "30A"];
const curvaPais = (c) => todosPlazos.map((p) => (c.plazos.includes(p) ? valorEn(mercados.serie(`${c.id}_${p.toLowerCase()}`), corte) : null));
const pendiente = combinar(mercados.serie("us_10a"), mercados.serie("us_2a"), (a, b) => (a - b) * 100);

display(html`<div class="paneles">
  ${panel({
    titulo: "Tasas de política monetaria",
    subtitulo: "%, diario",
    fuente: "Bloomberg",
    contenido: grafico({
      series: politica.map((id) => ({nombre: mercados.meta(id).corto, datos: mercados.serie(id), escalon: true})),
      frecuencia: "D", soloImagen: true, unidad: "%", decimales: 2
    })
  })}
  ${panel({
    titulo: "Curva de rendimientos del Tesoro de EE. UU.",
    subtitulo: "Rendimiento por plazo, %",
    fuente: "Bloomberg",
    contenido: graficoCategorias({
      categorias: plazosUS,
      series: [
        {nombre: `Hoy (${formatoPeriodo(corte, "D")})`, datos: curvaEn("us", plazosUS, corte), color: 0},
        {nombre: "Hace 3 meses", datos: curvaEn("us", plazosUS, corte - 91 * DIA), color: 2},
        {nombre: "Hace 12 meses", datos: curvaEn("us", plazosUS, referencias[2].t), color: "suave", punteado: true}
      ],
      unidad: "%", decimales: 2, soloImagen: true
    })
  })}
  ${panel({
    titulo: "Curvas soberanas por país",
    subtitulo: `Rendimiento por plazo, %, al ${formatoPeriodo(corte, "D")}`,
    fuente: "Bloomberg",
    contenido: graficoCategorias({
      categorias: todosPlazos,
      series: curvas.map((c) => ({nombre: c.pais, datos: curvaPais(c)})),
      unidad: "%", decimales: 2, soloImagen: true
    })
  })}
  ${panel({
    titulo: "Pendiente de la curva de EE. UU.",
    subtitulo: "Rendimiento a 10 años menos 2 años, puntos básicos",
    fuente: "Bloomberg; cálculo propio",
    contenido: grafico({
      series: [{nombre: "10 años – 2 años", datos: pendiente}],
      frecuencia: "D", soloImagen: true, unidad: "pb", decimales: 0, cero: true
    })
  })}
  ${panel({
    titulo: "Tasas de referencia en dólares",
    subtitulo: "Nivel, % · cambios en puntos básicos",
    fuente: "Bloomberg",
    ancho: true,
    contenido: tablaDesempeno([
      ["Política monetaria", ["fed", "fed_efectiva", "bce_tasa", "boe", "boj"]],
      ["Term SOFR", ["sofr_1m", "sofr_3m", "sofr_6m", "sofr_12m"]],
      ["Tesoro de EE. UU.", ["us_3m", "us_2a", "us_5a", "us_10a", "us_30a"]]
    ], {unidad: false})
  })}
</div>`);
```

## Monedas

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Índice del dólar (DXY)",
    ancho: true,
    subtitulo: "Índice, diario",
    fuente: "Bloomberg",
    contenido: grafico({
      series: [{nombre: "DXY", datos: mercados.serie("dxy")}],
      frecuencia: "D", soloImagen: true, unidad: "", decimales: 2
    })
  })}
  ${panel({
    titulo: "Tipos de cambio",
    ancho: true,
    subtitulo: "Variación, %; en los pares USD/XXX un aumento es apreciación del dólar",
    fuente: "Bloomberg",
    contenido: tablaDesempeno([
      [null, ["dxy", "eurusd", "gbpusd", "usdjpy", "usdcny", "usdcop", "usdbrl", "usdmxn"]]
    ])
  })}
</div>`);
```

## Materias primas

Precios de los productos que más pesan en las exportaciones e importaciones de Ecuador.

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Precios de materias primas",
    subtitulo: `Variación, % · al ${formatoPeriodo(corte, "D")}`,
    fuente: "Bloomberg",
    ancho: true,
    contenido: tablaDesempeno([
      ["Energía", ["wti", "brent", "gasolina", "diesel", "gas_natural"]],
      ["Agrícolas", ["cacao", "soya", "palma", "trigo", "maiz"]],
      ["Metales", ["oro", "cobre"]]
    ])
  })}
  ${panel({
    titulo: "Petróleo",
    subtitulo: "USD por barril, primer futuro",
    fuente: "Bloomberg",
    ancho: true,
    contenido: grafico({
      series: [
        {nombre: "WTI", datos: mercados.serie("wti")},
        {nombre: "Brent", datos: mercados.serie("brent")}
      ],
      frecuencia: "D", soloImagen: true, unidad: "USD/barril", decimales: 2, navegador: true, rango: "3a"
    })
  })}
  ${panel({
    titulo: "Cacao",
    subtitulo: "USD por tonelada, ICE Nueva York",
    fuente: "Bloomberg",
    contenido: grafico({
      series: [{nombre: "Cacao", datos: mercados.serie("cacao")}],
      frecuencia: "D", soloImagen: true, unidad: "USD/t", decimales: 0
    })
  })}
  ${panel({
    titulo: "Oro",
    subtitulo: "USD por onza troy, COMEX",
    fuente: "Bloomberg",
    contenido: grafico({
      series: [{nombre: "Oro", datos: mercados.serie("oro")}],
      frecuencia: "D", soloImagen: true, unidad: "USD/oz", decimales: 1
    })
  })}
  ${panel({
    titulo: "Cobre",
    subtitulo: "Centavos de USD por libra, COMEX",
    fuente: "Bloomberg",
    contenido: grafico({
      series: [{nombre: "Cobre", datos: mercados.serie("cobre")}],
      frecuencia: "D", soloImagen: true, unidad: "¢/libra", decimales: 1
    })
  })}
  ${panel({
    titulo: "Derivados de petróleo",
    subtitulo: "Centavos de USD por galón, Nymex",
    fuente: "Bloomberg",
    contenido: grafico({
      series: [
        {nombre: "Gasolina RBOB", datos: mercados.serie("gasolina")},
        {nombre: "Diésel (heating oil)", datos: mercados.serie("diesel")}
      ],
      frecuencia: "D", soloImagen: true, unidad: "¢/galón", decimales: 1
    })
  })}
</div>`);
```

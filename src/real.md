---
title: Sector real
---

```js
import {db, fechaIncidenciasIpc} from "./components/base.js";
import {acumuladoAnual, etiquetaAcumulado, mesUltimo, formatoNumero, formatoCambio, formatoPeriodo} from "./components/datos.js";
import {grafico, graficoCategorias} from "./components/graficos.js";
import {kpiSerie, panel, cabecera} from "./components/ui.js";

const fuente = (id) => db.meta(id).fuente;
const desde = (id, anio) => db.serie(id).filter(([t]) => t >= Date.UTC(anio, 0, 1));
```

```js
display(cabecera({
  antetitulo: "Sector real",
  titulo: "Actividad, precios y empleo",
  bajada: "Producción por el lado del gasto y por industrias, actividad mensual, inflación, mercado laboral e indicadores de coyuntura.",
  corte: db.ultimo("imaec")[0]
}));

display(html`<div class="kpis">
  ${kpiSerie(db, "pib_real_aa", {cambio: null})}
  ${kpiSerie(db, "imaec_aa", {cambio: null})}
  ${kpiSerie(db, "inflacion_aa")}
  ${kpiSerie(db, "desempleo")}
</div>`);
```

## Producción

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Crecimiento del PIB y aportes por componente del gasto",
    subtitulo: "Variación anual del PIB real (%) y aportes en puntos porcentuales, serie desestacionalizada",
    fuente: fuente("pib_real_aa"),
    ancho: true,
    contenido: grafico({
      series: [
        {nombre: "Consumo", datos: desde("aporte_consumo", 2015)},
        {nombre: "Inversión (FBKF)", datos: desde("aporte_fbkf", 2015)},
        {nombre: "Exportaciones netas", datos: desde("aporte_xnetas", 2015)},
        {nombre: "Variación de existencias", datos: desde("aporte_existencias", 2015)},
        {nombre: "PIB", datos: desde("pib_real_aa", 2015), tipo: "line", color: "tinta"}
      ],
      frecuencia: "T", unidad: "pp", decimales: 2, tipo: "column", apilado: true, cero: true, altura: 380
    })
  })}
  ${panel({
    titulo: "Valor agregado petrolero y no petrolero",
    subtitulo: "Variación anual, %, trimestral",
    fuente: fuente("vab_petrolero_aa"),
    contenido: grafico({
      series: [
        {nombre: "No petrolero", datos: desde("vab_no_petrolero_aa", 2015)},
        {nombre: "Petrolero", datos: desde("vab_petrolero_aa", 2015)}
      ],
      frecuencia: "T", unidad: "%", decimales: 1, cero: true
    })
  })}
  ${panel({
    titulo: "Índice de Actividad Económica coyuntural (IMAEc)",
    subtitulo: "Variación anual, %, mensual (serie desestacionalizada)",
    fuente: fuente("imaec_aa"),
    contenido: grafico({
      series: [{nombre: "IMAEc", datos: db.serie("imaec_aa")}],
      frecuencia: "M", unidad: "%", decimales: 1, tipo: "column", cero: true
    })
  })}
</div>`);
```

```js
const sectoresImae = ["agro", "petroleo", "manufactura", "construccion", "comercio", "servicios"];
const [tImae] = db.ultimo("imaec_aa");
const tImaePrevio = Date.UTC(new Date(tImae).getUTCFullYear(), new Date(tImae).getUTCMonth() - 1, 1);
const valor = (id, t) => db.serie(id).find(([x]) => x === t)?.[1];

display(html`<div class="paneles">
  ${panel({
    titulo: "IMAEc por actividad",
    subtitulo: "Variación anual, %",
    fuente: fuente("imaec_aa"),
    ancho: true,
    contenido: graficoCategorias({
      categorias: sectoresImae.map((s) => db.meta(`imaec_aa_${s}`).corto),
      series: [
        {nombre: formatoPeriodo(tImaePrevio, "M"), datos: sectoresImae.map((s) => valor(`imaec_aa_${s}`, tImaePrevio)), color: "suave"},
        {nombre: formatoPeriodo(tImae, "M"), datos: sectoresImae.map((s) => valor(`imaec_aa_${s}`, tImae)), color: 0}
      ],
      tipo: "bar", unidad: "%", decimales: 1, cero: true, altura: 320
    })
  })}
</div>`);
```

## Precios

```js
const incidencias = FileAttachment("data/ipc_incidencias.csv").csv({typed: true});
```

```js
const incOrdenadas = [...incidencias].sort((a, b) => b.incidencia - a.incidencia);

display(html`<div class="paneles">
  ${panel({
    titulo: "Inflación anual",
    subtitulo: "Variación anual del IPC, %",
    fuente: fuente("inflacion_aa"),
    contenido: grafico({
      series: [{nombre: "Inflación anual", datos: desde("inflacion_aa", 2015)}],
      frecuencia: "M", unidad: "%", decimales: 2, cero: true
    })
  })}
  ${panel({
    titulo: "Inflación mensual",
    subtitulo: "Variación mensual del IPC, %, últimos 36 meses",
    fuente: fuente("inflacion_mm"),
    contenido: grafico({
      series: [{nombre: "Inflación mensual", datos: db.serie("inflacion_mm").slice(-36)}],
      frecuencia: "M", unidad: "%", decimales: 2, tipo: "column", cero: true
    })
  })}
  ${panel({
    titulo: "Incidencia en la inflación mensual por división de consumo",
    subtitulo: `Puntos porcentuales, ${formatoPeriodo(+fechaIncidenciasIpc, "M")}`,
    fuente: "INEC, Índice de Precios al Consumidor",
    ancho: true,
    contenido: graficoCategorias({
      categorias: incOrdenadas.map((d) => d.division),
      series: [{nombre: "Incidencia", datos: incOrdenadas.map((d) => d.incidencia)}],
      tipo: "bar", unidad: "pp", decimales: 3, cero: true, altura: 420
    })
  })}
</div>`);
```

## Mercado laboral

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Tasa de desempleo",
    subtitulo: "% de la población económicamente activa",
    fuente: fuente("desempleo"),
    contenido: grafico({
      series: [{nombre: "Desempleo", datos: desde("desempleo", 2015)}],
      frecuencia: "M", unidad: "%", decimales: 1
    })
  })}
  ${panel({
    titulo: "Empleo adecuado y subempleo",
    subtitulo: "% de la población económicamente activa",
    fuente: fuente("empleo_adecuado"),
    contenido: grafico({
      series: [
        {nombre: "Empleo adecuado", datos: desde("empleo_adecuado", 2015)},
        {nombre: "Subempleo", datos: desde("subempleo", 2015)}
      ],
      frecuencia: "M", unidad: "%", decimales: 1
    })
  })}
</div>`);
```

## Indicadores de coyuntura

```js
const mesVentas = mesUltimo(db.serie("ventas_sri"));
const anioVentas = new Date(db.ultimo("ventas_sri")[0]).getUTCFullYear();
const ventasAcum = acumuladoAnual(db.serie("ventas_sri"), mesVentas);
const etiquetaVentas = (t) => etiquetaAcumulado(mesVentas, new Date(t).getUTCFullYear());

display(html`<div class="paneles">
  ${panel({
    titulo: "Expectativas empresariales",
    subtitulo: "Índice de Expectativas Empresariales (IEE); 50 = neutral",
    fuente: fuente("iee"),
    contenido: grafico({
      series: [{nombre: "IEE global", datos: desde("iee", 2018)}],
      frecuencia: "M", unidad: "", decimales: 1, referencia: 50
    })
  })}
  ${panel({
    titulo: "Confianza del consumidor",
    subtitulo: "Índice de Confianza del Consumidor (ICC); 50 = neutral",
    fuente: fuente("icc"),
    contenido: grafico({
      series: [
        {nombre: "Situación presente", datos: db.serie("icc_presente")},
        {nombre: "Situación futura", datos: db.serie("icc_futura")}
      ],
      frecuencia: "M", unidad: "", decimales: 1
    })
  })}
  ${panel({
    titulo: "Ventas declaradas al SRI",
    subtitulo: `Ventas totales y exportaciones, USD millones, acumulado ${etiquetaAcumulado(mesVentas)}`,
    fuente: fuente("ventas_sri"),
    contenido: grafico({
      series: [{nombre: "Ventas", datos: ventasAcum}],
      frecuencia: "A", unidad: "USD mm", decimales: 0, tipo: "column", periodo: etiquetaVentas
    })
  })}
  ${panel({
    titulo: "Despachos de cemento",
    subtitulo: "Miles de toneladas métricas, mensual",
    fuente: fuente("cemento_despachos"),
    contenido: grafico({
      series: [{nombre: "Despachos", datos: db.serie("cemento_despachos")}],
      frecuencia: "M", unidad: "miles t", decimales: 1, tipo: "column"
    })
  })}
</div>`);
```

```js
const ventasSector = FileAttachment("data/ventas_sector.csv").csv({typed: true});
```

```js
// Ventas por sección CIIU, acumulado del año frente al mismo período del año previo.
function ventasPorSector(anio) {
  const m = new Map();
  for (const {fecha, nombre, ventas} of ventasSector) {
    if (fecha.getUTCFullYear() !== anio || fecha.getUTCMonth() > mesVentas) continue;
    m.set(nombre, (m.get(nombre) ?? 0) + ventas);
  }
  return m;
}
const vActual = ventasPorSector(anioVentas);
const vPrevio = ventasPorSector(anioVentas - 1);
const totalVentas = [...vActual.values()].reduce((a, b) => a + b, 0);
const sectoresVentas = [...vActual.keys()].sort((a, b) => vActual.get(b) - vActual.get(a)).slice(0, 12);

display(panel({
  titulo: "Ventas por actividad económica",
  subtitulo: `USD millones, acumulado ${etiquetaAcumulado(mesVentas)}; 12 secciones CIIU con mayores ventas`,
  fuente: fuente("ventas_sri"),
  ancho: true,
  contenido: html`<div class="tabla-wrap"><table class="tablero cuadro">
    <thead><tr><th>Sección CIIU</th><th>${etiquetaAcumulado(mesVentas, anioVentas - 1)}</th><th>${etiquetaAcumulado(mesVentas, anioVentas)}</th><th>Var.</th><th>Part.</th></tr></thead>
    <tbody>${sectoresVentas.map((s) => html`<tr class="fila-item nivel-0">
      <td>${s}</td>
      <td>${formatoNumero(vPrevio.get(s) ?? 0, 0)}</td>
      <td>${formatoNumero(vActual.get(s), 0)}</td>
      <td>${vPrevio.get(s) ? formatoCambio((vActual.get(s) / vPrevio.get(s) - 1) * 100, 1, "%") : "–"}</td>
      <td>${formatoNumero((vActual.get(s) / totalVentas) * 100, 1)}%</td>
    </tr>`)}</tbody>
  </table></div>`
}));
```

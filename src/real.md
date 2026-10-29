---
title: Sector real
---

```js
import {db, fechaIncidenciasIpc, previsiones} from "./components/base.js";
import {acumuladoAnual, etiquetaAcumulado, mesUltimo, variacion, sumaMovil, formatoNumero, formatoCambio, formatoPeriodo} from "./components/datos.js";
import {grafico, graficoCategorias} from "./components/graficos.js";
import {kpiSerie, panel, cabecera, cuadroComparativo, graficoPrevisiones, tablaPrevisiones} from "./components/ui.js";

const fuente = (id) => db.meta(id).fuente;
const desde = (id, anio) => db.serie(id).filter(([t]) => t >= Date.UTC(anio, 0, 1));
```

```js
display(cabecera({
  antetitulo: "Sector real",
  titulo: "Actividad, precios y empleo",
  bajada: "Producción por el lado del gasto y por industrias, previsiones de crecimiento, actividad mensual, inflación, mercado laboral, indicadores de coyuntura y ventas locales.",
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

## Previsiones de crecimiento

Crecimiento real del PIB previsto por el BCE, el Ministerio de Economía y Finanzas, el FMI, el Banco Mundial y la CEPAL, según su informe más reciente.

```js
const aniosPrevision = [...new Set(previsiones.flatMap((p) => [...p.valores.keys()]))].sort();

display(html`<div class="paneles">
  ${panel({
    titulo: "Previsiones de crecimiento del PIB real",
    subtitulo: `Variación anual, %, ${aniosPrevision.slice(0, 2).join(" y ")}`,
    fuente: previsiones.map((p) => p.institucion).join(", "),
    ancho: true,
    contenido: graficoPrevisiones(previsiones, aniosPrevision.slice(0, 2))
  })}
  ${panel({
    titulo: "Previsiones por institución",
    subtitulo: "Crecimiento real del PIB, %",
    fuente: previsiones.map((p) => p.institucion).join(", "),
    ancho: true,
    contenido: tablaPrevisiones(previsiones, aniosPrevision.slice(0, 4))
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
    fuente: `${fuente("inflacion_mm")}; ponderaciones del INEC (cálculo propio)`,
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
    titulo: "Despachos de cemento",
    subtitulo: "Miles de toneladas métricas, mensual",
    fuente: fuente("cemento_despachos"),
    ancho: true,
    contenido: grafico({
      series: [{nombre: "Despachos", datos: db.serie("cemento_despachos")}],
      frecuencia: "M", unidad: "miles t", decimales: 1, tipo: "column"
    })
  })}
</div>`);
```

## Ventas locales

Ventas declaradas al SRI en el formulario 104 (casillero 419, ventas totales y exportaciones) menos las exportaciones de bienes y servicios (casilleros 417 y 418).

```js
const ventasSector = FileAttachment("data/ventas_sector.csv").csv({typed: true});
```

```js
const ventas = db.serie("ventas_locales");
const mesVentas = mesUltimo(ventas);
const anioVentas = new Date(db.ultimo("ventas_locales")[0]).getUTCFullYear();
const etiquetaVentas = (t) => etiquetaAcumulado(mesVentas, new Date(t).getUTCFullYear());

// Acumulado de enero al mes de corte por código (sección CIIU o división de comercio).
function ventasPorCodigo(anio) {
  const m = new Map();
  for (const {fecha, codigo, nombre, ventas} of ventasSector) {
    if (fecha.getUTCFullYear() !== anio || fecha.getUTCMonth() > mesVentas) continue;
    const x = m.get(codigo) ?? {nombre, ventas: 0};
    x.ventas += ventas;
    m.set(codigo, x);
  }
  return m;
}
const vActual = ventasPorCodigo(anioVentas);
const vPrevio = ventasPorCodigo(anioVentas - 1);
const v = (m, c) => m.get(c)?.ventas ?? 0;
const secciones = [...vActual.keys()].filter((c) => c.length === 1);
const total = (m) => secciones.reduce((a, c) => a + v(m, c), 0);
const principales = [...secciones].sort((a, b) => v(vActual, b) - v(vActual, a)).slice(0, 10);
const otras = secciones.filter((c) => !principales.includes(c));
const divisionesComercio = ["G46", "G47", "G45"];

const filasVentas = [
  {nombre: "Total", tipo: "total", nivel: 0, a: total(vPrevio), b: total(vActual)},
  ...principales.flatMap((c) => [
    {nombre: vActual.get(c).nombre, tipo: c === "G" ? "subgrupo" : "item", nivel: 0, a: v(vPrevio, c), b: v(vActual, c)},
    ...(c === "G" ? divisionesComercio.map((d) => ({nombre: vActual.get(d)?.nombre ?? d, tipo: "item", nivel: 1, a: v(vPrevio, d), b: v(vActual, d)})) : [])
  ]),
  {nombre: "Otras secciones", tipo: "item", nivel: 0, a: otras.reduce((s, c) => s + v(vPrevio, c), 0), b: otras.reduce((s, c) => s + v(vActual, c), 0)}
];

display(html`<div class="paneles">
  ${panel({
    titulo: "Ventas locales acumuladas",
    subtitulo: `USD millones, acumulado ${etiquetaAcumulado(mesVentas)}`,
    fuente: fuente("ventas_locales"),
    contenido: grafico({
      series: [{nombre: "Ventas locales", datos: acumuladoAnual(ventas, mesVentas)}],
      frecuencia: "A", unidad: "USD mm", decimales: 0, tipo: "column", periodo: etiquetaVentas
    })
  })}
  ${panel({
    titulo: "Crecimiento de las ventas locales",
    subtitulo: "Variación anual, %: mensual y de la suma de 12 meses",
    fuente: fuente("ventas_locales"),
    contenido: grafico({
      series: [
        // Desde 2022: las variaciones de 2021 reflejan la caída de 2020.
        {nombre: "Mensual", datos: variacion(ventas, 12).filter(([t]) => t >= Date.UTC(2022, 0, 1))},
        {nombre: "Suma 12 meses", datos: variacion(sumaMovil(ventas, 12), 12).filter(([t]) => t >= Date.UTC(2022, 0, 1)), tipo: "line", color: "tinta"}
      ],
      frecuencia: "M", unidad: "%", decimales: 1, tipo: "column", cero: true
    })
  })}
  ${panel({
    titulo: "Ventas locales por actividad económica",
    subtitulo: `USD millones, acumulado ${etiquetaAcumulado(mesVentas)}; 10 secciones CIIU con mayores ventas y, en comercio, sus divisiones`,
    fuente: fuente("ventas_locales"),
    ancho: true,
    contenido: cuadroComparativo({
      filas: filasVentas,
      columnaA: etiquetaAcumulado(mesVentas, anioVentas - 1),
      columnaB: etiquetaAcumulado(mesVentas, anioVentas)
    })
  })}
</div>`);
```

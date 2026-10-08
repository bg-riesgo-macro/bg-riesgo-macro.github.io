---
title: Sector externo
---

```js
import {db} from "./components/base.js";
import {acumuladoAnual, etiquetaAcumulado, mesUltimo, formatoNumero, formatoCambio, MESES} from "./components/datos.js";
import {grafico, graficoCategorias} from "./components/graficos.js";
import {kpi, panel, cabecera} from "./components/ui.js";

const fuente = (id) => db.meta(id).fuente;
```

```js
// Corte del acumulado: último mes con datos de balanza comercial.
const mes = mesUltimo(db.serie("x_total"));
const anioActual = new Date(db.ultimo("x_total")[0]).getUTCFullYear();
const anioPrevio = anioActual - 1;
const acum = (id) => acumuladoAnual(db.serie(id), mes).filter(([t]) => new Date(t).getUTCFullYear() >= 2018);
const etiqueta = (t) => etiquetaAcumulado(mes, new Date(t).getUTCFullYear());
const periodo = etiquetaAcumulado(mes, anioActual);
const periodoCorto = etiquetaAcumulado(mes);

// KPI de un acumulado: compara con el mismo período del año anterior.
function kpiAcumulado(titulo, datos, {nivel = true} = {}) {
  const [, v] = datos[datos.length - 1];
  const [, ant] = datos[datos.length - 2];
  return kpi({
    titulo, datos, frecuencia: "A", unidad: "USD mm", decimales: 0, periodo, etiquetaPunto: etiqueta,
    cambio: nivel
      ? {valor: (v / ant - 1) * 100, unidad: "%", etiqueta: "a/a"}
      : {valor: v - ant, unidad: "USD mm", decimales: 0, etiqueta: "vs. año previo"}
  });
}
```

```js
display(cabecera({
  antetitulo: "Sector externo",
  titulo: "Comercio exterior y balanza de pagos",
  bajada: `Exportaciones, importaciones y balanza comercial acumuladas de enero a ${MESES[mes]} de cada año; detalle por producto y por uso económico; cuenta corriente, remesas e inversión extranjera.`,
  corte: db.ultimo("x_total")[0]
}));

display(html`<div class="kpis">
  ${kpiAcumulado("Exportaciones", acum("x_total"))}
  ${kpiAcumulado("Exportaciones no petroleras", acum("x_no_pet"))}
  ${kpiAcumulado("Importaciones", acum("m_total"))}
  ${kpiAcumulado("Balanza comercial", acum("bc_total"), {nivel: false})}
</div>`);
```

## Balanza comercial

Cifras acumuladas de enero a ${MESES[mes]} de cada año, en millones de USD FOB.

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Exportaciones",
    subtitulo: `USD millones FOB, acumulado ${periodoCorto}`,
    fuente: fuente("x_total"),
    contenido: grafico({
      series: [
        {nombre: "Petroleras", datos: acum("x_pet")},
        {nombre: "No petroleras", datos: acum("x_no_pet")}
      ],
      frecuencia: "A", unidad: "USD mm", decimales: 0, tipo: "column", apilado: true, periodo: etiqueta
    })
  })}
  ${panel({
    titulo: "Importaciones",
    subtitulo: `USD millones FOB, acumulado ${periodoCorto}`,
    fuente: fuente("m_total"),
    contenido: grafico({
      series: [
        {nombre: "Petroleras", datos: acum("m_pet")},
        {nombre: "No petroleras", datos: acum("m_no_pet")}
      ],
      frecuencia: "A", unidad: "USD mm", decimales: 0, tipo: "column", apilado: true, periodo: etiqueta
    })
  })}
  ${panel({
    titulo: "Balanza comercial",
    subtitulo: `USD millones FOB, acumulado ${periodoCorto}`,
    fuente: fuente("bc_total"),
    contenido: grafico({
      series: [
        {nombre: "Petrolera", datos: acum("bc_pet")},
        {nombre: "No petrolera", datos: acum("bc_no_pet")},
        {nombre: "Total", datos: acum("bc_total"), tipo: "line", color: "tinta"}
      ],
      frecuencia: "A", unidad: "USD mm", decimales: 0, tipo: "column", apilado: true, cero: true, periodo: etiqueta
    })
  })}
  ${panel({
    titulo: "Términos de intercambio",
    subtitulo: "Índice, mensual",
    fuente: fuente("terminos_intercambio"),
    contenido: grafico({
      series: [{nombre: "Términos de intercambio", datos: db.serie("terminos_intercambio").filter(([t]) => t >= Date.UTC(2015, 0, 1))}],
      frecuencia: "M", unidad: "", decimales: 1
    })
  })}
</div>`);
```

## Exportaciones por producto

```js
const productos = FileAttachment("data/exportaciones.json").json();
const exportaciones = FileAttachment("data/exportaciones.csv").csv({typed: true});
```

```js
// Acumulado enero–mes de corte por producto, para el año actual y el previo.
function acumuladoPorProducto(anio) {
  const m = new Map();
  for (const {fecha, codigo, fob, tm} of exportaciones) {
    if (fecha.getUTCFullYear() !== anio || fecha.getUTCMonth() > mes) continue;
    const acc = m.get(codigo) ?? {fob: 0, tm: 0};
    acc.fob += fob;
    acc.tm += tm ?? 0;
    m.set(codigo, acc);
  }
  return m;
}
const actual = acumuladoPorProducto(anioActual);
const previo = acumuladoPorProducto(anioPrevio);
const codigos = Object.keys(productos).map(Number);
const del = (grupo) => codigos.filter((c) => productos[c].grupo === grupo);
const suma = (mapa, cs, campo = "fob") => cs.reduce((s, c) => s + (mapa.get(c)?.[campo] ?? 0), 0);

const NIVEL = {total: 0, grupo: 0, subgrupo: 1, item: 2};

function fila(nombre, cs, tipo, {volumen = false, nivel = NIVEL[tipo]} = {}) {
  return {nombre, tipo, nivel, a: suma(previo, cs), b: suma(actual, cs),
    tmA: volumen ? suma(previo, cs, "tm") : null, tmB: volumen ? suma(actual, cs, "tm") : null};
}

// Top 5 por valor acumulado del año actual y el resto agrupado.
function top(grupo, n = 5) {
  const cs = del(grupo).sort((x, y) => suma(actual, [y]) - suma(actual, [x]));
  return {top: cs.slice(0, n), resto: cs.slice(n)};
}
const primarios = top("primario");
const industrializados = top("industrializado");
const noPetroleros = [...del("primario"), ...del("industrializado"), ...del("otro")];

const filasCuadro = [
  fila("Exportaciones totales", codigos, "total"),
  fila("Petroleras", del("petrolero"), "grupo"),
  ...del("petrolero").map((c) => fila(productos[c].producto, [c], "item", {volumen: true, nivel: 1})),
  fila("No petroleras", noPetroleros, "grupo"),
  fila("Primarias", del("primario"), "subgrupo"),
  ...primarios.top.map((c) => fila(productos[c].producto, [c], "item", {volumen: true})),
  fila("Otras primarias", primarios.resto, "item"),
  fila("Industrializadas", del("industrializado"), "subgrupo"),
  ...industrializados.top.map((c) => fila(productos[c].producto, [c], "item", {volumen: true})),
  fila("Otras industrializadas", industrializados.resto, "item"),
  fila("Otras no petroleras", del("otro"), "subgrupo")
];
const totalActual = filasCuadro[0].b;

function cuadro(filas, {volumen = true} = {}) {
  const variacion = (a, b) => (a > 0 ? formatoCambio((b / a - 1) * 100, 1, "%") : "–");
  return html`<div class="tabla-wrap"><table class="tablero cuadro">
    <thead><tr>
      <th></th>
      <th>${etiquetaAcumulado(mes, anioPrevio)}</th>
      <th>${etiquetaAcumulado(mes, anioActual)}</th>
      <th>Var. valor</th>
      <th>Part. ${anioActual}</th>
      ${volumen ? html`<th>Var. volumen</th>` : null}
    </tr></thead>
    <tbody>${filas.map((f) => html`<tr class=${`fila-${f.tipo} nivel-${f.nivel}`}>
      <td>${f.nombre}</td>
      <td>${formatoNumero(f.a, 1)}</td>
      <td>${formatoNumero(f.b, 1)}</td>
      <td>${variacion(f.a, f.b)}</td>
      <td>${formatoNumero((f.b / filas[0].b) * 100, 1)}%</td>
      ${volumen ? html`<td>${f.tmA != null ? variacion(f.tmA, f.tmB) : ""}</td>` : null}
    </tr>`)}</tbody>
  </table></div>`;
}
```

Valores FOB en millones de USD, acumulados de enero a ${MESES[mes]}. Los cinco principales productos primarios e industrializados se ordenan por su valor en ${anioActual}. La variación de volumen se calcula en toneladas métricas.

```js
display(panel({
  titulo: "Exportaciones por producto principal",
  subtitulo: `USD millones FOB, acumulado ${periodoCorto}`,
  fuente: "BCE, base de exportaciones por producto (clasificación BCE)",
  ancho: true,
  contenido: cuadro(filasCuadro)
}));
```

```js
// Diez principales productos no petroleros, comparación con el año previo.
const top10 = noPetroleros
  .filter((c) => productos[c].grupo !== "otro")
  .sort((x, y) => suma(actual, [y]) - suma(actual, [x]))
  .slice(0, 10);

display(html`<div class="paneles">
  ${panel({
    titulo: "Principales exportaciones no petroleras",
    subtitulo: `USD millones FOB, acumulado ${periodoCorto}`,
    fuente: "BCE",
    ancho: true,
    contenido: graficoCategorias({
      categorias: top10.map((c) => productos[c].producto),
      series: [
        {nombre: `${anioPrevio}`, datos: top10.map((c) => suma(previo, [c])), color: "suave"},
        {nombre: `${anioActual}`, datos: top10.map((c) => suma(actual, [c])), color: 0}
      ],
      tipo: "bar", unidad: "USD mm", decimales: 1, altura: 420
    })
  })}
</div>`);
```

## Importaciones por uso o destino económico

```js
const cuode = FileAttachment("data/importaciones.json").json();
const importaciones = FileAttachment("data/importaciones.csv").csv({typed: true});
```

```js
function importacionesPorCuode(anio) {
  const m = new Map();
  for (const {fecha, cuode: codigo, fob} of importaciones) {
    if (fecha.getUTCFullYear() !== anio || fecha.getUTCMonth() > mes) continue;
    const c = String(codigo).padStart(2, "0"); // el CSV tipado lee "01" como número
    m.set(c, (m.get(c) ?? 0) + fob);
  }
  return m;
}
const impActual = importacionesPorCuode(anioActual);
const impPrevio = importacionesPorCuode(anioPrevio);
const clavesCuode = Object.keys(cuode);
const filaImp = (nombre, cs, tipo) => ({
  nombre, tipo, nivel: {total: 0, grupo: 0, item: 1}[tipo],
  a: cs.reduce((s, c) => s + (impPrevio.get(c) ?? 0), 0),
  b: cs.reduce((s, c) => s + (impActual.get(c) ?? 0), 0)
});
const gruposCuode = ["Bienes de consumo", "Materias primas", "Bienes de capital", "Combustibles y lubricantes", "Diversos"];

const filasImp = [
  filaImp("Importaciones totales", clavesCuode, "total"),
  ...gruposCuode.flatMap((g) => {
    const cs = clavesCuode.filter((c) => cuode[c].grupo === g);
    return [filaImp(g, cs, "grupo"), ...(cs.length > 1 ? cs.map((c) => filaImp(cuode[c].descripcion, [c], "item")) : [])];
  })
];

display(html`<div class="paneles">
  ${panel({
    titulo: "Importaciones por uso o destino económico (CUODE)",
    subtitulo: `USD millones FOB, acumulado ${periodoCorto}`,
    fuente: "BCE, base de importaciones por CUODE",
    ancho: true,
    contenido: cuadro(filasImp, {volumen: false})
  })}
  ${panel({
    titulo: "Importaciones por grupo",
    subtitulo: `USD millones FOB, acumulado ${periodoCorto}`,
    fuente: "BCE",
    ancho: true,
    contenido: graficoCategorias({
      categorias: gruposCuode,
      series: [
        {nombre: `${anioPrevio}`, datos: gruposCuode.map((g) => filasImp.find((f) => f.nombre === g).a), color: "suave"},
        {nombre: `${anioActual}`, datos: gruposCuode.map((g) => filasImp.find((f) => f.nombre === g).b), color: 0}
      ],
      tipo: "bar", unidad: "USD mm", decimales: 0, altura: 340
    })
  })}
</div>`);
```

## Balanza de pagos

```js
// Acumulado de los trimestres disponibles del año (p. ej. T1–T2).
const trimestre = Math.floor(mesUltimo(db.serie("cuenta_corriente")) / 3) + 1;
const mesTrim = (trimestre - 1) * 3;
const acumT = (id) => acumuladoAnual(db.serie(id), mesTrim).filter(([t]) => new Date(t).getUTCFullYear() >= 2016);
const etiquetaT = (t) => `${trimestre === 4 ? "Año" : `T1–T${trimestre}`} ${new Date(t).getUTCFullYear()}`;
const subT = trimestre === 4 ? "anual" : `acumulado T1–T${trimestre}`;

display(html`<div class="paneles">
  ${panel({
    titulo: "Cuenta corriente por componente",
    subtitulo: "USD millones, trimestral",
    fuente: fuente("cuenta_corriente"),
    ancho: true,
    contenido: grafico({
      series: [
        {nombre: "Bienes", datos: db.serie("bp_bienes")},
        {nombre: "Servicios", datos: db.serie("bp_servicios")},
        {nombre: "Ingreso primario", datos: db.serie("bp_ingreso_primario")},
        {nombre: "Ingreso secundario", datos: db.serie("bp_ingreso_secundario")},
        {nombre: "Cuenta corriente", datos: db.serie("cuenta_corriente"), tipo: "line", color: "tinta"}
      ],
      frecuencia: "T", unidad: "USD mm", decimales: 0, tipo: "column", apilado: true, cero: true, altura: 360
    })
  })}
  ${panel({
    titulo: "Cuenta corriente",
    subtitulo: "Saldo anual, % del PIB",
    fuente: fuente("cuenta_corriente_pib"),
    contenido: grafico({
      series: [{nombre: "Cuenta corriente", datos: db.serie("cuenta_corriente_pib")}],
      frecuencia: "A", unidad: "% PIB", decimales: 1, tipo: "column", cero: true
    })
  })}
  ${panel({
    titulo: "Remesas",
    subtitulo: `USD millones, ${subT}`,
    fuente: fuente("remesas_recibidas"),
    contenido: grafico({
      series: [
        {nombre: "Recibidas", datos: acumT("remesas_recibidas")},
        {nombre: "Enviadas", datos: acumT("remesas_enviadas")}
      ],
      frecuencia: "A", unidad: "USD mm", decimales: 0, tipo: "column", periodo: etiquetaT
    })
  })}
  ${panel({
    titulo: "Inversión extranjera directa",
    subtitulo: `Pasivos netos incurridos, USD millones, ${subT}`,
    fuente: fuente("ied"),
    contenido: grafico({
      series: [{nombre: "IED", datos: acumT("ied")}],
      frecuencia: "A", unidad: "USD mm", decimales: 0, tipo: "column", cero: true, periodo: etiquetaT
    })
  })}
</div>`);
```

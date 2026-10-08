---
title: Sector fiscal
---

```js
import {db, fechaPerfilVencimientos} from "./components/base.js";
import {acumuladoAnual, etiquetaAcumulado, mesUltimo, sumaMovil, combinar, formatoPeriodo, MESES} from "./components/datos.js";
import {grafico} from "./components/graficos.js";
import {kpiSerie, kpiAcumulado, panel, cabecera, cuadroComparativo} from "./components/ui.js";

const fuente = (id) => db.meta(id).fuente;
const desde = (serie, anio) => serie.filter(([t]) => t >= Date.UTC(anio, 0, 1));
const anioDe = (t) => new Date(t).getUTCFullYear();

// Operaciones del SPNF: acumulado de enero al último mes disponible.
const mes = mesUltimo(db.serie("spnf_ingresos"));
const anioActual = anioDe(db.ultimo("spnf_ingresos")[0]);
const acum = (id, anio = 2014) => desde(acumuladoAnual(db.serie(id), mes), anio);
const etiqueta = (t) => etiquetaAcumulado(mes, anioDe(t));
const periodoCorto = etiquetaAcumulado(mes);

// Recaudación SRI: su propio mes de corte.
const mesSri = mesUltimo(db.serie("sri_neta"));
const acumSri = (id) => acumuladoAnual(db.serie(id), mesSri);
const etiquetaSri = (t) => etiquetaAcumulado(mesSri, anioDe(t));
```

```js
display(cabecera({
  antetitulo: "Sector fiscal",
  titulo: "Finanzas públicas y deuda",
  bajada: `Operaciones del Sector Público No Financiero acumuladas de enero a ${MESES[mes]}, recaudación tributaria, saldo de la deuda pública y su perfil de vencimientos.`,
  corte: db.ultimo("spnf_ingresos")[0]
}));

display(html`<div class="kpis">
  ${kpiAcumulado({titulo: "Resultado global del SPNF", datos: acum("spnf_resultado_global"), mes, nivel: false})}
  ${kpiAcumulado({titulo: "Resultado primario del SPNF", datos: acum("spnf_resultado_primario"), mes, nivel: false})}
  ${kpiSerie(db, "deuda_pib")}
  ${kpiAcumulado({titulo: "Recaudación neta SRI", datos: acumSri("sri_neta"), mes: mesSri})}
</div>`);
```

## Resultado fiscal

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Resultados del SPNF",
    subtitulo: "% del PIB, anual",
    fuente: fuente("resultado_global_pib"),
    contenido: grafico({
      series: [
        {nombre: "Resultado global", datos: db.serie("resultado_global_pib")},
        {nombre: "Resultado primario", datos: db.serie("resultado_primario_pib")},
        {nombre: "Primario no petrolero", datos: db.serie("primario_no_petrolero_pib")}
      ],
      frecuencia: "A", unidad: "% PIB", decimales: 1, tipo: "column", cero: true
    })
  })}
  ${panel({
    titulo: "Resultados acumulados en el año",
    subtitulo: `USD millones, acumulado ${periodoCorto}`,
    fuente: fuente("spnf_resultado_global"),
    contenido: grafico({
      series: [
        {nombre: "Resultado global", datos: acum("spnf_resultado_global")},
        {nombre: "Resultado primario", datos: acum("spnf_resultado_primario")}
      ],
      frecuencia: "A", unidad: "USD mm", decimales: 0, tipo: "column", cero: true, periodo: etiqueta
    })
  })}
</div>`);
```

## Ingresos y gastos

```js
const spnf = FileAttachment("data/spnf.csv").csv({typed: true});
```

```js
// Acumulado por partida (código del MEF) para el año actual y el previo.
function acumuladoPorCodigo(anio) {
  const m = new Map();
  for (const {fecha, codigo, valor} of spnf) {
    if (fecha.getUTCFullYear() !== anio || fecha.getUTCMonth() > mes) continue;
    const c = String(codigo);
    m.set(c, (m.get(c) ?? 0) + valor);
  }
  return m;
}
const actual = acumuladoPorCodigo(anioActual);
const previo = acumuladoPorCodigo(anioActual - 1);
const fila = (nombre, codigos, tipo, nivel) => ({
  nombre, tipo, nivel,
  a: codigos.reduce((s, c) => s + (previo.get(c) ?? 0), 0),
  b: codigos.reduce((s, c) => s + (actual.get(c) ?? 0), 0)
});

const filasSpnf = [
  fila("Ingresos totales", ["1"], "total", 0),
  fila("Petroleros", ["11"], "subgrupo", 1),
  fila("Exportación", ["111"], "item", 2),
  fila("Venta doméstica de derivados", ["112"], "item", 2),
  fila("No petroleros", ["12"], "subgrupo", 1),
  fila("Tributarios", ["121"], "item", 2),
  fila("Impuesto a la renta", ["1211"], "item", 3),
  fila("IVA", ["1212"], "item", 3),
  fila("ICE", ["1213"], "item", 3),
  fila("Arancelarios", ["1214"], "item", 3),
  fila("Otros impuestos", ["1215", "1216"], "item", 3),
  fila("Contribuciones a la seguridad social", ["122"], "item", 2),
  fila("Transferencias, intereses y otros", ["123", "124", "125"], "item", 2),
  fila("Gastos totales", ["2"], "total", 0),
  fila("Permanentes", ["21"], "subgrupo", 1),
  fila("Sueldos y salarios", ["211"], "item", 2),
  fila("Compra de bienes y servicios", ["212"], "item", 2),
  fila("Intereses", ["213"], "item", 2),
  fila("Transferencias", ["214"], "item", 2),
  fila("Prestaciones de seguridad social", ["215"], "item", 2),
  fila("Otros gastos permanentes", ["216"], "item", 2),
  fila("No permanentes", ["22"], "subgrupo", 1),
  fila("Inversión en activos no financieros", ["221"], "item", 2),
  fila("Transferencias y otros no permanentes", ["222", "223"], "item", 2),
  fila("Resultado global", ["3"], "grupo", 0),
  fila("Resultado primario", ["4"], "grupo", 0),
  fila("Resultado primario no petrolero", ["41"], "grupo", 0),
  fila("Pro memoria: subsidios a los combustibles", ["57"], "item", 0)
];

display(panel({
  titulo: "Operaciones del Sector Público No Financiero",
  subtitulo: `USD millones, acumulado ${periodoCorto}`,
  fuente: fuente("spnf_ingresos"),
  ancho: true,
  contenido: cuadroComparativo({
    filas: filasSpnf, participacion: false, diferencia: true,
    columnaA: etiquetaAcumulado(mes, anioActual - 1),
    columnaB: etiquetaAcumulado(mes, anioActual)
  })
}));
```

```js
const ingresosNoTributarios = combinar(
  combinar(db.serie("spnf_ingresos"), db.serie("spnf_ing_petroleros"), (a, b) => a - b),
  db.serie("spnf_tributarios"), (a, b) => a - b
);
const acumSerie = (serie) => desde(acumuladoAnual(serie, mes), 2014);
const gastosPermanentes = combinar(db.serie("spnf_gastos"), db.serie("spnf_inversion"), (a, b) => a - b);

display(html`<div class="paneles">
  ${panel({
    titulo: "Ingresos por fuente",
    subtitulo: `USD millones, acumulado ${periodoCorto}`,
    fuente: fuente("spnf_ingresos"),
    contenido: grafico({
      series: [
        {nombre: "Petroleros", datos: acum("spnf_ing_petroleros")},
        {nombre: "Tributarios", datos: acum("spnf_tributarios")},
        {nombre: "Otros no petroleros", datos: acumSerie(ingresosNoTributarios)}
      ],
      frecuencia: "A", unidad: "USD mm", decimales: 0, tipo: "column", apilado: true, periodo: etiqueta
    })
  })}
  ${panel({
    titulo: "Gastos: inversión e intereses",
    subtitulo: `USD millones, acumulado ${periodoCorto}`,
    fuente: fuente("spnf_gastos"),
    contenido: grafico({
      series: [
        {nombre: "Inversión en activos no financieros", datos: acum("spnf_inversion")},
        {nombre: "Intereses", datos: acum("spnf_intereses")},
        {nombre: "Subsidios a combustibles", datos: acum("spnf_subsidios_combustibles", 2018)}
      ],
      frecuencia: "A", unidad: "USD mm", decimales: 0, tipo: "column", periodo: etiqueta
    })
  })}
  ${panel({
    titulo: "Ingresos y gastos del SPNF",
    subtitulo: "USD millones, suma móvil de 12 meses",
    fuente: fuente("spnf_ingresos"),
    ancho: true,
    contenido: grafico({
      series: [
        {nombre: "Ingresos", datos: desde(sumaMovil(db.serie("spnf_ingresos"), 12), 2015)},
        {nombre: "Gastos", datos: desde(sumaMovil(db.serie("spnf_gastos"), 12), 2015)}
      ],
      frecuencia: "M", unidad: "USD mm", decimales: 0
    })
  })}
</div>`);
```

## Recaudación tributaria

```js
const impuestos = [["Impuesto a la renta", "sri_renta"], ["IVA", "sri_iva"], ["ICE", "sri_ice"], ["ISD", "sri_isd"], ["Vehículos", "sri_vehiculos"]];
const anioSri = anioDe(db.ultimo("sri_neta")[0]);
const enAnio = (id, anio) => acumSri(id).find(([t]) => anioDe(t) === anio)?.[1] ?? 0;
const filaSri = (nombre, ids, tipo, nivel, signo = 1) => ({
  nombre, tipo, nivel,
  a: signo * ids.reduce((s, id) => s + enAnio(id, anioSri - 1), 0),
  b: signo * ids.reduce((s, id) => s + enAnio(id, anioSri), 0)
});
const bruta = filaSri("Recaudación bruta", ["sri_bruta"], "total", 0);
const principales = impuestos.map(([n, id]) => filaSri(n, [id], "item", 1));
const otros = {
  nombre: "Otros impuestos y contribuciones", tipo: "item", nivel: 1,
  a: bruta.a - principales.reduce((s, f) => s + f.a, 0),
  b: bruta.b - principales.reduce((s, f) => s + f.b, 0)
};
const neta = filaSri("Recaudación neta", ["sri_neta"], "total", 0);
const descuentos = {nombre: "(−) Notas de crédito, compensaciones y devoluciones", tipo: "grupo", nivel: 0, a: neta.a - bruta.a, b: neta.b - bruta.b};

// Composición de la recaudación bruta por año (acumulado).
const otrosSerie = (() => {
  const restar = (serie, id) => combinar(serie, db.serie(id), (a, b) => a - b);
  return ["sri_renta", "sri_iva", "sri_isd"].reduce(restar, db.serie("sri_bruta"));
})();

display(html`<div class="paneles">
  ${panel({
    titulo: "Recaudación por impuesto",
    subtitulo: `Recaudación bruta, USD millones, acumulado ${etiquetaAcumulado(mesSri)}`,
    fuente: fuente("sri_neta"),
    ancho: true,
    contenido: grafico({
      series: [
        {nombre: "Impuesto a la renta", datos: acumSri("sri_renta")},
        {nombre: "IVA", datos: acumSri("sri_iva")},
        {nombre: "ISD", datos: acumSri("sri_isd")},
        {nombre: "Otros", datos: acumuladoAnual(otrosSerie, mesSri)}
      ],
      frecuencia: "A", unidad: "USD mm", decimales: 0, tipo: "column", apilado: true, periodo: etiquetaSri
    })
  })}
  ${panel({
    titulo: "Recaudación del SRI",
    subtitulo: `USD millones, acumulado ${etiquetaAcumulado(mesSri)}`,
    fuente: fuente("sri_neta"),
    ancho: true,
    contenido: cuadroComparativo({
      filas: [bruta, ...principales, otros, descuentos, neta], participacion: false, diferencia: true,
      columnaA: etiquetaAcumulado(mesSri, anioSri - 1),
      columnaB: etiquetaAcumulado(mesSri, anioSri)
    })
  })}
</div>`);
```

## Deuda pública

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Deuda pública y otras obligaciones",
    subtitulo: "% del PIB, mensual (PIB de referencia de cada boletín del MEF)",
    fuente: fuente("deuda_pib"),
    contenido: grafico({
      series: [{nombre: "Deuda / PIB", datos: db.serie("deuda_pib")}],
      frecuencia: "M", unidad: "% PIB", decimales: 1
    })
  })}
  ${panel({
    titulo: "Saldo de la deuda pública",
    subtitulo: "USD millones, fin de mes",
    fuente: fuente("deuda_total"),
    contenido: grafico({
      series: [
        {nombre: "Externa", datos: db.serie("deuda_externa")},
        {nombre: "Interna y otras obligaciones", datos: db.serie("deuda_interna")}
      ],
      frecuencia: "M", unidad: "USD mm", decimales: 0, tipo: "column", apilado: true
    })
  })}
</div>`);
```

```js
const vencimientos = FileAttachment("data/vencimientos.csv").csv({typed: true});
```

```js
// Perfil de vencimientos: el primer año cubre solo los meses posteriores al corte.
const mesPerfil = fechaPerfilVencimientos.getUTCMonth();
const anioPerfil = fechaPerfilVencimientos.getUTCFullYear();
const anual = (concepto, hasta = 2040) => vencimientos
  .filter((d) => d.tipo === "anual" && d.concepto === concepto && d.fecha.getUTCFullYear() <= hasta)
  .map((d) => [+d.fecha, d.valor]);
const sumarSeries = (...series) => series[0].map(([t], i) => [t, series.reduce((s, x) => s + x[i][1], 0)]);
const mensual = (concepto) => vencimientos
  .filter((d) => d.tipo === "mensual" && d.concepto === concepto)
  .map((d) => [+d.fecha, d.valor]);
const etiquetaAnio = (t) => (anioDe(t) === anioPerfil
  ? `${MESES[mesPerfil + 1] ?? "dic"}–dic ${anioPerfil}`
  : `${anioDe(t)}`);

display(html`<div class="paneles">
  ${panel({
    titulo: "Perfil de vencimientos de la deuda pública",
    subtitulo: `Capital e intereses por año, USD millones · perfil a ${formatoPeriodo(+fechaPerfilVencimientos, "M")}; ${anioPerfil} incluye solo los meses restantes`,
    fuente: "MEF, Perfil de vencimientos de la deuda externa e interna",
    ancho: true,
    contenido: grafico({
      series: [
        {nombre: "Capital: organismos internacionales", datos: anual("capital_organismos")},
        {nombre: "Capital: bonos internacionales", datos: anual("capital_bonos")},
        {nombre: "Capital: gobiernos y bancos", datos: sumarSeries(anual("capital_gobiernos"), anual("capital_bancos"))},
        {nombre: "Capital: deuda interna", datos: anual("capital_interna")},
        {nombre: "Intereses totales", datos: sumarSeries(anual("intereses_externa"), anual("intereses_interna")), tipo: "line", color: "tinta"}
      ],
      frecuencia: "A", unidad: "USD mm", decimales: 0, tipo: "column", apilado: true, altura: 380, periodo: etiquetaAnio
    })
  })}
  ${panel({
    titulo: "Servicio de la deuda en los próximos meses",
    subtitulo: "Capital e intereses, deuda externa e interna, USD millones",
    fuente: "MEF, Perfil de vencimientos de corto plazo",
    ancho: true,
    contenido: grafico({
      series: [
        {nombre: "Capital", datos: mensual("capital_total")},
        {nombre: "Intereses", datos: mensual("intereses_total")}
      ],
      frecuencia: "M", unidad: "USD mm", decimales: 0, tipo: "column", apilado: true
    })
  })}
</div>`);
```

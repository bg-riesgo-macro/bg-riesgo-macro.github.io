---
title: Sector financiero
---

```js
import {db} from "./components/base.js";
import {variacion, valorEn, formatoNumero, formatoCambio, formatoPeriodo} from "./components/datos.js";
import {grafico} from "./components/graficos.js";
import {kpiSerie, panel, cabecera} from "./components/ui.js";

const fuente = (id) => db.meta(id).fuente;
const desde = (serie, anio) => serie.filter(([t]) => t >= Date.UTC(anio, 0, 1));
const s = (id, anio = 2015) => desde(db.serie(id), anio);

// Cambio de un saldo frente al último dato del año anterior (desde 2018).
function variacionEnElAnio(serie) {
  const cierre = new Map();
  for (const [t, v] of serie) cierre.set(new Date(t).getUTCFullYear(), v);
  return desde(serie, 2018).map(([t, v]) => [t, v - cierre.get(new Date(t).getUTCFullYear() - 1)]);
}
```

```js
display(cabecera({
  antetitulo: "Sector monetario y financiero",
  titulo: "Riesgo soberano, liquidez, crédito y tasas",
  bajada: "Riesgo país, bonos soberanos y reservas internacionales; depósitos, cartera, calidad de cartera, liquidez, solvencia y rentabilidad de los bancos privados; tasas de interés referenciales y por segmento de crédito.",
  corte: db.ultimo("depositos_bp")[0]
}));

display(html`<div class="kpis">
  ${kpiSerie(db, "embi")}
  ${kpiSerie(db, "reservas")}
  ${kpiSerie(db, "depositos_bp", {titulo: "Depósitos, bancos privados"})}
  ${kpiSerie(db, "morosidad_bp", {titulo: "Morosidad, bancos privados"})}
</div>`);
```

## Riesgo país

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Riesgo país (EMBI Ecuador)",
    subtitulo: "Puntos básicos, diario",
    fuente: fuente("embi"),
    nota: "Diferencia entre el rendimiento de los bonos de Ecuador en dólares y el de los bonos del Tesoro de EE. UU. (100 pb = 1 punto porcentual). Cuando sube, al Estado le cuesta más financiarse en los mercados internacionales, y ese mayor costo tiende a trasladarse a bancos y empresas.",
    ancho: true,
    contenido: grafico({
      series: [{nombre: "EMBI Ecuador", datos: db.serie("embi")}],
      frecuencia: "D", unidad: "pb", decimales: 0, navegador: true, rango: "5a", altura: 420
    })
  })}
</div>`);
```

## Bonos soberanos de Ecuador

Precio de los bonos globales en el mercado secundario, en dólares por cada 100 de valor nominal.

```js
const bonos = ["2030", "2034", "2035", "2039", "2040"];
const [tBonos] = db.ultimo("bono_2035");
const refBonos = [
  {etiqueta: "Var. 1 mes", t: tBonos - 30 * 864e5},
  {etiqueta: "Var. en el año", t: Date.UTC(new Date(tBonos).getUTCFullYear() - 1, 11, 31)},
  {etiqueta: "Var. 12 meses", t: Date.UTC(new Date(tBonos).getUTCFullYear() - 1, new Date(tBonos).getUTCMonth(), new Date(tBonos).getUTCDate())}
];

display(html`<div class="paneles">
  ${panel({
    titulo: "Precio de los bonos globales",
    subtitulo: "USD por 100 de valor nominal, diario",
    fuente: fuente("bono_2035"),
    nota: "Precio y rendimiento se mueven en sentido contrario: cuando el precio de un bono baja, el rendimiento que exige el mercado sube, y viceversa. Un precio por debajo de 100 indica que el mercado exige un rendimiento mayor que el cupón del bono.",
    ancho: true,
    contenido: grafico({
      series: ["2030", "2035", "2040"].map((b) => ({nombre: `Ecuador ${b}`, datos: db.serie(`bono_${b}`)})),
      frecuencia: "D", unidad: "USD por 100", decimales: 2, navegador: true, rango: "Todo"
    })
  })}
  ${panel({
    titulo: "Bonos globales de Ecuador",
    subtitulo: `Precio y variación, %, al ${formatoPeriodo(tBonos, "D")}`,
    fuente: fuente("bono_2035"),
    ancho: true,
    contenido: html`<div class="tabla-wrap"><table class="tablero cuadro">
      <thead><tr><th>Bono</th><th>Precio</th>${refBonos.map((r) => html`<th>${r.etiqueta}</th>`)}</tr></thead>
      <tbody>${bonos.map((b) => {
        const s = db.serie(`bono_${b}`);
        const actual = valorEn(s, tBonos);
        return html`<tr class="fila-item nivel-0">
          <td>Ecuador ${b}</td>
          <td><b>${formatoNumero(actual, 2)}</b></td>
          ${refBonos.map((r) => {
            // Los bonos 2034 y 2039 se emitieron en 2026: sin precio antes de su emisión.
            const ref = s[0][0] <= r.t ? valorEn(s, r.t) : undefined;
            return html`<td>${ref != null ? formatoCambio((actual / ref - 1) * 100, 1, "%") : "–"}</td>`;
          })}
        </tr>`;
      })}</tbody>
    </table></div>`
  })}
</div>`);
```

## Reservas internacionales

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Reservas internacionales",
    subtitulo: "USD millones, semanal",
    fuente: fuente("reservas"),
    ancho: true,
    contenido: grafico({
      series: [{nombre: "Reservas internacionales", datos: db.serie("reservas")}],
      frecuencia: "S", unidad: "USD mm", decimales: 0, tipo: "area", navegador: true, rango: "5a"
    })
  })}
  ${panel({
    titulo: "Composición de las reservas",
    subtitulo: "USD millones, semanal",
    fuente: fuente("reservas"),
    contenido: grafico({
      series: [
        {nombre: "Posición neta en divisas", datos: s("reservas_divisas", 2018)},
        {nombre: "Oro", datos: s("reservas_oro", 2018)},
        {nombre: "DEG, FMI, ALADI y SUCRE", datos: s("reservas_otros", 2018)}
      ],
      frecuencia: "S", unidad: "USD mm", decimales: 0, tipo: "area", apilado: true
    })
  })}
  ${panel({
    titulo: "Variación de las reservas en el año",
    subtitulo: "Cambio frente al cierre del año anterior, USD millones",
    fuente: fuente("reservas"),
    contenido: grafico({
      series: [{nombre: "Variación en el año", datos: variacionEnElAnio(db.serie("reservas"))}],
      frecuencia: "S", unidad: "USD mm", decimales: 0, tipo: "area", cero: true
    })
  })}
</div>`);
```

## Depósitos y crédito

Sistema de bancos privados.

```js
const segmentosCartera = [["productivo", "Productivo"], ["consumo", "Consumo"], ["inmobiliario", "Inmobiliario"], ["microcredito", "Microcrédito"]];

display(html`<div class="paneles">
  ${panel({
    titulo: "Depósitos y cartera",
    subtitulo: "Saldos, USD millones, bancos privados",
    fuente: fuente("depositos_bp"),
    contenido: grafico({
      series: [
        {nombre: "Depósitos", datos: s("depositos_bp")},
        {nombre: "Cartera", datos: s("cartera_bp")}
      ],
      frecuencia: "M", unidad: "USD mm", decimales: 0
    })
  })}
  ${panel({
    titulo: "Crecimiento de depósitos y cartera",
    subtitulo: "Variación anual, %, bancos privados",
    fuente: fuente("depositos_bp"),
    contenido: grafico({
      series: [
        {nombre: "Depósitos", datos: desde(variacion(db.serie("depositos_bp"), 12), 2015)},
        {nombre: "Cartera", datos: desde(variacion(db.serie("cartera_bp"), 12), 2015)}
      ],
      frecuencia: "M", unidad: "%", decimales: 1, cero: true
    })
  })}
  ${panel({
    titulo: "Crecimiento de la cartera por segmento",
    subtitulo: "Variación anual de la cartera bruta, %, bancos privados",
    fuente: fuente("cartera_bp"),
    contenido: grafico({
      series: segmentosCartera.map(([id, nombre]) => ({nombre, datos: desde(variacion(db.serie(`cartera_${id}_bp`), 12), 2018)})),
      frecuencia: "M", unidad: "%", decimales: 1, cero: true
    })
  })}
  ${panel({
    titulo: "Depósitos por tipo",
    subtitulo: "Saldos, USD millones, bancos privados",
    fuente: fuente("depositos_bp"),
    nota: "Monetarios: depósitos a la vista (cuenta 2101) sin los de ahorro. Ahorro: depósitos de ahorro (210135). Plazo: depósitos a plazo y restringidos (2103 + 2105).",
    contenido: grafico({
      series: [
        {nombre: "Monetarios", datos: s("dep_monetarios_bp")},
        {nombre: "Ahorro", datos: s("dep_ahorro_bp")},
        {nombre: "Plazo", datos: s("dep_plazo_bp")}
      ],
      frecuencia: "M", unidad: "USD mm", decimales: 0, tipo: "area", apilado: true
    })
  })}
  ${panel({
    titulo: "Relación cartera / depósitos",
    subtitulo: "%, bancos privados",
    fuente: fuente("ltd_bp"),
    contenido: grafico({
      series: [{nombre: "Cartera / depósitos", datos: s("ltd_bp")}],
      frecuencia: "M", unidad: "%", decimales: 1
    })
  })}
  ${panel({
    titulo: "Depósitos a la vista",
    subtitulo: "% de los depósitos totales, bancos privados",
    fuente: fuente("dep_vista_pct"),
    contenido: grafico({
      series: [{nombre: "Depósitos a la vista", datos: s("dep_vista_pct")}],
      frecuencia: "M", unidad: "%", decimales: 1
    })
  })}
</div>`);
```

## Calidad de cartera

La morosidad es la cartera improductiva (vencida y que no devenga intereses) sobre la cartera bruta.

```js
// Cambio normativo por la pandemia: el vencido se registraba a los 60 días de mora (marzo 2020 a diciembre 2022).
const bandaVencido = [{desde: Date.UTC(2020, 2, 1), hasta: Date.UTC(2022, 11, 31), etiqueta: "Vencido a 60 días"}];
const fuenteVencido = "resoluciones 569-2020-F, 609-2020-F y JPRF-F-2022-030";
const notaVencido = "Zona sombreada: por la pandemia, entre marzo de 2020 y diciembre de 2022 los créditos impagos pasaban a cartera vencida a los 60 días de mora (61 días desde fines de 2020) y no a los 30. Por eso la morosidad de ese período no es comparable y tiende a verse más baja. Desde enero de 2023 se volvió a 30 días, salvo en vivienda.";

display(html`<div class="paneles">
  ${panel({
    titulo: "Morosidad de la cartera",
    subtitulo: "%, bancos privados",
    fuente: `${fuente("morosidad_bp")}; ${fuenteVencido}`,
    nota: notaVencido,
    contenido: grafico({
      series: [{nombre: "Morosidad", datos: s("morosidad_bp")}],
      bandas: bandaVencido,
      frecuencia: "M", unidad: "%", decimales: 2
    })
  })}
  ${panel({
    titulo: "Cobertura de la cartera improductiva",
    subtitulo: "Provisiones / cartera improductiva, %, bancos privados",
    fuente: `${fuente("cobertura_bp")}; ${fuenteVencido}`,
    nota: "Zona sombreada: entre marzo de 2020 y diciembre de 2022 la cartera pasaba a vencida a los 60 días de mora y no a los 30. Con menos cartera improductiva registrada, la cobertura de ese período se ve más alta y no es comparable.",
    contenido: grafico({
      series: [{nombre: "Cobertura", datos: s("cobertura_bp")}],
      bandas: bandaVencido,
      frecuencia: "M", unidad: "%", decimales: 0, referencia: 100
    })
  })}
  ${panel({
    titulo: "Morosidad por segmento de crédito",
    subtitulo: "% de la cartera bruta del segmento, bancos privados",
    fuente: `${fuente("morosidad_bp")}; ${fuenteVencido}`,
    nota: notaVencido,
    ancho: true,
    contenido: grafico({
      series: [
        ...segmentosCartera.map(([id, nombre]) => ({nombre, datos: s(`morosidad_${id}_bp`, 2018)})),
        {nombre: "Total", datos: s("morosidad_bp", 2018), color: "tinta"}
      ],
      bandas: bandaVencido,
      frecuencia: "M", unidad: "%", decimales: 2, altura: 340
    })
  })}
</div>`);
```

## Liquidez, solvencia y rentabilidad

La liquidez de primera y segunda línea son aproximaciones, con información pública, a los indicadores regulatorios. El indicador de fondos disponibles frente a los depósitos a corto plazo, que publican la Superintendencia de Bancos y Asobanca, es una medida estricta: solo cuenta el efectivo y los depósitos en el BCE y en otras entidades, y deja fuera las inversiones y otros activos de alta calidad que se pueden vender rápido.

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Liquidez",
    subtitulo: "%, bancos privados",
    fuente: `${fuente("liquidez_primera_bp")}; ${fuente("liquidez_bp")}`,
    nota: "Primera y segunda línea: aproximaciones a los indicadores regulatorios calculadas con información pública. Fondos disponibles / depósitos a corto plazo (a la vista y a plazo hasta 90 días): solo cuenta efectivo y depósitos en el BCE y en otras entidades; no incluye inversiones ni otros activos líquidos, por lo que subestima la liquidez.",
    contenido: grafico({
      series: [
        {nombre: "Primera línea", datos: s("liquidez_primera_bp")},
        {nombre: "Segunda línea", datos: s("liquidez_segunda_bp")},
        {nombre: "Disponibles / dep. CP", datos: s("liquidez_bp")}
      ],
      frecuencia: "M", unidad: "%", decimales: 1
    })
  })}
  ${panel({
    titulo: "Solvencia",
    subtitulo: "Patrimonio técnico / activos y contingentes ponderados por riesgo, %; mínimo regulatorio: 9%",
    fuente: fuente("solvencia_bp"),
    contenido: grafico({
      series: [{nombre: "Solvencia", datos: db.serie("solvencia_bp")}],
      frecuencia: "M", unidad: "%", decimales: 1
    })
  })}
  ${panel({
    titulo: "Rentabilidad sobre patrimonio (ROE)",
    subtitulo: "%, bancos privados",
    fuente: fuente("roe_bp"),
    contenido: grafico({
      series: [{nombre: "ROE", datos: s("roe_bp")}],
      frecuencia: "M", unidad: "%", decimales: 1
    })
  })}
  ${panel({
    titulo: "Rentabilidad sobre activos (ROA)",
    subtitulo: "%, bancos privados",
    fuente: fuente("roa_bp"),
    contenido: grafico({
      series: [{nombre: "ROA", datos: s("roa_bp")}],
      frecuencia: "M", unidad: "%", decimales: 2
    })
  })}
</div>`);
```

## Tasas de interés

Tasas referenciales y tasas activas efectivas por segmento de crédito publicadas por el BCE, frente a las tasas máximas vigentes.

```js
// Subsegmentos de crédito: id de la tasa efectiva (la máxima es tasa_max_<subsegmento>).
const segmentos = [
  ["Productivo", ["productivo_corporativo", "productivo_empresarial", "productivo_pymes"]],
  ["Consumo", ["consumo"]],
  ["Microcrédito", ["microcredito_minorista", "microcredito_acumulacion_simple", "microcredito_acumulacion_ampliada"]],
  ["Vivienda", ["inmobiliario", "vivienda_de_interes_publico"]],
  ["Educativo", ["educativo"]]
];
const [tTasas] = db.ultimo("tasa_consumo");
const enTasas = (id, t = tTasas) => valorEn(db.serie(id), t);
const haceUnAnoTasas = Date.UTC(new Date(tTasas).getUTCFullYear() - 1, new Date(tTasas).getUTCMonth(), 1);

display(html`<div class="paneles">
  ${panel({
    titulo: "Tasas referenciales pasiva y activa",
    subtitulo: "%, mensual",
    fuente: fuente("tasa_pasiva"),
    contenido: grafico({
      series: [
        {nombre: "Activa", datos: db.serie("tasa_activa")},
        {nombre: "Pasiva", datos: db.serie("tasa_pasiva")}
      ],
      frecuencia: "M", unidad: "%", decimales: 2
    })
  })}
  ${panel({
    titulo: "Tasas activas efectivas por segmento",
    subtitulo: "Tasa efectiva referencial, %, mensual",
    fuente: fuente("tasa_consumo"),
    contenido: grafico({
      series: [
        {nombre: "Microcrédito minorista", datos: db.serie("tasa_microcredito_minorista")},
        {nombre: "Consumo", datos: db.serie("tasa_consumo")},
        {nombre: "Productivo PYMES", datos: db.serie("tasa_productivo_pymes")},
        {nombre: "Productivo corporativo", datos: db.serie("tasa_productivo_corporativo")}
      ],
      frecuencia: "M", unidad: "%", decimales: 2
    })
  })}
  ${panel({
    titulo: "Tasas activas efectivas y máximas por segmento",
    subtitulo: `%, ${formatoPeriodo(tTasas, "M")}; el margen es la distancia a la tasa máxima`,
    fuente: fuente("tasa_consumo"),
    ancho: true,
    contenido: html`<div class="tabla-wrap"><table class="tablero cuadro">
      <thead><tr><th>Segmento</th><th>Efectiva</th><th>Máxima</th><th>Margen</th><th>Efectiva hace un año</th><th>Cambio</th></tr></thead>
      <tbody>${segmentos.flatMap(([grupo, subs]) => [
        html`<tr class="fila-grupo nivel-0"><td colspan="6">${grupo}</td></tr>`,
        ...subs.map((s) => {
          const ef = enTasas(`tasa_${s}`);
          const max = enTasas(`tasa_max_${s}`);
          const ant = enTasas(`tasa_${s}`, haceUnAnoTasas);
          return html`<tr class="fila-item nivel-1">
            <td>${db.meta(`tasa_${s}`).corto}</td>
            <td><b>${formatoNumero(ef, 2)}</b></td>
            <td>${formatoNumero(max, 2)}</td>
            <td>${formatoCambio(ef - max, 2, "pp")}</td>
            <td>${formatoNumero(ant, 2)}</td>
            <td>${ant != null ? formatoCambio((ef - ant) * 100, 0, "pb") : "–"}</td>
          </tr>`;
        })
      ])}</tbody>
    </table></div>`
  })}
</div>`);
```

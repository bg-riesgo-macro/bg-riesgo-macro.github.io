---
title: Sector financiero
---

```js
import {db} from "./components/base.js";
import {mercados} from "./components/mercados.js";
import {variacion, combinar, valorEn, formatoNumero, formatoCambio, formatoPeriodo} from "./components/datos.js";
import {grafico} from "./components/graficos.js";
import {kpiSerie, panel, cabecera} from "./components/ui.js";

const fuente = (id) => db.meta(id).fuente;
const desde = (serie, anio) => serie.filter(([t]) => t >= Date.UTC(anio, 0, 1));
const s = (id, anio = 2015) => desde(db.serie(id), anio);
```

```js
display(cabecera({
  antetitulo: "Sector monetario y financiero",
  titulo: "Depósitos, crédito y riesgo soberano",
  bajada: "Evolución de depósitos y cartera, liquidez, solvencia y morosidad del sistema financiero privado, tasa pasiva referencial y bonos soberanos de Ecuador.",
  corte: db.ultimo("depositos_bp")[0]
}));

display(html`<div class="kpis">
  ${kpiSerie(db, "depositos_bp", {titulo: "Depósitos, bancos privados"})}
  ${kpiSerie(db, "cartera_bp", {titulo: "Cartera, bancos privados"})}
  ${kpiSerie(db, "morosidad_sf", {titulo: "Morosidad del sistema"})}
  ${kpiSerie(mercados, "ec2035_ytm", {titulo: "Rendimiento bono 2035"})}
</div>`);
```

## Depósitos y crédito

```js
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

## Liquidez, solvencia y calidad de cartera

Sistema financiero privado: bancos, cooperativas y mutualistas.

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Liquidez",
    subtitulo: "Fondos disponibles / depósitos de corto plazo, %",
    fuente: fuente("liquidez_bp"),
    contenido: grafico({
      series: [
        {nombre: "Bancos privados", datos: s("liquidez_bp")},
        {nombre: "Cooperativas segmento 1", datos: s("liquidez_coac1")}
      ],
      frecuencia: "M", unidad: "%", decimales: 1
    })
  })}
  ${panel({
    titulo: "Solvencia",
    subtitulo: "Patrimonio técnico / activos ponderados por riesgo, %",
    fuente: fuente("solvencia_sf"),
    contenido: grafico({
      series: [{nombre: "Solvencia", datos: s("solvencia_sf")}],
      frecuencia: "M", unidad: "%", decimales: 1
    })
  })}
  ${panel({
    titulo: "Morosidad por segmento de crédito",
    subtitulo: "% de la cartera bruta del segmento",
    fuente: fuente("morosidad_sf"),
    ancho: true,
    contenido: grafico({
      series: [
        {nombre: "Productivo", datos: s("morosidad_productivo", 2018)},
        {nombre: "Comercial", datos: s("morosidad_comercial", 2018)},
        {nombre: "Microcrédito", datos: s("morosidad_microcredito", 2018)},
        {nombre: "Vivienda", datos: s("morosidad_vivienda", 2018)},
        {nombre: "Total", datos: s("morosidad_sf", 2018), color: "tinta"}
      ],
      frecuencia: "M", unidad: "%", decimales: 2, altura: 340
    })
  })}
</div>`);
```

## Tasa pasiva referencial

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Tasa pasiva referencial",
    subtitulo: "%, semanal",
    fuente: fuente("tpr"),
    ancho: true,
    contenido: grafico({
      series: [
        {nombre: "Sistema", datos: db.serie("tpr"), color: "tinta"},
        {nombre: "Bancos privados", datos: db.serie("tpr_bp")},
        {nombre: "Cooperativas", datos: db.serie("tpr_coop")}
      ],
      frecuencia: "S", unidad: "%", decimales: 2, navegador: true, rango: "5a"
    })
  })}
</div>`);
```

## Bonos soberanos de Ecuador

Rendimiento al vencimiento de los bonos globales. El diferencial frente al bono del Tesoro de EE. UU. a 10 años sirve como aproximación del riesgo soberano mientras se incorpora el EMBI.

```js
const bonos = ["2030", "2034", "2035", "2039", "2040"];
const spread = combinar(mercados.serie("ec2035_ytm"), mercados.serie("us_10a"), (a, b) => (a - b) * 100);
const [tBonos] = mercados.ultimo("ec2035_ytm");
const hace = (dias) => tBonos - dias * 864e5;
const inicioAnio = Date.UTC(new Date(tBonos).getUTCFullYear() - 1, 11, 31);

display(html`<div class="paneles">
  ${panel({
    titulo: "Rendimiento de los bonos soberanos",
    subtitulo: "Rendimiento al vencimiento, %, diario",
    fuente: "Bloomberg",
    contenido: grafico({
      series: [
        {nombre: "2030", datos: mercados.serie("ec2030_ytm")},
        {nombre: "2035", datos: mercados.serie("ec2035_ytm")},
        {nombre: "2040", datos: mercados.serie("ec2040_ytm")}
      ],
      frecuencia: "D", unidad: "%", decimales: 2
    })
  })}
  ${panel({
    titulo: "Diferencial del bono 2035 frente al Tesoro a 10 años",
    subtitulo: "Puntos básicos, diario",
    fuente: "Bloomberg; cálculo propio",
    contenido: grafico({
      series: [{nombre: "Diferencial", datos: spread}],
      frecuencia: "D", unidad: "pb", decimales: 0
    })
  })}
  ${panel({
    titulo: "Bonos globales de Ecuador",
    subtitulo: `Al ${formatoPeriodo(tBonos, "D")}`,
    fuente: "Bloomberg",
    ancho: true,
    contenido: html`<div class="tabla-wrap"><table class="tablero cuadro">
      <thead><tr><th>Bono</th><th>Precio</th><th>Rendimiento</th><th>Var. 1 mes</th><th>Var. en el año</th></tr></thead>
      <tbody>${bonos.map((b) => {
        const px = mercados.serie(`ec${b}_px`);
        const y = mercados.serie(`ec${b}_ytm`);
        const actual = valorEn(y, tBonos);
        const cambio = (t) => {
          const ref = valorEn(y, t);
          return ref == null ? "–" : formatoCambio((actual - ref) * 100, 0, "pb");
        };
        return html`<tr class="fila-item nivel-0">
          <td>Ecuador ${b}</td>
          <td>${formatoNumero(valorEn(px, tBonos), 2)}</td>
          <td><b>${formatoNumero(actual, 2)}%</b></td>
          <td>${cambio(hace(30))}</td>
          <td>${cambio(inicioAnio)}</td>
        </tr>`;
      })}</tbody>
    </table></div>`
  })}
</div>`);
```

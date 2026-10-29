---
title: Resumen
toc: false
---

```js
import {db, previsiones} from "./components/base.js";
import {mercados} from "./components/mercados.js";
import {acumuladoAnual, etiquetaAcumulado, mesUltimo, variacion, cambioAnual, haceUnAno, formatoNumero, formatoCambio, formatoPeriodo} from "./components/datos.js";
import {grafico} from "./components/graficos.js";
import {kpiSerie, panel, cabecera, graficoPrevisiones, tablaPrevisiones, kpiAcumulado as kpiAcumuladoBase} from "./components/ui.js";

const desde = (serie, anio) => serie.filter(([t]) => t >= Date.UTC(anio, 0, 1));
```

```js
// Comercio exterior acumulado de enero al último mes disponible.
const mes = mesUltimo(db.serie("x_total"));
const acum = (id) => desde(acumuladoAnual(db.serie(id), mes), 2018);
const etiqueta = (t) => etiquetaAcumulado(mes, new Date(t).getUTCFullYear());

const kpiAcumulado = (titulo, datos, opciones = {}) => kpiAcumuladoBase({titulo, datos, mes, ...opciones});

// Sector fiscal: acumulado del SPNF a su propio mes de corte.
const mesFiscal = mesUltimo(db.serie("spnf_resultado_global"));
const acumFiscal = (id) => desde(acumuladoAnual(db.serie(id), mesFiscal), 2018);

// Primer año con previsiones (el año en curso).
const anioPrevision = Math.min(...previsiones.flatMap((p) => [...p.valores.keys()]));
```

```js
display(cabecera({
  antetitulo: "Resumen",
  titulo: "Economía ecuatoriana: últimas cifras",
  bajada: "Lectura del mes del área y los indicadores macroeconómicos que explican el entorno del negocio: actividad, entrada de dólares, riesgo soberano, hogares y entorno internacional.",
  corte: mercados.corte(),
  frecuencia: "D"
}));
```

<!--
  Lectura del mes: la escribe el área cada mes. Es texto Markdown: para actualizarla, edita la
  fecha de la línea "lectura-firma", la síntesis (siempre visible) y las viñetas de cada sección
  (se muestran al pulsar "Leer más"). Deja las líneas en blanco alrededor del
  Markdown dentro de los bloques <div>, o no se interpretará.
-->

## Lectura del mes

<div class="lectura">

<p class="lectura-firma">Octubre de 2026 · Riesgo Macroeconómico y Sectorial</p>

<div class="lectura-sintesis">

**En síntesis:** la economía crece a un ritmo moderado y siguen entrando dólares, pero el panorama se vuelve más exigente: el riesgo país repunta, los depósitos se desaceleran y ya crecen menos que el crédito. El Niño y el déficit eléctrico amenazan la actividad de los próximos meses.

</div>

<details class="lectura-detalle">
<summary><span class="abrir">Leer más <span class="separador">|</span> Cifras y riesgos</span><span class="cerrar">Ocultar</span></summary>
<div class="lectura-columnas">
<div>

### Lo que muestran las cifras

- **Crecimiento moderado.** El PIB creció 2.1% anual en el segundo trimestre y el IMAEc 3.5% en agosto. Las previsiones para 2026 van de 2.5% a 2.7%, con una inflación baja (1.34% en septiembre).
- **Siguen entrando dólares.** Las exportaciones crecen 9.8% entre enero y agosto, con el petróleo cerca de USD 100 por barril, y las reservas internacionales suman USD 2,911 millones más que en diciembre.
- **El riesgo país repunta.** El EMBI llegó a 587 pb, 87 pb más que al cierre de 2025 y unos 200 pb sobre su mínimo de junio (383 pb). En septiembre la Fed volvió a subir su tasa, lo que encarece el financiamiento externo.
- **Los depósitos se desaceleran.** Crecen 12.0% anual, frente a 19.0% en marzo de 2025, y desde junio avanzan más lento que la cartera (13.2%). Entre enero y septiembre, los bancos captaron USD 4,095 millones, menos que los USD 4,719 millones del mismo período de 2025.

</div>
<div>

### Riesgos a vigilar

- **El Niño.** Mantuvo su intensidad en octubre (índice RONI, región Niño 3.4) y el mar frente a la costa ecuatoriana sigue más cálido de lo normal (región Niño 1+2). Hasta ahora los eventos extremos han sido intensos pero puntuales, como la inundación de Guayaquil del 26 de octubre y las lluvias con granizo en Quito; el riesgo es que se vuelvan frecuentes con la temporada de lluvias de la Costa, que empieza en diciembre. El BCE estima que un evento fuerte restaría 1.4 puntos al crecimiento de 2027 (0.5 si es moderado), aunque aclara que son escenarios y no una predicción. Lo más expuesto: cultivos, vías y la capacidad de pago de hogares y empresas de las provincias costeras.
- **Energía.** El déficit de generación, estimado entre 1,000 y 1,200 MW, se ha enfrentado sobre todo con racionamientos que el Gobierno concentró en las industrias: en octubre ordenó desconexiones periódicas de las conectadas en alto voltaje (AV1), de dos y luego tres días por semana, y a fines de mes también de algunas de medio voltaje. Las importaciones desde Colombia, suspendidas a inicios de mes, se reanudaron el 16 de octubre en volúmenes mínimos. Con el embalse de Mazar cerca de su cota mínima, el abastecimiento depende de las lluvias en la vertiente amazónica, donde está la mayor parte de la generación hidroeléctrica, y El Niño no las garantiza. A diferencia de 2024, cuando para octubre ya había apagones generalizados, este año los cortes se han limitado a la industria; pero el margen es estrecho: un retraso de las lluvias podría extenderlos a hogares y comercios.

</div>
</div>
</details>

</div>


## Indicadores principales

```js
// Ventas locales acumuladas a su propio mes de corte.
const mesVentas = mesUltimo(db.serie("ventas_locales"));

display(html`<div class="kpis-sectores">
  <div class="kpi-columna">
    <h3><a href="./real">¿Cómo va la economía?</a></h3>
    ${kpiSerie(db, "pib_real_aa", {cambio: null})}
    ${kpiSerie(db, "imaec_aa", {titulo: "Actividad mensual (IMAEc)", cambio: null})}
    ${kpiAcumuladoBase({titulo: "Ventas locales (SRI)", datos: desde(acumuladoAnual(db.serie("ventas_locales"), mesVentas), 2018), mes: mesVentas})}
  </div>
  <div class="kpi-columna">
    <h3><a href="./externo">¿Entran dólares?</a></h3>
    ${kpiAcumulado("Exportaciones", acum("x_total"))}
    ${kpiSerie(db, "remesas_recibidas")}
    ${kpiSerie(db, "reservas")}
  </div>
  <div class="kpi-columna">
    <h3><a href="./fiscal">¿Cómo está el riesgo soberano?</a></h3>
    ${kpiSerie(db, "embi")}
    ${kpiAcumuladoBase({titulo: "Resultado global del SPNF", datos: acumFiscal("spnf_resultado_global"), mes: mesFiscal, nivel: false})}
    ${kpiSerie(db, "deuda_pib")}
  </div>
  <div class="kpi-columna">
    <h3><a href="./real">¿Cómo están los hogares?</a></h3>
    ${kpiSerie(db, "inflacion_aa")}
    ${kpiSerie(db, "empleo_adecuado")}
    ${kpiSerie(db, "icc", {titulo: "Confianza del consumidor"})}
  </div>
</div>`);
```

## Evolución reciente

```js
display(html`<div class="paneles">
  ${panel({
    titulo: "Crecimiento del PIB real",
    subtitulo: "Variación anual, %, trimestral (serie desestacionalizada)",
    fuente: db.meta("pib_real_aa").fuente,
    enlace: {href: "./real", texto: "Sector real"},
    contenido: grafico({
      series: [{nombre: "PIB real", datos: db.serie("pib_real_aa")}],
      frecuencia: "T", unidad: "%", decimales: 1, tipo: "column", cero: true, navegador: true, rango: "10a"
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
    nota: "Diferencia entre el rendimiento de los bonos de Ecuador en dólares y el de los bonos del Tesoro de EE. UU. (100 pb = 1 punto porcentual). Cuando sube, al Estado le cuesta más financiarse en los mercados internacionales, y ese mayor costo tiende a trasladarse a bancos y empresas.",
    contenido: grafico({
      series: [{nombre: "EMBI Ecuador", datos: db.serie("embi")}],
      frecuencia: "D", unidad: "pb", decimales: 0, navegador: true, rango: "10a"
    })
  })}
  ${panel({
    titulo: "Crecimiento de depósitos y cartera",
    subtitulo: "Variación anual, %, bancos privados",
    fuente: db.meta("depositos_bp").fuente,
    enlace: {href: "./financiero", texto: "Sector financiero"},
    nota: "En una economía dolarizada, los depósitos crecen cuando entran dólares (exportaciones, remesas, inversión y financiamiento externos) y se frenan cuando salen; por eso este gráfico se lee junto con el sector externo.",
    contenido: grafico({
      series: [
        {nombre: "Depósitos", datos: variacion(db.serie("depositos_bp"), 12)},
        {nombre: "Cartera", datos: variacion(db.serie("cartera_bp"), 12)}
      ],
      frecuencia: "M", unidad: "%", decimales: 1, cero: true, navegador: true, rango: "10a"
    })
  })}
</div>`);
```

## Previsiones de crecimiento

```js
const aniosPrevision = [anioPrevision, anioPrevision + 1];

display(html`<div class="paneles">
  ${panel({
    titulo: "Previsiones de crecimiento del PIB real",
    subtitulo: `Variación anual, %, ${aniosPrevision.join(" y ")}`,
    fuente: previsiones.map((p) => p.institucion).join(", "),
    enlace: {href: "./real", texto: "Sector real"},
    contenido: graficoPrevisiones(previsiones, aniosPrevision)
  })}
  ${panel({
    titulo: "Previsiones por institución",
    subtitulo: "Crecimiento real del PIB, %",
    fuente: previsiones.map((p) => p.institucion).join(", "),
    enlace: {href: "./real", texto: "Sector real"},
    contenido: tablaPrevisiones(previsiones, aniosPrevision)
  })}
</div>`);
```

## Tablero de indicadores

Último dato disponible de cada indicador y su comparación con el mismo período del año anterior.

```js
const grupos = [
  ["¿Cómo va la economía?", db, ["pib_real_aa", "vab_no_petrolero_aa", "imaec_aa", "ventas_locales"]],
  ["¿Entran dólares?", db, ["x_total", "x_no_pet", "m_total", "remesas_recibidas", "ied", "cuenta_corriente_pib", "terminos_intercambio", "reservas"]],
  ["¿Cómo está el riesgo soberano?", db, ["embi", "resultado_global_pib", "resultado_primario_pib", "deuda_total", "deuda_pib"]],
  ["¿Cómo están los hogares?", db, ["inflacion_aa", "desempleo", "empleo_adecuado", "subempleo", "icc"]],
  ["Sistema financiero (bancos privados)", db, ["depositos_bp", "cartera_bp", "morosidad_bp", "liquidez_bp", "tasa_pasiva", "tasa_activa"]],
  ["Entorno internacional", mercados, ["fed", "fed_inf", "us_3m", "us_10a", "dxy", "wti", "cacao", "oro"]]
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
    <td>${c ? formatoCambio(c.valor, c.decimales ?? (c.unidad === "pp" ? m.decimales : 1), c.unidad) : "–"}</td>
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

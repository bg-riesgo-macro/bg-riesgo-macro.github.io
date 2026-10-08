// Piezas de interfaz: tarjetas de indicadores y paneles de gráfico.

import {html} from "npm:htl";
import {cambioAnual, etiquetaAcumulado, formatoCambio, formatoNumero, formatoPeriodo} from "./datos.js";
import {minigrafico} from "./graficos.js";

/**
 * Tarjeta de indicador (KPI).
 *
 * @param {object} o
 * @param {string} o.titulo
 * @param {[number, number][]} o.datos   serie a mostrar; el último punto es el valor
 * @param {"D"|"M"|"T"|"A"} o.frecuencia
 * @param {string} o.unidad
 * @param {number} [o.decimales=1]
 * @param {{valor: number, unidad: string, decimales?: number, etiqueta: string}} [o.cambio]
 * @param {number} [o.ventana]           observaciones a mostrar en la minilínea
 * @param {string} [o.periodo]           etiqueta del período (por omisión, la fecha del último dato)
 * @param {(t: number) => string} [o.etiquetaPunto]  etiqueta de cada punto en la minilínea
 */
export function kpi({titulo, datos, frecuencia, unidad, decimales = 1, cambio, ventana, periodo, etiquetaPunto}) {
  const [t, v] = datos[datos.length - 1];
  const tramo = ventana ? datos.slice(-ventana) : datos;
  return html`<div class="kpi">
    <p class="kpi-titulo">${titulo}</p>
    <div class="kpi-valor">${formatoNumero(v, decimales)}<span class="kpi-unidad">${unidad}</span></div>
    <div class="kpi-detalle">
      <span>${periodo ?? formatoPeriodo(t, frecuencia)}</span>
      ${cambio
        ? html`<span class="kpi-cambio">${cambio.valor > 0 ? "▲" : cambio.valor < 0 ? "▼" : "■"} ${formatoCambio(
            cambio.valor,
            cambio.decimales ?? 1,
            cambio.unidad
          )} ${cambio.etiqueta}</span>`
        : null}
    </div>
    ${tramo.length > 2 ? minigrafico(tramo, {frecuencia, unidad, decimales, etiquetaPunto}) : null}
  </div>`;
}

/**
 * KPI a partir de una serie del catálogo. `datos`, `unidad` y `titulo` pueden
 * sobrescribirse cuando se muestra una transformación (p. ej. suma 12 meses).
 */
export function kpiSerie(db, id, opciones = {}) {
  const m = db.meta(id);
  const datos = opciones.datos ?? db.serie(id);
  const unidad = opciones.unidad ?? m.unidad;
  const ventana = opciones.ventana ?? {D: 260, M: 36, T: 16, A: 10}[m.frecuencia];
  return kpi({
    titulo: opciones.titulo ?? m.corto,
    datos,
    frecuencia: m.frecuencia,
    unidad,
    decimales: opciones.decimales ?? m.decimales,
    cambio: opciones.cambio === null ? undefined : opciones.cambio ?? cambioAnual(datos, unidad),
    ventana,
    periodo: opciones.periodo,
    etiquetaPunto: opciones.etiquetaPunto
  });
}

/**
 * KPI de un acumulado anual (enero al mes de corte), comparado con el mismo período del año previo.
 * `nivel: false` muestra la diferencia absoluta en lugar de la variación porcentual (para saldos).
 */
export function kpiAcumulado({titulo, datos, mes, unidad = "USD mm", decimales = 0, nivel = true}) {
  const [t, v] = datos[datos.length - 1];
  const [, ant] = datos[datos.length - 2];
  return kpi({
    titulo, datos, frecuencia: "A", unidad, decimales,
    periodo: etiquetaAcumulado(mes, new Date(t).getUTCFullYear()),
    etiquetaPunto: (x) => etiquetaAcumulado(mes, new Date(x).getUTCFullYear()),
    cambio: nivel
      ? {valor: (v / ant - 1) * 100, unidad: "%", etiqueta: "a/a"}
      : {valor: v - ant, unidad, decimales, etiqueta: "vs. año previo"}
  });
}

// --- Pantalla completa de paneles -----------------------------------------
const pantallaCompletaDisponible = document.fullscreenEnabled || document.webkitFullscreenEnabled;
const elementoCompleto = () => document.fullscreenElement ?? document.webkitFullscreenElement;

const ETIQUETA_ENTRAR = "Ver panel en pantalla completa";
const ETIQUETA_SALIR = "Salir de pantalla completa";

for (const evento of ["fullscreenchange", "webkitfullscreenchange"]) {
  document.addEventListener(evento, () => {
    const actual = elementoCompleto();
    for (const b of document.querySelectorAll(".panel-boton")) {
      const activo = b.closest(".panel") === actual;
      b.setAttribute("aria-label", activo ? ETIQUETA_SALIR : ETIQUETA_ENTRAR);
      b.title = activo ? ETIQUETA_SALIR : ETIQUETA_ENTRAR;
    }
  });
}

function botonPantallaCompleta() {
  const boton = html`<button type="button" class="panel-boton" aria-label=${ETIQUETA_ENTRAR} title=${ETIQUETA_ENTRAR}>
    <svg class="icono-expandir" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M2 6V2h4M10 2h4v4M14 10v4h-4M6 14H2v-4"/></svg>
    <svg class="icono-contraer" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M6 2v4H2M10 2v4h4M14 10h-4v4M2 10h4v4"/></svg>
  </button>`;
  boton.onclick = () => {
    const panel = boton.closest(".panel");
    if (elementoCompleto() === panel) (document.exitFullscreen ?? document.webkitExitFullscreen).call(document);
    else (panel.requestFullscreen ?? panel.webkitRequestFullscreen).call(panel);
  };
  return boton;
}

/** Panel con título, subtítulo, gráfico y fuente; se puede ver en pantalla completa. */
export function panel({titulo, subtitulo, fuente, contenido, ancho = false, enlace}) {
  return html`<section class="panel${ancho ? " ancho" : ""}">
    <div class="panel-cabeza">
      <h3>${titulo}</h3>
      <div class="panel-acciones">
        ${enlace ? html`<a class="panel-enlace" href=${enlace.href}>${enlace.texto} →</a>` : null}
        ${pantallaCompletaDisponible ? botonPantallaCompleta() : null}
      </div>
    </div>
    ${subtitulo ? html`<p class="panel-sub">${subtitulo}</p>` : null}
    ${contenido}
    ${fuente ? html`<p class="panel-pie">Fuente: ${fuente}.</p>` : null}
    <p class="panel-marca"><span class="marca-cuadro" aria-hidden="true"></span><strong>BG</strong> Riesgo Macro</p>
  </section>`;
}

/**
 * Cuadro comparativo de dos períodos (p. ej. acumulado ene–jul de dos años).
 *
 * @param {object} o
 * @param {{nombre: string, tipo: "total"|"grupo"|"subgrupo"|"item", nivel: number, a: number, b: number,
 *          tmA?: number, tmB?: number}[]} o.filas   la primera fila es el total de referencia
 * @param {string} o.columnaA   encabezado del período base
 * @param {string} o.columnaB   encabezado del período actual
 * @param {boolean} [o.participacion=true]  columna de participación sobre la primera fila
 * @param {boolean} [o.diferencia=false]    columna de diferencia absoluta (útil para saldos negativos)
 * @param {boolean} [o.volumen=false]       columna de variación de volumen (tmA, tmB)
 */
export function cuadroComparativo({filas, columnaA, columnaB, participacion = true, diferencia = false, volumen = false}) {
  // La variación porcentual solo tiene sentido entre valores positivos.
  const variacion = (a, b) => (a > 0 && b >= 0 ? formatoCambio((b / a - 1) * 100, 1, "%") : "–");
  return html`<div class="tabla-wrap"><table class="tablero cuadro">
    <thead><tr>
      <th></th><th>${columnaA}</th><th>${columnaB}</th><th>Var. %</th>
      ${diferencia ? html`<th>Diferencia</th>` : null}
      ${participacion ? html`<th>Part.</th>` : null}
      ${volumen ? html`<th>Var. volumen</th>` : null}
    </tr></thead>
    <tbody>${filas.map((f) => html`<tr class=${`fila-${f.tipo} nivel-${f.nivel}`}>
      <td>${f.nombre}</td>
      <td>${formatoNumero(f.a, 1)}</td>
      <td>${formatoNumero(f.b, 1)}</td>
      <td>${variacion(f.a, f.b)}</td>
      ${diferencia ? html`<td>${formatoCambio(f.b - f.a, 1)}</td>` : null}
      ${participacion ? html`<td>${formatoNumero((f.b / filas[0].b) * 100, 1)}%</td>` : null}
      ${volumen ? html`<td>${f.tmA != null ? variacion(f.tmA, f.tmB) : ""}</td>` : null}
    </tr>`)}</tbody>
  </table></div>`;
}

/** Cabecera de página con antetítulo, título, bajada y fecha de corte. */
export function cabecera({antetitulo, titulo, bajada, corte, frecuencia = "M", aviso = "Versión preliminar"}) {
  return html`<header class="cabecera">
    <p class="antetitulo">${antetitulo}</p>
    <h1>${titulo}</h1>
    ${bajada ? html`<p class="bajada">${bajada}</p>` : null}
    <div class="meta">
      <span>${frecuencia === "D" ? "Información disponible al" : "Datos hasta"} ${formatoPeriodo(corte, frecuencia)}</span>
      ${aviso ? html`<span class="etiqueta">${aviso}</span>` : null}
    </div>
  </header>`;
}

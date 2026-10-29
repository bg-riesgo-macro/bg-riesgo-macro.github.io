// Carga única de las series macro, compartida por todas las páginas.
import {FileAttachment} from "observablehq:stdlib";
import {crearBase} from "./datos.js";

const [filas, catalogo, filasPrevisiones] = await Promise.all([
  FileAttachment("../data/series.csv").csv({typed: true}),
  FileAttachment("../data/catalogo.json").json(),
  FileAttachment("../data/previsiones.csv").csv({typed: true})
]);

export const db = crearBase(filas, catalogo.series);

/** Fecha (UTC) del cuadro de incidencias del IPC. */
export const fechaIncidenciasIpc = new Date(catalogo.incidencias_ipc);

/**
 * Previsiones de crecimiento del PIB real por institución, en el orden del archivo:
 * [{institucion, informe, fecha, valores: Map(año → %)}].
 */
export const previsiones = [];
for (const {institucion, informe, fecha, anio, valor} of filasPrevisiones) {
  let p = previsiones.find((x) => x.institucion === institucion);
  if (!p) previsiones.push((p = {institucion, informe, fecha, valores: new Map()}));
  p.valores.set(anio, valor);
}

/** Fecha (UTC) de corte del perfil de vencimientos de la deuda. */
export const fechaPerfilVencimientos = new Date(catalogo.perfil_vencimientos);

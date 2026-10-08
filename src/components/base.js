// Carga única de las series macro, compartida por todas las páginas.
import {FileAttachment} from "observablehq:stdlib";
import {crearBase} from "./datos.js";

const [filas, catalogo] = await Promise.all([
  FileAttachment("../data/series.csv").csv({typed: true}),
  FileAttachment("../data/catalogo.json").json()
]);

export const db = crearBase(filas, catalogo.series);

/** Fecha (UTC) del cuadro de incidencias del IPC. */
export const fechaIncidenciasIpc = new Date(catalogo.incidencias_ipc);

/** Fecha (UTC) de corte del perfil de vencimientos de la deuda. */
export const fechaPerfilVencimientos = new Date(catalogo.perfil_vencimientos);

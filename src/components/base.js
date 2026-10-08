// Carga única de las series macro, compartida por todas las páginas.
import {FileAttachment} from "observablehq:stdlib";
import {crearBase} from "./datos.js";

const [filas, catalogo, filasFiscal, catalogoFiscal] = await Promise.all([
  FileAttachment("../data/series.csv").csv({typed: true}),
  FileAttachment("../data/catalogo.json").json(),
  // Sector fiscal: datos ilustrativos hasta completar la información.
  FileAttachment("../data/fiscal_ilustrativo.csv").csv({typed: true}),
  FileAttachment("../data/fiscal_ilustrativo.json").json()
]);

export const db = crearBase([...filas, ...filasFiscal], [...catalogo.series, ...catalogoFiscal]);

/** Fecha (UTC) del cuadro de incidencias del IPC. */
export const fechaIncidenciasIpc = new Date(catalogo.incidencias_ipc);

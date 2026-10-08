// Series diarias de mercados (Bloomberg). Se cargan solo en las páginas que las usan.
import {FileAttachment} from "observablehq:stdlib";
import {crearBase} from "./datos.js";

const [ancho, meta] = await Promise.all([
  FileAttachment("../data/mercados.csv").csv({typed: true}),
  FileAttachment("../data/mercados.json").json()
]);

const ids = meta.series.map((s) => s.id);
const filas = [];
for (const fila of ancho) for (const id of ids) filas.push({id, fecha: fila.fecha, valor: fila[id]});

export const mercados = crearBase(filas, meta.series);

/** Metadatos de las series de un grupo (bolsa, politica, fx, commodity, ecuador, curva_us…). */
export const grupo = (g) => meta.series.filter((s) => s.grupo === g);

/** Curvas soberanas disponibles: [{id, pais, plazos}]. */
export const curvas = meta.curvas;

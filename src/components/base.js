// Carga única de los datos, compartida por todas las páginas.
import {FileAttachment} from "observablehq:stdlib";
import {crearBase} from "./datos.js";

const [filas, catalogo] = await Promise.all([
  FileAttachment("../data/series.csv").csv({typed: true}),
  FileAttachment("../data/catalogo.json").json()
]);

export const db = crearBase(filas, catalogo);

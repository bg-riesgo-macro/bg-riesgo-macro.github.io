// Acceso a las series y utilidades de transformación/formato.
//
// Las series viven en formato largo (id, fecha, valor) y se describen en
// catalogo.json. Las fechas marcan el inicio del período (2026-04-01 = T2 2026).

const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

// Formato numérico: punto decimal y coma de miles (convención del BCE).
// Cambia la configuración regional aquí si prefieres "1.234,5".
const LOCALE = "en-US";

export function crearBase(filas, catalogo) {
  const meta = new Map(catalogo.map((d) => [d.id, d]));
  const series = new Map();
  for (const {id, fecha, valor} of filas) {
    if (valor == null || Number.isNaN(valor)) continue;
    if (!series.has(id)) series.set(id, []);
    series.get(id).push([+fecha, valor]);
  }
  for (const s of series.values()) s.sort((a, b) => a[0] - b[0]);

  const obtener = (id) => {
    if (!series.has(id)) throw new Error(`Serie desconocida: ${id}`);
    return series.get(id);
  };

  return {
    meta(id) {
      const m = meta.get(id);
      if (!m) throw new Error(`Serie sin metadatos: ${id}`);
      return m;
    },
    serie: obtener,
    ultimo(id) {
      const s = obtener(id);
      return s[s.length - 1];
    },
    /** Fecha más reciente entre todas las series (Date). */
    corte() {
      let max = -Infinity;
      for (const s of series.values()) max = Math.max(max, s[s.length - 1][0]);
      return new Date(max);
    }
  };
}

/** Suma móvil de n períodos (p. ej. 12 meses acumulados). */
export function sumaMovil(serie, n) {
  const out = [];
  let acc = 0;
  for (let i = 0; i < serie.length; i++) {
    acc += serie[i][1];
    if (i >= n) acc -= serie[i - n][1];
    if (i >= n - 1) out.push([serie[i][0], acc]);
  }
  return out;
}

/** Variación porcentual frente a `rezago` períodos atrás (12 = anual en series mensuales). */
export function variacion(serie, rezago) {
  return serie.slice(rezago).map(([t, v], i) => [t, (v / serie[i][1] - 1) * 100]);
}

/** Combina dos series por fecha con una función (p. ej. resta). */
export function combinar(a, b, f) {
  const mb = new Map(b);
  return a.filter(([t]) => mb.has(t)).map(([t, v]) => [t, f(v, mb.get(t))]);
}

/** Valor de la serie `n` observaciones antes de la última. */
export function previo(serie, n) {
  return serie[serie.length - 1 - n];
}

export function formatoNumero(v, decimales = 1) {
  if (v == null || Number.isNaN(v)) return "–";
  return v.toLocaleString(LOCALE, {minimumFractionDigits: decimales, maximumFractionDigits: decimales});
}

export function formatoCambio(v, decimales = 1, unidad = "") {
  const signo = v > 0 ? "+" : v < 0 ? "−" : "±";
  const sep = unidad && unidad !== "%" ? " " : "";
  return `${signo}${formatoNumero(Math.abs(v), decimales)}${sep}${unidad}`;
}

/** Etiqueta del período según la frecuencia: D (diaria), S (semanal), M, T (trimestral) o A (anual). */
export function formatoPeriodo(t, frecuencia) {
  const d = new Date(t);
  const y = d.getUTCFullYear();
  const m = d.getUTCMonth();
  switch (frecuencia) {
    case "D":
    case "S":
      return `${d.getUTCDate()} ${MESES[m]} ${y}`;
    case "M":
      return `${MESES[m]} ${y}`;
    case "T":
      return `T${Math.floor(m / 3) + 1} ${y}`;
    default:
      return `${y}`;
  }
}

export {MESES};

/** Observación más reciente con fecha igual o anterior a un año antes del último dato. */
export function haceUnAno(serie) {
  const d = new Date(serie[serie.length - 1][0]);
  const objetivo = Date.UTC(d.getUTCFullYear() - 1, d.getUTCMonth(), d.getUTCDate());
  for (let i = serie.length - 1; i >= 0; i--) if (serie[i][0] <= objetivo) return serie[i];
  return undefined;
}

/**
 * Cambio interanual del último dato: diferencia en puntos (pp, pb) para tasas y
 * spreads; variación porcentual para niveles.
 */
export function cambioAnual(serie, unidad) {
  const ant = haceUnAno(serie);
  if (!ant) return undefined;
  const v = serie[serie.length - 1][1];
  if (unidad.includes("%")) return {valor: v - ant[1], unidad: "pp", etiqueta: "a/a"};
  if (unidad === "pb") return {valor: v - ant[1], unidad: "pb", decimales: 0, etiqueta: "a/a"};
  return {valor: (v / ant[1] - 1) * 100, unidad: "%", etiqueta: "a/a"};
}

/** Valor de la última observación con fecha igual o anterior a `t`. */
export function valorEn(serie, t) {
  for (let i = serie.length - 1; i >= 0; i--) if (serie[i][0] <= t) return serie[i][1];
  return undefined;
}

/** Mes (0–11) de la última observación de una serie mensual o trimestral. */
export function mesUltimo(serie) {
  return new Date(serie[serie.length - 1][0]).getUTCMonth();
}

/**
 * Acumulado de enero al mes `mesCorte` (0–11) de cada año, solo para años completos
 * hasta ese mes. Devuelve [[1-ene-año, suma], …].
 */
export function acumuladoAnual(serie, mesCorte = mesUltimo(serie)) {
  const porAnio = new Map();
  for (const [t, v] of serie) {
    const d = new Date(t);
    if (d.getUTCMonth() > mesCorte) continue;
    const a = d.getUTCFullYear();
    const acc = porAnio.get(a) ?? {suma: 0, n: 0};
    acc.suma += v;
    acc.n += 1;
    porAnio.set(a, acc);
  }
  const esperado = new Set(serie.map(([t]) => new Date(t).getUTCMonth()).filter((m) => m <= mesCorte)).size;
  return [...porAnio]
    .filter(([, {n}]) => n === esperado)
    .map(([a, {suma}]) => [Date.UTC(a, 0, 1), suma])
    .sort((x, y) => x[0] - y[0]);
}

/** Etiqueta de un acumulado: "ene–jul 2026" (o "2026" si cubre el año completo). */
export function etiquetaAcumulado(mesCorte, anio) {
  return mesCorte === 11 ? `${anio}` : `ene–${MESES[mesCorte]}${anio != null ? ` ${anio}` : ""}`;
}

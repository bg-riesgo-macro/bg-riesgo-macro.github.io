// Envoltorio de Highcharts Stock con el estilo del sitio.
//
// Los colores se leen de las variables CSS de style.css, de modo que los
// gráficos siguen el modo claro/oscuro del sistema y se redibujan al cambiar.

// Se usan los paquetes UMD: cada módulo se registra sobre la misma instancia
// global de Highcharts. (Los paquetes ESM se empaquetarían por separado,
// cada uno con su propia copia del núcleo.)
import Highcharts from "highcharts/highstock.js";
import "highcharts/modules/accessibility.js";
import "highcharts/modules/exporting.js";
import "highcharts/modules/export-data.js";
import "highcharts/modules/offline-exporting.js";
import {MESES, formatoNumero, formatoPeriodo} from "./datos.js";

Highcharts.setOptions({
  lang: {
    locale: "es-EC",
    months: ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
    shortMonths: MESES,
    weekdays: ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"],
    decimalPoint: ".",
    thousandsSep: ",",
    numericSymbols: null,
    rangeSelectorZoom: "",
    contextButtonTitle: "Opciones del gráfico",
    viewFullscreen: "Pantalla completa",
    exitFullscreen: "Salir de pantalla completa",
    downloadPNG: "Descargar PNG",
    downloadSVG: "Descargar SVG",
    downloadCSV: "Descargar CSV",
    downloadXLS: "Descargar Excel",
    viewData: "Ver tabla de datos",
    hideData: "Ocultar tabla de datos",
    resetZoom: "Restablecer zoom",
    noData: "Sin datos"
  },
  credits: {enabled: false},
  exporting: {libURL: "https://code.highcharts.com/13.1.1/lib"}
});

function tokens() {
  const s = getComputedStyle(document.documentElement);
  const v = (n) => s.getPropertyValue(`--${n}`).trim();
  return {
    fondo: v("fondo"),
    fondoAlt: v("fondo-alt"),
    tinta: v("tinta"),
    tinta2: v("tinta-2"),
    suave: v("tinta-suave"),
    linea: v("linea"),
    rejilla: v("rejilla"),
    eje: v("eje"),
    acento: v("acento"),
    acentoSuave: v("acento-suave"),
    series: [v("serie-1"), v("serie-2"), v("serie-3"), v("serie-4")],
    fuente: v("sans-serif")
  };
}

/** Quita las claves sin valor para que no anulen las opciones heredadas. */
const definida = (o) => Object.fromEntries(Object.entries(o).filter(([, v]) => v !== undefined));

/** Color de una serie: índice de la paleta categórica o nombre de un token ("tinta", "suave"). */
const colorSerie = (t, c, i) => (typeof c === "string" ? t[c] : t.series[c ?? i]);

// --- Redibujo al cambiar de modo claro/oscuro -------------------------------
const registro = new Set();
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  for (const r of registro) {
    if (!r.el.isConnected) registro.delete(r);
    else r.dibujar();
  }
});

const enPantallaCompleta = (el) =>
  (document.fullscreenElement ?? document.webkitFullscreenElement)?.contains(el) ?? false;

function montar(el, construir, altura) {
  let chart = null;
  // Alto fijo en la página; en pantalla completa ocupa el alto que le da el panel.
  const ajustar = () => {
    const alto = enPantallaCompleta(el) ? el.clientHeight : altura;
    if (alto > 0 && Math.round(chart.chartHeight) !== Math.round(alto)) chart.setSize(null, alto, false);
    else chart.reflow();
  };
  const r = {
    el,
    dibujar() {
      chart?.destroy();
      chart = construir(tokens());
      if (enPantallaCompleta(el)) ajustar();
    }
  };
  // Se crea cuando el contenedor ya tiene ancho (al insertarse en la página).
  const ro = new ResizeObserver(([e]) => {
    if (e.contentRect.width === 0) return;
    if (!chart) {
      r.dibujar();
      registro.add(r);
    } else {
      ajustar();
    }
  });
  ro.observe(el);
  return el;
}

// --- Opciones base ----------------------------------------------------------
function base(t, {altura, frecuencia, unidad, decimales, encabezado, soloImagen = false}) {
  const ejeTexto = {color: t.suave, fontSize: "11px"};
  return {
    chart: {
      height: altura,
      backgroundColor: "transparent",
      spacing: [8, 4, 4, 0],
      style: {fontFamily: t.fuente, fontSize: "12px"},
      zooming: {mouseWheel: {enabled: false}}
    },
    colors: t.series,
    title: {text: undefined},
    xAxis: {
      type: "datetime",
      lineColor: t.eje,
      tickColor: t.eje,
      tickLength: 4,
      labels: {style: ejeTexto},
      crosshair: {color: t.eje, width: 1},
      dateTimeLabelFormats: {day: "%e %b", week: "%e %b", month: "%b %Y", year: "%Y"}
    },
    yAxis: {
      title: {text: undefined},
      opposite: false,
      gridLineColor: t.rejilla,
      gridLineWidth: 1,
      labels: {style: ejeTexto, distance: 6, align: "right"},
      showLastLabel: true
    },
    legend: {
      enabled: false,
      align: "left",
      verticalAlign: "top",
      margin: 8,
      padding: 0,
      itemDistance: 16,
      symbolRadius: 2,
      itemStyle: {color: t.tinta2, fontWeight: "400", fontSize: "12px"},
      itemHoverStyle: {color: t.tinta},
      itemHiddenStyle: {color: t.eje}
    },
    tooltip: {
      shared: true,
      split: false,
      useHTML: true,
      backgroundColor: t.fondo,
      borderColor: t.linea,
      borderRadius: 6,
      shadow: false,
      padding: 10,
      style: {color: t.tinta, fontSize: "12px"},
      formatter() {
        const puntos = this.points ?? [this];
        const filas = puntos
          .map(
            (p) => `<div style="display:flex;gap:6px;align-items:center;margin-top:3px">
              <span style="width:8px;height:8px;border-radius:50%;background:${p.color};flex:none"></span>
              <span style="color:${t.tinta2}">${p.series.name}</span>
              <b style="margin-left:auto;padding-left:12px">${formatoNumero(p.y, decimales)}</b>
              <span style="color:${t.suave}">${unidad}</span></div>`
          )
          .join("");
        const titulo = encabezado ? encabezado(this) : formatoPeriodo(this.x, frecuencia);
        return `<div style="font-weight:600;margin-bottom:2px">${titulo}</div>${filas}`;
      }
    },
    plotOptions: {
      series: {
        lineWidth: 2,
        marker: {enabled: false, radius: 4, lineWidth: 2, lineColor: t.fondo},
        states: {hover: {lineWidthPlus: 0}, inactive: {opacity: 0.35}},
        dataGrouping: {enabled: frecuencia === "D", approximation: "average", groupPixelWidth: 2}
      },
      line: {linecap: "round"},
      column: {
        borderWidth: 0,
        borderRadius: {radius: 4, where: "end"},
        maxPointWidth: 24,
        pointPadding: 0.08,
        groupPadding: 0.1
      },
      area: {fillOpacity: 0.1, lineWidth: 2}
    },
    navigation: {
      buttonOptions: {
        theme: {fill: "transparent", stroke: "none", states: {hover: {fill: t.fondoAlt}, select: {fill: t.fondoAlt}}},
        symbolStroke: t.suave,
        symbolSize: 12,
        y: -6
      },
      menuStyle: {background: t.fondo, border: `1px solid ${t.linea}`, boxShadow: "none", borderRadius: "6px"},
      menuItemStyle: {color: t.tinta, fontSize: "12px", padding: "6px 12px"},
      menuItemHoverStyle: {background: t.acentoSuave, color: t.tinta}
    },
    exporting: {
      buttons: {
        contextButton: {
          // Datos con licencia (Bloomberg): solo se ofrece la imagen del gráfico.
          menuItems: soloImagen
            ? ["downloadPNG", "downloadSVG"]
            : ["downloadPNG", "downloadSVG", "separator", "downloadCSV", "downloadXLS", "viewData"]
        }
      },
      chartOptions: {chart: {backgroundColor: t.fondo}},
      csv: {dateFormat: "%Y-%m-%d"}
    },
    accessibility: {enabled: true}
  };
}

function opcionesStock(t, rangoInicial) {
  const botones = [
    {type: "year", count: 1, text: "1a"},
    {type: "year", count: 3, text: "3a"},
    {type: "year", count: 5, text: "5a"},
    {type: "all", text: "Todo"}
  ];
  return {
    rangeSelector: {
      enabled: true,
      inputEnabled: false,
      buttons: botones,
      selected: Math.max(0, botones.findIndex((b) => b.text === rangoInicial)),
      buttonPosition: {align: "left", x: 0},
      buttonSpacing: 4,
      buttonTheme: {
        fill: "none",
        stroke: t.linea,
        "stroke-width": 1,
        r: 4,
        width: 34,
        height: 16,
        style: {color: t.tinta2, fontWeight: "500", fontSize: "12px"},
        states: {
          hover: {fill: t.fondoAlt, style: {color: t.tinta}},
          select: {fill: t.acentoSuave, stroke: t.acento, style: {color: t.acento, fontWeight: "600"}},
          disabled: {style: {color: t.eje}}
        }
      }
    },
    navigator: {
      height: 32,
      margin: 10,
      maskFill: t.acentoSuave,
      outlineColor: t.linea,
      outlineWidth: 1,
      handles: {backgroundColor: t.fondo, borderColor: t.acento, width: 7, height: 15},
      series: {type: "line", color: t.suave, lineWidth: 1, dataGrouping: {groupPixelWidth: 2}},
      xAxis: {gridLineColor: t.rejilla, labels: {style: {color: t.suave, fontSize: "10px", textOutline: "none", opacity: 1}}}
    },
    scrollbar: {enabled: false}
  };
}

// Las etiquetas al final de las líneas se apilan verticalmente en lugar de
// ocultarse cuando se superponen.
function separarEtiquetas() {
  const etiquetas = this.series
    .filter((s) => s.visible)
    .map((s) => s.points?.[s.points.length - 1]?.dataLabel)
    .filter((l) => l?.translateY != null)
    .map((l) => ({l, y: l.translateY, alto: l.getBBox().height}))
    .sort((a, b) => a.y - b.y);
  for (let i = 1; i < etiquetas.length; i++) {
    const minimo = etiquetas[i - 1].y + etiquetas[i - 1].alto;
    if (etiquetas[i].y < minimo) etiquetas[i].y = minimo;
  }
  for (const {l, y} of etiquetas) if (y !== l.translateY) l.attr({translateY: y});
}

/**
 * Gráfico de series de tiempo.
 *
 * @param {object} o
 * @param {{nombre: string, datos: [number, number][], tipo?: string, color?: number|string, escalon?: boolean}[]} o.series
 * @param {"D"|"S"|"M"|"T"|"A"} o.frecuencia
 * @param {(t: number) => string} [o.periodo]  etiqueta del período en el tooltip (p. ej. "ene–jul 2026")
 * @param {string} o.unidad          unidad mostrada en el tooltip
 * @param {number} [o.decimales=1]
 * @param {"line"|"column"|"area"} [o.tipo="line"]
 * @param {boolean} [o.apilado=false]
 * @param {boolean} [o.navegador=false] usa Highcharts Stock con navegador y selector de rango
 * @param {string} [o.rango="5a"]       rango inicial del selector ("1a", "3a", "5a", "Todo")
 * @param {boolean} [o.cero=false]      línea de referencia en cero
 * @param {number} [o.referencia]       línea de referencia en otro valor (p. ej. 50 en índices de difusión)
 * @param {boolean} [o.soloImagen=false] menú sin descarga de datos (para fuentes con licencia)
 * @param {number} [o.altura=300]
 */
export function grafico(o) {
  const {
    series,
    frecuencia,
    unidad = "",
    decimales = 1,
    tipo = "line",
    apilado = false,
    navegador = false,
    rango = "5a",
    cero = false,
    referencia = cero ? 0 : undefined,
    periodo,
    soloImagen = false,
    altura = navegador ? 380 : 300
  } = o;
  const el = document.createElement("div");
  el.className = "grafico";
  el.style.minHeight = `${altura}px`;

  const etiquetasFinales = !navegador && tipo === "line" && series.length >= 2 && series.length <= 4;

  return montar(el, (t) => {
    const encabezado = periodo ? (ctx) => periodo(ctx.x) : undefined;
    const op = base(t, {altura, frecuencia, unidad, decimales, encabezado, soloImagen});
    op.legend.enabled = series.length > 1;
    if (etiquetasFinales) {
      // Espacio a la derecha según el nombre más largo (≈6.5 px por carácter a 11 px).
      op.chart.spacingRight = Math.min(150, 14 + 6.5 * Math.max(...series.map((s) => s.nombre.length)));
      op.chart.events = {render: separarEtiquetas};
    }
    if (referencia != null) op.yAxis.plotLines = [{value: referencia, color: t.eje, width: 1, zIndex: 3}];
    if (frecuencia === "A") op.xAxis.tickInterval = 365.25 * 864e5;
    if (apilado) op.plotOptions[tipo] = {...op.plotOptions[tipo], stacking: "normal"};
    if (apilado && tipo === "area") op.plotOptions.area.fillOpacity = 0.35;
    if (tipo === "column" && apilado) op.plotOptions.column.borderRadius = 0;

    op.series = series.map((s, i) => definida(serieTiempo(s, i)));
    function serieTiempo(s, i) {
      const color = colorSerie(t, s.color, i);
      const ultimo = s.datos[s.datos.length - 1];
      return {
        name: s.nombre,
        type: s.tipo ?? tipo,
        data: s.datos,
        step: s.escalon ? "left" : undefined,
        stacking: s.tipo && s.tipo !== tipo ? undefined : apilado ? "normal" : undefined,
        marker: s.tipo === "line" && tipo === "column" ? {enabled: true, symbol: "circle"} : undefined,
        zIndex: s.tipo && s.tipo !== tipo ? 5 : undefined,
        color,
        borderColor: t.fondo,
        borderWidth: tipo === "column" && apilado ? 1 : 0,
        dataLabels: etiquetasFinales
          ? {
              enabled: true,
              filter: {property: "x", operator: "===", value: ultimo?.[0]},
              format: s.nombre,
              align: "left",
              verticalAlign: "middle",
              x: 6,
              y: 0,
              crop: false,
              overflow: "allow",
              allowOverlap: true,
              style: {color: t.tinta2, fontWeight: "500", fontSize: "11px", textOutline: "none"}
            }
          : undefined
      };
    }

    // En pantallas angostas las etiquetas finales restan demasiado espacio.
    if (etiquetasFinales) {
      op.responsive = {
        rules: [{
          condition: {maxWidth: 360},
          chartOptions: {chart: {spacingRight: 4}, series: series.map(() => ({dataLabels: {enabled: false}}))}
        }]
      };
    }

    if (navegador) {
      Object.assign(op, opcionesStock(t, rango));
      return Highcharts.stockChart(el, op);
    }
    return Highcharts.chart(el, op);
  }, altura);
}

/**
 * Gráfico con eje de categorías (curvas de rendimiento, rankings, incidencias).
 *
 * @param {object} o
 * @param {string[]} o.categorias
 * @param {{nombre: string, datos: number[], color?: number|string, punteado?: boolean}[]} o.series
 * @param {"line"|"column"|"bar"} [o.tipo="line"]
 */
export function graficoCategorias(o) {
  const {categorias, series, unidad = "", decimales = 1, tipo = "line", cero = false, altura = 300, soloImagen = false} = o;
  const el = document.createElement("div");
  el.className = "grafico";
  el.style.minHeight = `${altura}px`;
  return montar(el, (t) => {
    const op = base(t, {altura, unidad, decimales, soloImagen, encabezado: (ctx) => ctx.key ?? categorias[ctx.x]});
    op.xAxis = {...op.xAxis, type: "category", categories: categorias, dateTimeLabelFormats: undefined};
    if (tipo === "bar") {
      op.xAxis.labels = {...op.xAxis.labels, style: {...op.xAxis.labels.style, fontSize: "11.5px", color: t.tinta2}};
      op.xAxis.crosshair = false;
      op.tooltip.shared = false;
    }
    op.legend.enabled = series.length > 1;
    if (cero) op.yAxis.plotLines = [{value: 0, color: t.eje, width: 1, zIndex: 3}];
    op.plotOptions.bar = {...op.plotOptions.column, maxPointWidth: 18};
    op.series = series.map((s, i) => ({
      name: s.nombre,
      type: tipo,
      data: s.datos,
      color: colorSerie(t, s.color, i),
      dashStyle: s.punteado ? "ShortDash" : undefined,
      connectNulls: true,
      marker: tipo === "line" ? {enabled: true, symbol: "circle", radius: 4} : undefined
    }));
    return Highcharts.chart(el, op);
  }, altura);
}

/** Línea mínima para las tarjetas de indicadores; marca el último dato en magenta. */
export function minigrafico(datos, {frecuencia, unidad = "", decimales = 1, altura = 44, etiquetaPunto} = {}) {
  const el = document.createElement("div");
  el.className = "kpi-spark";
  return montar(el, (t) =>
    Highcharts.chart(el, {
      chart: {
        height: altura,
        backgroundColor: "transparent",
        margin: [6, 6, 6, 6],
        style: {fontFamily: t.fuente}
      },
      title: {text: undefined},
      credits: {enabled: false},
      exporting: {enabled: false},
      legend: {enabled: false},
      accessibility: {enabled: false},
      xAxis: {visible: false, type: "datetime"},
      yAxis: {visible: false, startOnTick: false, endOnTick: false},
      tooltip: {
        outside: true,
        useHTML: true,
        backgroundColor: t.fondo,
        borderColor: t.linea,
        borderRadius: 6,
        shadow: false,
        padding: 6,
        style: {color: t.tinta, fontSize: "11px"},
        formatter() {
          const etiqueta = etiquetaPunto ? etiquetaPunto(this.x) : formatoPeriodo(this.x, frecuencia);
          return `<span style="color:${t.tinta2}">${etiqueta}</span>&nbsp; <b>${formatoNumero(this.y, decimales)}</b> ${unidad}`;
        }
      },
      plotOptions: {
        series: {
          animation: false,
          turboThreshold: 0,
          lineWidth: 2,
          color: t.series[0],
          marker: {enabled: false, radius: 4, lineWidth: 2, lineColor: t.fondoAlt},
          states: {hover: {lineWidthPlus: 0}}
        }
      },
      series: [
        {
          type: "line",
          data: datos.map(([x, y], i) =>
            i === datos.length - 1 ? {x, y, marker: {enabled: true, fillColor: t.acento}} : [x, y]
          )
        }
      ]
    }),
    altura
  );
}

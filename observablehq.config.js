// Configuración de Observable Framework: https://observablehq.com/framework/config

const secciones = [
  {name: "Resumen", path: "/"},
  {name: "Sector real", path: "/real"},
  {name: "Sector financiero", path: "/financiero"},
  {name: "Sector fiscal", path: "/fiscal"},
  {name: "Sector externo", path: "/externo"}
];

const activo = (actual, destino) =>
  destino === "/" ? actual === "/" || actual === "/index" : actual.startsWith(destino);

export default {
  title: "BG Riesgo Macro",
  root: "src",
  lang: "es",

  // Navegación en la barra superior en lugar de la barra lateral.
  pages: secciones.slice(1),
  sidebar: false,
  pager: false,
  toc: {label: "En esta página"},
  search: false,

  head: `<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Crect width='16' height='16' rx='2' fill='%23b5106a'/%3E%3C/svg%3E">`,
  globalStylesheets: [
    "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap"
  ],
  style: "style.css",

  header: ({path}) => `
    <a class="marca" href="/">
      <span class="marca-cuadro" aria-hidden="true"></span>
      <span class="marca-texto"><strong>BG</strong> Riesgo Macro</span>
    </a>
    <nav class="nav-principal" aria-label="Secciones">
      ${secciones
        .map(
          (s) =>
            `<a href="${s.path}"${activo(path, s.path) ? ` aria-current="page"` : ""}>${s.name}</a>`
        )
        .join("")}
    </nav>`,

  footer: `BG Riesgo Macroeconómico y Sectorial · Fuentes: BCE, INEC, MEF, SRI, Superintendencia de Bancos.
    <span class="pie-aviso">Maqueta con datos ilustrativos; no constituyen cifras oficiales.</span>`
};

# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.2", "openpyxl>=3.1", "duckdb>=1.1"]
# ///
"""Convierte los archivos de data_raw/ en los archivos livianos que usa el sitio.

Uso (desde la raíz del repositorio):

    uv run scripts/procesar_datos.py

Salidas en src/data/:
    series.csv / catalogo.json     series macro en formato largo (id, fecha, valor)
    mercados.csv / mercados.json   series diarias de Bloomberg en formato ancho
    exportaciones.csv / .json      exportaciones mensuales por producto (clasificación BCE)
    importaciones.csv / .json      importaciones mensuales por CUODE
    ventas_sector.csv              ventas SRI mensuales por sección CIIU
    ipc_incidencias.csv            incidencia mensual por división del IPC (último mes)
    spnf.csv                       operaciones mensuales del SPNF por partida (MEF)
    vencimientos.csv               perfil de vencimientos de la deuda pública (MEF)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import duckdb
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "data_raw"
OUT = RAIZ / "src" / "data"

MESES = {m: i + 1 for i, m in enumerate(
    ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"])}
MESES_LARGOS = {m: i + 1 for i, m in enumerate(
    ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
     "septiembre", "octubre", "noviembre", "diciembre"])}
ROMANOS = {"I": 1, "II": 4, "III": 7, "IV": 10}

filas: list[tuple[str, str, float]] = []
catalogo: list[dict] = []


def limpiar(texto) -> str:
    return " ".join(str(texto).split())


def registrar(id_, fechas, valores, *, sector, nombre, corto, unidad, frecuencia,
              decimales, fuente, escala=1.0):
    """Agrega una serie (descartando vacíos) y su ficha de catálogo."""
    n = 0
    for f, v in zip(fechas, valores):
        if v is None or pd.isna(v):
            continue
        filas.append((id_, pd.Timestamp(f).strftime("%Y-%m-%d"), round(float(v) * escala, 6)))
        n += 1
    if n == 0:
        raise ValueError(f"Serie vacía: {id_}")
    catalogo.append(dict(id=id_, sector=sector, nombre=nombre, corto=corto, unidad=unidad,
                         frecuencia=frecuencia, decimales=decimales, fuente=fuente))


# --------------------------------------------------------------- utilidades de lectura
def hoja_cn(ruta: Path, hoja: str) -> pd.DataFrame:
    """Hoja de cuentas nacionales trimestrales (filas '2026.II') → DataFrame por fecha."""
    df = pd.read_excel(ruta, sheet_name=hoja, header=None)
    fila_cab = next(i for i in range(20) if limpiar(df.iat[i, 0]) in ("Industrias", "Variables"))
    cab = [limpiar(c) for c in df.iloc[fila_cab]]
    datos = df.iloc[fila_cab + 1:].copy()
    datos.columns = cab
    etiqueta = datos.iloc[:, 0].astype(str).str.strip()
    datos = datos[etiqueta.str.match(r"^\d{4}\.(I|II|III|IV)$")]
    datos.index = [pd.Timestamp(int(t[:4]), ROMANOS[t[5:]], 1) for t in datos.iloc[:, 0].str.strip()]
    return datos.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")


def hoja_imaec(hoja: str) -> pd.DataFrame:
    df = pd.read_excel(RAW / "IMAEc" / "IMAEc_202607.xlsx", sheet_name=hoja, header=None)
    fila_cab = next(i for i in range(20) if limpiar(df.iat[i, 0]) == "Fecha")
    datos = df.iloc[fila_cab + 1:].copy()
    datos.columns = [limpiar(c) for c in df.iloc[fila_cab]]
    datos = datos[datos["Fecha"].astype(str).str.match(r"^\d{4}\.[a-z]{3}$")]
    datos.index = [pd.Timestamp(int(f[:4]), MESES[f[5:]], 1) for f in datos["Fecha"]]
    return datos.drop(columns="Fecha").apply(pd.to_numeric, errors="coerce")


def ipc_ancho(hoja: str) -> pd.Series:
    """Cuadros del IPC con años en filas y meses en columnas → serie mensual."""
    df = pd.read_excel(RAW / "IPC incidencias.xlsx", sheet_name=hoja, header=7)
    df = df[pd.to_numeric(df["Periodo"], errors="coerce").notna()]
    meses = list(MESES_LARGOS)
    largo = df.melt(id_vars="Periodo", value_vars=[m.capitalize() for m in meses])
    largo["fecha"] = [pd.Timestamp(int(a), MESES_LARGOS[m.lower()], 1)
                      for a, m in zip(largo["Periodo"], largo["variable"])]
    return largo.set_index("fecha")["value"].astype(float).dropna().sort_index()


# ============================================================== SECTOR REAL
FUENTE_CN = "BCE, Cuentas Nacionales Trimestrales"
cn = RAW / "cuentas_nacionales_trim"

dem_vy = hoja_cn(cn / "tou_136_202602.xlsx", "Dem_Ivol_ajus_vY")
registrar("pib_real_aa", dem_vy.index, dem_vy["PIB"], sector="real",
          nombre="PIB real, variación anual (serie desestacionalizada)", corto="Crecimiento del PIB",
          unidad="%", frecuencia="T", decimales=1, fuente=FUENTE_CN)

# Aportes al crecimiento anual del PIB por componente del gasto.
contr = hoja_cn(cn / "tou_136_202602.xlsx", "Dem_contr_ajus_vY")
col = {c.lower(): c for c in contr.columns}
buscar = lambda texto: next(c for k, c in col.items() if texto in k)
c_hog, c_gob = buscar("consumo final hogar"), buscar("consumo final gobierno")
c_fbkf, c_exist = buscar("fbkf"), buscar("existencias")
c_x, c_m = buscar("exportaciones"), buscar("importaciones")
netas = contr[c_x] - contr[c_m]
residuo = (contr[c_hog] + contr[c_gob] + contr[c_fbkf] + contr[c_exist] + netas - contr["PIB"]).abs().max()
if residuo > 0.2:  # si el signo de las importaciones viniera invertido
    netas = contr[c_x] + contr[c_m]
for id_, valores, corto in [
    ("aporte_consumo", contr[c_hog] + contr[c_gob], "Consumo"),
    ("aporte_fbkf", contr[c_fbkf], "Inversión (FBKF)"),
    ("aporte_xnetas", netas, "Exportaciones netas"),
    ("aporte_existencias", contr[c_exist], "Variación de existencias"),
]:
    registrar(id_, contr.index, valores, sector="real", nombre=f"Aporte al crecimiento anual del PIB: {corto}",
              corto=corto, unidad="pp", frecuencia="T", decimales=2, fuente=FUENTE_CN)

dem_corr = hoja_cn(cn / "tou_136_202602.xlsx", "Dem_Corr_bru")
pib_nominal_t = dem_corr["PIB"] / 1000  # miles → millones de USD
pib_anual = pib_nominal_t.groupby(pib_nominal_t.index.year).agg(["sum", "count"])
pib_anual = pib_anual[pib_anual["count"] == 4]["sum"]
registrar("pib_nominal", [pd.Timestamp(a, 1, 1) for a in pib_anual.index], pib_anual, sector="real",
          nombre="PIB nominal", corto="PIB nominal", unidad="USD mm", frecuencia="A", decimales=0,
          fuente=FUENTE_CN)

pet = hoja_cn(cn / "vab_p_np_136_202602.xlsx", "Of_Ivol_ajus_pet_vY")
registrar("vab_petrolero_aa", pet.index, pet["Valor Agregado Petrolero"], sector="real",
          nombre="VAB petrolero real, variación anual", corto="VAB petrolero", unidad="%",
          frecuencia="T", decimales=1, fuente=FUENTE_CN)
registrar("vab_no_petrolero_aa", pet.index, pet["Valor Agregado no Petrolero"], sector="real",
          nombre="VAB no petrolero real, variación anual", corto="VAB no petrolero", unidad="%",
          frecuencia="T", decimales=1, fuente=FUENTE_CN)

# IMAEc
FUENTE_IMAE = "BCE, IMAEc"
imae = hoja_imaec("Of_Ivol_ajus_clas")
imae_vy = hoja_imaec("Of_Ivol_ajus_clas_vY")
registrar("imaec", imae.index, imae["IMAEc"], sector="real",
          nombre="Índice de Actividad Económica coyuntural (IMAEc), desestacionalizado",
          corto="IMAEc", unidad="índice", frecuencia="M", decimales=1, fuente=FUENTE_IMAE)
registrar("imaec_aa", imae_vy.index, imae_vy["IMAEc"], sector="real",
          nombre="IMAEc, variación anual", corto="IMAEc, variación anual", unidad="%",
          frecuencia="M", decimales=1, fuente=FUENTE_IMAE)
for col_, id_, corto in [
    ("Agricultura", "agro", "Agropecuario"), ("Petróleo", "petroleo", "Petróleo y minas"),
    ("Manufactura", "manufactura", "Manufactura"), ("Construcción", "construccion", "Construcción"),
    ("Comercio", "comercio", "Comercio"), ("Servicios", "servicios", "Servicios"),
]:
    c = next(c for c in imae_vy.columns if c.startswith(col_))
    registrar(f"imaec_aa_{id_}", imae_vy.index, imae_vy[c], sector="real",
              nombre=f"IMAEc {corto}, variación anual", corto=corto, unidad="%", frecuencia="M",
              decimales=1, fuente=FUENTE_IMAE)

# Inflación
FUENTE_IPC = "INEC, Índice de Precios al Consumidor"
for hoja, id_, nombre, corto in [
    ("3.Var_anu", "inflacion_aa", "Inflación anual (IPC)", "Inflación anual"),
    ("2.Var_mens", "inflacion_mm", "Inflación mensual (IPC)", "Inflación mensual"),
    ("4.Var_acum", "inflacion_acum", "Inflación acumulada en el año (IPC)", "Inflación acumulada"),
]:
    s = ipc_ancho(hoja)
    s = s[s.index >= "2010-01-01"]
    registrar(id_, s.index, s, sector="real", nombre=nombre, corto=corto, unidad="%",
              frecuencia="M", decimales=2, fuente=FUENTE_IPC)

inc = pd.read_excel(RAW / "IPC nacional.xlsx", sheet_name="1.Inc_mens", header=7)
mes_inc = inc.columns[-1]
inc = inc[inc["Nivel"] == "División"]
pd.DataFrame({
    "ccif": inc["CCIF"].astype(str).str.zfill(2),
    "division": inc["Descripción CCIF"].map(limpiar),
    "ponderacion": (inc["Ponderación"] * 100).round(3),
    "incidencia": inc[mes_inc].astype(float).round(4),
}).to_csv(OUT / "ipc_incidencias.csv", index=False)
mm, aa = str(mes_inc).split("-")
fecha_incidencias = pd.Timestamp(2000 + int(aa), MESES[mm[:3]], 1)

# Mercado laboral (microdatos ENEMDU, ponderados con el factor de expansión)
con = duckdb.connect()
enemdu = con.execute(f"""
    select cast(periodo as int) periodo,
      sum(fexp) filter (where condact between 1 and 8) pea,
      sum(fexp) filter (where condact in (7, 8)) desempleo,
      sum(fexp) filter (where condact = 1) adecuado,
      sum(fexp) filter (where condact in (2, 3)) subempleo,
      sum(fexp) filter (where condact in (4, 5, 6)) otro_no_pleno
    from '{RAW / "enemdu_mensual.parquet"}' group by 1 order by 1
""").df()
enemdu["fecha"] = [pd.Timestamp(p // 100, p % 100, 1) for p in enemdu["periodo"]]
for col_, id_, nombre, corto in [
    ("desempleo", "desempleo", "Tasa de desempleo nacional", "Desempleo"),
    ("adecuado", "empleo_adecuado", "Tasa de empleo adecuado", "Empleo adecuado"),
    ("subempleo", "subempleo", "Tasa de subempleo", "Subempleo"),
    ("otro_no_pleno", "otro_no_pleno", "Otro empleo no pleno y no remunerado", "Otro no pleno"),
]:
    registrar(id_, enemdu["fecha"], enemdu[col_] / enemdu["pea"] * 100, sector="real", nombre=nombre,
              corto=corto, unidad="%", frecuencia="M", decimales=1,
              fuente="INEC, ENEMDU (cálculo propio con factor de expansión)")

# Coyuntura
iee = pd.read_excel(RAW / "coyuntura" / "IEE.xlsx", header=7)
iee = iee[pd.to_datetime(iee["Fecha"], errors="coerce").notna()]
fechas = pd.to_datetime(iee["Fecha"])
for col_, id_, corto in [("IEE Global (2)", "iee", "IEE global"), ("Comercio", "iee_comercio", "Comercio"),
                         ("Construcción", "iee_construccion", "Construcción"),
                         ("Manufactura", "iee_manufactura", "Manufactura"), ("Servicios", "iee_servicios", "Servicios")]:
    registrar(id_, fechas, pd.to_numeric(iee[col_]), sector="real",
              nombre=f"Índice de Expectativas Empresariales: {corto}", corto=corto, unidad="índice",
              frecuencia="M", decimales=1, fuente="Por confirmar")

icc = pd.read_excel(RAW / "coyuntura" / "ICC.xlsx", header=7)
icc = icc[icc["Periodo"].astype(str).str.match(r"^\d{4}-\d{2}$")]
fechas = pd.to_datetime(icc["Periodo"] + "-01")
for col_, id_, corto in [("ICC Global (2)", "icc", "ICC global"),
                         ("Índice de Situación Presente", "icc_presente", "Situación presente"),
                         ("Índice de Situación Futura", "icc_futura", "Situación futura")]:
    c = next(x for x in icc.columns if str(x).startswith(col_))
    registrar(id_, fechas, pd.to_numeric(icc[c]), sector="real",
              nombre=f"Índice de Confianza del Consumidor: {corto}", corto=corto, unidad="índice",
              frecuencia="M", decimales=1, fuente="Por confirmar")

cem = pd.read_excel(RAW / "coyuntura" / "EstadisticasCemento.xlsx", sheet_name="Producción_despachos_inven",
                    header=None)
anio, fechas, despachos, produccion = None, [], [], []
for _, r in cem.iterrows():
    etiqueta = str(r[1]).strip()
    m = re.match(r"^(\d{4})\s+(\w+)$", etiqueta)
    if m:
        anio, mes = int(m[1]), m[2].lower()
    elif anio and etiqueta.lower() in MESES_LARGOS:
        mes = etiqueta.lower()
    else:
        continue
    fechas.append(pd.Timestamp(anio, MESES_LARGOS[mes], 1))
    produccion.append(r[2])
    despachos.append(r[3])
registrar("cemento_despachos", fechas, despachos, sector="real", nombre="Despachos de cemento",
          corto="Despachos de cemento", unidad="miles t", frecuencia="M", decimales=1,
          fuente="Empresas cementeras", escala=1 / 1000)
registrar("cemento_produccion", fechas, produccion, sector="real", nombre="Producción de cemento",
          corto="Producción de cemento", unidad="miles t", frecuencia="M", decimales=1,
          fuente="Empresas cementeras", escala=1 / 1000)

# Ventas SRI
SECCIONES = {
    "A": "Agricultura y pesca", "B": "Minas y canteras", "C": "Manufactura", "D": "Electricidad y gas",
    "E": "Agua y saneamiento", "F": "Construcción", "G": "Comercio", "H": "Transporte y almacenamiento",
    "I": "Alojamiento y comidas", "J": "Información y comunicación", "K": "Actividades financieras",
    "L": "Actividades inmobiliarias", "M": "Actividades profesionales", "N": "Servicios administrativos",
    "O": "Administración pública", "P": "Enseñanza", "Q": "Salud", "R": "Artes y recreación",
    "S": "Otros servicios", "T": "Hogares", "U": "Organizaciones extraterritoriales",
}
ventas = con.execute(f"""
    select cast("ANIO FISCAL" as int) anio, cast("MES FISCAL" as int) mes,
           upper(left("ACTIVIDAD ECONÓMICA", 1)) seccion,
           sum("TOTAL VENTAS Y EXPORTACIONES (419)") / 1e6 ventas
    from '{RAW / "ventas-saiku-ciiu6.parquet"}' group by all order by all
""").df()
ventas["fecha"] = [pd.Timestamp(a, m, 1) for a, m in zip(ventas["anio"], ventas["mes"])]
ventas["nombre"] = ventas["seccion"].map(SECCIONES).fillna("Sin clasificar")
ventas[["fecha", "seccion", "nombre", "ventas"]].assign(
    fecha=lambda d: d["fecha"].dt.strftime("%Y-%m-%d"), ventas=lambda d: d["ventas"].round(3)
).to_csv(OUT / "ventas_sector.csv", index=False)
total_ventas = ventas.groupby("fecha")["ventas"].sum()
registrar("ventas_sri", total_ventas.index, total_ventas, sector="real",
          nombre="Ventas totales y exportaciones declaradas (formulario 104, casillero 419)",
          corto="Ventas SRI", unidad="USD mm", frecuencia="M", decimales=0, fuente="SRI, Saiku")

# ============================================================== SECTOR FINANCIERO
FUENTE_SB = "Superintendencia de Bancos (compilación interna)"
dep = pd.read_excel(RAW / "tendencias_depósitos_macro.xlsx", sheet_name="indicadores bancos")
dep.index = pd.to_datetime(dep.iloc[:, 0])
registrar("depositos_bp", dep.index, dep["Depósitos"], sector="financiero",
          nombre="Depósitos del público, bancos privados", corto="Depósitos", unidad="USD mm",
          frecuencia="M", decimales=0, fuente=FUENTE_SB, escala=1 / 1000)
registrar("cartera_bp", dep.index, dep["Cartera"], sector="financiero",
          nombre="Cartera bruta, bancos privados", corto="Cartera", unidad="USD mm", frecuencia="M",
          decimales=0, fuente=FUENTE_SB, escala=1 / 1000)
registrar("ltd_bp", dep.index, dep["LTD ratio"], sector="financiero",
          nombre="Relación cartera / depósitos (LTD), bancos privados", corto="Cartera / depósitos",
          unidad="%", frecuencia="M", decimales=1, fuente=FUENTE_SB, escala=100)
registrar("dep_vista_pct", dep.index, dep["% vista"], sector="financiero",
          nombre="Depósitos a la vista, % del total, bancos privados", corto="Depósitos a la vista",
          unidad="%", frecuencia="M", decimales=1, fuente=FUENTE_SB, escala=100)

sf = pd.read_excel(RAW / "tendencias_depósitos_macro.xlsx", sheet_name="bancos+coop")
sf.index = pd.to_datetime(sf.iloc[:, 0])
for col_, id_, nombre, corto, unidad, esc, dec in [
    ("depositos_total", "depositos_sf", "Depósitos del sistema financiero privado", "Depósitos", "USD mm", 1, 0),
    ("cartera_total", "cartera_sf", "Cartera bruta del sistema financiero privado", "Cartera", "USD mm", 1, 0),
    ("activos_liquidos", "activos_liquidos_sf", "Activos líquidos del sistema financiero privado",
     "Activos líquidos", "USD mm", 1, 0),
    ("morosidad_total", "morosidad_sf", "Morosidad de la cartera, sistema financiero privado",
     "Morosidad", "%", 100, 2),
    ("morosidad_productivo", "morosidad_productivo", "Morosidad, segmento productivo", "Productivo", "%", 100, 2),
    ("morosidad_comercial", "morosidad_comercial", "Morosidad, segmento comercial", "Comercial", "%", 100, 2),
    ("morosidad_microcredito", "morosidad_microcredito", "Morosidad, microcrédito", "Microcrédito", "%", 100, 2),
    ("morosidad_vivienda", "morosidad_vivienda", "Morosidad, vivienda", "Vivienda", "%", 100, 2),
    ("solvencia", "solvencia_sf", "Índice de solvencia, sistema financiero privado", "Solvencia", "%", 100, 1),
    ("liquidez_bancospriv", "liquidez_bp", "Liquidez de bancos privados", "Liquidez bancos", "%", 100, 1),
    ("liquidez_coac1", "liquidez_coac1", "Liquidez de cooperativas segmento 1", "Liquidez COAC 1", "%", 100, 1),
]:
    registrar(id_, sf.index, sf[col_], sector="financiero", nombre=nombre, corto=corto, unidad=unidad,
              frecuencia="M", decimales=dec, fuente=FUENTE_SB, escala=esc)

tpr = pd.read_excel(RAW / "tpr.xlsx")
tpr.index = pd.to_datetime(tpr["semana"], format="%d/%m/%Y")
for col_, id_, nombre, corto in [
    ("tpr", "tpr", "Tasa pasiva referencial", "Tasa pasiva referencial"),
    ("tpr_bpriv", "tpr_bp", "Tasa pasiva referencial, bancos privados", "Bancos privados"),
    ("tpr_coop", "tpr_coop", "Tasa pasiva referencial, cooperativas", "Cooperativas"),
]:
    registrar(id_, tpr.index, tpr[col_], sector="financiero", nombre=nombre, corto=corto, unidad="%",
              frecuencia="S", decimales=2, fuente="BCE")

# Riesgo país: el archivo trae días calendario (fines de semana repetidos); se dejan días hábiles.
embi = pd.read_excel(RAW / "bce_riesgo_país2.xlsx")
embi["Fecha"] = pd.to_datetime(embi["Fecha"])
embi = embi[embi["Fecha"].dt.dayofweek < 5]
registrar("embi", embi["Fecha"], embi["Valor"], sector="financiero", nombre="Riesgo país (EMBI Ecuador)",
          corto="Riesgo país", unidad="pb", frecuencia="D", decimales=0, fuente="BCE, con datos de JP Morgan")

# Reservas internacionales semanales. Códigos del BCE:
#   c1 posición neta en divisas (c11 caja en divisas; c12 depósitos netos en bancos e
#      instituciones financieras del exterior; c13 inversiones, depósitos a plazo y títulos)
#   c2 oro; c3 DEG; c4 posición de reserva en el FMI; c5 posición en ALADI; c6 posición en SUCRE
# El resto (c3 a c6) se calcula como RI − c1 − c2: desde febrero de 2026 la fuente no trae c3 (DEG),
# aunque el total sí lo incluye.
ri = con.execute(f"""
    select FECHA fecha, RI ri, c1 divisas, c2 oro, RI - coalesce(c1, 0) - coalesce(c2, 0) otros
    from '{RAW / "reserva_internacional_semanal.parquet"}' order by 1
""").df()
FUENTE_RI = "BCE, Reservas internacionales (semanal)"
for id_, valores, nombre, corto in [
    ("reservas", ri["ri"], "Reservas internacionales", "Reservas internacionales"),
    ("reservas_divisas", ri["divisas"], "Reservas internacionales: posición neta en divisas",
     "Posición neta en divisas"),
    ("reservas_oro", ri["oro"], "Reservas internacionales: oro", "Oro"),
    ("reservas_otros", ri["otros"], "Reservas internacionales: DEG, FMI, ALADI y SUCRE",
     "DEG, FMI, ALADI y SUCRE"),
]:
    registrar(id_, ri["fecha"], valores, sector="financiero", nombre=nombre, corto=corto, unidad="USD mm",
              frecuencia="S", decimales=0, fuente=FUENTE_RI)

# ============================================================== SECTOR FISCAL
import warnings  # noqa: E402

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Operaciones del SPNF (MEF): columnas anuales, trimestrales y mensuales; se usan las mensuales.
FUENTE_SPNF = "MEF, Operaciones del Sector Público No Financiero"
op = pd.read_excel(RAW / "mef_spnf" / "8.Operaciones-de-Ingresos-y-Gastos-SPNF-2013-2026.xlsx",
                   sheet_name="SPNF", header=None)
fila_fechas = op.iloc[4]
cols_mes = [j for j, v in enumerate(fila_fechas) if isinstance(v, pd.Timestamp) or hasattr(v, "month")]
fechas_spnf = [pd.Timestamp(fila_fechas[j]) for j in cols_mes]
spnf = []
for i in range(5, len(op)):
    codigo, concepto = op.iat[i, 0], op.iat[i, 1]
    if pd.isna(codigo) or pd.isna(concepto):
        continue
    codigo = str(codigo).split()[0].split(".")[0]
    for j, f in zip(cols_mes, fechas_spnf):
        v = pd.to_numeric(op.iat[i, j], errors="coerce")
        if pd.notna(v):
            spnf.append((f.strftime("%Y-%m-%d"), codigo, limpiar(concepto), round(float(v), 3)))
spnf = pd.DataFrame(spnf, columns=["fecha", "codigo", "concepto", "valor"]).drop_duplicates(["fecha", "codigo"])
# Quitar notas al pie del nombre ("Exportación 1/" → "Exportación").
spnf["concepto"] = spnf["concepto"].str.replace(r"\s*\d+/\s*$|\s*\(\*+\)\s*$|\s*/\d+$", "", regex=True)
spnf.to_csv(OUT / "spnf.csv", index=False)

por_codigo = spnf.pivot(index="fecha", columns="codigo", values="valor")
por_codigo.index = pd.to_datetime(por_codigo.index)
for codigo, id_, nombre, corto in [
    ("1", "spnf_ingresos", "Ingresos totales del SPNF", "Ingresos"),
    ("2", "spnf_gastos", "Gastos totales del SPNF", "Gastos"),
    ("3", "spnf_resultado_global", "Resultado global del SPNF", "Resultado global"),
    ("4", "spnf_resultado_primario", "Resultado primario del SPNF", "Resultado primario"),
    ("41", "spnf_primario_no_petrolero", "Resultado primario no petrolero del SPNF", "Primario no petrolero"),
    ("11", "spnf_ing_petroleros", "Ingresos petroleros del SPNF", "Petroleros"),
    ("121", "spnf_tributarios", "Ingresos tributarios del SPNF", "Tributarios"),
    ("213", "spnf_intereses", "Intereses de la deuda pública", "Intereses"),
    ("221", "spnf_inversion", "Inversión en activos no financieros", "Inversión"),
    ("57", "spnf_subsidios_combustibles", "Subsidios a los combustibles", "Subsidios a combustibles"),
]:
    registrar(id_, por_codigo.index, por_codigo[codigo], sector="fiscal", nombre=nombre, corto=corto,
              unidad="USD mm", frecuencia="M", decimales=0, fuente=FUENTE_SPNF)

# Resultados anuales en % del PIB (años completos), con el PIB nominal de cuentas nacionales.
anual = por_codigo.groupby(por_codigo.index.year).agg(["sum", "count"])
for codigo, id_, nombre, corto in [
    ("3", "resultado_global_pib", "Resultado global del SPNF", "Resultado global"),
    ("4", "resultado_primario_pib", "Resultado primario del SPNF", "Resultado primario"),
    ("41", "primario_no_petrolero_pib", "Resultado primario no petrolero del SPNF", "Primario no petrolero"),
    ("1", "ingresos_spnf_pib", "Ingresos totales del SPNF", "Ingresos"),
    ("2", "gastos_spnf_pib", "Gastos totales del SPNF", "Gastos"),
]:
    completos = [a for a in anual.index if anual.loc[a, (codigo, "count")] == 12 and a in pib_anual.index]
    registrar(id_, [pd.Timestamp(a, 1, 1) for a in completos],
              [anual.loc[a, (codigo, "sum")] / pib_anual[a] * 100 for a in completos], sector="fiscal",
              nombre=nombre, corto=corto, unidad="% PIB", frecuencia="A", decimales=1,
              fuente=f"{FUENTE_SPNF}; BCE, Cuentas Nacionales (cálculo propio)")

# Deuda pública: un boletín mensual del MEF por archivo; la hoja del indicador cambia de
# nombre entre boletines, así que se ubica por su contenido.
MES_ARCHIVO = {"ENE": 1, "FEB": 2, "MAR": 3, "ABR": 4, "MAY": 5, "JUN": 6, "JUL": 7, "AGO": 8,
               "SEP": 9, "OCT": 10, "NOV": 11, "DIC": 12}
CLAVES_DEUDA = {"externa": "total deuda externa", "interna": "total deuda interna",
                "total": "deuda pública total", "pib": "pib nominal"}


def indicador_deuda(ruta: Path) -> dict:
    import openpyxl
    wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
    candidatas = [n for n in wb.sheetnames if re.fullmatch(r"1\.?", n.strip()) or "indicador" in n.lower()]
    for nombre in candidatas + [n for n in wb.sheetnames if n not in candidatas]:
        out = {}
        for r in wb[nombre].iter_rows(values_only=True):
            v = [x for x in r if x is not None]
            if len(v) < 2:
                continue
            etiqueta = limpiar(v[0]).lower()
            for k, c in CLAVES_DEUDA.items():
                if etiqueta.startswith(c) and k not in out and isinstance(v[1], (int, float)):
                    out[k] = float(v[1])
        if "total" in out and "externa" in out:
            return out
    raise ValueError(f"No se encontró el indicador de deuda en {ruta.name}")


deuda = []
for ruta in sorted((RAW / "mef_deuda").glob("*.xlsx")):
    if "PERFIL" in ruta.name.upper():
        continue
    nombre = ruta.name.upper()
    mes = next(m for clave, m in MES_ARCHIVO.items() if clave in nombre)
    anio = int(re.search(r"20\d\d", nombre)[0])
    deuda.append({"fecha": pd.Timestamp(anio, mes, 1), **indicador_deuda(ruta)})
deuda = pd.DataFrame(deuda).sort_values("fecha").drop_duplicates("fecha", keep="last").set_index("fecha")
# PIB de referencia de cada boletín (proyección del año); si falta, el del boletín más cercano.
deuda["pib"] = deuda["pib"].where(deuda["pib"] > 1e7).bfill().ffill()
FUENTE_DEUDA = "MEF, Boletín de deuda pública"
for col_, id_, nombre, corto in [
    ("externa", "deuda_externa", "Deuda pública externa", "Externa"),
    ("interna", "deuda_interna", "Deuda pública interna y otras obligaciones", "Interna"),
    ("total", "deuda_total", "Deuda pública total y otras obligaciones", "Deuda pública"),
]:
    registrar(id_, deuda.index, deuda[col_], sector="fiscal", nombre=nombre, corto=corto, unidad="USD mm",
              frecuencia="M", decimales=0, fuente=FUENTE_DEUDA, escala=1 / 1000)
registrar("deuda_pib", deuda.index, deuda["total"] / deuda["pib"] * 100, sector="fiscal",
          nombre="Deuda pública y otras obligaciones / PIB", corto="Deuda pública / PIB", unidad="% PIB",
          frecuencia="M", decimales=1, fuente=f"{FUENTE_DEUDA} (PIB de referencia de cada boletín)")

# Perfil de vencimientos (MEF): capital e intereses por año (largo plazo) y por mes (corto plazo).
perfil_lp = sorted((RAW / "mef_deuda").glob("PERFIL*LP*.xlsx"))[-1]
perfil_cp = sorted((RAW / "mef_deuda").glob("PERFIL*CP*.xlsx"))[-1]


def perfil_anual(hoja: str, prefijo: str) -> list[tuple]:
    """Totales por año de la deuda externa (por tipo de acreedor) e interna."""
    df = pd.read_excel(perfil_lp, sheet_name=hoja, header=None)
    fila_anios = next(i for i in range(20) if isinstance(df.iat[i, 1], (int, float)) and df.iat[i, 1] > 2000)
    anios = {j: int(v) for j, v in enumerate(df.iloc[fila_anios]) if isinstance(v, (int, float)) and v > 2000}
    etiquetas = [limpiar(x) if isinstance(x, str) else "" for x in df.iloc[:, 0]]
    totales = [i for i, e in enumerate(etiquetas) if e.lower() == "total general"]
    filas_ = {"externa": totales[0], "interna": totales[1]}
    if prefijo == "capital":
        for clave, texto in [("bonos", "BONOS EMITIDOS EN MERCADOS"), ("bancos", "CONVENIOS ORIGINALES (BANCOS"),
                             ("gobiernos", "CONVENIOS ORIGINALES (GOB"), ("organismos", "ORGANISMOS INTERNACIONALES")]:
            filas_[clave] = next(i for i, e in enumerate(etiquetas) if e.upper().startswith(texto))
    out = []
    for clave, i in filas_.items():
        for j, a in anios.items():
            v = pd.to_numeric(df.iat[i, j], errors="coerce")
            out.append(("anual", f"{a}-01-01", f"{prefijo}_{clave}", round((v if pd.notna(v) else 0) / 1e6, 3)))
    return out


def perfil_mensual(hoja: str, prefijo: str, rotulo: str) -> list[tuple]:
    """Total (externa + interna) de los próximos meses."""
    df = pd.read_excel(perfil_cp, sheet_name=hoja, header=None)
    i = next(i for i in range(30) if limpiar(df.iat[i, 0]).upper().startswith(f"{rotulo} DEUDA EXTERNA + INTERNA"))
    cab = df.iloc[i - 1]
    out = []
    for j in range(1, df.shape[1]):
        m = re.match(r"([A-ZÁÉÍÓÚ]+)\s+(\d{4})", limpiar(cab[j]).upper()) if isinstance(cab[j], str) else None
        if m and m[1].lower() in MESES_LARGOS:
            fecha = pd.Timestamp(int(m[2]), MESES_LARGOS[m[1].lower()], 1)
            out.append(("mensual", fecha.strftime("%Y-%m-%d"), f"{prefijo}_total",
                        round(float(pd.to_numeric(df.iat[i, j], errors="coerce") or 0) / 1e6, 3)))
    return out


vencimientos = (perfil_anual("19.", "capital") + perfil_anual("20.", "intereses")
                + perfil_mensual("16.", "capital", "CAPITAL") + perfil_mensual("17.", "intereses", "INTERES"))
pd.DataFrame(vencimientos, columns=["tipo", "fecha", "concepto", "valor"]).to_csv(OUT / "vencimientos.csv", index=False)
corte_perfil = re.search(r"(ENERO|FEBRERO|MARZO|ABRIL|MAYO|JUNIO|JULIO|AGOSTO|SEPTIEMBRE|OCTUBRE|NOVIEMBRE|DICIEMBRE)-(\d{4})",
                         perfil_lp.name.upper())
fecha_perfil = pd.Timestamp(int(corte_perfil[2]), MESES_LARGOS[corte_perfil[1].lower()], 1)

# Recaudación del SRI: hoja "Recaudación abierta" de cada archivo anual (miles de USD).
IMPUESTOS_SRI = [
    ("sri_renta", "Impuesto a la Renta", "Impuesto a la renta"),
    ("sri_iva", "Impuesto al Valor Agregado", "IVA"),
    ("sri_ice", "Impuesto a los Consumos Especiales", "ICE"),
    ("sri_isd", "Impuesto a la Salida de Divisas", "ISD"),
    ("sri_vehiculos", "Impuesto a los Vehículos Motorizados", "Vehículos"),
    ("sri_bruta", "RECAUDACIÓN BRUTA", "Recaudación bruta"),
    ("sri_neta", "RECAUDACIÓN NETA", "Recaudación neta"),
]
sri = {id_: {} for id_, _, _ in IMPUESTOS_SRI}
for ruta in sorted((RAW / "sri").glob("*.xlsx")):
    df = pd.read_excel(ruta, sheet_name="Recaudación abierta", header=None)
    fila_cab = next(i for i in range(15) if limpiar(df.iat[i, 0]).upper() == "CONCEPTOS")
    anio = int(re.search(r"20\d\d", limpiar(df.iat[1, 0]) + " " + ruta.name)[0])
    cols = {j: MESES_LARGOS[limpiar(c).lower()] for j, c in enumerate(df.iloc[fila_cab])
            if isinstance(c, str) and limpiar(c).lower() in MESES_LARGOS}
    etiquetas = [limpiar(x) if isinstance(x, str) else "" for x in df.iloc[:, 0]]
    # Meses con dato: el archivo del año en curso trae ceros en los meses futuros.
    i_neta = next(i for i, e in enumerate(etiquetas) if e.upper().startswith("RECAUDACIÓN NETA"))
    meses_con_dato = [j for j in cols if (pd.to_numeric(df.iat[i_neta, j], errors="coerce") or 0) > 0]
    for id_, texto, _ in IMPUESTOS_SRI:
        i = next(i for i, e in enumerate(etiquetas) if e.upper().startswith(texto.upper()))
        for j in meses_con_dato:
            sri[id_][pd.Timestamp(anio, cols[j], 1)] = float(pd.to_numeric(df.iat[i, j], errors="coerce") or 0) / 1000
for id_, _, corto in IMPUESTOS_SRI:
    s = pd.Series(sri[id_]).sort_index()
    registrar(id_, s.index, s, sector="fiscal", nombre=f"Recaudación SRI: {corto}", corto=corto,
              unidad="USD mm", frecuencia="M", decimales=0, fuente="SRI, Estadísticas de recaudación")

# ============================================================== SECTOR EXTERNO
bc = pd.read_excel(RAW / "balanza comercial.xlsx", header=4)
bc = bc[pd.to_datetime(bc["fecha_corte"], errors="coerce").notna()]
fechas = pd.to_datetime(bc["fecha_corte"]).dt.to_period("M").dt.to_timestamp()
for col_, id_, nombre, corto in [
    ("bc_total_exp", "x_total", "Exportaciones totales FOB", "Exportaciones"),
    ("bc_exp_pet", "x_pet", "Exportaciones petroleras FOB", "Petroleras"),
    ("bc_exp_no_pet", "x_no_pet", "Exportaciones no petroleras FOB", "No petroleras"),
    ("bc_tot_imp", "m_total", "Importaciones totales FOB", "Importaciones"),
    ("bc_imp_pet", "m_pet", "Importaciones petroleras FOB", "Petroleras"),
    ("bc_imp_no_pet", "m_no_pet", "Importaciones no petroleras FOB", "No petroleras"),
    ("bc_tot_bal_com", "bc_total", "Balanza comercial total", "Total"),
    ("bc_bal_com_pet", "bc_pet", "Balanza comercial petrolera", "Petrolera"),
    ("bc_bal_com_no_pet", "bc_no_pet", "Balanza comercial no petrolera", "No petrolera"),
]:
    registrar(id_, fechas, pd.to_numeric(bc[col_]), sector="externo", nombre=nombre, corto=corto,
              unidad="USD mm", frecuencia="M", decimales=0, fuente="BCE, Balanza Comercial")
registrar("terminos_intercambio", fechas, pd.to_numeric(bc["bc_ind_term_int"]), sector="externo",
          nombre="Índice de términos de intercambio", corto="Términos de intercambio", unidad="índice",
          frecuencia="M", decimales=1, fuente="BCE, Balanza Comercial")

bp = pd.read_excel(RAW / "Balanza de pagos.xlsx", header=None)
fila_cab = next(i for i in range(20) if limpiar(bp.iat[i, 1]) == "Componentes normalizados")
trimestres = {j: c for j, c in enumerate(bp.iloc[fila_cab]) if isinstance(c, str) and re.match(r"^(I|II|III|IV)-\d{4}$", c)}
fechas_bp = [pd.Timestamp(int(c.split("-")[1]), ROMANOS[c.split("-")[0]], 1) for c in trimestres.values()]
etiquetas = [limpiar(x) if isinstance(x, str) else "" for x in bp.iloc[:, 1]]


def fila_bp(texto: str, ocurrencia: int = 0, desde: int = 0) -> pd.Series:
    idx = [i for i, e in enumerate(etiquetas) if i >= desde and e.startswith(texto)][ocurrencia]
    return pd.to_numeric(bp.iloc[idx, list(trimestres)], errors="coerce").values


pasivos = next(i for i, e in enumerate(etiquetas) if e.startswith("Pasivos netos incurridos"))
FUENTE_BP = "BCE, Balanza de Pagos"
for id_, valores, nombre, corto in [
    ("cuenta_corriente", fila_bp("CUENTA CORRIENTE"), "Saldo de la cuenta corriente", "Cuenta corriente"),
    ("bp_bienes", fila_bp("BIENES ("), "Balanza de bienes (balanza de pagos)", "Bienes"),
    ("bp_servicios", fila_bp("SERVICIOS"), "Balanza de servicios", "Servicios"),
    ("bp_ingreso_primario", fila_bp("INGRESO PRIMARIO"), "Ingreso primario", "Ingreso primario"),
    ("bp_ingreso_secundario", fila_bp("INGRESO SECUNDARIO"), "Ingreso secundario", "Ingreso secundario"),
    ("remesas_recibidas", fila_bp("Remesas de trabajadores", 0), "Remesas recibidas", "Remesas recibidas"),
    ("remesas_enviadas", fila_bp("Remesas de trabajadores", 1), "Remesas enviadas", "Remesas enviadas"),
    ("ied", fila_bp("Inversión directa", 0, pasivos), "Inversión extranjera directa (pasivos netos)", "IED"),
]:
    registrar(id_, fechas_bp, valores, sector="externo", nombre=nombre, corto=corto, unidad="USD mm",
              frecuencia="T", decimales=0, fuente=FUENTE_BP)

cc = pd.Series(fila_bp("CUENTA CORRIENTE"), index=fechas_bp)
cc_anual = cc.groupby(cc.index.year).agg(["sum", "count"])
cc_anual = cc_anual[cc_anual["count"] == 4]["sum"]
anios = [a for a in cc_anual.index if a in pib_anual.index]
registrar("cuenta_corriente_pib", [pd.Timestamp(a, 1, 1) for a in anios],
          [cc_anual[a] / pib_anual[a] * 100 for a in anios], sector="externo",
          nombre="Saldo de la cuenta corriente", corto="Cuenta corriente", unidad="% PIB", frecuencia="A",
          decimales=1, fuente="BCE, Balanza de Pagos y Cuentas Nacionales")

# Comercio exterior por producto (exportaciones) y por uso o destino económico (importaciones)
exp = con.execute(f"""
    select make_date(year, month, 1) fecha, cast(matricero as int) codigo,
           any_value(desc_matricero) producto, sum(fob) / 1000 fob, sum(tm) / 1000 tm
    from '{RAW / "exports.parquet"}' where year >= 2018 and matricero > 0 group by 1, 2 order by 1, 2
""").df()
PETROLEO = {150101: "Crudo", 230601: "Derivados"}


def grupo_exportacion(codigo: int) -> str:
    if codigo in PETROLEO:
        return "petrolero"
    return {"1": "primario", "2": "industrializado"}.get(str(codigo)[0], "otro")


productos = (exp.groupby("codigo")["producto"].last().map(lambda p: limpiar(p).capitalize()).to_dict())
productos.update({c: n for c, n in PETROLEO.items()})
json.dump({str(c): {"producto": productos[c], "grupo": grupo_exportacion(c)} for c in sorted(productos)},
          open(OUT / "exportaciones.json", "w"), ensure_ascii=False, indent=1)
exp.assign(fecha=exp["fecha"].dt.strftime("%Y-%m-%d"), fob=exp["fob"].round(3), tm=exp["tm"].round(3))[
    ["fecha", "codigo", "fob", "tm"]].to_csv(OUT / "exportaciones.csv", index=False)

imp = con.execute(f"""
    select make_date(year, month, 1) fecha, trim(cuode1) cuode, any_value(desc_cuode1) descripcion,
           sum(fob) / 1000 fob, sum(cif) / 1000 cif
    from '{RAW / "imports.parquet"}' where year >= 2018 and trim(cuode1) not like '-%' group by 1, 2 order by 1, 2
""").df()
GRUPOS_CUODE = {"01": "Bienes de consumo", "02": "Bienes de consumo", "99": "Bienes de consumo",
                "03": "Combustibles y lubricantes", "04": "Materias primas", "05": "Materias primas",
                "06": "Materias primas", "07": "Bienes de capital", "08": "Bienes de capital",
                "09": "Bienes de capital", "10": "Diversos"}
json.dump({c: {"descripcion": limpiar(d).capitalize(), "grupo": GRUPOS_CUODE.get(c, "Diversos")}
           for c, d in imp.groupby("cuode")["descripcion"].last().items()},
          open(OUT / "importaciones.json", "w"), ensure_ascii=False, indent=1)
imp.assign(fecha=imp["fecha"].dt.strftime("%Y-%m-%d"), fob=imp["fob"].round(3), cif=imp["cif"].round(3))[
    ["fecha", "cuode", "fob", "cif"]].to_csv(OUT / "importaciones.csv", index=False)

# Control: el detalle por producto debe cuadrar con la balanza comercial.
x_detalle = exp.groupby("fecha")["fob"].sum()
x_bc = pd.Series(pd.to_numeric(bc["bc_total_exp"]).values, index=fechas)
dif = (x_detalle - x_bc.reindex(x_detalle.index)).abs().max()
print(f"Exportaciones: diferencia máxima detalle vs. balanza comercial = USD {dif:.1f} mm")

# ============================================================== MERCADOS (Bloomberg)
# id, ticker, campo, nombre, corto, grupo, unidad, decimales
MERCADOS = [
    # Índices bursátiles
    ("spx", "SPX Index", "PX_LAST", "S&P 500", "S&P 500", "bolsa", "puntos", 0),
    ("nasdaq", "CCMP Index", "PX_LAST", "Nasdaq Composite", "Nasdaq", "bolsa", "puntos", 0),
    ("dow", "INDU Index", "PX_LAST", "Dow Jones Industrial Average", "Dow Jones", "bolsa", "puntos", 0),
    ("stoxx50", "SX5E Index", "PX_LAST", "Euro Stoxx 50", "Euro Stoxx 50", "bolsa", "puntos", 0),
    ("dax", "DAX Index", "PX_LAST", "DAX (Alemania)", "DAX", "bolsa", "puntos", 0),
    ("ftse", "UKX Index", "PX_LAST", "FTSE 100 (Reino Unido)", "FTSE 100", "bolsa", "puntos", 0),
    ("cac", "CAC Index", "PX_LAST", "CAC 40 (Francia)", "CAC 40", "bolsa", "puntos", 0),
    ("ibex", "IBEX Index", "PX_LAST", "IBEX 35 (España)", "IBEX 35", "bolsa", "puntos", 0),
    ("nikkei", "NKY Index", "PX_LAST", "Nikkei 225 (Japón)", "Nikkei 225", "bolsa", "puntos", 0),
    ("hangseng", "HSI Index", "PX_LAST", "Hang Seng (Hong Kong)", "Hang Seng", "bolsa", "puntos", 0),
    ("shanghai", "SHCOMP Index", "PX_LAST", "Shanghai Composite (China)", "Shanghai", "bolsa", "puntos", 0),
    ("bovespa", "IBOV Index", "PX_LAST", "Bovespa (Brasil)", "Bovespa", "bolsa", "puntos", 0),
    # Tasas de política monetaria
    ("fed", "FDTR Index", "PX_LAST", "Fed: tasa de fondos federales (límite superior)", "Fed (EE. UU.)", "politica", "%", 2),
    ("fed_efectiva", "FEDL01 Index", "PX_LAST", "Tasa efectiva de fondos federales", "Fed funds efectiva", "politica", "%", 2),
    ("bce_tasa", "EURR002W Index", "PX_LAST", "BCE: tasa de operaciones principales de financiación", "BCE (zona euro)", "politica", "%", 2),
    ("boe", "UKBRBASE Index", "PX_LAST", "Banco de Inglaterra: Bank Rate", "BoE (Reino Unido)", "politica", "%", 2),
    ("boj", "BOJDTR Index", "PX_LAST", "Banco de Japón: tasa de política", "BoJ (Japón)", "politica", "%", 2),
    ("sofr_1m", "TSFR1M INDEX", "PX_LAST", "Term SOFR 1 mes", "Term SOFR 1M", "politica", "%", 2),
    ("sofr_3m", "TSFR3M INDEX", "PX_LAST", "Term SOFR 3 meses", "Term SOFR 3M", "politica", "%", 2),
    ("sofr_6m", "TSFR6M INDEX", "PX_LAST", "Term SOFR 6 meses", "Term SOFR 6M", "politica", "%", 2),
    ("sofr_12m", "TSFR12M INDEX", "PX_LAST", "Term SOFR 12 meses", "Term SOFR 12M", "politica", "%", 2),
    # Monedas
    ("dxy", "DXY Index", "PX_LAST", "Índice del dólar (DXY)", "DXY", "fx", "índice", 2),
    ("eurusd", "EURUSD Curncy", "PX_LAST", "EUR/USD", "EUR/USD", "fx", "USD por EUR", 4),
    ("gbpusd", "GBPUSD Curncy", "PX_LAST", "GBP/USD", "GBP/USD", "fx", "USD por GBP", 4),
    ("usdjpy", "USDJPY Curncy", "PX_LAST", "USD/JPY", "USD/JPY", "fx", "JPY por USD", 2),
    ("usdcny", "USDCNY Curncy", "PX_LAST", "USD/CNY", "USD/CNY", "fx", "CNY por USD", 4),
    ("usdcop", "USDCOP Curncy", "PX_LAST", "USD/COP", "USD/COP", "fx", "COP por USD", 0),
    ("usdbrl", "USDBRL Curncy", "PX_LAST", "USD/BRL", "USD/BRL", "fx", "BRL por USD", 4),
    ("usdmxn", "USDMXN Curncy", "PX_LAST", "USD/MXN", "USD/MXN", "fx", "MXN por USD", 4),
    # Commodities
    ("wti", "CL1 Comdty", "PX_LAST", "Petróleo WTI (Nymex, 1er futuro)", "WTI", "commodity", "USD/barril", 2),
    ("brent", "CO1 Comdty", "PX_LAST", "Petróleo Brent (ICE, 1er futuro)", "Brent", "commodity", "USD/barril", 2),
    ("gasolina", "XB1 Comdty", "PX_LAST", "Gasolina RBOB (Nymex)", "Gasolina RBOB", "commodity", "¢/galón", 1),
    ("diesel", "HO1 Comdty", "PX_LAST", "Heating oil / diésel (Nymex)", "Diésel (HO)", "commodity", "¢/galón", 1),
    ("gas_natural", "NG1 Comdty", "PX_LAST", "Gas natural (Nymex)", "Gas natural", "commodity", "USD/MMBtu", 2),
    ("cacao", "CC1 Comdty", "PX_LAST", "Cacao (ICE NY, 1er futuro)", "Cacao", "commodity", "USD/t", 0),
    ("oro", "GC1 Comdty", "PX_LAST", "Oro (COMEX, 1er futuro)", "Oro", "commodity", "USD/oz", 1),
    ("cobre", "HG1 Comdty", "PX_LAST", "Cobre (COMEX, 1er futuro)", "Cobre", "commodity", "¢/libra", 1),
    ("soya", "S 1 COMB Comdty", "PX_LAST", "Soya (CBOT)", "Soya", "commodity", "¢/bushel", 1),
    ("palma", "KOX6 Comdty", "PX_LAST", "Aceite de palma (Bursa Malaysia)", "Aceite de palma", "commodity", "MYR/t", 0),
    ("trigo", "W Z6 COMB Comdty", "PX_LAST", "Trigo (CBOT, dic-26)", "Trigo", "commodity", "¢/bushel", 1),
    ("maiz", "EPX6 Comdty", "PX_LAST", "Maíz (Euronext, nov-26)", "Maíz", "commodity", "EUR/t", 1),
    # Bonos soberanos de Ecuador
    ("ec2030_px", "ZO2094456 Corp", "PX_LAST", "Bono Ecuador 2030: precio", "Ecuador 2030", "ecuador", "USD por 100", 2),
    ("ec2034_px", "YI4276048 Corp", "PX_LAST", "Bono Ecuador 2034: precio", "Ecuador 2034", "ecuador", "USD por 100", 2),
    ("ec2035_px", "ZO2104214 Corp", "PX_LAST", "Bono Ecuador 2035: precio", "Ecuador 2035", "ecuador", "USD por 100", 2),
    ("ec2039_px", "YI4276055 Corp", "PX_LAST", "Bono Ecuador 2039: precio", "Ecuador 2039", "ecuador", "USD por 100", 2),
    ("ec2040_px", "ZO2104560 Corp", "PX_LAST", "Bono Ecuador 2040: precio", "Ecuador 2040", "ecuador", "USD por 100", 2),
    ("ec2030_ytm", "ZO2094456 Corp", "YLD_YTM_MID", "Bono Ecuador 2030: rendimiento", "Ecuador 2030", "ecuador", "%", 2),
    ("ec2034_ytm", "YI4276048 Corp", "YLD_YTM_MID", "Bono Ecuador 2034: rendimiento", "Ecuador 2034", "ecuador", "%", 2),
    ("ec2035_ytm", "ZO2104214 Corp", "YLD_YTM_MID", "Bono Ecuador 2035: rendimiento", "Ecuador 2035", "ecuador", "%", 2),
    ("ec2039_ytm", "YI4276055 Corp", "YLD_YTM_MID", "Bono Ecuador 2039: rendimiento", "Ecuador 2039", "ecuador", "%", 2),
    ("ec2040_ytm", "ZO2104560 Corp", "YLD_YTM_MID", "Bono Ecuador 2040: rendimiento", "Ecuador 2040", "ecuador", "%", 2),
]
# Curvas soberanas: (prefijo, país, [(plazo, ticker)])
CURVAS = [
    ("us", "EE. UU.", [("1M", "USGG1M Index"), ("3M", "USGG3M Index"), ("6M", "USGG6M Index"),
                       ("1A", "USGG12M Index"), ("2A", "USGG2YR Index"), ("3A", "USGG3YR Index"),
                       ("5A", "USGG5YR Index"), ("7A", "USGG7YR Index"), ("10A", "USGG10YR Index"),
                       ("30A", "USGG30YR Index")]),
    ("de", "Alemania", [("2A", "BV020910 BVLI INDEX"), ("5A", "BV050910 BVLI INDEX"),
                        ("10A", "BV100910 BVLI INDEX"), ("30A", "BV300910 BVLI INDEX")]),
    ("uk", "Reino Unido", [("1A", "GUKG1 Index"), ("2A", "GUKG2 Index"), ("5A", "GUKG5 Index"),
                           ("7A", "GUKG7 Index"), ("10A", "GUKG10 Index"), ("15A", "GUKG15 Index"),
                           ("20A", "GUKG20 Index"), ("30A", "GUKG30 Index")]),
    ("jp", "Japón", [("3M", "BVCSEI3M BVLI INDEX"), ("1A", "BVCSEI01 BVLI INDEX"), ("2A", "BVCSEI02 BVLI INDEX"),
                     ("3A", "BVCSEI03 BVLI INDEX"), ("5A", "BVCSEI05 BVLI INDEX"), ("7A", "BVCSEI07 BVLI INDEX"),
                     ("10A", "BVCSEI10 BVLI INDEX"), ("20A", "BVCSEI20 BVLI INDEX"), ("30A", "BVCSEI30 BVLI INDEX")]),
]
for pref, pais, plazos in CURVAS:
    for plazo, ticker in plazos:
        MERCADOS.append((f"{pref}_{plazo.lower()}", ticker, "PX_LAST", f"Bono soberano {pais} {plazo}",
                         f"{pais} {plazo}", f"curva_{pref}", "%", 3))

archivo_bbg = sorted(RAW.glob("series_bloomberg_*.csv"))[-1]
bbg = pd.read_csv(archivo_bbg, parse_dates=["fecha"])
bbg = bbg.drop_duplicates(["ticker", "campo", "fecha"])
ancho = {}
meta_mercados = []
for id_, ticker, campo, nombre, corto, grupo, unidad, dec in MERCADOS:
    s = bbg[(bbg["ticker"] == ticker) & (bbg["campo"] == campo)].set_index("fecha")["valor"]
    if s.empty:
        raise ValueError(f"Sin datos de Bloomberg para {ticker} {campo}")
    ancho[id_] = s
    meta_mercados.append(dict(id=id_, sector="internacional", grupo=grupo, nombre=nombre, corto=corto,
                              unidad=unidad, frecuencia="D", decimales=dec, fuente="Bloomberg", ticker=ticker))
mercados = pd.DataFrame(ancho).sort_index()
mercados = mercados[mercados.index.dayofweek < 5]

# Licencia de Bloomberg: el sitio publica solo lo que muestra. Las series que se grafican
# completas viajan completas; las que solo aparecen en tablas o curvas viajan con los valores
# de las fechas de referencia que usan las páginas (hoy, 1 mes, 3 meses, cierre del año
# anterior y 12 meses).
HISTORIA_COMPLETA = {"fed", "bce_tasa", "boe", "boj", "us_10a", "us_2a", "dxy", "wti", "brent", "cacao",
                     "oro", "cobre", "gasolina", "diesel", "ec2030_ytm", "ec2035_ytm", "ec2040_ytm"}
ULTIMO_ANIO = {"spx", "stoxx50", "nikkei", "bovespa"}
corte = mercados.index.max()
referencias = [corte, corte - pd.Timedelta(days=30), corte - pd.Timedelta(days=91),
               pd.Timestamp(corte.year - 1, 12, 31), corte - pd.DateOffset(years=1)]
for id_ in mercados.columns:
    if id_ in HISTORIA_COMPLETA:
        continue
    s = mercados[id_].dropna()
    conservar = {s.index[s.index <= r].max() for r in referencias if (s.index <= r).any()}
    if id_ in ULTIMO_ANIO:
        conservar |= set(s.index[s.index >= referencias[-1] - pd.Timedelta(days=7)])
    mercados.loc[~mercados.index.isin(conservar), id_] = None
mercados = mercados.dropna(how="all")
mercados.index = mercados.index.strftime("%Y-%m-%d")
mercados.index.name = "fecha"
mercados.round(4).to_csv(OUT / "mercados.csv")
json.dump({"curvas": [{"id": p, "pais": n, "plazos": [t for t, _ in pl]} for p, n, pl in CURVAS],
           "series": meta_mercados},
          open(OUT / "mercados.json", "w"), ensure_ascii=False, indent=1)

# ============================================================== Escritura
pd.DataFrame(filas, columns=["id", "fecha", "valor"]).to_csv(OUT / "series.csv", index=False)
json.dump({"incidencias_ipc": fecha_incidencias.strftime("%Y-%m-%d"),
           "perfil_vencimientos": fecha_perfil.strftime("%Y-%m-%d"), "series": catalogo},
          open(OUT / "catalogo.json", "w"), ensure_ascii=False, indent=1)

ids = [c["id"] for c in catalogo]
assert len(ids) == len(set(ids)), "IDs duplicados en el catálogo"
print(f"series.csv: {len(filas)} filas, {len(catalogo)} series")
print(f"mercados.csv: {mercados.shape[0]} fechas × {mercados.shape[1]} series (archivo {archivo_bbg.name})")
print(f"exportaciones.csv: {len(exp)} filas · importaciones.csv: {len(imp)} filas")

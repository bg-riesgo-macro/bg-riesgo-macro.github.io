# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.2"]
# ///
"""Descarga de internet las series que no llegan como archivo: mercados internacionales y
previsiones de crecimiento del FMI y del Banco Mundial.

Uso (desde la raíz del repositorio, antes de procesar_datos.py):

    uv run scripts/descargar_datos.py

Salidas en data_raw/:
    mercados.csv              series diarias de mercados en formato largo (id, fecha, valor)
    bonos_soberanos.json      precios diarios de los bonos globales de Ecuador (BCE, un día de rezago)
    riesgo_pais.json          riesgo país (EMBI Ecuador) diario (BCE, con datos de JP Morgan)
    previsiones/fmi.csv       crecimiento del PIB de Ecuador, Perspectivas de la economía mundial (WEO)
    previsiones/bm.csv        crecimiento del PIB de Ecuador, Perspectivas económicas mundiales (GEP)
"""

from __future__ import annotations

import csv
import io
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from catalogo_mercados import MERCADOS

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "data_raw"
INICIO = date(2020, 1, 1)
HOY = date.today()

# Cada servidor acepta clientes distintos: FRED y el FMI no responden a un navegador
# genérico y Yahoo rechaza a curl.
NAVEGADOR = "Mozilla/5.0 (X11; Linux x86_64)"
CURL = "curl/8.5.0"
MESES_EN = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august", "september",
     "october", "november", "december"])}
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def bajar(url: str, agente: str = NAVEGADOR, intentos: int = 3) -> bytes:
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": agente})
            return urllib.request.urlopen(req, timeout=60).read()
        except Exception:
            if i == intentos - 1:
                raise
            time.sleep(3 * (i + 1))


def numero(texto) -> float | None:
    try:
        return float(texto)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ fuentes de mercados
def yahoo(codigo: str) -> pd.Series:
    inicio = int(datetime(INICIO.year, INICIO.month, INICIO.day).timestamp())
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(codigo)}"
           f"?period1={inicio}&period2={int(time.time())}&interval=1d")
    r = json.loads(bajar(url))["chart"]["result"][0]
    zona = ZoneInfo(r["meta"]["exchangeTimezoneName"])
    # Solo cierres: mientras la sesión vigente no termina, su barra es un precio intradía.
    sesion = r["meta"]["currentTradingPeriod"]["regular"]
    corte = sesion["start"] if time.time() < sesion["end"] else float("inf")
    pares = [(t, v) for t, v in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]) if t < corte]
    # Yahoo tarda en llenar el cierre de la última sesión terminada (pasa con las bolsas asiáticas);
    # mientras tanto, el cierre está en la ficha.
    if pares and pares[-1][1] is None and r["meta"]["regularMarketTime"] > pares[-1][0]:
        pares[-1] = (pares[-1][0], r["meta"]["regularMarketPrice"])
    return pd.Series({datetime.fromtimestamp(t, zona).date(): v for t, v in pares}, dtype=float)


def fred(codigo: str) -> pd.Series:
    texto = bajar(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={codigo}&cosd={INICIO}", CURL).decode()
    df = pd.read_csv(io.StringIO(texto))
    return pd.Series(pd.to_numeric(df.iloc[:, 1], errors="coerce").values,
                     index=pd.to_datetime(df.iloc[:, 0]).dt.date)


_cache: dict[str, object] = {}


def boe(codigo: str) -> pd.Series:
    # Una sola consulta para todas las series del Banco de Inglaterra.
    if "boe" not in _cache:
        codigos = ",".join(c for _, f, c, *_ in MERCADOS if f == "boe")
        url = ("https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes"
               f"&Datefrom={INICIO:%d/%b/%Y}&Dateto=now&SeriesCodes={codigos}&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N")
        df = pd.read_csv(io.BytesIO(bajar(url)))
        df.index = pd.to_datetime(df["DATE"], format="%d %b %Y").dt.date
        _cache["boe"] = df
    return pd.to_numeric(_cache["boe"][codigo], errors="coerce")


def bundesbank(codigo: str) -> pd.Series:
    texto = bajar(f"https://api.statistiken.bundesbank.de/rest/download/{codigo}?format=csv&lang=en").decode("utf-8-sig")
    datos = {}
    for fila in csv.reader(io.StringIO(texto)):
        if fila and re.fullmatch(r"\d{4}-\d{2}-\d{2}", fila[0]) and fila[0] >= str(INICIO):
            datos[date.fromisoformat(fila[0])] = numero(fila[1])
    return pd.Series(datos, dtype=float)


def mof(codigo: str) -> pd.Series:
    # Histórico (hasta el mes anterior) más el archivo del mes en curso.
    if "mof" not in _cache:
        base = "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate"
        filas = []
        for archivo in ("historical/jgbcme_all.csv", "jgbcme.csv"):
            texto = bajar(f"{base}/{archivo}").decode("latin-1")
            lector = list(csv.reader(io.StringIO(texto)))
            cab = next(f for f in lector if f and f[0] == "Date")
            for f in lector:
                if f and re.fullmatch(r"\d{4}/\d{1,2}/\d{1,2}", f[0]):
                    filas.append({"fecha": datetime.strptime(f[0], "%Y/%m/%d").date(),
                                  **{c: numero(v) for c, v in zip(cab[1:], f[1:])}})
        df = pd.DataFrame(filas).drop_duplicates("fecha", keep="last").set_index("fecha")
        _cache["mof"] = df[df.index >= INICIO]
    return _cache["mof"][codigo]


def boj(codigo: str) -> pd.Series:
    datos, posicion = {}, ""
    while True:
        url = ("https://www.stat-search.boj.or.jp/api/v1/getDataCode?format=csv&lang=en&db=FM01"
               f"&code={codigo}&startDate={INICIO:%Y%m}&endDate={HOY:%Y%m}{posicion}")
        lineas = list(csv.reader(io.StringIO(bajar(url).decode("utf-8-sig"))))
        cab = next(i for i, f in enumerate(lineas) if f and f[0] == "SERIES_CODE")
        for f in lineas[cab + 1:]:
            if len(f) >= 8 and f[0] == codigo:
                datos[datetime.strptime(f[6], "%Y%m%d").date()] = numero(f[7])
        siguiente = next((f[1] for f in lineas if f and f[0] == "NEXTPOSITION"), "")
        if not siguiente:
            break
        posicion = f"&startPosition={siguiente}"
    return pd.Series(datos, dtype=float)


DESCARGA = {"yahoo": yahoo, "fred": fred, "boe": boe, "bundesbank": bundesbank, "mof": mof, "boj": boj}

filas = []
fallas = []
for id_, fuente, codigo, *_ in MERCADOS:
    try:
        s = DESCARGA[fuente](codigo).dropna()
    except Exception as e:  # una fuente caída no debe impedir actualizar las demás
        fallas.append(f"{id_} ({fuente} {codigo}): {e}")
        continue
    s = s[[d.weekday() < 5 for d in s.index]]
    s = s[~s.index.duplicated(keep="last")]  # Yahoo repite el día en curso mientras el mercado está abierto
    filas += [(id_, f.isoformat(), round(float(v), 6)) for f, v in s.items()]
    print(f"{id_:<14} {fuente:<10} {len(s):>5} obs. hasta {max(s.index)}")
    if fuente == "yahoo":
        time.sleep(0.5)

if fallas:
    print("mercados.csv no se actualizó: falló la descarga de alguna serie")
else:
    pd.DataFrame(filas, columns=["id", "fecha", "valor"]).to_csv(RAW / "mercados.csv", index=False)
    print(f"mercados.csv: {len(filas)} filas")

# Bonos soberanos de Ecuador: precios que publica el BCE en su sitio.
try:
    bonos = bajar("https://contenido.bce.fin.ec/wp-content/uploads/ESTADISTICAS-ECONOMICAS/indicadores/"
                  "datos_bonos_soberanos.json")
    n = len(json.loads(bonos)["view_ind_bonos"])
    (RAW / "bonos_soberanos.json").write_bytes(bonos)
    print(f"bonos_soberanos.json: {n} observaciones")
except Exception as e:
    fallas.append(f"bonos soberanos (BCE): {e}")

# Riesgo país: lo publica el BCE en el mismo directorio, junto con el precio del oro.
try:
    formulario = bajar("https://contenido.bce.fin.ec/wp-content/uploads/ESTADISTICAS-ECONOMICAS/indicadores/"
                       "datos_formulario.json")
    embi = [x for x in json.loads(formulario)["view_ind_formulario"] if x["Indicador"] == "Riesgo País"]
    (RAW / "riesgo_pais.json").write_bytes(formulario)
    print(f"riesgo_pais.json: {len(embi)} observaciones hasta {max(x['Fecha'] for x in embi)}")
except Exception as e:
    fallas.append(f"riesgo país (BCE): {e}")


# ------------------------------------------------------------------ previsiones
def guardar_previsiones(archivo: str, institucion: str, informe: str, publicacion: date, valores: dict):
    df = pd.DataFrame([(institucion, informe, publicacion.isoformat(), int(a), v)
                       for a, v in sorted(valores.items()) if int(a) >= HOY.year - 1],
                      columns=["institucion", "informe", "fecha", "anio", "valor"])
    (RAW / "previsiones").mkdir(exist_ok=True)
    df.to_csv(RAW / "previsiones" / archivo, index=False)
    print(f"previsiones/{archivo}: {informe} → " + ", ".join(f"{a}: {v}" for a, v in zip(df["anio"], df["valor"])))


def previsiones_fmi():
    # FMI: la ficha del indicador dice de qué edición del WEO son los datos ("October 2026").
    weo = json.loads(bajar("https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH/ECU", CURL))
    ficha = json.loads(bajar("https://www.imf.org/external/datamapper/api/v1/indicators", CURL))["indicators"]["NGDP_RPCH"]
    m = re.search(r"\((\w+) (\d{4})\)", ficha["source"])
    pub = date(int(m[2]), MESES_EN[m[1].lower()], 1)
    guardar_previsiones("fmi.csv", "FMI", f"Perspectivas de la economía mundial (WEO), {MESES[pub.month - 1]}-{pub.year}",
                        pub, weo["values"]["NGDP_RPCH"]["ECU"])


def previsiones_bm():
    # Banco Mundial: fuente 27 = Global Economic Prospects; la fecha de actualización marca la edición.
    gep = json.loads(bajar("https://api.worldbank.org/v2/country/ECU/indicator/NYGDPMKTPKDZ"
                           f"?source=27&format=json&date={HOY.year - 1}:{HOY.year + 5}&per_page=100", CURL))
    pub = date.fromisoformat(gep[0]["lastupdated"]).replace(day=1)
    guardar_previsiones("bm.csv", "Banco Mundial",
                        f"Perspectivas económicas mundiales (GEP), {MESES[pub.month - 1]}-{pub.year}", pub,
                        {x["date"]: x["value"] for x in gep[1] if x["value"] is not None})


for descarga in (previsiones_fmi, previsiones_bm):
    try:
        descarga()
    except Exception as e:
        fallas.append(f"{descarga.__name__}: {e}")

if fallas:
    raise SystemExit("No se pudo descargar:\n  " + "\n  ".join(fallas))

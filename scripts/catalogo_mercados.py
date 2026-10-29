"""Series de mercados internacionales: de dónde se descargan y cómo se muestran.

Lo usan descargar_datos.py (para bajarlas) y procesar_datos.py (para publicarlas).

Fuentes:
    yahoo       Yahoo Finance (cierre diario)
    fred        FRED, Reserva Federal de St. Louis
    boe         Banco de Inglaterra (Interactive Database)
    bundesbank  Deutsche Bundesbank (estructura temporal de tasas, método Svensson)
    mof         Ministerio de Finanzas de Japón (rendimientos de bonos JGB)
    boj         Banco de Japón (Time-Series Data Search)
"""

FUENTES = {
    "yahoo": "Yahoo Finance",
    "fred": "FRED (Reserva Federal de St. Louis)",
    "boe": "Banco de Inglaterra",
    "bundesbank": "Deutsche Bundesbank",
    "mof": "Ministerio de Finanzas de Japón",
    "boj": "Banco de Japón",
}

# id, fuente, código, nombre, corto, grupo, unidad, decimales
MERCADOS = [
    # Índices bursátiles
    ("spx", "yahoo", "^GSPC", "S&P 500", "S&P 500", "bolsa", "puntos", 0),
    ("nasdaq", "yahoo", "^IXIC", "Nasdaq Composite", "Nasdaq", "bolsa", "puntos", 0),
    ("dow", "yahoo", "^DJI", "Dow Jones Industrial Average", "Dow Jones", "bolsa", "puntos", 0),
    ("stoxx50", "yahoo", "^STOXX50E", "Euro Stoxx 50", "Euro Stoxx 50", "bolsa", "puntos", 0),
    ("dax", "yahoo", "^GDAXI", "DAX (Alemania)", "DAX", "bolsa", "puntos", 0),
    ("ftse", "yahoo", "^FTSE", "FTSE 100 (Reino Unido)", "FTSE 100", "bolsa", "puntos", 0),
    ("cac", "yahoo", "^FCHI", "CAC 40 (Francia)", "CAC 40", "bolsa", "puntos", 0),
    ("ibex", "yahoo", "^IBEX", "IBEX 35 (España)", "IBEX 35", "bolsa", "puntos", 0),
    ("nikkei", "yahoo", "^N225", "Nikkei 225 (Japón)", "Nikkei 225", "bolsa", "puntos", 0),
    ("hangseng", "yahoo", "^HSI", "Hang Seng (Hong Kong)", "Hang Seng", "bolsa", "puntos", 0),
    ("shanghai", "yahoo", "000001.SS", "Shanghai Composite (China)", "Shanghai", "bolsa", "puntos", 0),
    ("bovespa", "yahoo", "^BVSP", "Bovespa (Brasil)", "Bovespa", "bolsa", "puntos", 0),
    # Tasas de política monetaria y de corto plazo
    ("fed", "fred", "DFEDTARU", "Fed: tasa de fondos federales (límite superior)", "Fed (EE. UU.)", "politica", "%", 2),
    ("fed_inf", "fred", "DFEDTARL", "Fed: tasa de fondos federales (límite inferior)", "Fed, límite inferior", "politica", "%", 2),
    ("fed_efectiva", "fred", "DFF", "Tasa efectiva de fondos federales", "Fed funds efectiva", "politica", "%", 2),
    ("bce_tasa", "fred", "ECBMRRFR", "BCE: tasa de operaciones principales de financiación", "BCE (zona euro)", "politica", "%", 2),
    ("boe", "boe", "IUDBEDR", "Banco de Inglaterra: Bank Rate", "BoE (Reino Unido)", "politica", "%", 2),
    ("boj", "boj", "STRDCLUCON", "Banco de Japón: tasa call a un día sin garantía (promedio)", "BoJ (Japón)", "politica", "%", 2),
    # La SOFR a plazo (Term SOFR) es de CME y no es pública; las letras del Tesoro (curva "us")
    # sirven de referencia de tasas a plazo en dólares.
    ("sofr", "fred", "SOFR", "SOFR a un día", "SOFR a un día", "politica", "%", 2),
    # Monedas
    ("dxy", "yahoo", "DX-Y.NYB", "Índice del dólar (DXY)", "DXY", "fx", "índice", 2),
    ("eurusd", "yahoo", "EURUSD=X", "EUR/USD", "EUR/USD", "fx", "USD por EUR", 4),
    ("gbpusd", "yahoo", "GBPUSD=X", "GBP/USD", "GBP/USD", "fx", "USD por GBP", 4),
    ("usdjpy", "yahoo", "JPY=X", "USD/JPY", "USD/JPY", "fx", "JPY por USD", 2),
    ("usdcny", "yahoo", "CNY=X", "USD/CNY", "USD/CNY", "fx", "CNY por USD", 4),
    ("usdcop", "yahoo", "COP=X", "USD/COP", "USD/COP", "fx", "COP por USD", 0),
    ("usdbrl", "yahoo", "BRL=X", "USD/BRL", "USD/BRL", "fx", "BRL por USD", 4),
    ("usdmxn", "yahoo", "MXN=X", "USD/MXN", "USD/MXN", "fx", "MXN por USD", 4),
    # Materias primas (primer futuro)
    ("wti", "yahoo", "CL=F", "Petróleo WTI (Nymex, 1er futuro)", "WTI", "commodity", "USD/barril", 2),
    ("brent", "yahoo", "BZ=F", "Petróleo Brent (ICE, 1er futuro)", "Brent", "commodity", "USD/barril", 2),
    ("gasolina", "yahoo", "RB=F", "Gasolina RBOB (Nymex)", "Gasolina RBOB", "commodity", "USD/galón", 2),
    ("diesel", "yahoo", "HO=F", "Heating oil / diésel (Nymex)", "Diésel (HO)", "commodity", "USD/galón", 2),
    ("gas_natural", "yahoo", "NG=F", "Gas natural (Nymex)", "Gas natural", "commodity", "USD/MMBtu", 2),
    ("cacao", "yahoo", "CC=F", "Cacao (ICE NY, 1er futuro)", "Cacao", "commodity", "USD/t", 0),
    ("oro", "yahoo", "GC=F", "Oro (COMEX, 1er futuro)", "Oro", "commodity", "USD/oz", 1),
    ("cobre", "yahoo", "HG=F", "Cobre (COMEX, 1er futuro)", "Cobre", "commodity", "USD/libra", 2),
    ("soya", "yahoo", "ZS=F", "Soya (CBOT, 1er futuro)", "Soya", "commodity", "¢/bushel", 1),
    ("trigo", "yahoo", "ZW=F", "Trigo (CBOT, 1er futuro)", "Trigo", "commodity", "¢/bushel", 1),
    ("maiz", "yahoo", "ZC=F", "Maíz (CBOT, 1er futuro)", "Maíz", "commodity", "¢/bushel", 1),
]

# Curvas soberanas: (prefijo, país, fuente, [(plazo, código)])
CURVAS = [
    ("us", "EE. UU.", "fred", [("1M", "DGS1MO"), ("3M", "DGS3MO"), ("6M", "DGS6MO"), ("1A", "DGS1"), ("2A", "DGS2"),
                               ("3A", "DGS3"), ("5A", "DGS5"), ("7A", "DGS7"), ("10A", "DGS10"), ("30A", "DGS30")]),
    ("de", "Alemania", "bundesbank", [(f"{n}A", f"BBSIS/D.I.ZST.ZI.EUR.S1311.B.A604.R{n:02d}XX.R.A.A._Z._Z.A")
                                      for n in (1, 2, 5, 10, 20, 30)]),
    ("uk", "Reino Unido", "boe", [("5A", "IUDSNPY"), ("10A", "IUDMNPY"), ("20A", "IUDLNPY")]),
    ("jp", "Japón", "mof", [(p, p.replace("A", "Y")) for p in ("1A", "2A", "3A", "5A", "7A", "10A", "20A", "30A")]),
]

for _pref, _pais, _fuente, _plazos in CURVAS:
    for _plazo, _codigo in _plazos:
        _tipo = "Letra del Tesoro" if _plazo.endswith("M") else "Bono soberano"
        MERCADOS.append((f"{_pref}_{_plazo.lower()}", _fuente, _codigo, f"{_tipo} {_pais} {_plazo}",
                         f"{_pais} {_plazo}", f"curva_{_pref}", "%", 3))

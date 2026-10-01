from pathlib import Path
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo
from statistics import median
import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="C2 | Asignación Inteligente del Trabajo",
    page_icon="🧵",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE = Path(__file__).resolve().parent

TIPOS_VALIDOS = ["Gala", "Novia", "Quinceañera"]

MAPEO_TIPOS_LEGACY = {
    "gala": "Gala",
    "novia": "Novia",
    "quinceañera": "Quinceañera",
    "quinceanera": "Quinceañera",
    "15 años": "Quinceañera",
    "15 anos": "Quinceañera",
    # Categorías antiguas de los archivos de prueba:
    "promoción": "Gala",
    "promocion": "Gala",
    "civil": "Novia",
}


def normalizar_tipo_vestido(valor):
    """Convierte categorías antiguas al alcance actual de tres tipos."""
    if pd.isna(valor):
        return valor

    clave = str(valor).strip().casefold()
    return MAPEO_TIPOS_LEGACY.get(clave, str(valor).strip())
ETAPAS = ["Corte", "Ensamblaje", "Acabados y detalles", "Planchado"]

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(145deg, #061522 0%, #0B2131 52%, #0D2B3E 100%);
        color: #F5F9FC;
    }
    header[data-testid="stHeader"] { background: rgba(6,21,34,.92); }
    #MainMenu, footer { visibility: hidden; }
    .block-container {
        max-width: 1580px;
        padding-top: 1rem;
        padding-left: 1.15rem;
        padding-right: 1.15rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3, h4 { color: #F7FBFF !important; }
    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, rgba(29,66,91,.96), rgba(15,43,62,.96));
        border: 1px solid rgba(106,188,230,.22);
        border-radius: 14px;
        padding: .65rem .8rem;
        box-shadow: 0 9px 22px rgba(0,0,0,.18);
    }
    div[data-testid="stMetricLabel"] p { color: #AFC8D8 !important; font-weight: 700 !important; }
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: 900 !important; }
    .hero {
        background: linear-gradient(110deg, #0D3047, #123F5C);
        border: 1px solid rgba(115,199,239,.30);
        border-radius: 18px;
        padding: 15px 20px;
        box-shadow: 0 12px 30px rgba(0,0,0,.22);
        margin-bottom: 12px;
    }
    .hero-title { font-size: 1.34rem; font-weight: 900; color: #FFFFFF; }
    .hero-sub { color: #AFC5D4; font-size: .86rem; margin-top: 2px; }
    .section-label {
        font-size: .80rem; font-weight: 900; letter-spacing: .35px;
        text-transform: uppercase; color: #EAF4FA; margin-bottom: .35rem;
    }
    .light-card {
        background: linear-gradient(180deg, #EDF4F7, #DCE8EE);
        color: #132635;
        border: 1px solid #C0D0D9;
        border-radius: 14px;
        padding: 14px 15px;
        min-height: 168px;
    }
    .blue-card {
        background: linear-gradient(145deg, #1E5577, #163E58);
        color: #FFFFFF;
        border: 1px solid rgba(130,211,247,.28);
        border-radius: 14px;
        padding: 14px 15px;
        min-height: 168px;
    }
    .score { font-size: 2.25rem; font-weight: 900; color: #7DD8FF; line-height: 1; }
    .muted { color: #9FB7C8; font-size: .74rem; }
    .kit-ready {
        display:inline-block; padding:4px 8px; border-radius:999px;
        background:rgba(66,211,154,.16); color:#6FE2B8;
        border:1px solid rgba(111,226,184,.35); font-size:.68rem; font-weight:900;
    }
    .kit-prep {
        display:inline-block; padding:4px 8px; border-radius:999px;
        background:rgba(246,193,87,.16); color:#FFD47A;
        border:1px solid rgba(255,212,122,.35); font-size:.68rem; font-weight:900;
    }
    .kit-block {
        display:inline-block; padding:4px 8px; border-radius:999px;
        background:rgba(255,111,111,.16); color:#FF9A9A;
        border:1px solid rgba(255,154,154,.35); font-size:.68rem; font-weight:900;
    }
    .stButton > button, .stDownloadButton > button {
        border-radius: 10px !important;
        min-height: 42px;
        font-weight: 850 !important;
    }
    div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }


    /* =======================================================
       CONTRASTE GENERAL: FONDO OSCURO = TEXTO CLARO
       ======================================================= */

    /* Texto normal de Streamlit */
    .stApp,
    .stApp p,
    .stApp li,
    .stApp small,
    .stApp strong,
    .stApp em {
        color: #EAF3F8;
    }

    /* Etiquetas de filtros, selectores e inputs */
    div[data-testid="stSelectbox"] label,
    div[data-testid="stMultiSelect"] label,
    div[data-testid="stNumberInput"] label,
    div[data-testid="stTextInput"] label,
    div[data-testid="stDateInput"] label,
    div[data-testid="stSlider"] label,
    div[data-testid="stRadio"] label,
    div[data-testid="stCheckbox"] label,
    div[data-testid="stFileUploader"] label {
        color: #EAF3F8 !important;
        font-weight: 750 !important;
    }

    div[data-testid="stSelectbox"] label p,
    div[data-testid="stMultiSelect"] label p,
    div[data-testid="stNumberInput"] label p,
    div[data-testid="stTextInput"] label p,
    div[data-testid="stDateInput"] label p,
    div[data-testid="stSlider"] label p,
    div[data-testid="stRadio"] label p,
    div[data-testid="stCheckbox"] label p {
        color: #EAF3F8 !important;
    }

    /* Selectores: fondo claro, texto oscuro para legibilidad */
    div[data-baseweb="select"] > div {
        background-color: #F4F8FB !important;
        border-color: #B9CFDC !important;
        color: #102331 !important;
    }

    div[data-baseweb="select"] span,
    div[data-baseweb="select"] input {
        color: #102331 !important;
    }

    /* Menú desplegable */
    ul[role="listbox"],
    div[role="listbox"] {
        background: #F7FAFC !important;
        color: #102331 !important;
    }

    li[role="option"],
    div[role="option"] {
        color: #102331 !important;
        background: #F7FAFC !important;
    }

    li[role="option"]:hover,
    div[role="option"]:hover {
        background: #DCEAF2 !important;
    }

    /* Tabs */
    button[data-baseweb="tab"] {
        color: #BFD3DF !important;
        font-weight: 800 !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #FFFFFF !important;
        border-bottom-color: #63D4F2 !important;
    }

    button[data-baseweb="tab"] p {
        color: inherit !important;
    }

    /* Captions y mensajes secundarios */
    div[data-testid="stCaptionContainer"] p,
    .stCaptionContainer,
    .st-emotion-cache-qdbtli {
        color: #AFC6D5 !important;
    }

    /* Alertas */
    div[data-testid="stAlert"] p,
    div[data-testid="stAlert"] li {
        color: inherit !important;
    }

    /* Botones oscuros con texto blanco */
    .stButton > button {
        background: linear-gradient(180deg, #17617F, #0E435C) !important;
        color: #FFFFFF !important;
        border: 1px solid #54CDEB !important;
    }

    .stButton > button p,
    .stButton > button span {
        color: #FFFFFF !important;
    }

    .stButton > button:hover {
        background: linear-gradient(180deg, #1D789B, #12536E) !important;
        border-color: #8CEBFF !important;
        color: #FFFFFF !important;
    }

    .stDownloadButton > button {
        background: #17465F !important;
        color: #FFFFFF !important;
        border: 1px solid #65C9EA !important;
    }

    .stDownloadButton > button p,
    .stDownloadButton > button span {
        color: #FFFFFF !important;
    }

    /* Métricas */
    div[data-testid="stMetricDelta"] {
        color: #82E6BE !important;
    }

    /* Contenedores y separadores */
    hr {
        border-color: rgba(190, 220, 236, .18) !important;
    }

    /* Texto dentro de tarjetas claras: mantener oscuro */
    .light-card,
    .light-card *,
    .light-card p,
    .light-card span,
    .light-card strong,
    .light-card b {
        color: #132635 !important;
    }

    /* Tarjetas azules/oscuras: forzar texto claro */
    .blue-card,
    .blue-card *,
    .hero,
    .hero *,
    .dark-card,
    .dark-card *,
    .panel,
    .panel * {
        color: #F5FAFD;
    }

    /* Excepciones para colores semánticos */
    .score { color: #7DD8FF !important; }
    .muted { color: #AFC5D4 !important; }
    .kit-ready { color: #6FE2B8 !important; }
    .kit-prep { color: #FFD47A !important; }
    .kit-block { color: #FF9A9A !important; }

    /* Texto de ayuda debajo de widgets */
    div[data-testid="stWidgetLabel"] p {
        color: #EAF3F8 !important;
    }

    /* Expander */
    details summary,
    details summary span,
    details summary p {
        color: #F0F7FB !important;
    }

    /* Código si aparece */
    code {
        color: #D7F2FF !important;
        background: #102B3D !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# ARCHIVOS
# ============================================================

def localizar(preferido: str, palabras: list[str]):
    ruta = BASE / preferido
    if ruta.exists():
        return ruta
    candidatos = []
    for archivo in BASE.glob("*.xlsx"):
        nombre = archivo.stem.lower()
        if all(p.lower() in nombre for p in palabras):
            candidatos.append(archivo)
    return sorted(candidatos, key=lambda x: x.name)[0] if candidatos else None


ARCHIVO_PEDIDOS = localizar("01_pedidos.xlsx", ["pedidos"])
ARCHIVO_OPERARIAS = localizar("02_operarias.xlsx", ["operarias"])
ARCHIVO_OPERACIONES = localizar("03_operaciones_pedido.xlsx", ["operaciones", "pedido"])
ARCHIVO_TIEMPOS = localizar("04_tiempos.xlsx", ["tiempos"])

faltantes = [
    nombre
    for nombre, ruta in {
        "01_pedidos.xlsx": ARCHIVO_PEDIDOS,
        "02_operarias.xlsx": ARCHIVO_OPERARIAS,
        "03_operaciones_pedido.xlsx": ARCHIVO_OPERACIONES,
        "04_tiempos.xlsx": ARCHIVO_TIEMPOS,
    }.items()
    if ruta is None
]

if faltantes:
    st.error("Faltan archivos en el repositorio: " + ", ".join(faltantes))
    st.stop()


def leer_hoja_excel(archivo, hoja, columnas_clave):
    """
    Lee una hoja aunque tenga un título visual antes de la fila de encabezados.
    Primero intenta encabezado en la fila 1 y, si no encuentra las columnas
    esperadas, intenta la fila 4 (header=3).
    """
    intentos = [0, 3]

    for encabezado in intentos:
        df = pd.read_excel(
            archivo,
            sheet_name=hoja,
            header=encabezado
        )

        if set(columnas_clave).issubset(df.columns):
            return df

    raise ValueError(
        f"No se encontraron las columnas esperadas en la hoja '{hoja}'. "
        f"Columnas requeridas: {columnas_clave}"
    )


@st.cache_data(ttl=60, show_spinner=False)
def cargar_datos():
    pedidos = leer_hoja_excel(
        ARCHIVO_PEDIDOS,
        "Pedidos",
        ["ID_Pedido", "Fecha_Recepcion", "Fecha_Compromiso", "Kit_Liberado"]
    )

    kits = leer_hoja_excel(
        ARCHIVO_PEDIDOS,
        "Kits_SMED",
        ["ID_Pedido", "Estado_Kit", "Checklist_Completo"]
    )

    operarias = leer_hoja_excel(
        ARCHIVO_OPERARIAS,
        "Operarias",
        ["ID_Operaria", "Alias_Anonimo", "Activa", "Capacidad_Neta_Min"]
    )

    habilidades = leer_hoja_excel(
        ARCHIVO_OPERARIAS,
        "Habilidades",
        ["ID_Operaria", "Operacion", "Nivel", "Habilitada_Alta"]
    )

    calendario = leer_hoja_excel(
        ARCHIVO_OPERARIAS,
        "Calendario",
        ["Fecha", "ID_Operaria", "Disponible", "Capacidad_Programable_Min"]
    )

    parametros = leer_hoja_excel(
        ARCHIVO_OPERARIAS,
        "Parametros_C2",
        ["Criterio", "Peso", "Descripcion"]
    )

    operaciones = leer_hoja_excel(
        ARCHIVO_OPERACIONES,
        "Operaciones_Pedido",
        ["ID_Operacion_Pedido", "ID_Pedido", "Operacion", "Estado_Operacion"]
    )

    tiempos = leer_hoja_excel(
        ARCHIVO_TIEMPOS,
        "Tiempos",
        ["ID_Registro", "ID_Pedido", "ID_Operaria", "Tiempo_Real_Min"]
    )

    for col in ["Fecha_Recepcion", "Fecha_Compromiso", "Fecha_Liberacion_Kit"]:
        pedidos[col] = pd.to_datetime(pedidos[col], errors="coerce").dt.normalize()

    for col in ["Fecha_Inicio_Preparacion", "Fecha_Liberacion_Kit"]:
        kits[col] = pd.to_datetime(kits[col], errors="coerce").dt.normalize()

    calendario["Fecha"] = pd.to_datetime(calendario["Fecha"], errors="coerce").dt.normalize()
    tiempos["Fecha"] = pd.to_datetime(tiempos["Fecha"], errors="coerce").dt.normalize()
    operaciones["Fecha_Inicio_Real"] = pd.to_datetime(
        operaciones["Fecha_Inicio_Real"], errors="coerce"
    ).dt.normalize()
    operaciones["Fecha_Fin_Real"] = pd.to_datetime(
        operaciones["Fecha_Fin_Real"], errors="coerce"
    ).dt.normalize()

    # Normalizar el alcance actual del taller:
    # Gala, Novia y Quinceañera.
    if "Tipo_Vestido" in pedidos.columns:
        pedidos["Tipo_Vestido"] = pedidos["Tipo_Vestido"].apply(
            normalizar_tipo_vestido
        )

    if "Tipo_Vestido" in tiempos.columns:
        tiempos["Tipo_Vestido"] = tiempos["Tipo_Vestido"].apply(
            normalizar_tipo_vestido
        )

    return pedidos, kits, operarias, habilidades, calendario, parametros, operaciones, tiempos


P, KITS, W, H, CAL, PAR, O, R = cargar_datos()

# Validación del alcance real del taller: solo tres tipos de vestido.
tipos_detectados = sorted(
    P["Tipo_Vestido"].dropna().astype(str).str.strip().unique().tolist()
)
tipos_no_validos = [t for t in tipos_detectados if t not in TIPOS_VALIDOS]

if tipos_no_validos:
    st.error(
        "Hay categorías no reconocidas en Tipo_Vestido: "
        + ", ".join(tipos_no_validos)
        + ". Revisa el archivo 01_pedidos.xlsx."
    )
    st.stop()

# ============================================================
# UTILIDADES
# ============================================================

def es_si(valor):
    return str(valor).strip().casefold() in {"sí", "si", "true", "1"}


def nombre_operaria(id_operaria):
    fila = W[W["ID_Operaria"] == id_operaria]
    if fila.empty:
        return str(id_operaria)
    alias = fila.iloc[0]["Alias_Anonimo"]
    return str(alias) if pd.notna(alias) else str(id_operaria)


def nivel_complejidad(valor):
    return {"Alta": 3, "Media": 2, "Baja": 1}.get(str(valor), 0)


def fecha_operativa():
    hoy = pd.Timestamp.now(tz="America/Lima").tz_localize(None).normalize()
    fechas = sorted(pd.to_datetime(CAL["Fecha"].dropna()).dt.normalize().unique())
    if not fechas:
        return hoy
    fechas = [pd.Timestamp(x) for x in fechas]
    if hoy < fechas[0]:
        return fechas[0]
    if hoy > fechas[-1]:
        return fechas[-1]
    disponibles = [f for f in fechas if f <= hoy]
    return max(disponibles) if disponibles else fechas[0]


FECHA = fecha_operativa()

# Pesos desde Excel
pesos = {
    str(r["Criterio"]): float(r["Peso"])
    for _, r in PAR.iterrows()
}
P_HAB = pesos.get("Habilidad específica", 0.35)
P_DISP = pesos.get("Disponibilidad", 0.20)
P_BAL = pesos.get("Balance de carga", 0.20)
P_DESEMP = pesos.get("Desempeño histórico", 0.15)
P_COMP = pesos.get("Ajuste a complejidad", 0.10)


def capacidad_operaria(id_operaria, fecha):
    fila = CAL[
        (CAL["ID_Operaria"] == id_operaria)
        & (CAL["Fecha"] == pd.Timestamp(fecha).normalize())
    ]
    if fila.empty or not es_si(fila.iloc[0]["Disponible"]):
        return 0
    return int(fila.iloc[0]["Capacidad_Programable_Min"])


def carga_actual(id_operaria):
    activas = O[
        (O["ID_Operaria_Asignada"] == id_operaria)
        & (O["Estado_Operacion"] == "En proceso")
    ]
    return int(activas["Tiempo_Pendiente_Min"].fillna(0).sum())


def operacion_actual(id_operaria):
    activas = O[
        (O["ID_Operaria_Asignada"] == id_operaria)
        & (O["Estado_Operacion"] == "En proceso")
    ].sort_values(["ID_Pedido", "Secuencia"])
    if activas.empty:
        return "-"
    f = activas.iloc[0]
    return f'{f["Operacion"]} · {f["ID_Pedido"]}'


# Histórico por operación completa
terminadas = O.loc[
    O["Estado_Operacion"] == "Completada",
    ["ID_Operacion_Pedido", "ID_Pedido", "Operacion", "ID_Operaria_Asignada"],
].copy()

HIST = (
    R[R["ID_Operacion_Pedido"].isin(terminadas["ID_Operacion_Pedido"])]
    .groupby(["ID_Operacion_Pedido", "ID_Operaria"], as_index=False)["Tiempo_Real_Min"]
    .sum()
    .merge(terminadas, on="ID_Operacion_Pedido", how="inner")
)
HIST = HIST[HIST["ID_Operaria"] == HIST["ID_Operaria_Asignada"]].copy()
HIST = HIST.merge(
    P[["ID_Pedido", "Tipo_Vestido", "Complejidad"]],
    on="ID_Pedido",
    how="left",
)


def estimar_tiempo(id_operaria, operacion, tipo, complejidad, respaldo):
    filtros = [
        HIST[
            (HIST["ID_Operaria"] == id_operaria)
            & (HIST["Operacion"] == operacion)
            & (HIST["Tipo_Vestido"] == tipo)
            & (HIST["Complejidad"] == complejidad)
        ],
        HIST[
            (HIST["ID_Operaria"] == id_operaria)
            & (HIST["Operacion"] == operacion)
            & (HIST["Complejidad"] == complejidad)
        ],
        HIST[
            (HIST["Operacion"] == operacion)
            & (HIST["Complejidad"] == complejidad)
        ],
        HIST[HIST["Operacion"] == operacion],
    ]
    for df in filtros:
        if len(df) >= 3:
            return max(1, int(round(float(df["Tiempo_Real_Min"].median())))), "Histórico"
    return max(1, int(round(float(respaldo)))), "Estimado"


def operacion_lista(fila, completadas):
    previa = fila["ID_Operacion_Previa"]
    return pd.isna(previa) or previa in completadas


def cola_asignable():
    completadas = set(
        O.loc[O["Estado_Operacion"] == "Completada", "ID_Operacion_Pedido"]
    )

    q = O[O["Estado_Operacion"].isin(["Pendiente", "En proceso"])].copy()
    q = q.merge(
        P[
            [
                "ID_Pedido",
                "Fecha_Compromiso",
                "Tipo_Vestido",
                "Complejidad",
                "Kit_Liberado",
                "Estado_Kit_SMED",
                "Fecha_Liberacion_Kit",
            ]
        ],
        on="ID_Pedido",
        how="left",
    )

    q = q[
        q["Kit_Liberado"].map(es_si)
        & (
            q["Fecha_Liberacion_Kit"].isna()
            | (q["Fecha_Liberacion_Kit"] <= FECHA)
        )
    ].copy()

    q = q[q.apply(lambda r: operacion_lista(r, completadas), axis=1)].copy()
    q["_en_proceso"] = (q["Estado_Operacion"] == "En proceso").astype(int)
    q["_comp"] = q["Complejidad"].map({"Alta": 3, "Media": 2, "Baja": 1}).fillna(0)

    return q.sort_values(
        ["_en_proceso", "Fecha_Compromiso", "_comp", "Secuencia"],
        ascending=[False, True, False, True],
    )


def evaluar_candidatas(tarea):
    pedido = P[P["ID_Pedido"] == tarea["ID_Pedido"]].iloc[0]
    operacion = tarea["Operacion"]
    nivel_req = int(tarea["Nivel_Requerido"])
    filas = []

    for _, op in W[W["Activa"].map(es_si)].iterrows():
        oid = op["ID_Operaria"]
        hab = H[(H["ID_Operaria"] == oid) & (H["Operacion"] == operacion)]
        if hab.empty:
            continue

        nivel = int(hab.iloc[0]["Nivel"])
        if nivel < nivel_req:
            continue
        if pedido["Complejidad"] == "Alta" and not es_si(hab.iloc[0]["Habilitada_Alta"]):
            continue

        cap = capacidad_operaria(oid, FECHA)
        carga = carga_actual(oid)
        libre = max(0, cap - carga)
        if cap <= 0 or libre <= 0:
            continue

        tiempo, fuente = estimar_tiempo(
            oid,
            operacion,
            pedido["Tipo_Vestido"],
            pedido["Complejidad"],
            tarea["Tiempo_Estimado_Min"],
        )

        # 0-100
        s_hab = min(100, nivel / 3 * 100)
        s_disp = min(100, libre / max(cap, 1) * 100)
        s_bal = max(0, 100 - carga / max(cap, 1) * 100)

        comparable = HIST[
            (HIST["Operacion"] == operacion)
            & (HIST["Complejidad"] == pedido["Complejidad"])
        ]["Tiempo_Real_Min"]
        referencia = float(comparable.median()) if len(comparable) >= 3 else float(tarea["Tiempo_Estimado_Min"])
        s_desemp = min(100, referencia / max(tiempo, 1) * 100)
        s_comp = 100

        score = (
            P_HAB * s_hab
            + P_DISP * s_disp
            + P_BAL * s_bal
            + P_DESEMP * s_desemp
            + P_COMP * s_comp
        )

        filas.append(
            {
                "ID_Operaria": oid,
                "Operaria": nombre_operaria(oid),
                "Score": round(score, 1),
                "Nivel": nivel,
                "Disponibilidad_%": round(s_disp, 1),
                "Carga_%": round(100 - s_bal, 1),
                "Desempeño_%": round(s_desemp, 1),
                "Tiempo_Estimado_Min": tiempo,
                "Fuente_Tiempo": fuente,
                "Minutos_Libres": libre,
            }
        )

    ranking = pd.DataFrame(filas)
    if ranking.empty:
        return ranking
    return ranking.sort_values(
        ["Score", "Nivel", "Minutos_Libres", "Tiempo_Estimado_Min"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)


def crear_excel_evaluacion(tarea, ranking, historial):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame([tarea]).to_excel(writer, sheet_name="Operacion_Prioritaria", index=False)
        ranking.to_excel(writer, sheet_name="Ranking_Candidatas", index=False)
        if historial:
            pd.DataFrame(historial).to_excel(writer, sheet_name="Historial", index=False)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# PLAN COMPLETO HEURÍSTICO
# ============================================================

def generar_plan_completo():
    pedidos = P.set_index("ID_Pedido").to_dict("index")
    tareas = O.set_index("ID_Operacion_Pedido").to_dict("index")
    dias = [pd.Timestamp(x) for x in sorted(CAL["Fecha"].dropna().unique())]

    completadas = set(
        O.loc[O["Estado_Operacion"] == "Completada", "ID_Operacion_Pedido"]
    )
    fin_tarea = {x: (dias[0] - pd.Timedelta(days=1), 0) for x in completadas}

    restante = {}
    responsable = {}

    for tid, t in tareas.items():
        pid = t["ID_Pedido"]
        if pid not in pedidos or not es_si(pedidos[pid]["Kit_Liberado"]):
            continue
        if t["Estado_Operacion"] == "Pendiente":
            restante[tid] = None
        elif t["Estado_Operacion"] == "En proceso":
            restante[tid] = max(1, int(t["Tiempo_Pendiente_Min"]))
            if pd.notna(t["ID_Operaria_Asignada"]):
                responsable[tid] = t["ID_Operaria_Asignada"]

    carga_acum = {x: 0 for x in W["ID_Operaria"]}
    plan = []

    for dia in dias:
        capacidad = {
            oid: capacidad_operaria(oid, dia)
            for oid in W["ID_Operaria"]
        }
        cursor = {oid: 0 for oid in W["ID_Operaria"]}

        while True:
            candidatos = []

            for tid in list(restante):
                t = tareas[tid]
                p = pedidos[t["ID_Pedido"]]

                if pd.notna(p.get("Fecha_Liberacion_Kit")) and pd.Timestamp(p["Fecha_Liberacion_Kit"]) > dia:
                    continue

                previa = t["ID_Operacion_Previa"]
                min_habilitado = 0
                if pd.notna(previa):
                    if previa not in fin_tarea:
                        continue
                    fecha_prev, fin_prev = fin_tarea[previa]
                    if fecha_prev > dia:
                        continue
                    if fecha_prev == dia:
                        min_habilitado = fin_prev

                opciones_op = [responsable[tid]] if tid in responsable else list(W[W["Activa"].map(es_si)]["ID_Operaria"])

                for oid in opciones_op:
                    hab = H[(H["ID_Operaria"] == oid) & (H["Operacion"] == t["Operacion"])]
                    if hab.empty or int(hab.iloc[0]["Nivel"]) < int(t["Nivel_Requerido"]):
                        continue
                    if p["Complejidad"] == "Alta" and not es_si(hab.iloc[0]["Habilitada_Alta"]):
                        continue

                    inicio = max(cursor[oid], min_habilitado)
                    if inicio >= capacidad[oid]:
                        continue

                    if restante[tid] is None:
                        dur, _ = estimar_tiempo(
                            oid,
                            t["Operacion"],
                            p["Tipo_Vestido"],
                            p["Complejidad"],
                            t["Tiempo_Estimado_Min"],
                        )
                    else:
                        dur = restante[tid]

                    nivel = int(hab.iloc[0]["Nivel"])
                    prioridad = (
                        0 if tid in responsable else 1,
                        pd.Timestamp(p["Fecha_Compromiso"]),
                        -nivel_complejidad(p["Complejidad"]),
                        -nivel,
                        carga_acum[oid],
                        dur,
                    )
                    candidatos.append((prioridad, tid, oid, inicio, dur))

            if not candidatos:
                break

            _, tid, oid, inicio, dur = min(candidatos, key=lambda x: x[0])
            if tid not in responsable:
                responsable[tid] = oid
                restante[tid] = dur

            disponibles = capacidad[oid] - inicio
            minutos = min(restante[tid], disponibles)
            if minutos <= 0:
                break

            fin = inicio + minutos
            restante[tid] -= minutos
            cursor[oid] = fin
            carga_acum[oid] += minutos

            t = tareas[tid]
            p = pedidos[t["ID_Pedido"]]
            plan.append(
                {
                    "Fecha": dia,
                    "ID_Pedido": t["ID_Pedido"],
                    "Operacion": t["Operacion"],
                    "ID_Operacion_Pedido": tid,
                    "ID_Operaria": oid,
                    "Operaria": nombre_operaria(oid),
                    "Complejidad": p["Complejidad"],
                    "Fecha_Compromiso": p["Fecha_Compromiso"],
                    "Inicio_Minuto_Neto": inicio,
                    "Fin_Minuto_Neto": fin,
                    "Minutos_Asignados": minutos,
                    "Minutos_Pendientes": restante[tid],
                    "Estado_Tramo": "Finaliza" if restante[tid] == 0 else "Continúa siguiente turno",
                }
            )

            if restante[tid] == 0:
                fin_tarea[tid] = (dia, fin)
                del restante[tid]

    plan_df = pd.DataFrame(plan)
    sin_df = pd.DataFrame(
        [
            {
                "ID_Operacion_Pedido": tid,
                "ID_Pedido": tareas[tid]["ID_Pedido"],
                "Operacion": tareas[tid]["Operacion"],
                "Minutos_Pendientes": val if val is not None else tareas[tid]["Tiempo_Estimado_Min"],
                "Motivo": "No finalizada dentro del horizonte de calendario",
            }
            for tid, val in restante.items()
        ]
    )

    if plan_df.empty:
        resumen = pd.DataFrame()
    else:
        resumen = (
            plan_df.groupby(["ID_Operaria", "Operaria"], as_index=False)
            .agg(
                Operaciones_Asignadas=("ID_Operacion_Pedido", "nunique"),
                Pedidos_Atendidos=("ID_Pedido", "nunique"),
                Minutos_Asignados=("Minutos_Asignados", "sum"),
            )
            .sort_values("Minutos_Asignados", ascending=False)
        )

    return plan_df, sin_df, resumen


def exportar_plan(plan, sin_programar, resumen):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        plan.to_excel(writer, sheet_name="Plan_Asignacion", index=False)
        sin_programar.to_excel(writer, sheet_name="Sin_Programar", index=False)
        resumen.to_excel(writer, sheet_name="Resumen_Operarias", index=False)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# SESIÓN
# ============================================================

if "historial" not in st.session_state:
    st.session_state["historial"] = []
if "plan_completo" not in st.session_state:
    st.session_state["plan_completo"] = None

# ============================================================
# CABECERA
# ============================================================

ahora = datetime.now(ZoneInfo("America/Lima"))

st.markdown(
    f"""
    <div class="hero">
        <div style="display:grid;grid-template-columns:1fr auto;align-items:center;gap:20px;">
            <div>
                <div class="hero-title">⚙️ DASHBOARD DE ASIGNACIÓN INTELIGENTE DEL TRABAJO</div>
                <div class="hero-sub">Human-Centered Scheduling · Bellísimas Novias · Corte → Ensamblaje → Acabados y detalles → Planchado</div>
            </div>
            <div style="text-align:right;color:#D9E9F3;font-size:.82rem;font-weight:700;">
                {ahora.strftime('%d/%m/%Y')}<br>{ahora.strftime('%I:%M %p')}
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# KPIs Smart Setup + C2
kits_listos = int((KITS["Estado_Kit"] == "Listo").sum())
kits_preparacion = int((KITS["Estado_Kit"] == "En preparación").sum())
kits_bloqueados = int((KITS["Estado_Kit"] == "Bloqueado").sum())

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Operarias activas", int(W["Activa"].map(es_si).sum()))
k2.metric("Kits listos (SMED)", kits_listos)
k3.metric("Kits en preparación", kits_preparacion)
k4.metric("Kits bloqueados", kits_bloqueados)
k5.metric("Fecha operativa", FECHA.strftime("%d/%m/%Y"))

# Filtros
f1, f2 = st.columns(2)
with f1:
    tipo_sel = st.selectbox(
        "Tipo de vestido",
        ["Todos"] + TIPOS_VALIDOS,
    )
with f2:
    comp_sel = st.selectbox("Complejidad", ["Todas", "Alta", "Media", "Baja"])

cola = cola_asignable()
if tipo_sel != "Todos":
    cola = cola[cola["Tipo_Vestido"] == tipo_sel]
if comp_sel != "Todas":
    cola = cola[cola["Complejidad"] == comp_sel]

# ============================================================
# LAYOUT PRINCIPAL
# ============================================================

izq, centro, der = st.columns([1.05, 1.65, 1.0], gap="medium")

with izq:
    st.markdown('<div class="section-label">Estado general de operarias</div>', unsafe_allow_html=True)

    estado_rows = []
    for _, op in W[W["Activa"].map(es_si)].iterrows():
        oid = op["ID_Operaria"]
        cap = capacidad_operaria(oid, FECHA)
        carga = carga_actual(oid)
        libre = max(0, cap - carga)
        actual = operacion_actual(oid)
        if cap == 0:
            estado = "🔴 No disponible"
        elif actual != "-":
            estado = "🔵 Ocupada"
        else:
            estado = "🟢 Disponible"
        estado_rows.append(
            {
                "Operaria": nombre_operaria(oid),
                "Estado": estado,
                "Operación actual": actual,
                "Min libres": libre,
            }
        )

    estado_df = pd.DataFrame(estado_rows)
    e1, e2 = st.columns(2)
    e1.metric("Disponibles", int((estado_df["Estado"] == "🟢 Disponible").sum()))
    e2.metric("Ocupadas", int((estado_df["Estado"] == "🔵 Ocupada").sum()))
    st.dataframe(
        estado_df,
        use_container_width=True,
        hide_index=True,
        height=560,
    )

with centro:
    if cola.empty:
        st.success("No hay operaciones liberadas y listas para asignar con los filtros actuales.")
        tarea = None
        ranking = pd.DataFrame()
    else:
        tarea = cola.iloc[0].to_dict()
        pedido = P[P["ID_Pedido"] == tarea["ID_Pedido"]].iloc[0]
        ranking = evaluar_candidatas(tarea)

        c1, c2 = st.columns(2, gap="medium")
        with c1:
            st.markdown('<div class="section-label">Operación pendiente más prioritaria</div>', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="light-card">
                    <b>ID:</b> {tarea['ID_Operacion_Pedido']}<br>
                    <b>Pedido:</b> {tarea['ID_Pedido']} · {pedido['Tipo_Vestido']}<br>
                    <b>Operación:</b> {tarea['Operacion']}<br>
                    <b>Complejidad:</b> {pedido['Complejidad']}<br>
                    <b>Fecha compromiso:</b> {pedido['Fecha_Compromiso'].strftime('%d/%m/%Y')}<br><br>
                    <span class="kit-ready">✓ KIT LISTO · SMED</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown('<div class="section-label">Recomendación activa · Sistema C2</div>', unsafe_allow_html=True)
            if ranking.empty:
                st.warning("No hay una candidata compatible y disponible para esta operación.")
            else:
                rec = ranking.iloc[0]
                st.markdown(
                    f"""
                    <div class="blue-card">
                        <div style="font-size:1.05rem;font-weight:900;">{rec['Operaria']}</div>
                        <div class="muted">Nivel {int(rec['Nivel'])}/3 · {int(rec['Minutos_Libres'])} min libres</div>
                        <div style="margin-top:18px;display:flex;justify-content:space-between;align-items:end;">
                            <div class="muted">Tiempo estimado<br><b style="color:white;font-size:.95rem;">{int(rec['Tiempo_Estimado_Min'])} min</b></div>
                            <div style="text-align:right;"><div class="score">{rec['Score']:.0f}%</div><div class="muted">compatibilidad</div></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown('<div class="section-label" style="margin-top:10px;">Detalle de la evaluación</div>', unsafe_allow_html=True)

        if not ranking.empty:
            top3 = ranking.head(3)[
                ["Operaria", "Score", "Nivel", "Disponibilidad_%", "Carga_%", "Desempeño_%", "Tiempo_Estimado_Min"]
            ].copy()
            top3.columns = [
                "Operaria", "Score %", "Habilidad", "Disponibilidad %", "Carga %", "Desempeño %", "Tiempo est. min"
            ]
            st.dataframe(top3, use_container_width=True, hide_index=True)

            # Radar para recomendada
            rec = ranking.iloc[0]
            categorias = ["Habilidad", "Disponibilidad", "Balance", "Desempeño", "Complejidad"]
            valores = [
                min(100, rec["Nivel"] / 3 * 100),
                rec["Disponibilidad_%"],
                max(0, 100 - rec["Carga_%"]),
                rec["Desempeño_%"],
                100,
            ]
            fig_radar = go.Figure()
            fig_radar.add_trace(
                go.Scatterpolar(
                    r=valores + [valores[0]],
                    theta=categorias + [categorias[0]],
                    fill="toself",
                    name=rec["Operaria"],
                )
            )
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#DCECF5",
                margin=dict(l=30, r=30, t=20, b=20),
                showlegend=False,
                height=300,
            )
            st.plotly_chart(fig_radar, use_container_width=True)

            st.caption(
                f"Pesos del score: habilidad {P_HAB:.0%}, disponibilidad {P_DISP:.0%}, "
                f"balance de carga {P_BAL:.0%}, desempeño histórico {P_DESEMP:.0%} y "
                f"ajuste a complejidad {P_COMP:.0%}."
            )

with der:
    st.markdown('<div class="section-label">Operaciones pendientes por asignar</div>', unsafe_allow_html=True)
    if cola.empty:
        st.info("Sin operaciones listas.")
    else:
        qvista = cola.head(8)[
            ["ID_Operacion_Pedido", "Operacion", "ID_Pedido", "Complejidad", "Fecha_Compromiso"]
        ].copy()
        qvista["Fecha_Compromiso"] = qvista["Fecha_Compromiso"].dt.strftime("%d/%m")
        qvista.columns = ["ID", "Operación", "Pedido", "Prioridad", "Vence"]
        st.dataframe(qvista, use_container_width=True, hide_index=True, height=300)

    st.markdown('<div class="section-label" style="margin-top:10px;">Kits SMED</div>', unsafe_allow_html=True)
    km1, km2, km3 = st.columns(3)
    km1.metric("Listos", kits_listos)
    km2.metric("Preparación", kits_preparacion)
    km3.metric("Bloqueados", kits_bloqueados)

    kits_pend = KITS[KITS["Estado_Kit"] != "Listo"][
        ["ID_Pedido", "Estado_Kit", "Checklist_Completo", "Incidencia_SMED"]
    ].head(6)
    st.dataframe(kits_pend, use_container_width=True, hide_index=True, height=225)

    st.markdown('<div class="section-label" style="margin-top:10px;">Acciones</div>', unsafe_allow_html=True)

    if tarea is not None and not ranking.empty:
        opciones = ranking.head(5)["Operaria"].tolist()
        seleccion = st.selectbox("Operaria a confirmar", opciones, index=0)

        if st.button("✓ Confirmar asignación", use_container_width=True, type="primary"):
            rr = ranking[ranking["Operaria"] == seleccion].iloc[0]
            st.session_state["historial"].append(
                {
                    "Fecha_Confirmacion": ahora.strftime("%Y-%m-%d %H:%M:%S"),
                    "ID_Operacion_Pedido": tarea["ID_Operacion_Pedido"],
                    "ID_Pedido": tarea["ID_Pedido"],
                    "Operacion": tarea["Operacion"],
                    "Operaria": seleccion,
                    "ID_Operaria": rr["ID_Operaria"],
                    "Score": rr["Score"],
                    "Estado": "Confirmada por supervisor",
                }
            )
            st.success(f"Asignación confirmada: {seleccion} → {tarea['Operacion']}")

        if st.button("↻ Recalcular recomendación", use_container_width=True):
            st.rerun()

        evaluacion = crear_excel_evaluacion(tarea, ranking, st.session_state["historial"])
        st.download_button(
            "⬇ Descargar evaluación",
            data=evaluacion,
            file_name="evaluacion_asignacion_C2.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

# ============================================================
# PESTAÑAS DE SOPORTE
# ============================================================

st.markdown("### Vista operativa complementaria")
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Plan completo C2", "Carga de operarias", "Matriz de habilidades", "Smart Setup", "Historial"]
)

with tab1:
    st.write(
        "Genera una programación heurística para todas las operaciones liberadas por Smart Setup, "
        "respetando secuencia, habilidades, calendario, capacidad y continuidad entre turnos."
    )
    if st.button("▶ Generar plan completo", key="plan_completo_btn"):
        st.session_state["plan_completo"] = generar_plan_completo()

    if st.session_state["plan_completo"] is not None:
        plan_df, sin_df, resumen_df = st.session_state["plan_completo"]
        p1, p2, p3 = st.columns(3)
        p1.metric("Operaciones programadas", int(plan_df["ID_Operacion_Pedido"].nunique()) if not plan_df.empty else 0)
        p2.metric("Pedidos programados", int(plan_df["ID_Pedido"].nunique()) if not plan_df.empty else 0)
        p3.metric("Sin finalizar", len(sin_df))
        st.dataframe(plan_df, use_container_width=True, hide_index=True, height=420)
        if not resumen_df.empty:
            fig = px.bar(
                resumen_df,
                x="Operaria",
                y="Minutos_Asignados",
                hover_data=["Operaciones_Asignadas", "Pedidos_Atendidos"],
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#E3F0F7",
                xaxis_title="",
                yaxis_title="Minutos asignados",
            )
            st.plotly_chart(fig, use_container_width=True)
        archivo_plan = exportar_plan(plan_df, sin_df, resumen_df)
        st.download_button(
            "⬇ Descargar resultado_asignacion_C2.xlsx",
            data=archivo_plan,
            file_name="resultado_asignacion_C2.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

with tab2:
    carga_rows = []
    for _, op in W[W["Activa"].map(es_si)].iterrows():
        oid = op["ID_Operaria"]
        cap = capacidad_operaria(oid, FECHA)
        carga = carga_actual(oid)
        carga_rows.append(
            {
                "Operaria": nombre_operaria(oid),
                "Capacidad_Min": cap,
                "Carga_Pendiente_Min": carga,
                "Utilizacion_%": round(100 * carga / cap, 1) if cap else 0,
            }
        )
    cdf = pd.DataFrame(carga_rows)
    fig = px.bar(cdf, x="Operaria", y="Utilizacion_%", text="Utilizacion_%")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E3F0F7",
        yaxis_range=[0, 100],
        xaxis_title="",
        yaxis_title="Utilización (%)",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(cdf, use_container_width=True, hide_index=True)

with tab3:
    matriz = H.pivot(index="ID_Operaria", columns="Operacion", values="Nivel")
    matriz.index = [nombre_operaria(x) for x in matriz.index]
    st.dataframe(matriz, use_container_width=True)

with tab4:
    s1, s2 = st.columns([1.0, 1.3])
    with s1:
        estado_kit = KITS["Estado_Kit"].value_counts().rename_axis("Estado").reset_index(name="Pedidos")
        figk = px.pie(estado_kit, names="Estado", values="Pedidos", hole=.48)
        figk.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#E3F0F7",
            margin=dict(l=10, r=10, t=15, b=10),
        )
        st.plotly_chart(figk, use_container_width=True)
    with s2:
        st.dataframe(
            KITS[
                [
                    "ID_Pedido", "Estado_Kit", "Checklist_Completo", "Tiempo_Setup_Min",
                    "Incidencia_SMED", "Fecha_Liberacion_Kit"
                ]
            ].sort_values(["Estado_Kit", "ID_Pedido"]),
            use_container_width=True,
            hide_index=True,
            height=390,
        )

with tab5:
    if st.session_state["historial"]:
        st.dataframe(pd.DataFrame(st.session_state["historial"]), use_container_width=True, hide_index=True)
    else:
        st.info("Aún no se han confirmado asignaciones durante esta sesión.")

st.caption(
    "El C2 solo evalúa operaciones pertenecientes a pedidos con kit liberado por Smart Setup. "
    "La recomendación del sistema requiere validación del supervisor. El plan completo es una heurística de prototipo, no una optimización matemática global."
)

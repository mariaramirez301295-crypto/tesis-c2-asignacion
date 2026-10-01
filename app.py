
from pathlib import Path
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo
import math

import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Dashboard C2 - Asignación Inteligente",
    page_icon="🧵",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE = Path(__file__).resolve().parent

ETAPAS = [
    "Corte",
    "Ensamblaje",
    "Acabados y detalles",
    "Planchado",
]

PESO_HABILIDAD = 0.35
PESO_DISPONIBILIDAD = 0.20
PESO_BALANCE_CARGA = 0.20
PESO_DESEMPENO = 0.15
PESO_COMPLEJIDAD = 0.10

# ============================================================
# ESTILOS
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 55% 15%, rgba(36, 91, 130, 0.22), transparent 28%),
            linear-gradient(145deg, #071521 0%, #0b1e2d 42%, #10283a 100%);
        color: #F5F8FC;
    }

    header[data-testid="stHeader"] {
        background: rgba(7, 21, 33, 0.88);
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    .block-container {
        max-width: 1550px;
        padding-top: 1.15rem;
        padding-bottom: 2rem;
        padding-left: 1.3rem;
        padding-right: 1.3rem;
    }

    h1, h2, h3 {
        color: #F8FBFF !important;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, rgba(21, 55, 78, 0.98), rgba(12, 36, 54, 0.98));
        border: 1px solid rgba(102, 178, 218, 0.22);
        border-radius: 15px;
        padding: 0.8rem 0.9rem;
        box-shadow: 0 10px 26px rgba(0,0,0,.20);
    }

    div[data-testid="stMetricLabel"] p {
        color: #AFC8D9 !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
    }

    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: 800 !important;
    }

    .hero {
        background: linear-gradient(110deg, rgba(9, 36, 55, .98), rgba(17, 64, 92, .93));
        border: 1px solid rgba(101, 185, 226, .28);
        border-radius: 18px;
        padding: 16px 20px;
        box-shadow: 0 12px 34px rgba(0,0,0,.24);
        margin-bottom: 12px;
    }

    .hero-title {
        font-size: 1.38rem;
        font-weight: 900;
        letter-spacing: .2px;
        margin: 0;
        color: #FFFFFF;
    }

    .hero-sub {
        color: #AEC3D2;
        margin-top: 2px;
        font-size: .88rem;
    }

    .hero-time {
        text-align: right;
        color: #D6E6F2;
        font-size: .82rem;
        font-weight: 600;
    }

    .panel {
        background: linear-gradient(180deg, rgba(24, 59, 82, .95), rgba(12, 36, 53, .96));
        border: 1px solid rgba(111, 186, 224, .22);
        border-radius: 16px;
        padding: 14px 15px;
        box-shadow: 0 12px 32px rgba(0,0,0,.20);
        margin-bottom: 12px;
    }

    .panel-light {
        background: linear-gradient(180deg, #EAF1F5 0%, #D9E5EC 100%);
        border: 1px solid #BFD0DA;
        border-radius: 16px;
        padding: 15px 16px;
        color: #102231;
        box-shadow: 0 10px 28px rgba(0,0,0,.18);
        margin-bottom: 12px;
    }

    .panel-title {
        font-size: .92rem;
        font-weight: 900;
        color: #FFFFFF;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: .3px;
    }

    .panel-title-dark {
        font-size: .92rem;
        font-weight: 900;
        color: #122738;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: .3px;
    }

    .operator-row {
        display: grid;
        grid-template-columns: 34px 1fr 92px;
        gap: 8px;
        align-items: center;
        padding: 8px 8px;
        margin-bottom: 6px;
        background: rgba(255,255,255,.035);
        border-radius: 11px;
        border: 1px solid rgba(255,255,255,.05);
    }

    .avatar {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display:flex;
        align-items:center;
        justify-content:center;
        background: linear-gradient(135deg,#4B9CC7,#1C5477);
        color: white;
        font-weight: 900;
        font-size: .72rem;
        border: 1px solid rgba(255,255,255,.25);
    }

    .op-name {
        color: #F3F8FC;
        font-weight: 800;
        font-size: .82rem;
    }

    .op-detail {
        color: #9FB7C8;
        font-size: .70rem;
        line-height: 1.25;
    }

    .badge {
        display: inline-flex;
        align-items:center;
        border-radius: 999px;
        padding: 4px 8px;
        font-size: .66rem;
        font-weight: 900;
        letter-spacing: .15px;
    }

    .badge-green {
        background: rgba(65, 210, 157, .15);
        color: #6CE4B9;
        border: 1px solid rgba(108, 228, 185, .35);
    }

    .badge-blue {
        background: rgba(68, 160, 220, .16);
        color: #7CC9F2;
        border: 1px solid rgba(124, 201, 242, .30);
    }

    .badge-red {
        background: rgba(255, 111, 111, .16);
        color: #FF9D9D;
        border: 1px solid rgba(255, 157, 157, .30);
    }

    .badge-yellow {
        background: rgba(246, 193, 87, .16);
        color: #FFD47B;
        border: 1px solid rgba(255, 212, 123, .30);
    }

    .priority-box {
        background: #EFF4F7;
        color: #132533;
        border-radius: 13px;
        padding: 12px 13px;
        min-height: 150px;
        border: 1px solid #CAD8E0;
    }

    .recommend-box {
        background: linear-gradient(145deg,#244E69,#17394F);
        color: white;
        border-radius: 13px;
        padding: 13px;
        min-height: 150px;
        border: 1px solid rgba(131, 208, 245, .25);
    }

    .score {
        font-size: 2.1rem;
        font-weight: 900;
        color: #7DD3FC;
        line-height: 1;
    }

    .score-label {
        color: #B8D2E1;
        font-size: .72rem;
    }

    .candidate {
        display:grid;
        grid-template-columns: 34px 1.35fr .75fr .7fr .7fr .7fr;
        gap:8px;
        align-items:center;
        padding: 8px 7px;
        border-bottom: 1px solid rgba(255,255,255,.07);
        font-size:.74rem;
    }

    .candidate-head {
        color:#9DB6C7;
        font-size:.66rem;
        font-weight:800;
        text-transform:uppercase;
    }

    .criteria-grid {
        display:grid;
        grid-template-columns: repeat(2, 1fr);
        gap:10px;
    }

    .criterion {
        background:rgba(255,255,255,.04);
        border:1px solid rgba(255,255,255,.06);
        padding:10px;
        border-radius:12px;
        text-align:center;
    }

    .criterion strong {
        display:block;
        font-size:.76rem;
        color:#EAF5FB;
    }

    .criterion span {
        font-size:.65rem;
        color:#9FB8C9;
    }

    .pending-item {
        background:rgba(255,255,255,.035);
        border:1px solid rgba(255,255,255,.06);
        border-radius:11px;
        padding:9px 10px;
        margin-bottom:7px;
    }

    .pending-id {
        color:#F7FBFE;
        font-weight:900;
        font-size:.77rem;
    }

    .pending-desc {
        color:#A8BFCE;
        font-size:.69rem;
    }

    .stButton > button {
        border-radius: 10px;
        border: 1px solid #40D9F2;
        background: linear-gradient(180deg,#155B78,#0D3E57);
        color:#FFFFFF;
        font-weight:800;
        min-height:42px;
    }

    .stButton > button:hover {
        border-color:#89EAFA;
        color:#FFFFFF;
        background:linear-gradient(180deg,#197196,#0E4B68);
    }

    .stDownloadButton > button {
        border-radius:10px;
        border:1px solid rgba(126, 208, 244, .5);
        background:#153F58;
        color:white;
        font-weight:800;
    }

    div[data-testid="stDataFrame"] {
        border-radius:12px;
        overflow:hidden;
    }

    .small-note {
        color:#90AABD;
        font-size:.68rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# CARGA DE ARCHIVOS
# ============================================================

def localizar(preferido, palabras):
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
ARCHIVO_OPERACIONES = localizar(
    "03_operaciones_pedido.xlsx",
    ["operaciones", "pedido"],
)
ARCHIVO_TIEMPOS = localizar("04_tiempos.xlsx", ["tiempos"])

faltantes = [
    n for n, a in {
        "01_pedidos.xlsx": ARCHIVO_PEDIDOS,
        "02_operarias.xlsx": ARCHIVO_OPERARIAS,
        "03_operaciones_pedido.xlsx": ARCHIVO_OPERACIONES,
        "04_tiempos.xlsx": ARCHIVO_TIEMPOS,
    }.items()
    if a is None
]

if faltantes:
    st.error("Faltan archivos en el repositorio: " + ", ".join(faltantes))
    st.stop()


@st.cache_data
def cargar_datos():
    pedidos = pd.read_excel(ARCHIVO_PEDIDOS, sheet_name="Pedidos")
    operarias = pd.read_excel(ARCHIVO_OPERARIAS, sheet_name="Operarias")
    habilidades = pd.read_excel(ARCHIVO_OPERARIAS, sheet_name="Habilidades")
    calendario = pd.read_excel(ARCHIVO_OPERARIAS, sheet_name="Calendario")
    operaciones = pd.read_excel(
        ARCHIVO_OPERACIONES,
        sheet_name="Operaciones_Pedido",
    )
    tiempos = pd.read_excel(ARCHIVO_TIEMPOS, sheet_name="Tiempos")

    pedidos["Fecha_Recepcion"] = pd.to_datetime(
        pedidos["Fecha_Recepcion"], errors="coerce"
    )
    pedidos["Fecha_Compromiso"] = pd.to_datetime(
        pedidos["Fecha_Compromiso"], errors="coerce"
    )
    pedidos["Fecha_Liberacion_Kit"] = pd.to_datetime(
        pedidos["Fecha_Liberacion_Kit"], errors="coerce"
    )

    calendario["Fecha"] = pd.to_datetime(calendario["Fecha"], errors="coerce")
    tiempos["Fecha"] = pd.to_datetime(tiempos["Fecha"], errors="coerce")
    operaciones["Fecha_Inicio_Real"] = pd.to_datetime(
        operaciones["Fecha_Inicio_Real"], errors="coerce"
    )
    operaciones["Fecha_Fin_Real"] = pd.to_datetime(
        operaciones["Fecha_Fin_Real"], errors="coerce"
    )

    return pedidos, operarias, habilidades, calendario, operaciones, tiempos


P, W, H, CAL, O, R = cargar_datos()

# ============================================================
# FUNCIONES
# ============================================================

def es_si(valor):
    return str(valor).strip().casefold() in {"sí", "si", "true", "1"}


def nombre_operaria(id_operaria):
    fila = W[W["ID_Operaria"] == id_operaria]
    if fila.empty:
        return id_operaria
    alias = fila.iloc[0].get("Alias_Anonimo", "")
    return alias if pd.notna(alias) and str(alias).strip() else id_operaria


def iniciales(texto):
    partes = [p for p in str(texto).split() if p]
    if not partes:
        return "OP"
    return "".join(p[0].upper() for p in partes[:2])


def nivel_complejidad(valor):
    return {"Alta": 3, "Media": 2, "Baja": 1}.get(str(valor), 0)


def badge_complejidad(valor):
    cls = {
        "Alta": "badge-red",
        "Media": "badge-yellow",
        "Baja": "badge-green",
    }.get(str(valor), "badge-blue")
    return f'<span class="badge {cls}">{valor}</span>'


def minutos_a_horas(minutos):
    minutos = int(round(float(minutos)))
    h = minutos // 60
    m = minutos % 60
    return f"{h} h {m:02d} min"


def base_historica():
    terminadas = O.loc[
        O["Estado_Operacion"].eq("Completada"),
        [
            "ID_Operacion_Pedido",
            "ID_Pedido",
            "Operacion",
            "ID_Operaria_Asignada",
        ],
    ].copy()

    acumulado = (
        R[R["ID_Operacion_Pedido"].isin(terminadas["ID_Operacion_Pedido"])]
        .groupby(["ID_Operacion_Pedido", "ID_Operaria"], as_index=False)[
            "Tiempo_Real_Min"
        ]
        .sum()
    )

    acumulado = acumulado.merge(
        terminadas,
        on="ID_Operacion_Pedido",
        how="inner",
        validate="many_to_one",
    )

    acumulado = acumulado[
        acumulado["ID_Operaria"].eq(acumulado["ID_Operaria_Asignada"])
    ].copy()

    acumulado = acumulado.merge(
        P[["ID_Pedido", "Tipo_Vestido", "Complejidad"]],
        on="ID_Pedido",
        how="left",
        validate="many_to_one",
    )

    return acumulado


HIST = base_historica()


def tiempo_historico_estimado(id_operaria, operacion, tipo, complejidad):
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
            return float(df["Tiempo_Real_Min"].median())

    return None


def fecha_dashboard():
    fechas = CAL["Fecha"].dropna().sort_values().unique()
    if len(fechas) == 0:
        return pd.Timestamp.today().normalize()
    return pd.Timestamp(fechas[0]).normalize()


def carga_operaria_en_fecha(id_operaria, fecha):
    en_proceso = O[
        (O["ID_Operaria_Asignada"] == id_operaria)
        & (O["Estado_Operacion"] == "En proceso")
    ]
    return float(en_proceso["Tiempo_Pendiente_Min"].fillna(0).sum())


def capacidad_fecha(id_operaria, fecha):
    fila = CAL[
        (CAL["ID_Operaria"] == id_operaria)
        & (CAL["Fecha"].dt.normalize() == fecha.normalize())
    ]
    if fila.empty:
        return 0
    if not es_si(fila.iloc[0]["Disponible"]):
        return 0
    return int(fila.iloc[0]["Capacidad_Programable_Min"])


def operacion_actual(id_operaria):
    fila = O[
        (O["ID_Operaria_Asignada"] == id_operaria)
        & (O["Estado_Operacion"] == "En proceso")
    ].sort_values(["ID_Pedido", "Secuencia"])
    if fila.empty:
        return "-"
    f = fila.iloc[0]
    return f'{f["Operacion"]} · {f["ID_Pedido"]}'


def operaciones_ready():
    completadas = set(
        O.loc[O["Estado_Operacion"] == "Completada", "ID_Operacion_Pedido"]
    )

    candidatas = O[
        O["Estado_Operacion"].isin(["Pendiente", "En proceso"])
    ].copy()

    candidatas = candidatas.merge(
        P[
            [
                "ID_Pedido",
                "Fecha_Compromiso",
                "Tipo_Vestido",
                "Complejidad",
                "Kit_Liberado",
            ]
        ],
        on="ID_Pedido",
        how="left",
        validate="many_to_one",
    )

    candidatas = candidatas[
        candidatas["Kit_Liberado"].astype(str).str.casefold().isin(
            ["sí", "si", "true", "1"]
        )
    ].copy()

    def lista(fila):
        previa = fila["ID_Operacion_Previa"]
        return pd.isna(previa) or previa in completadas

    candidatas = candidatas[candidatas.apply(lista, axis=1)].copy()

    candidatas["_comp"] = candidatas["Complejidad"].map(
        {"Alta": 3, "Media": 2, "Baja": 1}
    ).fillna(0)

    candidatas = candidatas.sort_values(
        ["Fecha_Compromiso", "_comp", "Secuencia"],
        ascending=[True, False, True],
    )

    return candidatas


def evaluar_candidatas(tarea, fecha):
    pedido = P[P["ID_Pedido"] == tarea["ID_Pedido"]].iloc[0]
    operacion = tarea["Operacion"]
    nivel_req = int(tarea["Nivel_Requerido"])
    filas = []

    # carga relativa global para balance
    cargas = {
        op: carga_operaria_en_fecha(op, fecha)
        for op in W["ID_Operaria"]
    }

    for _, op in W.iterrows():
        id_op = op["ID_Operaria"]

        if not es_si(op["Disponible_Corte"]):
            continue

        hab = H[
            (H["ID_Operaria"] == id_op)
            & (H["Operacion"] == operacion)
        ]

        if hab.empty:
            continue

        nivel = int(hab.iloc[0]["Nivel"])

        if nivel < nivel_req:
            continue

        if pedido["Complejidad"] == "Alta" and not es_si(
            hab.iloc[0]["Habilitada_Alta"]
        ):
            continue

        capacidad = capacidad_fecha(id_op, fecha)
        carga = cargas[id_op]
        disponible = max(0, capacidad - carga)

        if capacidad <= 0 or disponible <= 0:
            continue

        habilidad = min(100, nivel / 3 * 100)
        disponibilidad = min(100, disponible / max(capacidad, 1) * 100)
        balance = max(0, 100 - (carga / max(capacidad, 1) * 100))

        tiempo = tiempo_historico_estimado(
            id_op,
            operacion,
            pedido["Tipo_Vestido"],
            pedido["Complejidad"],
        )

        if tiempo is None:
            tiempo = float(tarea["Tiempo_Estimado_Min"])
            fuente = "Tiempo estimado"
        else:
            fuente = "Histórico"

        comparables = []
        for id_aux in W["ID_Operaria"]:
            aux = tiempo_historico_estimado(
                id_aux,
                operacion,
                pedido["Tipo_Vestido"],
                pedido["Complejidad"],
            )
            if aux is not None and aux > 0:
                comparables.append(aux)

        if comparables and tiempo > 0:
            mejor = min(comparables)
            desempeno = min(100, mejor / tiempo * 100)
        else:
            desempeno = 75

        ajuste_complejidad = 100 if (
            pedido["Complejidad"] != "Alta"
            or es_si(hab.iloc[0]["Habilitada_Alta"])
        ) else 0

        score = (
            PESO_HABILIDAD * habilidad
            + PESO_DISPONIBILIDAD * disponibilidad
            + PESO_BALANCE_CARGA * balance
            + PESO_DESEMPENO * desempeno
            + PESO_COMPLEJIDAD * ajuste_complejidad
        )

        filas.append(
            {
                "ID_Operaria": id_op,
                "Operaria": nombre_operaria(id_op),
                "Nivel": nivel,
                "Capacidad": capacidad,
                "Carga": carga,
                "Disponible_Min": disponible,
                "Disponibilidad_%": round(disponibilidad, 1),
                "Balance_%": round(balance, 1),
                "Desempeño_%": round(desempeno, 1),
                "Complejidad_%": round(ajuste_complejidad, 1),
                "Tiempo_Estimado_Min": int(round(tiempo)),
                "Fuente_Tiempo": fuente,
                "Score": round(score, 1),
            }
        )

    ranking = pd.DataFrame(filas)

    if not ranking.empty:
        ranking = ranking.sort_values(
            ["Score", "Disponible_Min", "Nivel"],
            ascending=[False, False, False],
        ).reset_index(drop=True)

    return ranking


def exportar_recomendacion(tarea, ranking):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame([tarea]).to_excel(
            writer,
            sheet_name="Operacion_Prioritaria",
            index=False,
        )
        ranking.to_excel(
            writer,
            sheet_name="Ranking_Candidatas",
            index=False,
        )

        if "historial_confirmaciones" in st.session_state:
            pd.DataFrame(
                st.session_state["historial_confirmaciones"]
            ).to_excel(
                writer,
                sheet_name="Historial_Confirmaciones",
                index=False,
            )

    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# ESTADO DE LA APP
# ============================================================

if "historial_confirmaciones" not in st.session_state:
    st.session_state["historial_confirmaciones"] = []

if "ultima_confirmacion" not in st.session_state:
    st.session_state["ultima_confirmacion"] = None

fecha_base = fecha_dashboard()
pendientes = operaciones_ready()

# ============================================================
# ENCABEZADO
# ============================================================

ahora = datetime.now(ZoneInfo("America/Lima"))

st.markdown(
    f"""
    <div class="hero">
        <div style="display:grid;grid-template-columns:1fr auto;align-items:center;gap:20px;">
            <div>
                <div class="hero-title">⚙️ DASHBOARD DE ASIGNACIÓN INTELIGENTE DEL TRABAJO</div>
                <div class="hero-sub">Human-Centered Scheduling · Confección personalizada · 4 etapas</div>
            </div>
            <div class="hero-time">
                {ahora.strftime("%A, %d/%m/%Y")}<br>
                {ahora.strftime("%I:%M %p")}
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Filtros de cabecera
f1, f2, f3 = st.columns([1.2, 1.2, 2.6])

with f1:
    tipo_filtro = st.selectbox(
        "Tipo de vestido",
        ["Todos"] + sorted(P["Tipo_Vestido"].dropna().unique().tolist()),
    )

with f2:
    complejidad_filtro = st.selectbox(
        "Complejidad",
        ["Todas"] + ["Alta", "Media", "Baja"],
    )

with f3:
    st.markdown(
        '<div class="small-note" style="padding-top:30px;">'
        "La recomendación es una propuesta del sistema y debe ser validada por el supervisor."
        "</div>",
        unsafe_allow_html=True,
    )

pendientes_vista = pendientes.copy()

if tipo_filtro != "Todos":
    pendientes_vista = pendientes_vista[
        pendientes_vista["Tipo_Vestido"] == tipo_filtro
    ]

if complejidad_filtro != "Todas":
    pendientes_vista = pendientes_vista[
        pendientes_vista["Complejidad"] == complejidad_filtro
    ]

# ============================================================
# LAYOUT PRINCIPAL
# ============================================================

izq, centro, der = st.columns([1.05, 1.85, 0.95], gap="medium")

# ------------------------------------------------------------
# PANEL IZQUIERDO - ESTADO OPERARIAS
# ------------------------------------------------------------

with izq:
    disponibles = 0
    ocupadas = 0

    filas_html = ""

    for _, op in W.iterrows():
        id_op = op["ID_Operaria"]
        cap = capacidad_fecha(id_op, fecha_base)
        carga = carga_operaria_en_fecha(id_op, fecha_base)
        libre = max(0, cap - carga)

        if cap > 0 and libre > 0:
            estado = "DISPONIBLE"
            cls = "badge-green"
            disponibles += 1
        else:
            estado = "OCUPADA"
            cls = "badge-blue"
            ocupadas += 1

        nombre = nombre_operaria(id_op)
        actual = operacion_actual(id_op)

        filas_html += f"""
        <div class="operator-row">
            <div class="avatar">{iniciales(nombre)}</div>
            <div>
                <div class="op-name">{nombre}</div>
                <div class="op-detail">{actual}<br>{libre:.0f} min libres</div>
            </div>
            <div style="text-align:right;">
                <span class="badge {cls}">{estado}</span>
            </div>
        </div>
        """

    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">Estado general de operarias</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px;">
                <div class="criterion">
                    <strong style="font-size:1.5rem;color:#67E3B4;">{disponibles}</strong>
                    <span>Disponibles</span>
                </div>
                <div class="criterion">
                    <strong style="font-size:1.5rem;color:#7CC9F2;">{ocupadas}</strong>
                    <span>Ocupadas</span>
                </div>
            </div>
            {filas_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------
# CENTRO - RECOMENDACIÓN Y RANKING
# ------------------------------------------------------------

with centro:
    if pendientes_vista.empty:
        st.success("No hay operaciones listas para asignar con los filtros seleccionados.")
        tarea = None
        ranking = pd.DataFrame()
    else:
        tarea = pendientes_vista.iloc[0].to_dict()
        ranking = evaluar_candidatas(tarea, fecha_base)

        pedido = P[P["ID_Pedido"] == tarea["ID_Pedido"]].iloc[0]

        if ranking.empty:
            recomendada = None
            score = 0
        else:
            recomendada = ranking.iloc[0]
            score = recomendada["Score"]

        c1, c2 = st.columns([1.1, 1.0], gap="medium")

        with c1:
            st.markdown(
                f"""
                <div class="panel-light">
                    <div class="panel-title-dark">Operación pendiente más prioritaria</div>
                    <div style="font-size:.78rem;line-height:1.65;">
                        <b>ID:</b> {tarea["ID_Operacion_Pedido"]}<br>
                        <b>Pedido:</b> {tarea["ID_Pedido"]} · {pedido["Tipo_Vestido"]}<br>
                        <b>Operación:</b> {tarea["Operacion"]}<br>
                        <b>Complejidad:</b> {badge_complejidad(pedido["Complejidad"])}<br>
                        <b>Fecha compromiso:</b> {pedido["Fecha_Compromiso"].strftime("%d/%m/%Y")}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            if recomendada is not None:
                st.markdown(
                    f"""
                    <div class="recommend-box">
                        <div class="panel-title">Recomendación activa · Sistema C2</div>
                        <div style="display:grid;grid-template-columns:46px 1fr auto;gap:10px;align-items:center;">
                            <div class="avatar" style="width:44px;height:44px;font-size:.9rem;">
                                {iniciales(recomendada["Operaria"])}
                            </div>
                            <div>
                                <div style="font-size:1.05rem;font-weight:900;">{recomendada["Operaria"]}</div>
                                <div class="op-detail">Nivel {int(recomendada["Nivel"])}/3 · {int(recomendada["Disponible_Min"])} min disponibles</div>
                            </div>
                            <div style="text-align:right;">
                                <div class="score">{score:.0f}%</div>
                                <div class="score-label">compatibilidad</div>
                            </div>
                        </div>
                        <div style="margin-top:10px;color:#C7DCE8;font-size:.72rem;">
                            Razones: habilidad compatible · disponibilidad suficiente ·
                            balance de carga · desempeño histórico · ajuste a complejidad.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.warning("No existe una operaria compatible y disponible para esta operación.")

        st.markdown(
            '<div class="panel"><div class="panel-title">Detalle de la evaluación</div>',
            unsafe_allow_html=True,
        )

        if not ranking.empty:
            top = ranking.head(3).copy()

            encabezado = """
            <div class="candidate candidate-head">
                <div></div><div>Operaria</div><div>Score</div><div>Habilidad</div><div>Disponible</div><div>Carga</div>
            </div>
            """

            filas = ""
            for _, r in top.iterrows():
                carga_pct = 100 - r["Balance_%"]
                filas += f"""
                <div class="candidate">
                    <div class="avatar">{iniciales(r["Operaria"])}</div>
                    <div><b>{r["Operaria"]}</b><br><span class="op-detail">{r["Tiempo_Estimado_Min"]} min est.</span></div>
                    <div><b>{r["Score"]:.0f}%</b></div>
                    <div>{int(r["Nivel"])}/3</div>
                    <div>{r["Disponibilidad_%"]:.0f}%</div>
                    <div>{carga_pct:.0f}%</div>
                </div>
                """

            st.markdown(
                f"""
                <div style="display:grid;grid-template-columns:1.55fr .95fr;gap:12px;">
                    <div>
                        <div style="font-size:.75rem;font-weight:900;margin-bottom:5px;">RANKING DE CANDIDATAS (Top 3)</div>
                        {encabezado}
                        {filas}
                    </div>
                    <div>
                        <div style="font-size:.75rem;font-weight:900;margin-bottom:8px;">CRITERIOS DE SELECCIÓN</div>
                        <div class="criteria-grid">
                            <div class="criterion"><strong>35%</strong><span>Habilidad específica</span></div>
                            <div class="criterion"><strong>20%</strong><span>Disponibilidad</span></div>
                            <div class="criterion"><strong>20%</strong><span>Balance de carga</span></div>
                            <div class="criterion"><strong>15%</strong><span>Desempeño histórico</span></div>
                            <div class="criterion" style="grid-column:1/3;"><strong>10%</strong><span>Ajuste a complejidad</span></div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("No hay candidatas que cumplan las restricciones para la operación prioritaria.")

        st.markdown("</div>", unsafe_allow_html=True)

        # KPIs
        if not ranking.empty:
            utilizacion_prom = (
                100
                * sum(carga_operaria_en_fecha(op, fecha_base) for op in W["ID_Operaria"])
                / max(
                    1,
                    sum(capacidad_fecha(op, fecha_base) for op in W["ID_Operaria"]),
                )
            )
            mejor_tiempo = ranking.iloc[0]["Tiempo_Estimado_Min"]
            mediana_tiempo = ranking["Tiempo_Estimado_Min"].median()
            mejora_tiempo = (
                max(0, (mediana_tiempo - mejor_tiempo) / mediana_tiempo * 100)
                if mediana_tiempo > 0
                else 0
            )

            k1, k2 = st.columns(2)
            k1.metric("Utilización actual", f"{utilizacion_prom:.1f}%")
            k2.metric("Ventaja estimada de tiempo", f"{mejora_tiempo:.1f}%")

# ------------------------------------------------------------
# PANEL DERECHO - PENDIENTES + ACCIONES
# ------------------------------------------------------------

with der:
    cards = ""

    for _, r in pendientes_vista.head(6).iterrows():
        cards += f"""
        <div class="pending-item">
            <div style="display:flex;justify-content:space-between;gap:8px;">
                <div class="pending-id">{r["ID_Operacion_Pedido"]}</div>
                <div>{badge_complejidad(r["Complejidad"])}</div>
            </div>
            <div class="pending-desc">
                {r["Operacion"]}<br>
                Pedido {r["ID_Pedido"]} · vence {r["Fecha_Compromiso"].strftime("%d/%m")}
            </div>
        </div>
        """

    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">Operaciones pendientes por asignar</div>
            {cards if cards else '<div class="op-detail">No hay pendientes.</div>'}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="panel"><div class="panel-title">Acciones</div>',
        unsafe_allow_html=True,
    )

    if tarea is not None and not ranking.empty:
        if st.button("✓ Confirmar asignación", use_container_width=True):
            elegida = ranking.iloc[0]

            registro = {
                "Fecha_Confirmacion": ahora.strftime("%Y-%m-%d %H:%M:%S"),
                "ID_Operacion_Pedido": tarea["ID_Operacion_Pedido"],
                "ID_Pedido": tarea["ID_Pedido"],
                "Operacion": tarea["Operacion"],
                "ID_Operaria": elegida["ID_Operaria"],
                "Operaria": elegida["Operaria"],
                "Score": elegida["Score"],
                "Estado": "Confirmada por supervisor",
            }

            st.session_state["historial_confirmaciones"].append(registro)
            st.session_state["ultima_confirmacion"] = registro
            st.success(
                f'Asignación confirmada: {elegida["Operaria"]} → {tarea["Operacion"]}'
            )

        if st.button("↻ Recalcular recomendación", use_container_width=True):
            st.rerun()

        excel = exportar_recomendacion(tarea, ranking)

        st.download_button(
            "⬇ Descargar evaluación",
            data=excel,
            file_name="evaluacion_asignacion_C2.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    if st.button("🕘 Ver historial", use_container_width=True):
        st.session_state["mostrar_historial"] = not st.session_state.get(
            "mostrar_historial",
            False,
        )

    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# HISTORIAL DE CONFIRMACIONES
# ============================================================

if st.session_state.get("mostrar_historial", False):
    st.markdown("### Historial de asignaciones confirmadas")

    if st.session_state["historial_confirmaciones"]:
        historial = pd.DataFrame(st.session_state["historial_confirmaciones"])
        st.dataframe(
            historial,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Todavía no se han confirmado asignaciones en esta sesión.")

# ============================================================
# ANÁLISIS COMPLEMENTARIO
# ============================================================

st.markdown("### Vista operativa complementaria")

t1, t2, t3 = st.tabs(
    [
        "Carga por operaria",
        "Matriz de habilidades",
        "Pedidos y operaciones",
    ]
)

with t1:
    carga_data = []

    for _, op in W.iterrows():
        id_op = op["ID_Operaria"]
        cap = capacidad_fecha(id_op, fecha_base)
        carga = carga_operaria_en_fecha(id_op, fecha_base)

        carga_data.append(
            {
                "Operaria": nombre_operaria(id_op),
                "Carga_Min": carga,
                "Capacidad_Min": cap,
                "Utilizacion_%": round(100 * carga / cap, 1) if cap else 0,
            }
        )

    df_carga = pd.DataFrame(carga_data)

    fig = px.bar(
        df_carga,
        x="Operaria",
        y="Utilizacion_%",
        text="Utilizacion_%",
        hover_data=["Carga_Min", "Capacidad_Min"],
    )

    fig.update_traces(texttemplate="%{text:.1f}%")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E7F0F6",
        xaxis_title="",
        yaxis_title="Utilización (%)",
        yaxis_range=[0, 100],
        showlegend=False,
        margin=dict(l=10, r=10, t=20, b=10),
    )

    st.plotly_chart(fig, use_container_width=True)

with t2:
    matriz = H.pivot(
        index="ID_Operaria",
        columns="Operacion",
        values="Nivel",
    )
    matriz.index = [nombre_operaria(x) for x in matriz.index]
    st.dataframe(matriz, use_container_width=True)

with t3:
    cols_ped = [
        "ID_Pedido",
        "Tipo_Vestido",
        "Complejidad",
        "Fecha_Compromiso",
        "Kit_Liberado",
        "Estado_Pedido",
    ]
    st.dataframe(
        P[cols_ped].sort_values("Fecha_Compromiso"),
        use_container_width=True,
        hide_index=True,
    )

# ============================================================
# NOTA METODOLÓGICA
# ============================================================

st.markdown(
    """
    <div class="small-note" style="margin-top:12px;">
    Score de compatibilidad propuesto para el prototipo: 35% habilidad específica,
    20% disponibilidad, 20% balance de carga, 15% desempeño histórico y 10% ajuste
    a la complejidad. Estos pesos deben validarse con el responsable del proceso antes
    de utilizarse como regla operativa definitiva.
    </div>
    """,
    unsafe_allow_html=True,
)

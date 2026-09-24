from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="C2 - Asignación Inteligente del Trabajo",
    page_icon="🧵",
    layout="wide"
)

st.title("🧵 C2 - Asignación Inteligente del Trabajo")
st.caption(
    "Dashboard académico para visualizar pedidos, operarias, habilidades, "
    "operaciones, tiempos y resultados del módulo de asignación."
)

BASE = Path(__file__).resolve().parent


# ============================================================
# LOCALIZAR ARCHIVOS
# ============================================================

def buscar_archivo(palabras, excluir=None):
    archivos = list(BASE.glob("*.xlsx"))
    excluir = excluir or []

    candidatos = []
    for archivo in archivos:
        nombre = archivo.stem.lower()

        if all(p.lower() in nombre for p in palabras):
            if not any(e.lower() in nombre for e in excluir):
                candidatos.append(archivo)

    if not candidatos:
        return None

    return sorted(candidatos, key=lambda x: x.name)[0]


ARCHIVO_PEDIDOS = (
    BASE / "01_pedidos.xlsx"
    if (BASE / "01_pedidos.xlsx").exists()
    else buscar_archivo(["pedidos"], excluir=["operaciones", "resultado"])
)

ARCHIVO_OPERARIAS = (
    BASE / "02_operarias.xlsx"
    if (BASE / "02_operarias.xlsx").exists()
    else buscar_archivo(["operarias"])
)

ARCHIVO_OPERACIONES = (
    BASE / "03_operaciones_pedido.xlsx"
    if (BASE / "03_operaciones_pedido.xlsx").exists()
    else buscar_archivo(["operaciones", "pedido"])
)

ARCHIVO_TIEMPOS = (
    BASE / "04_tiempos.xlsx"
    if (BASE / "04_tiempos.xlsx").exists()
    else buscar_archivo(["tiempos"])
)

ARCHIVO_RESULTADOS = None
for nombre in [
    "resultado_asignacion_C2.xlsx",
    "resultado_asignacion_c2.xlsx",
    "resultados_asignacion_C2.xlsx",
]:
    candidato = BASE / nombre
    if candidato.exists():
        ARCHIVO_RESULTADOS = candidato
        break


faltantes = []
for etiqueta, archivo in {
    "Pedidos": ARCHIVO_PEDIDOS,
    "Operarias": ARCHIVO_OPERARIAS,
    "Operaciones": ARCHIVO_OPERACIONES,
    "Tiempos": ARCHIVO_TIEMPOS,
}.items():
    if archivo is None or not archivo.exists():
        faltantes.append(etiqueta)

if faltantes:
    st.error(
        "Faltan archivos requeridos en el repositorio: "
        + ", ".join(faltantes)
    )
    st.stop()


# ============================================================
# CARGA DE DATOS
# ============================================================

@st.cache_data
def cargar_datos():
    pedidos = pd.read_excel(ARCHIVO_PEDIDOS, sheet_name="Pedidos")
    operarias = pd.read_excel(ARCHIVO_OPERARIAS, sheet_name="Operarias")
    habilidades = pd.read_excel(ARCHIVO_OPERARIAS, sheet_name="Habilidades")
    calendario = pd.read_excel(ARCHIVO_OPERARIAS, sheet_name="Calendario")
    operaciones = pd.read_excel(
        ARCHIVO_OPERACIONES,
        sheet_name="Operaciones_Pedido"
    )
    tiempos = pd.read_excel(ARCHIVO_TIEMPOS, sheet_name="Tiempos")

    pedidos["Fecha_Compromiso"] = pd.to_datetime(
        pedidos["Fecha_Compromiso"], errors="coerce"
    )
    calendario["Fecha"] = pd.to_datetime(
        calendario["Fecha"], errors="coerce"
    )
    tiempos["Fecha"] = pd.to_datetime(
        tiempos["Fecha"], errors="coerce"
    )

    return pedidos, operarias, habilidades, calendario, operaciones, tiempos


P, W, H, CAL, O, R = cargar_datos()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Filtros")

tipos = ["Todos"] + sorted(P["Tipo_Vestido"].dropna().unique().tolist())
tipo_sel = st.sidebar.selectbox("Tipo de vestido", tipos)

complejidades = ["Todas"] + sorted(
    P["Complejidad"].dropna().unique().tolist()
)
complejidad_sel = st.sidebar.selectbox(
    "Complejidad",
    complejidades
)

operarias_lista = ["Todas"] + sorted(
    W["ID_Operaria"].dropna().unique().tolist()
)
operaria_sel = st.sidebar.selectbox(
    "Operaria",
    operarias_lista
)

P_F = P.copy()

if tipo_sel != "Todos":
    P_F = P_F[P_F["Tipo_Vestido"] == tipo_sel]

if complejidad_sel != "Todas":
    P_F = P_F[P_F["Complejidad"] == complejidad_sel]

ids_filtrados = set(P_F["ID_Pedido"])

O_F = O[O["ID_Pedido"].isin(ids_filtrados)].copy()
R_F = R[R["ID_Pedido"].isin(ids_filtrados)].copy()

if operaria_sel != "Todas":
    R_F = R_F[R_F["ID_Operaria"] == operaria_sel]


# ============================================================
# KPI PRINCIPALES
# ============================================================

pedidos_total = P_F["ID_Pedido"].nunique()

operaciones_total = O_F["ID_Operacion_Pedido"].nunique()

ops_completadas = (
    O_F["Estado_Operacion"]
    .astype(str)
    .str.casefold()
    .eq("completada")
    .sum()
)

ops_en_proceso = (
    O_F["Estado_Operacion"]
    .astype(str)
    .str.casefold()
    .eq("en proceso")
    .sum()
)

ops_pendientes = (
    O_F["Estado_Operacion"]
    .astype(str)
    .str.casefold()
    .eq("pendiente")
    .sum()
)

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Pedidos", f"{pedidos_total}")
k2.metric("Operaciones", f"{operaciones_total}")
k3.metric("Completadas", f"{ops_completadas}")
k4.metric("En proceso", f"{ops_en_proceso}")
k5.metric("Pendientes", f"{ops_pendientes}")


# ============================================================
# PESTAÑAS
# ============================================================

tab_resumen, tab_operarias, tab_pedidos, tab_tiempos, tab_plan = st.tabs(
    [
        "📊 Resumen",
        "👷 Operarias",
        "👗 Pedidos",
        "⏱️ Tiempos",
        "🗓️ Plan C2",
    ]
)


# ============================================================
# TAB 1 - RESUMEN
# ============================================================

with tab_resumen:

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Operaciones por estado")

        estado = (
            O_F["Estado_Operacion"]
            .fillna("Sin estado")
            .value_counts()
            .rename_axis("Estado")
            .reset_index(name="Cantidad")
        )

        fig_estado = px.bar(
            estado,
            x="Estado",
            y="Cantidad",
            text="Cantidad"
        )

        fig_estado.update_layout(
            xaxis_title="Estado",
            yaxis_title="Operaciones",
            showlegend=False
        )

        st.plotly_chart(
            fig_estado,
            use_container_width=True
        )

    with c2:
        st.subheader("Pedidos por complejidad")

        complejidad = (
            P_F["Complejidad"]
            .fillna("Sin dato")
            .value_counts()
            .rename_axis("Complejidad")
            .reset_index(name="Pedidos")
        )

        fig_comp = px.pie(
            complejidad,
            names="Complejidad",
            values="Pedidos",
            hole=0.45
        )

        st.plotly_chart(
            fig_comp,
            use_container_width=True
        )

    st.subheader("Operaciones por etapa")

    etapas = (
        O_F["Operacion"]
        .fillna("Sin dato")
        .value_counts()
        .rename_axis("Operacion")
        .reset_index(name="Cantidad")
    )

    fig_etapas = px.bar(
        etapas,
        x="Operacion",
        y="Cantidad",
        text="Cantidad"
    )

    fig_etapas.update_layout(
        xaxis_title="Etapa",
        yaxis_title="Operaciones",
        showlegend=False
    )

    st.plotly_chart(
        fig_etapas,
        use_container_width=True
    )


# ============================================================
# TAB 2 - OPERARIAS
# ============================================================

with tab_operarias:

    st.subheader("Capacidad y especialidad de las operarias")

    columnas_operarias = [
        c for c in [
            "ID_Operaria",
            "Alias_Anonimo",
            "Disponible_Corte",
            "Turno_Inicio",
            "Turno_Fin",
            "Capacidad_Neta_Min",
            "Especialidad_Referencia",
        ]
        if c in W.columns
    ]

    st.dataframe(
        W[columnas_operarias],
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Matriz de habilidades")

    matriz = H.pivot(
        index="ID_Operaria",
        columns="Operacion",
        values="Nivel"
    )

    st.dataframe(
        matriz,
        use_container_width=True
    )

    st.subheader("Carga histórica registrada")

    carga = (
        R_F.groupby("ID_Operaria", as_index=False)
        ["Tiempo_Real_Min"]
        .sum()
        .rename(columns={"Tiempo_Real_Min": "Minutos_Registrados"})
    )

    fig_carga = px.bar(
        carga,
        x="ID_Operaria",
        y="Minutos_Registrados",
        text_auto=True
    )

    fig_carga.update_layout(
        xaxis_title="Operaria",
        yaxis_title="Minutos registrados",
        showlegend=False
    )

    st.plotly_chart(
        fig_carga,
        use_container_width=True
    )


# ============================================================
# TAB 3 - PEDIDOS
# ============================================================

with tab_pedidos:

    st.subheader("Pedidos del modelo")

    columnas_pedidos = [
        c for c in [
            "ID_Pedido",
            "Fecha_Recepcion",
            "Fecha_Compromiso",
            "Tipo_Vestido",
            "Complejidad",
            "Tela_Principal",
            "Detalle_Personalizado",
            "Kit_Liberado",
            "Estado_Pedido",
        ]
        if c in P_F.columns
    ]

    st.dataframe(
        P_F[columnas_pedidos]
        .sort_values("Fecha_Compromiso"),
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Detalle de operaciones por pedido")

    pedido_sel = st.selectbox(
        "Selecciona un pedido",
        sorted(P_F["ID_Pedido"].astype(str).unique())
    )

    detalle = (
        O_F[O_F["ID_Pedido"].astype(str) == pedido_sel]
        .sort_values("Secuencia")
    )

    columnas_detalle = [
        c for c in [
            "Secuencia",
            "Operacion",
            "Estado_Operacion",
            "ID_Operaria_Asignada",
            "Tiempo_Estimado_Min",
            "Tiempo_Ejecutado_Min",
            "Tiempo_Pendiente_Min",
            "Nivel_Requerido",
        ]
        if c in detalle.columns
    ]

    st.dataframe(
        detalle[columnas_detalle],
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TAB 4 - TIEMPOS
# ============================================================

with tab_tiempos:

    st.subheader("Tiempo real promedio por etapa")

    promedio = (
        R_F.groupby("Operacion", as_index=False)
        ["Tiempo_Real_Min"]
        .mean()
        .rename(
            columns={
                "Tiempo_Real_Min": "Tiempo_Promedio_Min"
            }
        )
    )

    promedio["Tiempo_Promedio_Min"] = promedio[
        "Tiempo_Promedio_Min"
    ].round(1)

    fig_prom = px.bar(
        promedio,
        x="Operacion",
        y="Tiempo_Promedio_Min",
        text="Tiempo_Promedio_Min"
    )

    fig_prom.update_layout(
        xaxis_title="Etapa",
        yaxis_title="Minutos promedio",
        showlegend=False
    )

    st.plotly_chart(
        fig_prom,
        use_container_width=True
    )

    st.subheader("Registros de tiempos")

    columnas_tiempo = [
        c for c in [
            "Fecha",
            "ID_Pedido",
            "ID_Operacion_Pedido",
            "ID_Operaria",
            "Operacion",
            "Tipo_Vestido",
            "Complejidad",
            "Tiempo_Real_Min",
            "Tiempo_Espera_Min",
            "Causa_Espera",
            "Reproceso",
        ]
        if c in R_F.columns
    ]

    st.dataframe(
        R_F[columnas_tiempo]
        .sort_values("Fecha", ascending=False),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TAB 5 - PLAN DEL ALGORITMO C2
# ============================================================

with tab_plan:

    if ARCHIVO_RESULTADOS is None:

        st.info(
            "Todavía no se encontró `resultado_asignacion_C2.xlsx` "
            "en el repositorio. Cuando tu código de asignación genere "
            "ese archivo y lo subas a GitHub, esta pestaña lo mostrará "
            "automáticamente."
        )

    else:

        st.success(
            f"Resultados detectados: {ARCHIVO_RESULTADOS.name}"
        )

        xls_resultado = pd.ExcelFile(ARCHIVO_RESULTADOS)

        if "Plan_Asignacion" in xls_resultado.sheet_names:

            plan = pd.read_excel(
                ARCHIVO_RESULTADOS,
                sheet_name="Plan_Asignacion"
            )

            st.subheader("Plan de asignación")

            p1, p2, p3 = st.columns(3)

            p1.metric(
                "Operaciones programadas",
                plan["ID_Operacion_Pedido"].nunique()
                if "ID_Operacion_Pedido" in plan.columns else len(plan)
            )

            p2.metric(
                "Pedidos programados",
                plan["ID_Pedido"].nunique()
                if "ID_Pedido" in plan.columns else "-"
            )

            p3.metric(
                "Operarias utilizadas",
                plan["ID_Operaria"].nunique()
                if "ID_Operaria" in plan.columns else "-"
            )

            st.dataframe(
                plan,
                use_container_width=True,
                hide_index=True
            )

            if {
                "ID_Operaria",
                "Minutos_Asignados"
            }.issubset(plan.columns):

                carga_plan = (
                    plan.groupby(
                        "ID_Operaria",
                        as_index=False
                    )["Minutos_Asignados"]
                    .sum()
                )

                st.subheader(
                    "Carga asignada por el algoritmo"
                )

                fig_plan = px.bar(
                    carga_plan,
                    x="ID_Operaria",
                    y="Minutos_Asignados",
                    text_auto=True
                )

                fig_plan.update_layout(
                    xaxis_title="Operaria",
                    yaxis_title="Minutos asignados",
                    showlegend=False
                )

                st.plotly_chart(
                    fig_plan,
                    use_container_width=True
                )

        if "Sin_Programar" in xls_resultado.sheet_names:

            sin_programar = pd.read_excel(
                ARCHIVO_RESULTADOS,
                sheet_name="Sin_Programar"
            )

            st.subheader("Operaciones sin programar")

            st.dataframe(
                sin_programar,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# DESCARGA
# ============================================================

st.divider()

st.caption(
    "El dashboard se actualiza automáticamente cuando cambian "
    "los archivos del repositorio y Streamlit vuelve a ejecutar la app."
)

from pathlib import Path
from collections import defaultdict
from statistics import median
from io import BytesIO
import math

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="C2 - Asignación Inteligente del Trabajo",
    page_icon="🧵",
    layout="wide"
)

st.title("🧵 C2 - Asignación Inteligente del Trabajo")
st.caption(
    "Generación automática de una propuesta de asignación por operaria "
    "considerando secuencia, habilidades, disponibilidad, carga, "
    "fecha de entrega y complejidad."
)

BASE = Path(__file__).resolve().parent


# ============================================================
# ARCHIVOS
# ============================================================

def encontrar_archivo(nombre_preferido, palabras):
    preferido = BASE / nombre_preferido
    if preferido.exists():
        return preferido

    candidatos = []
    for archivo in BASE.glob("*.xlsx"):
        nombre = archivo.stem.lower()
        if all(p.lower() in nombre for p in palabras):
            candidatos.append(archivo)

    if not candidatos:
        return None

    return sorted(candidatos, key=lambda x: x.name)[0]


ARCHIVO_PEDIDOS = encontrar_archivo(
    "01_pedidos.xlsx",
    ["pedidos"]
)
ARCHIVO_OPERARIAS = encontrar_archivo(
    "02_operarias.xlsx",
    ["operarias"]
)
ARCHIVO_OPERACIONES = encontrar_archivo(
    "03_operaciones_pedido.xlsx",
    ["operaciones", "pedido"]
)
ARCHIVO_TIEMPOS = encontrar_archivo(
    "04_tiempos.xlsx",
    ["tiempos"]
)

faltantes = [
    nombre
    for nombre, archivo in {
        "01_pedidos.xlsx": ARCHIVO_PEDIDOS,
        "02_operarias.xlsx": ARCHIVO_OPERARIAS,
        "03_operaciones_pedido.xlsx": ARCHIVO_OPERACIONES,
        "04_tiempos.xlsx": ARCHIVO_TIEMPOS,
    }.items()
    if archivo is None
]

if faltantes:
    st.error(
        "Faltan archivos en el repositorio: "
        + ", ".join(faltantes)
    )
    st.stop()


# ============================================================
# CARGA
# ============================================================

@st.cache_data
def cargar_datos():
    pedidos = pd.read_excel(
        ARCHIVO_PEDIDOS,
        sheet_name="Pedidos"
    )
    operarias = pd.read_excel(
        ARCHIVO_OPERARIAS,
        sheet_name="Operarias"
    )
    habilidades = pd.read_excel(
        ARCHIVO_OPERARIAS,
        sheet_name="Habilidades"
    )
    calendario = pd.read_excel(
        ARCHIVO_OPERARIAS,
        sheet_name="Calendario"
    )
    operaciones = pd.read_excel(
        ARCHIVO_OPERACIONES,
        sheet_name="Operaciones_Pedido"
    )
    tiempos = pd.read_excel(
        ARCHIVO_TIEMPOS,
        sheet_name="Tiempos"
    )

    pedidos["Fecha_Compromiso"] = pd.to_datetime(
        pedidos["Fecha_Compromiso"],
        errors="coerce"
    ).dt.normalize()

    if "Fecha_Liberacion_Kit" in pedidos.columns:
        pedidos["Fecha_Liberacion_Kit"] = pd.to_datetime(
            pedidos["Fecha_Liberacion_Kit"],
            errors="coerce"
        ).dt.normalize()

    calendario["Fecha"] = pd.to_datetime(
        calendario["Fecha"],
        errors="coerce"
    ).dt.normalize()

    tiempos["Fecha"] = pd.to_datetime(
        tiempos["Fecha"],
        errors="coerce"
    ).dt.normalize()

    if "Fecha_Inicio_Real" in operaciones.columns:
        operaciones["Fecha_Inicio_Real"] = pd.to_datetime(
            operaciones["Fecha_Inicio_Real"],
            errors="coerce"
        ).dt.normalize()

    if "Fecha_Fin_Real" in operaciones.columns:
        operaciones["Fecha_Fin_Real"] = pd.to_datetime(
            operaciones["Fecha_Fin_Real"],
            errors="coerce"
        ).dt.normalize()

    return (
        pedidos,
        operarias,
        habilidades,
        calendario,
        operaciones,
        tiempos
    )


P, W, H, CAL, O, R = cargar_datos()


# ============================================================
# FUNCIONES BÁSICAS
# ============================================================

def es_si(valor):
    return str(valor).strip().casefold() in {
        "sí", "si", "true", "1"
    }


def nivel_complejidad(valor):
    return {
        "Alta": 3,
        "Media": 2,
        "Baja": 1
    }.get(str(valor), 0)


# ============================================================
# PREPARACIÓN DE TIEMPOS HISTÓRICOS
# ============================================================

def construir_base_tiempos(pedidos, operaciones, tiempos):
    terminadas = operaciones.loc[
        operaciones["Estado_Operacion"].eq("Completada"),
        [
            "ID_Operacion_Pedido",
            "ID_Pedido",
            "Operacion",
            "ID_Operaria_Asignada"
        ]
    ].copy()

    acumulado = (
        tiempos[
            tiempos["ID_Operacion_Pedido"].isin(
                terminadas["ID_Operacion_Pedido"]
            )
        ]
        .groupby(
            [
                "ID_Operacion_Pedido",
                "ID_Operaria"
            ],
            as_index=False
        )["Tiempo_Real_Min"]
        .sum()
    )

    acumulado = acumulado.merge(
        terminadas,
        on="ID_Operacion_Pedido",
        how="inner",
        validate="many_to_one"
    )

    acumulado = acumulado[
        acumulado["ID_Operaria"].eq(
            acumulado["ID_Operaria_Asignada"]
        )
    ].copy()

    acumulado = acumulado.merge(
        pedidos[
            [
                "ID_Pedido",
                "Tipo_Vestido",
                "Complejidad"
            ]
        ],
        on="ID_Pedido",
        how="left",
        validate="many_to_one"
    )

    acumulado = acumulado[
        pd.to_numeric(
            acumulado["Tiempo_Real_Min"],
            errors="coerce"
        ).fillna(0) > 0
    ].copy()

    grupos = defaultdict(list)

    for fila in acumulado.itertuples(index=False):
        duracion = float(fila.Tiempo_Real_Min)

        claves = [
            (
                "individual",
                fila.Operacion,
                fila.Tipo_Vestido,
                fila.Complejidad,
                fila.ID_Operaria
            ),
            (
                "tipo",
                fila.Operacion,
                fila.Tipo_Vestido,
                fila.Complejidad
            ),
            (
                "complejidad",
                fila.Operacion,
                fila.Complejidad
            ),
            (
                "operacion",
                fila.Operacion
            )
        ]

        for clave in claves:
            grupos[clave].append(duracion)

    return grupos


GRUPOS_TIEMPO = construir_base_tiempos(
    P, O, R
)


# ============================================================
# MOTOR C2
# ============================================================

def generar_asignacion(
    pedidos_df,
    operarias_df,
    habilidades_df,
    calendario_df,
    operaciones_df,
    grupos_tiempo
):
    pedidos = pedidos_df.set_index(
        "ID_Pedido"
    ).to_dict("index")

    operarias = operarias_df.set_index(
        "ID_Operaria"
    ).to_dict("index")

    tareas = operaciones_df.set_index(
        "ID_Operacion_Pedido"
    ).to_dict("index")

    habilidades = {
        (
            fila.ID_Operaria,
            fila.Operacion
        ): {
            "Nivel": int(fila.Nivel),
            "Habilitada_Alta": fila.Habilitada_Alta
        }
        for fila in habilidades_df.itertuples(index=False)
    }

    calendario = {
        (
            fila.Fecha,
            fila.ID_Operaria
        ): (
            int(fila.Capacidad_Programable_Min)
            if es_si(fila.Disponible)
            else 0
        )
        for fila in calendario_df.itertuples(index=False)
    }

    dias = sorted(
        calendario_df["Fecha"]
        .dropna()
        .unique()
    )

    dias = [
        pd.Timestamp(d).normalize()
        for d in dias
    ]

    if not dias:
        raise ValueError(
            "El calendario no contiene fechas utilizables."
        )

    primer_dia = min(dias)

    def habilitada(id_tarea, id_operaria):
        tarea = tareas[id_tarea]
        info = habilidades.get(
            (
                id_operaria,
                tarea["Operacion"]
            )
        )

        if info is None:
            return False

        if info["Nivel"] < int(
            tarea["Nivel_Requerido"]
        ):
            return False

        pedido = pedidos[
            tarea["ID_Pedido"]
        ]

        if (
            pedido["Complejidad"] == "Alta"
            and not es_si(
                info["Habilitada_Alta"]
            )
        ):
            return False

        return True

    def estimar_tiempo(
        id_tarea,
        id_operaria
    ):
        tarea = tareas[id_tarea]
        pedido = pedidos[
            tarea["ID_Pedido"]
        ]

        opciones = [
            (
                "Histórico operaria/tipo/complejidad",
                (
                    "individual",
                    tarea["Operacion"],
                    pedido["Tipo_Vestido"],
                    pedido["Complejidad"],
                    id_operaria
                )
            ),
            (
                "Histórico tipo/complejidad",
                (
                    "tipo",
                    tarea["Operacion"],
                    pedido["Tipo_Vestido"],
                    pedido["Complejidad"]
                )
            ),
            (
                "Histórico operación/complejidad",
                (
                    "complejidad",
                    tarea["Operacion"],
                    pedido["Complejidad"]
                )
            ),
            (
                "Histórico operación",
                (
                    "operacion",
                    tarea["Operacion"]
                )
            )
        ]

        for fuente, clave in opciones:
            valores = grupos_tiempo.get(
                clave,
                []
            )

            if len(valores) >= 3:
                return (
                    max(
                        1,
                        math.ceil(
                            median(valores)
                        )
                    ),
                    fuente
                )

        estimado = tarea.get(
            "Tiempo_Estimado_Min"
        )

        if pd.notna(estimado) and float(
            estimado
        ) > 0:
            return (
                math.ceil(float(estimado)),
                "Tiempo estimado del pedido"
            )

        return None, "Sin estimación"

    # --------------------------------------------
    # Operaciones ya completadas
    # --------------------------------------------

    completadas = {}

    for id_tarea, tarea in tareas.items():
        if tarea["Estado_Operacion"] == "Completada":
            fecha_fin = tarea.get(
                "Fecha_Fin_Real"
            )

            if pd.isna(fecha_fin):
                fecha_fin = (
                    primer_dia
                    - pd.Timedelta(days=1)
                )

            completadas[id_tarea] = (
                pd.Timestamp(
                    fecha_fin
                ).normalize(),
                0
            )

    # --------------------------------------------
    # Pedidos que sí pueden programarse
    # --------------------------------------------

    pedidos_liberados = {
        id_pedido
        for id_pedido, pedido in pedidos.items()
        if es_si(
            pedido["Kit_Liberado"]
        )
    }

    # --------------------------------------------
    # Estado inicial de tareas
    # --------------------------------------------

    restante = {}
    responsable = {}
    fuente_tiempo = {}

    for id_tarea, tarea in tareas.items():
        if (
            tarea["ID_Pedido"]
            not in pedidos_liberados
        ):
            continue

        estado = tarea[
            "Estado_Operacion"
        ]

        if estado == "En proceso":
            op = tarea[
                "ID_Operaria_Asignada"
            ]

            if (
                pd.isna(op)
                or op not in operarias
            ):
                continue

            responsable[
                id_tarea
            ] = op

            restante[
                id_tarea
            ] = max(
                1,
                math.ceil(
                    float(
                        tarea[
                            "Tiempo_Pendiente_Min"
                        ]
                    )
                )
            )

            fuente_tiempo[
                id_tarea
            ] = "Trabajo ya iniciado"

        elif estado == "Pendiente":
            restante[
                id_tarea
            ] = None

    # --------------------------------------------
    # Carga acumulada para balance
    # --------------------------------------------

    carga_total = {
        id_operaria: 0
        for id_operaria in operarias
    }

    plan = []

    for dia in dias:

        capacidad = {}

        for id_operaria in operarias:
            general = es_si(
                operarias[
                    id_operaria
                ]["Disponible_Corte"]
            )

            capacidad[
                id_operaria
            ] = (
                calendario.get(
                    (
                        dia,
                        id_operaria
                    ),
                    0
                )
                if general
                else 0
            )

        cursor = {
            id_operaria: 0
            for id_operaria in operarias
        }

        while True:

            candidatos = []

            for id_tarea in list(
                restante.keys()
            ):
                tarea = tareas[
                    id_tarea
                ]

                pedido = pedidos[
                    tarea["ID_Pedido"]
                ]

                # Kit liberado antes o durante el día
                fecha_lib = pedido.get(
                    "Fecha_Liberacion_Kit"
                )

                if (
                    pd.notna(fecha_lib)
                    and pd.Timestamp(
                        fecha_lib
                    ).normalize() > dia
                ):
                    continue

                previa = tarea.get(
                    "ID_Operacion_Previa"
                )

                minuto_habilitado = 0

                if pd.notna(previa):
                    if previa not in completadas:
                        continue

                    fecha_previa, fin_previa = (
                        completadas[previa]
                    )

                    if fecha_previa > dia:
                        continue

                    if fecha_previa == dia:
                        minuto_habilitado = (
                            fin_previa
                        )

                # Una operación iniciada permanece
                # con la misma operaria
                if id_tarea in responsable:
                    posibles = [
                        responsable[
                            id_tarea
                        ]
                    ]
                else:
                    posibles = list(
                        operarias.keys()
                    )

                for id_operaria in posibles:

                    if not habilitada(
                        id_tarea,
                        id_operaria
                    ):
                        continue

                    inicio = max(
                        cursor[
                            id_operaria
                        ],
                        minuto_habilitado
                    )

                    if (
                        inicio
                        >= capacidad[
                            id_operaria
                        ]
                    ):
                        continue

                    if (
                        restante[
                            id_tarea
                        ]
                        is None
                    ):
                        duracion, fuente = (
                            estimar_tiempo(
                                id_tarea,
                                id_operaria
                            )
                        )
                    else:
                        duracion = restante[
                            id_tarea
                        ]
                        fuente = fuente_tiempo[
                            id_tarea
                        ]

                    if (
                        duracion is None
                        or duracion <= 0
                    ):
                        continue

                    nivel = habilidades[
                        (
                            id_operaria,
                            tarea["Operacion"]
                        )
                    ]["Nivel"]

                    fecha_entrega = pedido[
                        "Fecha_Compromiso"
                    ]

                    if pd.isna(
                        fecha_entrega
                    ):
                        fecha_entrega = pd.Timestamp.max.normalize()

                    # Prioridad human-centered / operativa:
                    # 1. continuar lo iniciado
                    # 2. fecha de entrega
                    # 3. complejidad
                    # 4. mayor habilidad
                    # 5. menor carga acumulada
                    # 6. menor duración estimada
                    clave = (
                        0
                        if id_tarea
                        in responsable
                        else 1,
                        fecha_entrega,
                        -nivel_complejidad(
                            pedido["Complejidad"]
                        ),
                        -nivel,
                        carga_total[
                            id_operaria
                        ],
                        duracion,
                        str(id_tarea),
                        str(id_operaria)
                    )

                    candidatos.append(
                        (
                            clave,
                            id_tarea,
                            id_operaria,
                            inicio,
                            duracion,
                            fuente,
                            nivel
                        )
                    )

            if not candidatos:
                break

            (
                _,
                id_tarea,
                id_operaria,
                inicio,
                duracion,
                fuente,
                nivel
            ) = min(
                candidatos,
                key=lambda x: x[0]
            )

            if id_tarea not in responsable:
                responsable[
                    id_tarea
                ] = id_operaria

                restante[
                    id_tarea
                ] = duracion

                fuente_tiempo[
                    id_tarea
                ] = fuente

            disponible = (
                capacidad[
                    id_operaria
                ]
                - inicio
            )

            minutos = min(
                restante[
                    id_tarea
                ],
                disponible
            )

            if minutos <= 0:
                break

            fin = inicio + minutos

            restante[
                id_tarea
            ] -= minutos

            cursor[
                id_operaria
            ] = fin

            carga_total[
                id_operaria
            ] += minutos

            tarea = tareas[
                id_tarea
            ]
            pedido = pedidos[
                tarea["ID_Pedido"]
            ]

            plan.append(
                {
                    "Fecha": dia,
                    "ID_Pedido": tarea[
                        "ID_Pedido"
                    ],
                    "Tipo_Vestido": pedido[
                        "Tipo_Vestido"
                    ],
                    "Complejidad": pedido[
                        "Complejidad"
                    ],
                    "Fecha_Compromiso": pedido[
                        "Fecha_Compromiso"
                    ],
                    "ID_Operacion_Pedido": id_tarea,
                    "Secuencia": tarea[
                        "Secuencia"
                    ],
                    "Operacion": tarea[
                        "Operacion"
                    ],
                    "ID_Operaria": id_operaria,
                    "Nivel_Habilidad": nivel,
                    "Inicio_Minuto_Neto": inicio,
                    "Fin_Minuto_Neto": fin,
                    "Minutos_Asignados": minutos,
                    "Minutos_Pendientes": restante[
                        id_tarea
                    ],
                    "Fuente_Duracion": fuente,
                    "Estado_Tramo": (
                        "Finaliza"
                        if restante[
                            id_tarea
                        ] == 0
                        else "Continúa"
                    ),
                    "Estado_Propuesta":
                        "Pendiente de aprobación del supervisor"
                }
            )

            if restante[
                id_tarea
            ] == 0:
                completadas[
                    id_tarea
                ] = (
                    dia,
                    fin
                )

                del restante[
                    id_tarea
                ]

    plan_df = pd.DataFrame(plan)

    # --------------------------------------------
    # Operaciones no finalizadas
    # --------------------------------------------

    sin_programar = []

    for id_tarea, minutos in restante.items():
        tarea = tareas[
            id_tarea
        ]
        pedido = pedidos[
            tarea["ID_Pedido"]
        ]

        previa = tarea.get(
            "ID_Operacion_Previa"
        )

        habilitadas = [
            op
            for op in operarias
            if habilitada(
                id_tarea,
                op
            )
        ]

        if not habilitadas:
            motivo = (
                "No existe operaria con habilidad suficiente"
            )
        elif (
            pd.notna(previa)
            and previa not in completadas
        ):
            motivo = (
                "La operación previa todavía no finaliza"
            )
        else:
            motivo = (
                "Capacidad insuficiente dentro del calendario"
            )

        sin_programar.append(
            {
                "ID_Operacion_Pedido": id_tarea,
                "ID_Pedido": tarea[
                    "ID_Pedido"
                ],
                "Operacion": tarea[
                    "Operacion"
                ],
                "Fecha_Compromiso": pedido[
                    "Fecha_Compromiso"
                ],
                "Minutos_Pendientes": (
                    minutos
                    if minutos is not None
                    else tarea[
                        "Tiempo_Pendiente_Min"
                    ]
                ),
                "Motivo": motivo
            }
        )

    sin_df = pd.DataFrame(
        sin_programar
    )

    # --------------------------------------------
    # Resumen por operaria
    # --------------------------------------------

    if plan_df.empty:
        resumen_op = pd.DataFrame(
            columns=[
                "ID_Operaria",
                "Operaciones_Asignadas",
                "Pedidos_Atendidos",
                "Minutos_Asignados",
                "Dias_Con_Carga"
            ]
        )
    else:
        resumen_op = (
            plan_df.groupby(
                "ID_Operaria",
                as_index=False
            )
            .agg(
                Operaciones_Asignadas=(
                    "ID_Operacion_Pedido",
                    "nunique"
                ),
                Pedidos_Atendidos=(
                    "ID_Pedido",
                    "nunique"
                ),
                Minutos_Asignados=(
                    "Minutos_Asignados",
                    "sum"
                ),
                Dias_Con_Carga=(
                    "Fecha",
                    "nunique"
                )
            )
        )

        capacidad_total = (
            calendario_df[
                calendario_df[
                    "Disponible"
                ].astype(str)
                .str.casefold()
                .isin(
                    ["sí", "si", "true", "1"]
                )
            ]
            .groupby(
                "ID_Operaria",
                as_index=False
            )[
                "Capacidad_Programable_Min"
            ]
            .sum()
            .rename(
                columns={
                    "Capacidad_Programable_Min":
                        "Capacidad_Disponible_Min"
                }
            )
        )

        resumen_op = resumen_op.merge(
            capacidad_total,
            on="ID_Operaria",
            how="left"
        )

        resumen_op[
            "Utilizacion_%"
        ] = (
            100
            * resumen_op[
                "Minutos_Asignados"
            ]
            / resumen_op[
                "Capacidad_Disponible_Min"
            ].replace(0, pd.NA)
        ).round(1)

    # --------------------------------------------
    # Resumen por pedido
    # --------------------------------------------

    if plan_df.empty:
        resumen_pedido = pd.DataFrame()
    else:
        resumen_pedido = (
            plan_df.groupby(
                "ID_Pedido",
                as_index=False
            )
            .agg(
                Tipo_Vestido=(
                    "Tipo_Vestido",
                    "first"
                ),
                Complejidad=(
                    "Complejidad",
                    "first"
                ),
                Fecha_Compromiso=(
                    "Fecha_Compromiso",
                    "first"
                ),
                Fecha_Inicio_Plan=(
                    "Fecha",
                    "min"
                ),
                Fecha_Fin_Plan=(
                    "Fecha",
                    "max"
                ),
                Operaciones_Programadas=(
                    "ID_Operacion_Pedido",
                    "nunique"
                )
            )
        )

        resumen_pedido[
            "Estado_Plazo"
        ] = resumen_pedido.apply(
            lambda r: (
                "En fecha"
                if pd.isna(
                    r["Fecha_Compromiso"]
                )
                or r["Fecha_Fin_Plan"]
                <= r["Fecha_Compromiso"]
                else "Riesgo de atraso"
            ),
            axis=1
        )

    return (
        plan_df,
        sin_df,
        resumen_op,
        resumen_pedido
    )


# ============================================================
# EXPORTAR RESULTADOS
# ============================================================

def crear_excel_resultados(
    plan,
    sin_programar,
    resumen_operarias,
    resumen_pedidos
):
    buffer = BytesIO()

    with pd.ExcelWriter(
        buffer,
        engine="openpyxl"
    ) as writer:
        plan.to_excel(
            writer,
            sheet_name="Plan_Asignacion",
            index=False
        )
        sin_programar.to_excel(
            writer,
            sheet_name="Sin_Programar",
            index=False
        )
        resumen_operarias.to_excel(
            writer,
            sheet_name="Resumen_Operarias",
            index=False
        )
        resumen_pedidos.to_excel(
            writer,
            sheet_name="Resumen_Pedidos",
            index=False
        )

    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# DATOS GENERALES
# ============================================================

st.sidebar.header("Modelo C2")

st.sidebar.write(
    "**Criterios utilizados**"
)
st.sidebar.write(
    "1. Fecha de entrega"
)
st.sidebar.write(
    "2. Complejidad"
)
st.sidebar.write(
    "3. Nivel de habilidad"
)
st.sidebar.write(
    "4. Balance de carga"
)
st.sidebar.write(
    "5. Tiempo estimado"
)

st.sidebar.divider()

st.sidebar.write(
    "**Secuencia obligatoria**"
)
st.sidebar.write(
    "Corte → Ensamblaje → "
    "Acabados y detalles → Planchado"
)


# ============================================================
# KPIs BASE
# ============================================================

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Pedidos",
    P["ID_Pedido"].nunique()
)
k2.metric(
    "Operarias",
    W["ID_Operaria"].nunique()
)
k3.metric(
    "Operaciones",
    O["ID_Operacion_Pedido"].nunique()
)
k4.metric(
    "Registros de tiempo",
    len(R)
)


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🎯 Generar asignación",
        "👷 Habilidades",
        "👗 Pedidos",
        "⏱️ Datos de tiempos"
    ]
)


# ============================================================
# TAB ASIGNACIÓN
# ============================================================

with tab1:

    st.subheader(
        "Propuesta automática de asignación"
    )

    st.write(
        "El sistema asigna cada operación a una operaria "
        "compatible y construye un plan respetando la "
        "secuencia del vestido y la capacidad disponible."
    )

    if st.button(
        "▶ Generar asignación C2",
        type="primary",
        use_container_width=True
    ):
        try:
            (
                plan_df,
                sin_df,
                resumen_op,
                resumen_pedido
            ) = generar_asignacion(
                P,
                W,
                H,
                CAL,
                O,
                GRUPOS_TIEMPO
            )

            st.session_state[
                "plan_df"
            ] = plan_df

            st.session_state[
                "sin_df"
            ] = sin_df

            st.session_state[
                "resumen_op"
            ] = resumen_op

            st.session_state[
                "resumen_pedido"
            ] = resumen_pedido

        except Exception as e:
            st.error(
                f"No se pudo generar la asignación: {e}"
            )

    if "plan_df" in st.session_state:

        plan_df = st.session_state[
            "plan_df"
        ]
        sin_df = st.session_state[
            "sin_df"
        ]
        resumen_op = st.session_state[
            "resumen_op"
        ]
        resumen_pedido = st.session_state[
            "resumen_pedido"
        ]

        if plan_df.empty:
            st.warning(
                "No se generaron nuevas asignaciones."
            )
        else:
            a1, a2, a3, a4 = st.columns(4)

            a1.metric(
                "Pedidos programados",
                plan_df[
                    "ID_Pedido"
                ].nunique()
            )
            a2.metric(
                "Operaciones programadas",
                plan_df[
                    "ID_Operacion_Pedido"
                ].nunique()
            )
            a3.metric(
                "Operarias utilizadas",
                plan_df[
                    "ID_Operaria"
                ].nunique()
            )
            a4.metric(
                "Pendientes",
                len(sin_df)
            )

            st.subheader(
                "Asignación por operaria"
            )

            st.dataframe(
                resumen_op,
                use_container_width=True,
                hide_index=True
            )

            if not resumen_op.empty:
                fig = px.bar(
                    resumen_op,
                    x="ID_Operaria",
                    y="Minutos_Asignados",
                    text="Minutos_Asignados",
                    hover_data=[
                        "Operaciones_Asignadas",
                        "Pedidos_Atendidos",
                        "Utilizacion_%"
                    ]
                )

                fig.update_layout(
                    xaxis_title="Operaria",
                    yaxis_title="Minutos asignados",
                    showlegend=False
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            st.subheader(
                "Detalle de asignaciones"
            )

            operaria_filtro = st.selectbox(
                "Filtrar por operaria",
                ["Todas"]
                + sorted(
                    plan_df[
                        "ID_Operaria"
                    ].unique().tolist()
                )
            )

            vista = plan_df.copy()

            if operaria_filtro != "Todas":
                vista = vista[
                    vista[
                        "ID_Operaria"
                    ] == operaria_filtro
                ]

            st.dataframe(
                vista.sort_values(
                    [
                        "Fecha",
                        "ID_Operaria",
                        "Inicio_Minuto_Neto"
                    ]
                ),
                use_container_width=True,
                hide_index=True
            )

            st.subheader(
                "Programación por pedido"
            )

            st.dataframe(
                resumen_pedido.sort_values(
                    "Fecha_Compromiso"
                ),
                use_container_width=True,
                hide_index=True
            )

            if not sin_df.empty:
                st.subheader(
                    "Operaciones no finalizadas"
                )

                st.dataframe(
                    sin_df,
                    use_container_width=True,
                    hide_index=True
                )

            archivo_excel = (
                crear_excel_resultados(
                    plan_df,
                    sin_df,
                    resumen_op,
                    resumen_pedido
                )
            )

            st.download_button(
                "⬇ Descargar resultado_asignacion_C2.xlsx",
                data=archivo_excel,
                file_name=(
                    "resultado_asignacion_C2.xlsx"
                ),
                mime=(
                    "application/vnd.openxmlformats-"
                    "officedocument.spreadsheetml.sheet"
                ),
                use_container_width=True
            )


# ============================================================
# TAB HABILIDADES
# ============================================================

with tab2:

    st.subheader(
        "Matriz de habilidades"
    )

    matriz = H.pivot(
        index="ID_Operaria",
        columns="Operacion",
        values="Nivel"
    )

    st.dataframe(
        matriz,
        use_container_width=True
    )

    st.subheader(
        "Capacidad de operarias"
    )

    columnas = [
        c
        for c in [
            "ID_Operaria",
            "Alias_Anonimo",
            "Turno_Inicio",
            "Turno_Fin",
            "Capacidad_Neta_Min",
            "Especialidad_Referencia"
        ]
        if c in W.columns
    ]

    st.dataframe(
        W[columnas],
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TAB PEDIDOS
# ============================================================

with tab3:

    st.subheader(
        "Pedidos"
    )

    columnas = [
        c
        for c in [
            "ID_Pedido",
            "Fecha_Recepcion",
            "Fecha_Compromiso",
            "Tipo_Vestido",
            "Complejidad",
            "Tela_Principal",
            "Detalle_Personalizado",
            "Kit_Liberado",
            "Estado_Pedido"
        ]
        if c in P.columns
    ]

    st.dataframe(
        P[columnas].sort_values(
            "Fecha_Compromiso"
        ),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TAB TIEMPOS
# ============================================================

with tab4:

    st.subheader(
        "Tiempo histórico promedio por operación"
    )

    promedio = (
        R.groupby(
            "Operacion",
            as_index=False
        )[
            "Tiempo_Real_Min"
        ]
        .mean()
    )

    promedio[
        "Tiempo_Real_Min"
    ] = promedio[
        "Tiempo_Real_Min"
    ].round(1)

    fig = px.bar(
        promedio,
        x="Operacion",
        y="Tiempo_Real_Min",
        text="Tiempo_Real_Min"
    )

    fig.update_layout(
        xaxis_title="Operación",
        yaxis_title="Minutos promedio",
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.dataframe(
        R[
            [
                c
                for c in [
                    "Fecha",
                    "ID_Pedido",
                    "ID_Operaria",
                    "Operacion",
                    "Tipo_Vestido",
                    "Complejidad",
                    "Tiempo_Real_Min",
                    "Tiempo_Espera_Min",
                    "Causa_Espera",
                    "Reproceso"
                ]
                if c in R.columns
            ]
        ].sort_values(
            "Fecha",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True
    )

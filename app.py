
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

from mapa import mostrar_mapa
from chatbot import mostrar_chatbot
from indicadores import (
    calcular_indicadores,
    cobertura_municipal
)

st.set_page_config(
    page_title="Violeta 360",
    page_icon="🟣",
    layout="wide"
)

ruta = Path(__file__).resolve().parent / "datos_procesados"

color = "#7950B2"
claves = ["euv", "euv_caso"]


@st.cache_data
def cargar(archivo, modificacion):
    return pd.read_parquet(archivo)


def obtener(nombre):
    archivo = ruta / (nombre + ".parquet")

    if not archivo.exists():
        raise FileNotFoundError(nombre + ".parquet")

    return cargar(
        str(archivo),
        archivo.stat().st_mtime_ns
    )


try:
    casos = obtener("casos")
    servicios = obtener("servicios")
    agresores = obtener("agresores")
    ordenes = obtener("ordenes")

except FileNotFoundError as error:
    st.error(
        f"No se encontró {error}. "
        "Ejecuta limpieza.py antes de iniciar Violeta 360."
    )
    st.stop()


st.title("🟣 Violeta 360")

st.subheader(
    "Observatorio de violencia y atención institucional"
)

st.caption(
    "Tlaxcala | Datos para la toma de decisiones"
)

st.sidebar.title("Violeta 360")

pagina = st.sidebar.radio(
    "Menú principal",
    [
        "Resumen general",
        "Análisis territorial",
        "Patrones de violencia",
        "Atención institucional",
        "Órdenes de protección",
        "Brechas de atención",
        "Recomendaciones",
        "Atlas territorial"
    ]
)

st.sidebar.divider()
st.sidebar.header("Filtros")

municipios = sorted(
    casos["hecho_municipio"]
    .dropna()
    .unique()
    .tolist()
)

municipio = st.sidebar.selectbox(
    "Municipio del hecho",
    ["Todos"] + municipios
)

casos["anio"] = pd.to_datetime(
    casos["hecho_fecha"],
    errors="coerce"
).dt.year

anios = sorted(
    casos["anio"]
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)

anio = st.sidebar.selectbox(
    "Año del hecho",
    ["Todos"] + anios
)

filtrados = casos.copy()

if municipio != "Todos":
    filtrados = filtrados[
        filtrados["hecho_municipio"] == municipio
    ]

if anio != "Todos":
    filtrados = filtrados[
        filtrados["anio"] == anio
    ]

seleccion = (
    filtrados[claves]
    .dropna()
    .drop_duplicates()
)

servicios_f = servicios.merge(
    seleccion,
    on=claves,
    how="inner",
    validate="many_to_one"
)

ordenes_f = ordenes.merge(
    seleccion,
    on=claves,
    how="inner",
    validate="many_to_one"
)

agresores_f = agresores.merge(
    seleccion,
    on=claves,
    how="inner",
    validate="many_to_one"
)

kpi = calcular_indicadores(
    filtrados,
    servicios_f,
    ordenes_f,
    agresores_f
)

st.sidebar.divider()
st.sidebar.caption(
    "Los filtros se aplican a los casos "
    "y a sus registros asociados."
)

if kpi["total"] < 10:
    st.warning(
        "La selección contiene menos de 10 casos. "
        "Amplía los filtros para visualizar resultados."
    )
    st.stop()

mostrar_chatbot(
    filtrados,
    servicios_f,
    agresores_f,
    ordenes_f,
    kpi,
    municipio,
    anio
)


def mostrar_conteo(numero):
    if numero < 10:
        return "Reservado"

    return f"{numero:,}"


def mostrar_porcentaje(numero):
    if numero < 10 or kpi["total"] - numero < 10:
        return "Reservado"

    return f"{numero / kpi['total'] * 100:.1f}%"


def grafica(df, columna, titulo):

    if columna not in df.columns:
        st.warning("Variable no disponible")
        return

    conteo = (
        df[columna]
        .fillna("Sin información")
        .value_counts()
        .rename_axis("Categoria")
        .reset_index(name="Registros")
    )

    conteo = conteo[
        conteo["Registros"] >= 10
    ].head(15)

    if conteo.empty:
        st.info("No hay información suficiente.")
        return

    fig = px.bar(
        conteo,
        x="Registros",
        y="Categoria",
        orientation="h",
        text="Registros",
        title=titulo,
        color_discrete_sequence=[color]
    )

    fig.update_layout(
        yaxis={"categoryorder": "total ascending"}
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


if pagina == "Resumen general":

    st.header("Panorama general")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Casos únicos",
        f"{kpi['total']:,}"
    )

    c2.metric(
        "Servicios asociados",
        mostrar_conteo(len(servicios_f))
    )

    c3.metric(
        "Registros de agresores",
        mostrar_conteo(len(agresores_f))
    )

    c4.metric(
        "Órdenes asociadas",
        mostrar_conteo(len(ordenes_f))
    )

    st.divider()

    a, b, c = st.columns(3)

    a.metric(
        "Casos con servicios",
        mostrar_porcentaje(kpi["con_servicios"])
    )

    b.metric(
        "Casos con órdenes",
        mostrar_porcentaje(kpi["con_ordenes"])
    )

    c.metric(
        "Casos sin servicio vinculado",
        mostrar_conteo(kpi["sin_servicios"])
    )

    st.divider()

    tendencia = (
        filtrados
        .dropna(subset=["anio"] + claves)
        .drop_duplicates(claves + ["anio"])
        .groupby("anio")
        .size()
        .reset_index(name="Casos")
    )

    tendencia = tendencia[
        tendencia["Casos"] >= 10
    ]

    if not tendencia.empty:

        fig = px.line(
            tendencia,
            x="anio",
            y="Casos",
            markers=True,
            title="Evolución de casos por año",
            color_discrete_sequence=[color]
        )

        fig.update_xaxes(dtick=1)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    grafica(
        filtrados,
        "ambito_violencia",
        "Ámbitos de violencia registrados"
    )


elif pagina == "Análisis territorial":

    st.header("Distribución territorial")

    grafica(
        filtrados,
        "hecho_municipio",
        "Registros por municipio"
    )


elif pagina == "Patrones de violencia":

    st.header("Patrones de violencia")

    grafica(
        filtrados,
        "ambito_violencia",
        "Ámbitos de violencia"
    )

    edades = pd.to_numeric(
        filtrados["victima_edad"],
        errors="coerce"
    )

    edades = edades.where(
        edades.between(0, 120)
    )

    grupos = pd.cut(
        edades,
        bins=[-1, 11, 17, 29, 44, 59, 120],
        labels=[
            "0-11",
            "12-17",
            "18-29",
            "30-44",
            "45-59",
            "60 o más"
        ]
    )

    tabla = pd.DataFrame({
        "Grupo de edad": grupos.astype("string")
    })

    grafica(
        tabla,
        "Grupo de edad",
        "Distribución por grupos de edad"
    )

    grafica(
        agresores_f,
        "agresores_vinculo",
        "Vínculo registrado con la víctima"
    )


elif pagina == "Atención institucional":

    st.header("Servicios de atención")

    st.metric(
        "Servicios asociados",
        mostrar_conteo(len(servicios_f))
    )

    grafica(
        servicios_f,
        "catalogo_tipo_servicio",
        "Tipos de servicio"
    )

    grafica(
        servicios_f,
        "modalidad_servicios",
        "Modalidades de atención"
    )

    grafica(
        servicios_f,
        "tipo_subservicio",
        "Clasificación de servicios"
    )


elif pagina == "Órdenes de protección":

    st.header("Órdenes de protección")

    st.metric(
        "Casos con órdenes asociadas",
        mostrar_conteo(kpi["con_ordenes"])
    )

    grafica(
        ordenes_f,
        "tipo_ordenes_proteccion",
        "Tipos de órdenes"
    )

    grafica(
        ordenes_f,
        "autoridad_emisora_ordenes_proteccion",
        "Autoridades emisoras"
    )


elif pagina == "Brechas de atención":

    st.header("Vinculación con servicios")

    st.info(
        "Un caso sin servicio asociado no significa "
        "necesariamente que no haya recibido atención."
    )

    a, b = st.columns(2)

    a.metric(
        "Casos con servicio vinculado",
        mostrar_conteo(kpi["con_servicios"])
    )

    b.metric(
        "Casos sin servicio vinculado",
        mostrar_conteo(kpi["sin_servicios"])
    )

    if min(
        kpi["con_servicios"],
        kpi["sin_servicios"]
    ) >= 10:

        resumen = pd.DataFrame({
            "Situacion": [
                "Con servicio vinculado",
                "Sin servicio vinculado"
            ],
            "Casos": [
                kpi["con_servicios"],
                kpi["sin_servicios"]
            ]
        })

        fig = px.pie(
            resumen,
            names="Situacion",
            values="Casos",
            hole=0.55,
            color_discrete_sequence=[
                "#7950B2",
                "#D5C4E8"
            ]
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    tabla = cobertura_municipal(
        filtrados,
        servicios_f
    )

    tabla = tabla[
        (tabla["con_servicios"] >= 10) &
        (tabla["sin_servicios"] >= 10)
    ]

    if not tabla.empty:

        fig = px.bar(
            tabla.head(20),
            x="hecho_municipio",
            y=["con_servicios", "sin_servicios"],
            title="Vinculación de servicios por municipio",
            barmode="stack",
            color_discrete_sequence=[
                "#7950B2",
                "#D5C4E8"
            ]
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.dataframe(
            tabla,
            hide_index=True,
            use_container_width=True
        )


elif pagina == "Atlas territorial":

    mostrar_mapa(filtrados)


elif pagina == "Recomendaciones":

    st.header("Propuestas de intervención")

    st.subheader(
        "1. Fortalecer el seguimiento institucional"
    )

    st.write(
        "Revisar los casos que no cuentan con "
        "servicios asociados en las bases disponibles."
    )

    st.subheader(
        "2. Mejorar la integración de información"
    )

    st.write(
        "Establecer mecanismos de actualización "
        "y vinculación entre dependencias."
    )

    st.subheader(
        "3. Orientar recursos de atención"
    )

    st.write(
        "Evaluar las necesidades municipales "
        "combinando los registros disponibles "
        "con información poblacional y territorial."
    )

    st.subheader(
        "4. Fortalecer las acciones preventivas"
    )

    st.write(
        "Diseñar estrategias de prevención "
        "considerando los ámbitos y patrones "
        "de violencia registrados."
    )


st.divider()

st.caption(
    "Violeta 360 | Prototipo de análisis institucional. "
    "No representa la prevalencia real de violencia. "
    "Se restringen resultados de grupos pequeños. "
    "Uso local y autorizado."
)

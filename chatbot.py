
import streamlit as st
import pandas as pd
import unicodedata


CLAVES = ["euv", "euv_caso"]

UMBRAL = 10

PREGUNTAS = [
    "¿Cuántos casos están registrados?",
    "¿Cómo se distribuyen los casos por año?",
    "¿Qué municipios tienen más registros?",
    "¿Qué ámbitos de violencia aparecen?",
    "¿Cómo se distribuyen las víctimas por edad?",
    "¿Qué vínculos con agresores están registrados?",
    "¿Cómo se distribuyen los agresores por sexo?",
    "¿Qué edades tienen los agresores?",
    "¿Los agresores viven en el mismo domicilio?",
    "¿Cuántos registros de agresores hay?",
    "¿Cuántos servicios están asociados?",
    "¿Qué tipos de servicios se registran?",
    "¿Qué modalidades de atención existen?",
    "¿Cuántos casos tienen órdenes de protección?",
    "¿Qué tipos de órdenes se registran?",
    "¿Qué autoridades emiten las órdenes?",
    "¿Cuántos casos no tienen servicios vinculados?"
]


def normalizar(texto):

    texto = str(texto).lower().strip()

    texto = unicodedata.normalize("NFD", texto)

    return "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )


def fuente(archivo, variables, operacion, municipio, anio):

    filtros = []

    if municipio != "Todos":
        filtros.append(f"Municipio: {municipio}")

    if anio != "Todos":
        filtros.append(f"Año: {anio}")

    if not filtros:
        filtros.append("Sin filtros específicos")

    return (
        "\n\n---\n"
        #"**Fuente de esta respuesta**\n\n"
        #f"- Archivo: `{archivo}`\n"
        #f"- Variables: {variables}\n"
        #f"- Operación: {operacion}\n"
        #f"- Filtros: {'; '.join(filtros)}\n"
        #"- Alcance: registros disponibles en Violeta 360."
    )


def contar_categorias(df, columna, claves=None):

    if columna not in df.columns:
        return None

    datos = df.copy()

    if claves and all(c in datos.columns for c in claves):
        datos = datos.drop_duplicates(
            claves + [columna]
        )

    datos[columna] = (
        datos[columna]
        .fillna("Sin información")
        .astype(str)
        .str.strip()
        .replace("", "Sin información")
    )

    return datos[columna].value_counts()


def contar_casos_unicos(df):

    if not all(c in df.columns for c in CLAVES):
        return 0

    return (
        df[CLAVES]
        .dropna()
        .drop_duplicates()
        .shape[0]
    )


def mostrar_categorias(
    conteo,
    archivo,
    variables,
    operacion,
    municipio,
    anio,
    descripcion,
    unidad="registros"
):

    if conteo is None:
        return "La variable solicitada no está disponible."

    conteo = conteo[conteo >= UMBRAL].head(15)

    if conteo.empty:
        return (
            "No hay suficientes registros para mostrar "
            "esta información respetando la protección "
            "de grupos pequeños."
        )

    resultado = "\n".join(
        f"- **{nombre}:** {cantidad:,} {unidad}"
        for nombre, cantidad in conteo.items()
    )

    return (
        descripcion
        + "\n\n"
        + resultado
        + fuente(
            archivo,
            variables,
            operacion,
            municipio,
            anio
        )
    )


def responder_lia(
    pregunta,
    casos,
    servicios,
    agresores,
    ordenes,
    kpi,
    municipio,
    anio
):

    texto = normalizar(pregunta)

    if any(p in texto for p in [
        "sin servicio",
        "no tienen servicio",
        "sin servicios vinculados"
    ]):

        cantidad = kpi["sin_servicios"]

        if cantidad < UMBRAL:
            return (
                "La cantidad de casos sin servicios vinculados "
                "está protegida por el umbral de visualización."
            )

        return (
            f"Hay **{cantidad:,} casos sin un servicio vinculado** "
            "en los registros disponibles.\n\n"
            "Esto no significa necesariamente que no hayan "
            "recibido atención."
            + fuente(
                "casos.parquet y servicios.parquet",
                "euv, euv_caso",
                "Diferencia entre casos únicos y casos con servicios asociados",
                municipio,
                anio
            )
        )

    if any(p in texto for p in [
        "casos con orden",
        "cuantas ordenes",
        "ordenes asociadas",
        "casos tienen orden"
    ]):

        cantidad = kpi["con_ordenes"]

        if cantidad < UMBRAL:
            return (
                "La cantidad de casos con órdenes asociadas "
                "está protegida por el umbral de visualización."
            )

        return (
            f"Hay **{cantidad:,} casos con órdenes de protección asociadas**."
            + fuente(
                "ordenes.parquet y casos.parquet",
                "euv, euv_caso",
                "Conteo de casos únicos vinculados con órdenes",
                municipio,
                anio
            )
        )

    if any(p in texto for p in [
        "cuantos casos",
        "total de casos",
        "casos registrados"
    ]):

        total = contar_casos_unicos(casos)

        return (
            f"En la selección actual hay **{total:,} casos únicos registrados**."
            + fuente(
                "casos.parquet",
                "euv, euv_caso",
                "Conteo de identificadores únicos de caso",
                municipio,
                anio
            )
        )

    if any(p in texto for p in [
        "por ano",
        "por año",
        "distribucion anual",
        "evolucion"
    ]):

        if "anio" not in casos.columns:
            return "No encuentro la variable de año."

        datos = casos.dropna(
            subset=["anio"] + CLAVES
        )

        datos = datos.drop_duplicates(
            CLAVES + ["anio"]
        )

        conteo = datos.groupby("anio").size()

        conteo = conteo[conteo >= UMBRAL]

        if conteo.empty:
            return (
                "No hay suficientes registros para mostrar "
                "la distribución anual."
            )

        resultado = "\n".join(
            f"- **{int(año)}:** {cantidad:,} casos"
            for año, cantidad in conteo.items()
        )

        return (
            "La distribución de casos registrados por año es:\n\n"
            + resultado
            + fuente(
                "casos.parquet",
                "hecho_fecha, anio, euv, euv_caso",
                "Agrupación por año y conteo de casos únicos",
                municipio,
                anio
            )
        )

    if any(p in texto for p in [
        "municipios",
        "municipio",
        "distribucion territorial",
        "mas registros"
    ]):

        conteo = contar_categorias(
            casos,
            "hecho_municipio",
            CLAVES
        )

        return mostrar_categorias(
            conteo,
            "casos.parquet",
            "hecho_municipio, euv, euv_caso",
            "Agrupación municipal y conteo de casos únicos",
            municipio,
            anio,
            "Estos son los municipios con más casos registrados:",
            "casos"
        )

    if any(p in texto for p in [
        "ambito",
        "tipos de violencia",
        "violencia registrada"
    ]):

        conteo = contar_categorias(
            casos,
            "ambito_violencia",
            CLAVES
        )

        return mostrar_categorias(
            conteo,
            "casos.parquet",
            "ambito_violencia, euv, euv_caso",
            "Agrupación por ámbito y conteo de casos únicos",
            municipio,
            anio,
            "Los ámbitos de violencia registrados son:",
            "casos"
        )

    if any(p in texto for p in [
        "edad de las victimas",
        "edad de victimas",
        "edades de las victimas",
        "grupo de edad",
        "distribucion por edad"
    ]):

        if "victima_edad" not in casos.columns:
            return "No está disponible la edad de las víctimas."

        edades = pd.to_numeric(
            casos["victima_edad"],
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

        datos = casos.copy()

        datos["grupo_edad"] = grupos.astype("string")

        datos = datos.dropna(
            subset=["grupo_edad"] + CLAVES
        )

        datos = datos.drop_duplicates(
            CLAVES + ["grupo_edad"]
        )

        conteo = (
            datos["grupo_edad"]
            .value_counts()
            .sort_index()
        )

        conteo = conteo[conteo >= UMBRAL]

        resultado = "\n".join(
            f"- **{grupo}:** {cantidad:,} casos"
            for grupo, cantidad in conteo.items()
        )

        if conteo.empty:
            return "No hay suficientes registros para mostrar grupos de edad."

        return (
            "La distribución por grupos de edad de las víctimas es:\n\n"
            + resultado
            + fuente(
                "casos.parquet",
                "victima_edad, euv, euv_caso",
                "Clasificación por edad y conteo de casos únicos",
                municipio,
                anio
            )
        )

    if any(p in texto for p in [
        "sexo de los agresores",
        "agresores por sexo",
        "sexo agresor"
    ]):

        conteo = contar_categorias(
            agresores,
            "agresores_sexo"
        )

        return mostrar_categorias(
            conteo,
            "agresores.parquet",
            "agresores_sexo",
            "Conteo de registros por sexo registrado",
            municipio,
            anio,
            "La distribución de los registros de agresores por sexo es:"
        )

    if any(p in texto for p in [
        "edad de los agresores",
        "edades de agresores",
        "agresores por edad"
    ]):

        if "agresores_edad" not in agresores.columns:
            return "No está disponible la edad de los agresores."

        edades = pd.to_numeric(
            agresores["agresores_edad"],
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

        datos = agresores.copy()

        datos["grupo_edad"] = grupos.astype("string")

        conteo = datos["grupo_edad"].value_counts().sort_index()

        conteo = conteo[conteo >= UMBRAL]

        resultado = "\n".join(
            f"- **{grupo}:** {cantidad:,} registros"
            for grupo, cantidad in conteo.items()
        )

        if conteo.empty:
            return "No hay suficientes registros para mostrar grupos de edad."

        return (
            "La distribución por grupos de edad de los registros de agresores es:\n\n"
            + resultado
            + fuente(
                "agresores.parquet",
                "agresores_edad",
                "Clasificación por grupos de edad y conteo de registros",
                municipio,
                anio
            )
        )

    if any(p in texto for p in [
        "mismo domicilio",
        "viven juntos",
        "conviven",
        "domicilio del agresor"
    ]):

        conteo = contar_categorias(
            agresores,
            "agresores_mismo_domicilio"
        )

        return mostrar_categorias(
            conteo,
            "agresores.parquet",
            "agresores_mismo_domicilio",
            "Conteo de registros por condición de domicilio compartido",
            municipio,
            anio,
            "Los registros sobre convivencia en el mismo domicilio son:"
        )

    if any(p in texto for p in [
        "vinculo",
        "relacion con agresores",
        "agresores"
    ]):

        if "agresores_vinculo" not in agresores.columns:
            return "No está disponible la variable de vínculo con agresores."

        conteo = contar_categorias(
            agresores,
            "agresores_vinculo",
            CLAVES
        )

        return mostrar_categorias(
            conteo,
            "agresores.parquet",
            "agresores_vinculo, euv, euv_caso",
            "Conteo de registros por vínculo con el agresor",
            municipio,
            anio,
            "Los vínculos registrados son:",
            "casos vinculados"
        )

    if any(p in texto for p in [
        "cuantos agresores",
        "registros de agresores",
        "total de agresores"
    ]):

        cantidad = len(agresores)

        if cantidad < UMBRAL:
            return "La cantidad está protegida por el umbral de visualización."

        return (
            f"Hay **{cantidad:,} registros de agresores** asociados "
            "a la selección actual.\n\n"
            "Este número representa registros, no necesariamente "
            "personas únicas, porque la base disponible no incluye "
            "un identificador individual de cada agresor."
            + fuente(
                "agresores.parquet",
                "euv, euv_caso",
                "Conteo de filas asociadas a los casos seleccionados",
                municipio,
                anio
            )
        )

    if any(p in texto for p in [
        "cuantos servicios",
        "servicios asociados",
        "total de servicios"
    ]):

        cantidad = len(servicios)

        if cantidad < UMBRAL:
            return "La cantidad de servicios está protegida por el umbral."

        return (
            f"Hay **{cantidad:,} registros de servicios asociados** "
            "a los casos de la selección actual."
            + fuente(
                "servicios.parquet",
                "euv, euv_caso",
                "Conteo de filas de servicios asociadas",
                municipio,
                anio
            )
        )

    if any(p in texto for p in [
        "tipo de servicio",
        "tipos de servicio",
        "clasificacion de servicios"
    ]):

        conteo = contar_categorias(
            servicios,
            "catalogo_tipo_servicio"
        )

        return mostrar_categorias(
            conteo,
            "servicios.parquet",
            "catalogo_tipo_servicio",
            "Conteo de registros por tipo de servicio",
            municipio,
            anio,
            "Los tipos de servicio registrados son:"
        )

    if any(p in texto for p in [
        "modalidad",
        "modalidades de atencion"
    ]):

        conteo = contar_categorias(
            servicios,
            "modalidad_servicios"
        )

        return mostrar_categorias(
            conteo,
            "servicios.parquet",
            "modalidad_servicios",
            "Conteo de registros por modalidad",
            municipio,
            anio,
            "Las modalidades de atención registradas son:"
        )

    if any(p in texto for p in [
        "tipo de orden",
        "tipos de orden",
        "ordenes de proteccion"
    ]):

        conteo = contar_categorias(
            ordenes,
            "tipo_ordenes_proteccion"
        )

        return mostrar_categorias(
            conteo,
            "ordenes.parquet",
            "tipo_ordenes_proteccion",
            "Conteo de registros por tipo de orden",
            municipio,
            anio,
            "Los tipos de órdenes registrados son:"
        )

    if any(p in texto for p in [
        "autoridad",
        "autoridades emisoras",
        "quien emite"
    ]):

        conteo = contar_categorias(
            ordenes,
            "autoridad_emisora_ordenes_proteccion"
        )

        return mostrar_categorias(
            conteo,
            "ordenes.parquet",
            "autoridad_emisora_ordenes_proteccion",
            "Conteo de registros por autoridad emisora",
            municipio,
            anio,
            "Las autoridades emisoras registradas son:"
        )

    return (
        "No puedo responder esa pregunta con las variables "
        "disponibles en Violeta 360.\n\n"
        "Prueba seleccionando una de las preguntas sugeridas."
    )


def mostrar_chatbot(
    casos,
    servicios,
    agresores,
    ordenes,
    kpi,
    municipio,
    anio
):

    contexto = (
        str(municipio),
        str(anio)
    )

    if "contexto_lia" not in st.session_state:
        st.session_state.contexto_lia = contexto

    if st.session_state.contexto_lia != contexto:

        st.session_state.contexto_lia = contexto

        st.session_state.mensajes_lia = [
            {
                "role": "assistant",
                "content": (
                    "Los filtros han cambiado. 💜 "
                    "Ahora consultaré los datos de la nueva selección."
                )
            }
        ]

        st.session_state.pregunta_lia = None

    if "mensajes_lia" not in st.session_state:

        st.session_state.mensajes_lia = [
            {
                "role": "assistant",
                "content": (
                    "¡Hola! 💜 Soy Lía, asistente de Violeta 360.\n\n"
                    "Puedo consultar los casos, servicios, "
                    "agresores y órdenes de protección "
                    "registrados en las bases disponibles.\n\n"
                    "Selecciona una pregunta sugerida o escribe la tuya."
                )
            }
        ]

    if "pregunta_lia" not in st.session_state:
        st.session_state.pregunta_lia = None

    with st.sidebar:

        st.divider()

        st.subheader("💜 Lía | Asistente")

        st.caption(
            "Consultas basadas exclusivamente en los datos disponibles."
        )

        st.caption(
            f"Municipio: {municipio} | Año: {anio}"
        )

        with st.expander(
            "💡 Preguntas que puedes hacer",
            expanded=True
        ):

            for i, pregunta in enumerate(PREGUNTAS):

                if st.button(
                    pregunta,
                    key=f"lia_pregunta_{i}",
                    use_container_width=True
                ):
                    st.session_state.pregunta_lia = pregunta

        for mensaje in st.session_state.mensajes_lia[-6:]:

            with st.chat_message(mensaje["role"]):
                st.markdown(mensaje["content"])

        entrada = st.chat_input(
            "Pregunta sobre los datos...",
            key="entrada_lia"
        )

        pregunta = st.session_state.pregunta_lia

        if pregunta is None:
            pregunta = entrada

        if pregunta:

            st.session_state.pregunta_lia = None

            st.session_state.mensajes_lia.append({
                "role": "user",
                "content": pregunta
            })

            respuesta = responder_lia(
                pregunta,
                casos,
                servicios,
                agresores,
                ordenes,
                kpi,
                municipio,
                anio
            )

            st.session_state.mensajes_lia.append({
                "role": "assistant",
                "content": respuesta
            })

            st.rerun()

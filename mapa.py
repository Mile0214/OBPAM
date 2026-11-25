import streamlit as st
import folium
import pandas as pd
import json
import unicodedata

from pathlib import Path
from streamlit_folium import st_folium


def normalizar(texto):

    texto = str(texto).strip().upper()

    return "".join(
        letra for letra in unicodedata.normalize("NFD", texto)
        if not unicodedata.combining(letra)
    )


def mostrar_mapa(casos):

    st.header("Atlas territorial de Tlaxcala")

    ruta = Path(__file__).resolve().parent
    archivo = ruta / "mapas" / "tlaxcala.geojson"

    if not archivo.exists():
        st.error("Primero ejecuta descargar_mapa.py")
        return

    with open(archivo, encoding="utf-8") as f:
        geojson = json.load(f)

    claves = ["euv", "euv_caso"]

    datos = casos[
        claves + ["hecho_municipio"]
    ].dropna().copy()

    datos["municipio"] = datos[
        "hecho_municipio"
    ].apply(normalizar)

    datos = datos.drop_duplicates(
        claves + ["municipio"]
    )

    # Excluir casos con municipios contradictorios
    cantidad = datos.groupby(claves)[
        "municipio"
    ].transform("nunique")

    datos = datos[cantidad == 1]

    resumen = datos.groupby(
        "municipio"
    ).size().to_dict()

    for municipio in geojson["features"]:

        propiedades = municipio["properties"]

        nombre = normalizar(
            propiedades["nomgeo"]
        )

        total = resumen.get(nombre)

        propiedades["casos"] = (
            str(total)
            if total is not None and total >= 10
            else "Sin dato publicable"
        )

    mapa = folium.Map(
        location=[19.40, -98.17],
        zoom_start=9,
        tiles=None
    )

    def estilo(feature):

        valor = feature["properties"]["casos"]

        if not valor.isdigit():
            color = "#D9D9D9"

        elif int(valor) >= 300:
            color = "#45256A"

        elif int(valor) >= 100:
            color = "#7950B2"

        elif int(valor) >= 50:
            color = "#AF8AD6"

        else:
            color = "#E5D6F5"

        return {
            "fillColor": color,
            "color": "#51465B",
            "weight": 1,
            "fillOpacity": 0.8
        }

    folium.GeoJson(
        geojson,
        name="Casos registrados",
        style_function=estilo,
        highlight_function=lambda x: {
            "weight": 3,
            "color": "#7950B2"
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["nomgeo", "casos"],
            aliases=["Municipio:", "Casos unicos:"]
        )
    ).add_to(mapa)

    folium.LayerControl().add_to(mapa)

    st_folium(
        mapa,
        height=600,
        use_container_width=True,
        returned_objects=[]
    )

    st.markdown("""
    **Simbologia del mapa**

    - Violeta oscuro: 300 casos o mas.
    - Violeta: 100 a 299 casos.
    - Violeta medio: 50 a 99 casos.
    - Violeta claro: 10 a 49 casos.
    - Gris: sin dato publicable.
    """)

    st.caption(
        "Fuente cartografica: INEGI. "
        "Los colores representan casos registrados, "
        "no niveles de peligro ni prevalencia real."
    )
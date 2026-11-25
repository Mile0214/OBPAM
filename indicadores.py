import pandas as pd

claves = ["euv", "euv_caso"]


def casos_unicos(df):

    return df[claves].dropna().drop_duplicates()


def calcular_indicadores(casos, servicios, ordenes, agresores):

    base = casos_unicos(casos)

    total = len(base)

    con_servicios = base.merge(
        casos_unicos(servicios),
        on=claves,
        how="inner"
    )

    con_ordenes = base.merge(
        casos_unicos(ordenes),
        on=claves,
        how="inner"
    )

    con_agresores = base.merge(
        casos_unicos(agresores),
        on=claves,
        how="inner"
    )

    def porcentaje(n):
        return round(n / total * 100, 2) if total else 0

    return {
        "total": total,

        "con_servicios": len(con_servicios),

        "sin_servicios": total - len(con_servicios),

        "porcentaje_servicios":
            porcentaje(len(con_servicios)),

        "con_ordenes": len(con_ordenes),

        "porcentaje_ordenes":
            porcentaje(len(con_ordenes)),

        "con_agresores": len(con_agresores),

        "porcentaje_agresores":
            porcentaje(len(con_agresores))
    }


def cobertura_municipal(casos, servicios):

    datos = casos[
        claves + ["hecho_municipio"]
    ].dropna().drop_duplicates()

    # Excluir claves con municipios contradictorios
    cantidad = datos.groupby(claves)[
        "hecho_municipio"
    ].transform("nunique")

    datos = datos[cantidad == 1]

    servicios_unicos = casos_unicos(servicios)

    servicios_unicos["atendido"] = 1

    datos = datos.merge(
        servicios_unicos,
        on=claves,
        how="left",
        validate="many_to_one"
    )

    datos["atendido"] = datos["atendido"].fillna(0)

    resumen = datos.groupby(
        "hecho_municipio"
    ).agg(
        casos=("euv_caso", "size"),
        con_servicios=("atendido", "sum")
    ).reset_index()

    resumen["sin_servicios"] = (
        resumen["casos"] - resumen["con_servicios"]
    )

    resumen["porcentaje"] = (
        resumen["con_servicios"] /
        resumen["casos"] * 100
    ).round(2)

    return resumen.sort_values(
        "casos", ascending=False
    )
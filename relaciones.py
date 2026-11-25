import pandas as pd
from pathlib import Path

ruta = Path(__file__).resolve().parent / "datos_procesados"

claves = ["euv", "euv_caso"]


def cargar(nombre):
    return pd.read_parquet(ruta / (nombre + ".parquet"))


def claves_validas(df):

    return df[claves].dropna()


def main():

    casos = cargar("casos")
    servicios = cargar("servicios")
    agresores = cargar("agresores")
    ordenes = cargar("ordenes")

    casos_validos = claves_validas(casos)
    casos_unicos = casos_validos.drop_duplicates()

    print("=" * 60)
    print("VALIDACION DE RELACIONES")
    print("=" * 60)

    print("\nTotal de filas de casos:", len(casos))

    print("Claves completas:", len(casos_validos))

    print("Claves de caso unicas:", len(casos_unicos))

    print(
        "Claves repetidas:",
        casos_validos.duplicated().sum()
    )

    print(
        "Registros con claves incompletas:",
        len(casos) - len(casos_validos)
    )

    print(
        "Identificadores euv distintos:",
        casos["euv"].nunique()
    )

    tablas = {
        "SERVICIOS": servicios,
        "AGRESORES": agresores,
        "ORDENES": ordenes
    }

    for nombre, df in tablas.items():

        validos = claves_validas(df)

        relacion = validos.merge(
            casos_unicos,
            on=claves,
            how="left",
            indicator=True,
            validate="many_to_one"
        )

        asociados = relacion[
            relacion["_merge"] == "both"
        ]

        sin_asociar = relacion[
            relacion["_merge"] == "left_only"
        ]

        print("\n" + "-" * 50)
        print(nombre)
        print("Total de registros:", len(df))
        print("Registros relacionados:", len(asociados))

        print(
            "Registros sin caso asociado:",
            len(sin_asociar)
        )

        print(
            "Registros con clave incompleta:",
            len(df) - len(validos)
        )

        print(
            "Casos distintos asociados:",
            len(asociados[claves].drop_duplicates())
        )


if __name__ == "__main__":
    main()

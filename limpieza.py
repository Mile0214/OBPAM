import pandas as pd
from pathlib import Path
import unicodedata

base = Path(__file__).resolve().parent
entrada = base / "datos"
salida = base / "datos_procesados"

salida.mkdir(exist_ok=True)

violencias = [
    "psicologica", "fisica", "sexual",
    "economica", "patrimonial", "vicaria",
    "feminicida", "otra_violencia"
]

columnas = {
    "casos": [
        "euv", "euv_caso", "victima_edad",
        "hecho_municipio", "hecho_entidad",
        "hecho_fecha", "ambito_violencia"
    ] + violencias,

    "servicios": [
        "euv", "euv_caso",
        "fecha_atencion",
        "catalogo_tipo_servicio",
        "tipo_subservicio",
        "modalidad_servicios",
        "hecho_municipio"
    ],

    "agresores": [
        "euv", "euv_caso",
        "agresores_edad",
        "agresores_sexo",
        "agresores_vinculo",
        "agresores_mismo_domicilio"
    ],

    "ordenes": [
        "euv", "euv_caso",
        "tipo_ordenes_proteccion",
        "autoridad_emisora_ordenes_proteccion",
        "ordenes_proteccion_fecha_inicio",
        "ordenes_proteccion_fecha_emision",
        "ordenes_proteccion_municipio"
    ]
}


def normalizar(texto):

    texto = str(texto).strip().lower()

    texto = unicodedata.normalize("NFKD", texto)

    texto = "".join(
        letra for letra in texto
        if not unicodedata.combining(letra)
    )

    return texto.replace(" ", "_")


def identificar_archivo(nombre):

    nombre = nombre.lower()

    if nombre.startswith("casos"):
        return "casos"

    if nombre.startswith("servicios"):
        return "servicios"

    if nombre.startswith("p_agresora"):
        return "agresores"

    if nombre.startswith("ordenes"):
        return "ordenes"

    return None


def limpiar(archivo, tipo):

    print("\nProcesando:", archivo.name)

    df = pd.read_excel(archivo, dtype="string")

    df.columns = [
        normalizar(c) for c in df.columns
    ]

    print("Registros originales:", len(df))
    print("Columnas originales:", len(df.columns))

    print("Duplicados exactos:", df.duplicated().sum())

    disponibles = [
        c for c in columnas[tipo]
        if c in df.columns
    ]

    faltantes = [
        c for c in columnas[tipo]
        if c not in df.columns
    ]

    if faltantes:
        print("Columnas no encontradas:", faltantes)

    if not disponibles:
        raise ValueError("No hay columnas compatibles")

    df = df[disponibles].copy()

    for c in df.columns:

        df[c] = df[c].str.strip()

        df[c] = df[c].replace({
            "": pd.NA,
            "NULL": pd.NA,
            "null": pd.NA,
            "N/A": pd.NA
        })

        if c in [
            "hecho_fecha",
            "fecha_atencion",
            "ordenes_proteccion_fecha_inicio",
            "ordenes_proteccion_fecha_emision"
        ]:

            original = df[c].notna().sum()

            df[c] = pd.to_datetime(
                df[c],
                errors="coerce",
                format="mixed",
                dayfirst=True
            )

            print(
                "Fechas no interpretadas en", c,
                original - df[c].notna().sum()
            )

        elif c in ["victima_edad", "agresores_edad"]:

            df[c] = pd.to_numeric(
                df[c], errors="coerce"
            )

    destino = salida / (tipo + ".parquet")

    df.to_parquet(destino, index=False)

    print("Registros conservados:", len(df))
    print("Columnas seleccionadas:", len(df.columns))
    print("Archivo generado:", destino.name)


def main():

    print("=" * 60)
    print("VIOLETA 360 - PROCESAMIENTO DE DATOS")
    print("=" * 60)

    archivos = {}

    for archivo in entrada.glob("*.xlsx"):

        if archivo.name.startswith("~$"):
            continue

        tipo = identificar_archivo(archivo.name)

        if tipo:
            archivos.setdefault(tipo, []).append(archivo)

    if not archivos:
        print("No se encontraron archivos compatibles.")
        return

    for tipo, encontrados in archivos.items():

        if len(encontrados) != 1:
            print("Hay varios archivos para:", tipo)
            print("Conserva solamente la version que deseas usar.")
            continue

        try:
            limpiar(encontrados[0], tipo)

        except Exception as error:
            print("Error en", tipo, ":", error)

    print("\nProcesamiento terminado.")
    print("Revisa los mensajes anteriores.")


if __name__ == "__main__":
    main()
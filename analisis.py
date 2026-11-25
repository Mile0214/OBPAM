import pandas as pd
from pathlib import Path

# Ubicacion de las carpetas
base = Path(__file__).resolve().parent
carpeta = base / "datos"
salida = base / "datos_procesados"

carpeta.mkdir(exist_ok=True)
salida.mkdir(exist_ok=True)


def analizar_archivo(archivo):

    print("\n" + "=" * 65)
    print("ARCHIVO:", archivo.name)
    print("=" * 65)

    resultados = []

    try:
        with pd.ExcelFile(archivo) as excel:

            print("Hojas disponibles:", excel.sheet_names)

            for hoja in excel.sheet_names:

                df = pd.read_excel(excel, sheet_name=hoja)

                print("\nHOJA:", hoja)
                print("-" * 50)

                print("Cantidad de registros:", len(df))
                print("Cantidad de columnas:", len(df.columns))

                print("\nCOLUMNAS DISPONIBLES:")

                for columna in df.columns:
                    print("-", columna)

                print("\nTIPOS DE DATOS:")
                print(df.dtypes)

                print("\nVALORES FALTANTES:")

                faltantes = pd.DataFrame({
                    "Columna": df.columns,
                    "Tipo": df.dtypes.astype(str).values,
                    "Faltantes": df.isnull().sum().values,
                    "Porcentaje": (
                        df.isnull().mean() * 100
                    ).round(2).values,
                    "Valores unicos": df.nunique().values
                })

                print(faltantes.to_string(index=False))

                duplicados = df.duplicated().sum()

                print("\nPosibles registros duplicados:", duplicados)

                numericas = df.select_dtypes(include="number")

                if not numericas.empty:
                    print("\nESTADISTICAS NUMERICAS:")
                    print(numericas.describe().round(2))

                faltantes["Archivo"] = archivo.name
                faltantes["Hoja"] = hoja
                faltantes["Registros"] = len(df)

                resultados.append(faltantes)

    except Exception as error:
        print("Error al analizar el archivo:", error)

    return resultados


def main():

    print("=" * 65)
    print("DATATHON 2026 - ANALISIS PRELIMINAR")
    print("=" * 65)

    archivos = [
        archivo for archivo in carpeta.glob("*.xlsx")
        if not archivo.name.startswith("~$")
    ]

    if not archivos:
        print("\nNo se encontraron archivos Excel.")
        print("Coloca los archivos dentro de la carpeta datos.")
        return

    print("\nArchivos encontrados:", len(archivos))

    resultados_totales = []

    for archivo in archivos:

        resultados = analizar_archivo(archivo)
        resultados_totales.extend(resultados)

    if resultados_totales:

        reporte = pd.concat(
            resultados_totales,
            ignore_index=True
        )

        ruta = salida / "reporte_preliminar.xlsx"

        reporte.to_excel(ruta, index=False)

        print("\n" + "=" * 65)
        print("ANALISIS FINALIZADO")
        print("Reporte generado en:", ruta)
        print("=" * 65)


if __name__ == "__main__":
    main()

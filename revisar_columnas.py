
import pandas as pd
from pathlib import Path
import unicodedata

ruta = Path(__file__).resolve().parent / "datos"

palabras = [
    "denuncia",
    "municipio",
    "institucion",
    "fiscalia",
    "ministerio",
    "receptor",
    "agencia",
    "unidad",
    "registro",
    "atencion",
    "lugar",
    "dependencia"
]

def normalizar(texto):
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(
        letra for letra in texto
        if not unicodedata.combining(letra)
    )

for archivo in ruta.glob("*.xlsx"):
    print("\n" + "=" * 65)
    print("ARCHIVO:", archivo.name)
    print("=" * 65)

    columnas = pd.read_excel(archivo, nrows=0).columns

    encontradas = [
        columna for columna in columnas
        if any(p in normalizar(columna) for p in palabras)
    ]

    if encontradas:
        for columna in encontradas:
            print(columna)
    else:
        print("No se encontraron columnas candidatas.")

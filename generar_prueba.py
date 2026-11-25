import pandas as pd
from pathlib import Path

datos = {
    "id_caso": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "municipio": [
        "Tlaxcala", "Apizaco", "Zacatelco",
        "Huamantla", "Tlaxcala", "Apizaco",
        "Chiautempan", "Zacatelco", "Huamantla",
        "Tlaxcala"
    ],
    "edad": [
        24, 35, 19, 42, None,
        28, 31, 22, 45, 26
    ],
    "tipo_violencia": [
        "Psicologica", "Fisica", "Economica",
        "Psicologica", "Fisica", "Psicologica",
        "Economica", "Fisica", "Psicologica",
        "Economica"
    ],
    "anio": [
        2023, 2024, 2024, 2025, 2025,
        2025, 2026, 2026, 2026, 2026
    ],
    "orden_proteccion": [
        "Si", "Si", "No", "No", "Si",
        "No", "No", "Si", "No", "Si"
    ],
    "servicio": [
        "Psicologico", "Juridico", "Juridico",
        "Psicologico", "Medico", "Psicologico",
        None, "Medico", "Psicologico", "Juridico"
    ]
}

df = pd.DataFrame(datos)

carpeta = Path(__file__).resolve().parent / "datos"
carpeta.mkdir(exist_ok=True)

df.to_excel(
    carpeta / "casos_prueba.xlsx",
    index=False
)

print("Archivo Excel de prueba generado correctamente.")

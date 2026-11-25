import requests
import json
from pathlib import Path

url = "https://gaia.inegi.org.mx/wscatgeo/v2/geo/mgem/29"

carpeta = Path(__file__).resolve().parent / "mapas"
carpeta.mkdir(exist_ok=True)

respuesta = requests.get(url, timeout=90)
respuesta.raise_for_status()

datos = respuesta.json()

if datos.get("type") != "FeatureCollection":
    raise ValueError("La respuesta no es un GeoJSON valido")

destino = carpeta / "tlaxcala.geojson"

with open(destino, "w", encoding="utf-8") as archivo:
    json.dump(datos, archivo, ensure_ascii=False)

print("Mapa descargado correctamente")
print("Municipios encontrados:", len(datos["features"]))
print("Archivo guardado en:", destino)
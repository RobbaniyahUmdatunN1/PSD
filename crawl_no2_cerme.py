"""
Crawling Data NO2 (Sentinel-5P) - Kecamatan Cerme, Gresik
Tugas 3 - Proyek Sains Data

Cara pakai:
1. Pastikan file 'cerme-boundary.geojson' (hasil download dari batas-admin.geoit.dev)
   ada di folder yang sama dengan script ini.
2. pip install earthengine-api pandas
3. Jalankan: python crawl_no2_cerme.py
4. Hasil akan tersimpan di: mystorage/NO2-Cerme.csv
"""

import json
import os
import ee
import pandas as pd

# 1. INISIALISASI EARTH ENGINE
EE_PROJECT_ID = "tugas-psd-gresik"

try:
    ee.Initialize(project=EE_PROJECT_ID)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=EE_PROJECT_ID)

# 2. BACA BOUNDARY
GEOJSON_PATH = "cerme-boundary.geojson"

with open(GEOJSON_PATH, "r") as f:
    geojson_data = json.load(f)

if geojson_data["type"] == "FeatureCollection":
    geom = geojson_data["features"][0]["geometry"]
else:
    geom = geojson_data


def strip_z(coords):
    """Buang dimensi ke-3 (elevasi) dari koordinat, sisakan cuma [lon, lat]."""
    if isinstance(coords[0], (int, float)):
        return coords[:2]
    return [strip_z(c) for c in coords]


geom["coordinates"] = strip_z(geom["coordinates"])

boundary = ee.Geometry(geom)

# 3. RENTANG WAKTU
START_DATE = "2025-08-31"
END_DATE = "2026-08-31"

# 4. AMBIL DATA NO2 DARI SENTINEL-5P
COLLECTION_ID = "COPERNICUS/S5P/OFFL/L3_NO2"
BAND = "tropospheric_NO2_column_number_density"

coll = (
    ee.ImageCollection(COLLECTION_ID)
    .filterDate(START_DATE, END_DATE)
    .filterBounds(boundary)
    .select(BAND)
)


def reduce_image(img):
    stats = img.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=boundary,
        scale=1000,
        maxPixels=1e9,
    )
    date = img.date().format("YYYY-MM-dd")
    return ee.Feature(None, {"date": date, "NO2": stats.get(BAND)})


features = coll.map(reduce_image).filter(ee.Filter.notNull(["NO2"]))

print("Mengambil data NO2 dari Google Earth Engine, mohon tunggu...")
result = features.getInfo()["features"]

rows = [
    {"date": f["properties"]["date"], "NO2": f["properties"]["NO2"]}
    for f in result
]

df = pd.DataFrame(rows)
df = df.groupby("date", as_index=False)["NO2"].mean()
df = df.sort_values("date").reset_index(drop=True)

print(f"Berhasil mengambil {len(df)} baris data NO2.")

# 5. SIMPAN KE FOLDER mystorage/
os.makedirs("mystorage", exist_ok=True)
OUTPUT_PATH = "mystorage/NO2-Cerme.csv"
df.to_csv(OUTPUT_PATH, index=False)

print(f"Selesai! Data tersimpan di: {OUTPUT_PATH}")
print(df.head())

"""
Crawling Data Polutan (Sentinel-5P) - Wilayah Gresik
Tugas 1 - Proyek Sains Data

Nama: Robbaniyah Umdatun Ni'mah
NIM: 240411100101

Parameter yang diambil (sesuai instruksi dosen):
    CO, NO2, HCHO, O3, SO2, CH4
Sumber data: Copernicus Sentinel-5P TROPOMI (via Google Earth Engine)
Rentang waktu: 1 Sept 2024 - 31 Agustus 2025 (>= 1 tahun sebelum 31 Agustus)
"""

import json
import ee
import pandas as pd

# 1. INISIALISASI EARTH ENGINE
EE_PROJECT_ID = "tugas-psd-gresik" 
try: ee.Initialize(project=EE_PROJECT_ID) 
except Exception: 
    ee.Authenticate() 
    ee.Initialize(project=EE_PROJECT_ID)

# 2. BACA BOUNDARY DARI GEOJSON.IO
GEOJSON_PATH = "gresik_boundary.geojson"

with open(GEOJSON_PATH, "r") as f:
    geojson_data = json.load(f)

# Ambil geometry dari feature pertama (kalau geojson.io menghasilkan FeatureCollection)
if geojson_data["type"] == "FeatureCollection":
    geom = geojson_data["features"][0]["geometry"]
else:
    geom = geojson_data

boundary = ee.Geometry(geom)
centroid = boundary.centroid(maxError=1).coordinates().getInfo()  # [lon, lat]

# 3. KONFIGURASI RENTANG WAKTU
START_DATE = "2024-09-01"
END_DATE = "2025-08-31"

# 4. DEFINISI DATASET & BAND SENTINEL-5P PER POLUTAN
POLLUTANTS = {
    "CO": {
        "collection": "COPERNICUS/S5P/OFFL/L3_CO",
        "band": "CO_column_number_density",
    },
    "NO2": {
        "collection": "COPERNICUS/S5P/OFFL/L3_NO2",
        "band": "tropospheric_NO2_column_number_density",
    },
    "HCHO": {
        "collection": "COPERNICUS/S5P/OFFL/L3_HCHO",
        "band": "tropospheric_HCHO_column_number_density",
    },
    "O3": {
        "collection": "COPERNICUS/S5P/OFFL/L3_O3",
        "band": "O3_column_number_density",
    },
    "SO2": {
        "collection": "COPERNICUS/S5P/OFFL/L3_SO2",
        "band": "SO2_column_number_density",
    },
    "CH4": {
        "collection": "COPERNICUS/S5P/OFFL/L3_CH4",
        "band": "CH4_column_volume_mixing_ratio_dry_air",
    },
}


def get_daily_mean_series(collection_id, band, boundary, start, end):
    """
    Ambil rata-rata harian sebuah band dalam boundary tertentu,
    dikembalikan sebagai list of dict: {date, value}
    """
    coll = (
        ee.ImageCollection(collection_id)
        .filterDate(start, end)
        .filterBounds(boundary)
        .select(band)
    )

    def reduce_image(img):
        stats = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=boundary,
            scale=1000,
            maxPixels=1e9,
        )
        date = img.date().format("YYYY-MM-dd")
        return ee.Feature(
            None, {"date": date, "value": stats.get(band)}
        )

    features = coll.map(reduce_image).filter(
        ee.Filter.notNull(["value"])
    )

    # getInfo() menarik data dari server GEE ke Python
    result = features.getInfo()["features"]
    return [
        {"date": f["properties"]["date"], "value": f["properties"]["value"]}
        for f in result
    ]

 
# 5. TARIK DATA UNTUK SEMUA POLUTAN
all_data = {}

for name, info in POLLUTANTS.items():
    print(f"Mengambil data {name} ...")
    series = get_daily_mean_series(
        info["collection"], info["band"], boundary, START_DATE, END_DATE
    )
    df = pd.DataFrame(series).rename(columns={"value": name})
    df = df.groupby("date", as_index=False)[name].mean()  # gabung kalau ada duplikat tanggal
    all_data[name] = df
    print(f"  -> {len(df)} titik data ditemukan")

# 6. GABUNGKAN SEMUA POLUTAN JADI SATU TABEL (MERGE BY DATE)
merged = None
for name, df in all_data.items():
    merged = df if merged is None else pd.merge(merged, df, on="date", how="outer")

merged = merged.sort_values("date").reset_index(drop=True)
merged.insert(1, "longitude", centroid[0])
merged.insert(2, "latitude", centroid[1])

# 7. SIMPAN KE CSV
OUTPUT_PATH = "gresik_pollutant_data.csv"
merged.to_csv(OUTPUT_PATH, index=False)
print(f"\nSelesai! Data tersimpan di: {OUTPUT_PATH}")
print(merged.head())
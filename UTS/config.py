"""Konfigurasi bersama: kelas, fitur, rumus, dan teks deskripsi.
Dipakai oleh train_models.py, predict_map.py, build_static_web.py, dan app.py
supaya isi aplikasi Streamlit dan web statis selalu konsisten."""
from pathlib import Path

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
RESULT_DIR = ROOT / "results"
MODEL_DIR = ROOT / "models"
STATIC_DIR = ROOT / "static_web"

POLYGON_FILE = DATA_DIR / "training_polygons.geojson"
SAMPLES_CSV = DATA_DIR / "training_samples.csv"
RASTER_DIR = DATA_DIR / "raster"
RESULTS_JSON = RESULT_DIR / "results.json"
MAP_PNG = RESULT_DIR / "klasifikasi_jatim.png"
MAP_META = RESULT_DIR / "map_meta.json"
MODEL_FILE = MODEL_DIR / "best_model.joblib"

# ---------------------------------------------------------------- KELAS
# (class_id, nama, warna, file sumber, padanan dalam klasifikasi penutup lahan Indonesia)
CLASSES = [
    (1, "Sawah", "#f4d03f", "sawah_Jawa_Timur.geojson",
     "Sawah (pertanian lahan basah) - kelas 'Sawah' KLHK"),
    (2, "Bangunan", "#e74c3c", "bangunan.geojson",
     "Permukiman / lahan terbangun - kelas 'Permukiman' KLHK; 'Daerah terbangun' SNI 7645"),
    (3, "Mangrove", "#145a32", "Mangrove.geojson",
     "Hutan mangrove (primer/sekunder) - kelas 'Hutan Mangrove' KLHK"),
    (4, "Lahan Hijau", "#58d68d", "Lahan_ijo2.geojson",
     "Gabungan vegetasi non-sawah: hutan lahan kering, perkebunan, pertanian lahan kering, "
     "semak belukar, padang rumput"),
    (5, "Perairan Terbuka (Laut)", "#1f4e9c", "Laut.geojson",
     "Tubuh air - perairan laut (SNI 7645: 'Perairan')"),
    (6, "Danau (Ranu)", "#00bcd4", "Danau.geojson",
     "Tubuh air - perairan darat/danau (SNI 7645: 'Perairan')"),
]
CLASS_IDS = [c[0] for c in CLASSES]
CLASS_NAMES = {c[0]: c[1] for c in CLASSES}
CLASS_COLORS = {c[0]: c[2] for c in CLASSES}

# ---------------------------------------------------------------- FITUR
BANDS = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]
INDICES = ["NDVI", "NDWI", "MNDWI", "NDBI", "NDMI", "EVI", "SAVI", "MVI"]
FEATURES = BANDS + INDICES  # urutan ini HARUS sama dengan urutan band di GeoTIFF GEE

# batas nilai agar indeks berbentuk rasio tidak meledak (pembagi mendekati nol)
CLIP = {"MVI": (-20.0, 20.0), "EVI": (-2.0, 3.0)}
NODATA = -9999.0


def clip_features(df):
    """Terapkan batas nilai pada kolom indeks (DataFrame atau dict kolom)."""
    for col, (lo, hi) in CLIP.items():
        if col in df:
            df[col] = df[col].clip(lo, hi)
    return df


# ---------------------------------------------------------------- TEKS
TUJUAN = [
    "Memetakan penutup/penggunaan lahan (land use & land cover, LULC) Provinsi Jawa Timur "
    "dari citra Sentinel-2A menjadi 6 kelas: sawah, bangunan, mangrove, lahan hijau, "
    "perairan terbuka (laut), dan danau (ranu).",
    "Membandingkan beberapa algoritma klasifikasi terbimbing (Random Forest sebagai baseline, "
    "XGBoost, LightGBM, SVM, dll.) dan memilih model dengan akurasi tertinggi.",
    "Menyajikan hasil klasifikasi sebagai sistem informasi geografis berbasis web "
    "(Folium/Leaflet di Streamlit) di atas basemap satelit Google, sebagai dasar analisis spasial "
    "penggunaan lahan dan kebijakan tata ruang (mis. pemantauan alih fungsi sawah, "
    "perlindungan mangrove, dan kawasan terbangun).",
]

S2_BANDS = [  # (band, nama, panjang gelombang S2A nm, resolusi m, kegunaan, dipakai?)
    ("B1", "Coastal aerosol", 442.7, 60, "Koreksi aerosol atmosfer, perairan pesisir", False),
    ("B2", "Blue", 492.4, 10, "Pembeda air jernih, tanah, vegetasi; penyusun EVI", True),
    ("B3", "Green", 559.8, 10, "Puncak pantulan vegetasi hijau; NDWI/MNDWI/MVI", True),
    ("B4", "Red", 664.6, 10, "Penyerapan klorofil; NDVI/EVI/SAVI", True),
    ("B5", "Vegetation red edge 1", 704.1, 20, "Kondisi/kandungan klorofil vegetasi", True),
    ("B6", "Vegetation red edge 2", 740.5, 20, "Struktur kanopi, pembeda tipe vegetasi", True),
    ("B7", "Vegetation red edge 3", 782.8, 20, "Struktur kanopi, biomassa", True),
    ("B8", "NIR", 832.8, 10, "Pantulan tinggi vegetasi, serapan air", True),
    ("B8A", "Narrow NIR", 864.7, 20, "NIR sempit, sensitif terhadap vegetasi", True),
    ("B9", "Water vapour", 945.1, 60, "Koreksi uap air atmosfer", False),
    ("B10", "SWIR - Cirrus", 1373.5, 60, "Deteksi awan cirrus (tidak ada di produk L2A)", False),
    ("B11", "SWIR 1", 1613.7, 20, "Kadar air tanah/vegetasi, lahan terbangun; NDBI/MNDWI/NDMI", True),
    ("B12", "SWIR 2", 2202.4, 20, "Pembeda tanah terbuka, lahan terbangun, air", True),
]

# (nama, rumus teks, keterangan)
INDEX_INFO = [
    ("NDVI", "(B8 - B4) / (B8 + B4)",
     "Normalized Difference Vegetation Index. Tinggi pada vegetasi lebat (mangrove, lahan hijau), "
     "rendah/negatif pada air dan bangunan."),
    ("NDWI", "(B3 - B8) / (B3 + B8)",
     "Normalized Difference Water Index (McFeeters). Positif pada badan air."),
    ("MNDWI", "(B3 - B11) / (B3 + B11)",
     "Modified NDWI (Xu). Lebih baik memisahkan air dari lahan terbangun."),
    ("NDBI", "(B11 - B8) / (B11 + B8)",
     "Normalized Difference Built-up Index. Tinggi pada area terbangun."),
    ("NDMI", "(B8 - B11) / (B8 + B11)",
     "Normalized Difference Moisture Index. Kelembapan vegetasi; membantu pembeda sawah tergenang."),
    ("EVI", "2.5 * (B8 - B4) / (B8 + 6*B4 - 7.5*B2 + 1)",
     "Enhanced Vegetation Index. Tidak mudah jenuh pada vegetasi rapat; reflektansi skala 0-1."),
    ("SAVI", "1.5 * (B8 - B4) / (B8 + B4 + 0.5)",
     "Soil Adjusted Vegetation Index (L = 0,5). Mengurangi pengaruh latar tanah."),
    ("MVI", "(B8 - B3) / (B11 - B3)",
     "Mangrove Vegetation Index (Baloloy dkk., 2020). Menonjolkan mangrove terhadap vegetasi lain. "
     "Nilai dibatasi -20 s.d. 20."),
]

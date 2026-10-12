# UTS Proyek Sains Data - Klasifikasi LULC Jawa Timur (Sentinel-2A)

6 kelas: Sawah, Bangunan, Mangrove, Lahan Hijau, Perairan Terbuka (Laut), Danau (Ranu).

## Struktur
| File | Fungsi |
|---|---|
| `data/training_polygons_shp.zip` | Shapefile (dibuat `make_shapefile.py`) untuk upload ke GEE lewat Table upload > Shape files |
| `data/training_polygons.geojson` | 6 GeoJSON mentah digabung (360 poligon, atribut class_id/class_name/poly_id) |
| `gee/01_ekstraksi_sampel_dan_fitur.js` | Skrip GEE: komposit Sentinel-2A, 10 band + 8 indeks, ekstraksi titik, export CSV + GeoTIFF |
| `train_models.py` | Bandingkan 8 model, split per poligon, GroupKFold-CV, pilih terbaik, eksperimen jumlah data |
| `predict_map.py` | Terapkan model ke raster Jawa Timur -> PNG overlay + GeoTIFF + luas kelas |
| `build_static_web.py` | Bangun `static_web/proses.html` (HTML mandiri, seluruh proses + hasil) |
| `build_book_chapter.py` | Bangun `klasifikasi_lulc.md`, bab untuk Jupyter Book (daftarkan di `_toc.yml`) |
| `app.py` | Aplikasi Streamlit (Folium + basemap satelit Google) |
| `config.py` | Kelas, fitur, rumus, deskripsi band (dipakai semua skrip) |

## Langkah menjalankan
1. **GEE**: upload `data/training_polygons_shp.zip` sebagai asset (Assets > NEW > Table upload > Shape files), ganti
   `ASSET_POLYGON` di skrip JS, Run, lalu jalankan 2 task di tab *Tasks*.
2. Unduh dari Google Drive (folder `GEE_UTS`): CSV -> `data/training_samples.csv`, GeoTIFF -> `data/raster/`.
3. `pip install -r requirements-train.txt`
4. `python train_models.py`   (hasil: `results/results.json`, grafik, `models/best_model.joblib`)
5. `python predict_map.py`    (hasil: `results/klasifikasi_jatim.png`, `map_meta.json`)
6. `python build_static_web.py`
7. `streamlit run app.py`

## Deploy Streamlit Community Cloud
Push ke GitHub dengan: `app.py`, `config.py`, `requirements.txt`, `data/training_polygons.geojson`,
`results/` (results.json, PNG, map_meta.json), `static_web/`. Raster, CSV, dan model tidak perlu di-push
(app hanya membaca hasil). Pilih `app.py` sebagai main file.

## Eksperimen yang bisa kamu ubah
- `N_PER_POLY` di skrip GEE (25/50/100) -> jumlah data per kelas; `train_models.py` otomatis membuat tabel
  akurasi vs jumlah data latih.
- `PREDICT_SCALE` (250 m default) -> makin kecil makin detail, file makin besar.
- `--no-balance` di `train_models.py` untuk membandingkan dengan/tanpa penyeimbangan kelas.

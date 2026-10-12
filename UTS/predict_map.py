"""Terapkan model terbaik ke raster fitur Jawa Timur (hasil export GEE).

Keluaran:
  results/klasifikasi_jatim.png   -> overlay RGBA untuk Folium (nodata transparan)
  results/klasifikasi_jatim.tif   -> GeoTIFF kelas (uint8, 0 = nodata) untuk QGIS
  results/map_meta.json           -> bounds peta + luas tiap kelas (ha)
"""
import argparse, json
from glob import glob
from pathlib import Path
import numpy as np
import joblib
from PIL import Image
import rasterio
from rasterio.merge import merge

import config as C


def read_stack(raster_dir):
    files = sorted(glob(str(raster_dir / "*.tif")))
    if not files:
        raise SystemExit(f"Tidak ada .tif di {raster_dir}. Unduh hasil export GEE ke folder itu.")
    print(f"{len(files)} file raster ditemukan")
    srcs = [rasterio.open(f) for f in files]
    if len(srcs) == 1:
        data, transform = srcs[0].read(), srcs[0].transform
    else:  # GEE memecah file besar menjadi beberapa tile
        data, transform = merge(srcs, nodata=C.NODATA)
    crs = srcs[0].crs
    for s in srcs:
        s.close()
    return data.astype("float32"), transform, crs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raster-dir", default=str(C.RASTER_DIR))
    ap.add_argument("--chunk", type=int, default=200_000)
    args = ap.parse_args()

    bundle = joblib.load(C.MODEL_FILE)
    model, feats = bundle["model"], bundle["features"]
    data, transform, crs = read_stack(Path(args.raster_dir))
    nb, H, W = data.shape
    if nb != len(feats):
        raise SystemExit(f"Jumlah band raster ({nb}) != jumlah fitur model ({len(feats)}). "
                         f"Pastikan urutan band = {feats}")
    print(f"Raster {W}x{H} piksel, {nb} band")
    print("CRS:", crs)
    print("Transform:", transform)
    print("Pixel size deg:", abs(transform.a))

    X = data.reshape(nb, -1).T                       # (piksel, fitur)
    nodata = (X == C.NODATA).any(axis=1)
    X = np.where(np.isfinite(X), X, 0.0)             # NaN/inf (mis. 0/0 pada MVI) -> 0 lalu di-clip
    for col, (lo, hi) in C.CLIP.items():
        j = feats.index(col)
        X[:, j] = np.clip(X[:, j], lo, hi)

    out = np.zeros(X.shape[0], dtype="uint8")
    valid = np.where(~nodata)[0]
    for s in range(0, len(valid), args.chunk):
        idx = valid[s:s + args.chunk]
        out[idx] = model.predict(X[idx]).astype("int64") + 1   # kembali ke class_id 1..K
        print(f"  prediksi {min(s + args.chunk, len(valid))}/{len(valid)}", end="\r")
    print()
    out = out.reshape(H, W)

    # --- PNG RGBA
    rgba = np.zeros((H, W, 4), dtype="uint8")
    for cid, color in C.CLASS_COLORS.items():
        rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
        rgba[out == cid] = (*rgb, 255)
    Image.fromarray(rgba).save(C.MAP_PNG)

    # --- GeoTIFF kelas
    with rasterio.open(C.RESULT_DIR / "klasifikasi_jatim.tif", "w", driver="GTiff", height=H, width=W,
                       count=1, dtype="uint8", crs=crs, transform=transform, nodata=0, compress="lzw") as dst:
        dst.write(out, 1)

    # --- bounds & luas (CRS EPSG:4326: ukuran piksel derajat -> meter per baris lintang)
    west, north = transform * (0, 0)
    east, south = transform * (W, H)
    lat_rows = north + transform.e * (np.arange(H) + 0.5)
    px_area_m2 = (abs(transform.a) * 111320 * np.cos(np.radians(lat_rows))) * (abs(transform.e) * 110574)
    stats = {}
    for cid in C.CLASS_IDS:
        n_row = (out == cid).sum(axis=1)
        stats[C.CLASS_NAMES[cid]] = {"piksel": int(n_row.sum()),
                                     "luas_ha": round(float((n_row * px_area_m2).sum() / 1e4), 1)}
    meta = {"bounds": [[south, west], [north, east]], "width": W, "height": H,
            "pixel_size_deg": abs(transform.a), "class_stats": stats}
    json.dump(meta, open(C.MAP_META, "w"), indent=2, ensure_ascii=False)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    print(f"Tersimpan: {C.MAP_PNG}, klasifikasi_jatim.tif, {C.MAP_META}")


if __name__ == "__main__":
    main()
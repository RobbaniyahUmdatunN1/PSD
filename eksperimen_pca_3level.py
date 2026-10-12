"""
Eksperimen Reduksi Dimensi (PCA: 203, 74, 37) + K-Means + Silhouette + Peta Cluster

Untuk dataset gabungan 1 kelas (204 fitur: CO/NO2/SO2 x 68 fitur TSFEL).
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# ------------------------------------------------------------------
# GANTI SESUAI FILE KAMU
# ------------------------------------------------------------------
import sys
# Cara pakai:  python eksperimen_pca_3level.py <file_csv> <tag>
# Contoh:      python eksperimen_pca_3level.py ekstraksi_fitur_linear.csv linear
INPUT_CSV = sys.argv[1] if len(sys.argv) > 1 else "ekstraksi_fitur_linear.csv"
TAG = sys.argv[2] if len(sys.argv) > 2 else "linear"
COORD_CSV = "koordinat_kecamatan.csv"             # dipakai ulang kalau sudah ada (dari tugas sebelumnya)
DIM_LEVELS = [203, 74, 37]
JATIM_BBOX = (-8.9, -5.9, 110.8, 114.8)

CHART_DIR = Path(f"_static/charts/clustering_exp/{TAG}")
CHART_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR = Path("_static")

HEX_COLORS = ["#1F6F78", "#C97B2E", "#7A4B9E", "#B23A48", "#4F772D", "#3D5A80"]

# ------------------------------------------------------------------
# 1. LOAD DATA & STANDARISASI
# ------------------------------------------------------------------
df = pd.read_csv(INPUT_CSV)
# rapikan penulisan nama kecamatan (mis. "Jabon , Sidoarjo" -> "Jabon, Sidoarjo")
df["daerah"] = (df["daerah"].astype(str)
                .str.replace(r"\s+,", ",", regex=True)
                .str.replace(r"\s{2,}", " ", regex=True)
                .str.strip())
feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                if c.lower() != "id"]          # 'id' bukan fitur, jangan ikut dihitung
X = df[feature_cols].copy()
X = X.fillna(X.mean())
n_samples, n_features = X.shape
print(f"Dataset: {n_samples} kecamatan x {n_features} fitur")
print(f"Kolom yang di-exclude (bukan fitur): {[c for c in df.columns if c not in feature_cols]}")

X_scaled = StandardScaler().fit_transform(X)

# ------------------------------------------------------------------
# 2. FUNGSI: CARI k TERBAIK PAKAI SILHOUETTE, UNTUK 1 DATASET
# ------------------------------------------------------------------
def analisis_cluster(data, label_dim, k_range=range(2, 11)):
    inertias, silhouettes = [], []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(data)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(data, labels))
    best_k = list(k_range)[int(np.argmax(silhouettes))]

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    axes[0].plot(list(k_range), inertias, marker="o", color="#1F6F78")
    axes[0].set_xlabel("Jumlah Cluster (k)"); axes[0].set_ylabel("Inertia (WCSS)")
    axes[0].set_title(f"Elbow Method - Dimensi {label_dim}")
    axes[1].plot(list(k_range), silhouettes, marker="o", color="#C97B2E")
    axes[1].axvline(best_k, color="red", linestyle="--", alpha=0.5)
    axes[1].set_xlabel("Jumlah Cluster (k)"); axes[1].set_ylabel("Silhouette Score")
    axes[1].set_title(f"Silhouette Score - Dimensi {label_dim} (terbaik: k={best_k})")
    fig.tight_layout()
    fname = CHART_DIR / f"elbow-silhouette-dim{label_dim}.png"
    fig.savefig(fname, dpi=150)
    plt.close(fig)

    print(f"[Dimensi {label_dim}] k terbaik = {best_k} "
          f"(silhouette = {max(silhouettes):.4f}) | grafik: {fname.name}")
    return best_k, silhouettes


# ------------------------------------------------------------------
# 3. EKSPERIMEN UNTUK TIAP LEVEL DIMENSI (203, 74, 37)
# ------------------------------------------------------------------
hasil = df[[c for c in ("nama", "daerah") if c in df.columns]].copy()
ringkasan = []

for target_dim in DIM_LEVELS:
    n_comp = min(target_dim, n_samples - 1, n_features)
    if n_comp != target_dim:
        print(f"\nCatatan: target dimensi {target_dim} > batas matematis "
              f"({n_samples - 1} sampel-1 atau {n_features} fitur), dipakai {n_comp} komponen.")

    pca = PCA(n_components=n_comp)
    X_pca = pca.fit_transform(X_scaled)
    var_explained = np.sum(pca.explained_variance_ratio_) * 100
    print(f"\n=== Dimensi target {target_dim} (dipakai {n_comp} komponen), "
          f"varians dijelaskan: {var_explained:.2f}% ===")

    best_k, silhouettes = analisis_cluster(X_pca, target_dim)

    km_final = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    labels_final = km_final.fit_predict(X_pca)
    hasil[f"cluster_dim{target_dim}"] = labels_final

    # scatter plot PC1 vs PC2 untuk level dimensi ini
    fig, ax = plt.subplots(figsize=(8, 6))
    for c in range(best_k):
        mask = labels_final == c
        ax.scatter(X_pca[mask, 0], X_pca[mask, 1], s=80,
                   color=HEX_COLORS[c % len(HEX_COLORS)],
                   edgecolor="white", linewidth=0.8,
                   label=f"Cluster {c} ({mask.sum()})")
    ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
    ax.set_title(f"Scatter PCA - Dimensi {target_dim}, k={best_k}")
    ax.legend(); ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(CHART_DIR / f"scatter-dim{target_dim}.png", dpi=150)
    plt.close(fig)

    ringkasan.append({
        "Target Dimensi": target_dim,
        "Komponen Dipakai": n_comp,
        "Varians Dijelaskan (%)": round(var_explained, 2),
        "k Terbaik": best_k,
        "Silhouette Score": round(max(silhouettes), 4),
    })

hasil.to_csv(f"hasil_clustering_3level_{TAG}.csv", index=False)
print(f"\nTersimpan: hasil_clustering_3level_{TAG}.csv")

ringkasan_df = pd.DataFrame(ringkasan)
print("\n" + "=" * 70)
print("RINGKASAN EKSPERIMEN 3 LEVEL DIMENSI")
print("=" * 70)
print(ringkasan_df.to_string(index=False))
print("\n--- Tabel markdown (copy ke laporan) ---")
print("| " + " | ".join(ringkasan_df.columns) + " |")
print("|" + "|".join(["---"] * len(ringkasan_df.columns)) + "|")
for row in ringkasan_df.astype(object).itertuples(index=False):
    print("| " + " | ".join(str(v) for v in row) + " |")

# ------------------------------------------------------------------
# 4. PETA CLUSTER UNTUK TIAP LEVEL DIMENSI
# ------------------------------------------------------------------
def short_name(daerah):
    return str(daerah).split(",")[0].strip()


daerah_unik = df["daerah"].astype(str).str.strip().unique().tolist()

if os.path.exists(COORD_CSV):
    coords = pd.read_csv(COORD_CSV)
    print(f"\nMemakai koordinat dari {COORD_CSV}")
else:
    coords = pd.DataFrame(columns=["daerah", "lat", "lon"])

todo = [d for d in daerah_unik if d not in coords["daerah"].astype(str).str.strip().values]
if todo:
    from geopy.geocoders import Nominatim
    geolocator = Nominatim(user_agent="psd-tugas-pca3level")
    rows = []
    print(f"Geocoding {len(todo)} kecamatan yang belum punya koordinat (butuh internet)...")
    for d in todo:
        lat = lon = np.nan
        for q in [f"Kecamatan {d}, Indonesia", f"{d}, Indonesia"]:
            try:
                loc = geolocator.geocode(q, timeout=10)
            except Exception:
                loc = None
            time.sleep(1.1)
            if loc:
                lat, lon = loc.latitude, loc.longitude
                break
        print(f"  {d:35s} -> {lat}, {lon}")
        rows.append({"daerah": d, "lat": lat, "lon": lon})
    coords = pd.concat([coords, pd.DataFrame(rows)], ignore_index=True)
    coords.to_csv(COORD_CSV, index=False)
    print(f"Tersimpan: {COORD_CSV} <- cek & perbaiki koordinat yang aneh/kosong, lalu jalankan ulang")

kosong = coords[coords["lat"].isna()]["daerah"].tolist()
if kosong:
    print(f"PERINGATAN: koordinat kosong untuk {kosong}. Isi manual lat/lon di {COORD_CSV}.")

import folium

base = hasil.copy()
base["daerah"] = base["daerah"].astype(str).str.strip()
base = base.merge(coords, on="daerah", how="left")
dup_idx = base.groupby("daerah").cumcount()
base["lat"] = base["lat"] + dup_idx * 0.004
base["lon"] = base["lon"] + dup_idx * 0.004

for target_dim in DIM_LEVELS:
    col = f"cluster_dim{target_dim}"
    valid = base.dropna(subset=["lat", "lon", col])
    lat_min, lat_max, lon_min, lon_max = JATIM_BBOX
    in_jatim = valid["lat"].between(lat_min, lat_max) & valid["lon"].between(lon_min, lon_max)
    focus = valid[in_jatim] if in_jatim.any() else valid
    k_dim = int(valid[col].max()) + 1

    # ---- PNG statis ----
    fig, ax = plt.subplots(figsize=(9, 7))
    for c in range(k_dim):
        sub = focus[focus[col] == c]
        ax.scatter(sub["lon"], sub["lat"], s=100,
                   color=HEX_COLORS[c % len(HEX_COLORS)],
                   edgecolor="white", linewidth=0.8,
                   label=f"Cluster {c} ({len(sub)})")
    for _, r in focus.iterrows():
        ax.annotate(short_name(r["daerah"]), (r["lon"], r["lat"]),
                    fontsize=6.5, alpha=0.75, xytext=(5, 4), textcoords="offset points")
    ax.set_xlim(focus["lon"].min() - 0.15, focus["lon"].max() + 0.15)
    ax.set_ylim(focus["lat"].min() - 0.15, focus["lat"].max() + 0.15)
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    ax.set_title(f"Peta Cluster - Reduksi Dimensi {target_dim}")
    ax.set_aspect("equal", adjustable="box")
    ax.legend(); ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(CHART_DIR / f"peta-dim{target_dim}.png", dpi=150)
    plt.close(fig)

    # ---- HTML interaktif ----
    m = folium.Map(location=[focus["lat"].mean(), focus["lon"].mean()],
                    zoom_start=8, tiles="OpenStreetMap")
    for _, r in focus.iterrows():
        color = HEX_COLORS[int(r[col]) % len(HEX_COLORS)]
        folium.CircleMarker(
            location=[r["lat"], r["lon"]], radius=9, color="white", weight=1.5,
            fill=True, fill_color=color, fill_opacity=0.9,
            tooltip=f"{r['daerah']} - Cluster {int(r[col])}",
            popup=f"<b>{r['daerah']}</b><br>Dimensi {target_dim}, Cluster {int(r[col])}",
        ).add_to(m)
    m.fit_bounds([[focus["lat"].min(), focus["lon"].min()],
                  [focus["lat"].max(), focus["lon"].max()]])
    legend_items = "".join(
        f'<div><span style="background:{HEX_COLORS[c % len(HEX_COLORS)]};'
        f'display:inline-block;width:12px;height:12px;border-radius:50%;'
        f'margin-right:6px;"></span>Cluster {c}</div>' for c in range(k_dim))
    legend_html = (
        '<div style="position:fixed;bottom:30px;left:30px;z-index:9999;background:white;'
        'padding:10px 14px;border:1px solid #bbb;border-radius:6px;font-size:13px;'
        f'font-family:sans-serif;"><b>Dimensi {target_dim} (k={k_dim})</b>{legend_items}</div>')
    m.get_root().html.add_child(folium.Element(legend_html))
    m.save(str(STATIC_DIR / f"peta-cluster-{TAG}-dim{target_dim}.html"))
    print(f"Tersimpan: peta-dim{target_dim}.png dan peta-cluster-{TAG}-dim{target_dim}.html")

print("\nSelesai eksperimen 3 level dimensi!")

"""
Visualisasi Hasil Clustering
  1. Scatter plot: PCA1 vs PCA2, titik diwarnai sesuai cluster
  2. Peta: tiap kecamatan ditaruh di lokasi aslinya, diwarnai sesuai cluster

Cara pakai:
    pip install pandas scikit-learn matplotlib folium geopy
    python visualisasi_cluster.py

Hasil:
    _static/charts/clustering/scatter-cluster-k2.png  (dan k3, k4)
    _static/charts/clustering/peta-cluster-k2.png     (dan k3, k4)
    _static/peta-cluster-k2.html                      (peta interaktif, dan k3, k4)
    koordinat_kecamatan.csv                           (koordinat hasil geocoding)

CATATAN: koordinat diambil otomatis lewat geocoding (OpenStreetMap). Nama
kecamatan yang ambigu bisa salah lokasi. Setelah script pertama kali jalan,
BUKA koordinat_kecamatan.csv, cek/perbaiki lat & lon yang aneh, lalu jalankan
script lagi (script akan memakai file itu, tidak geocoding ulang).
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

DATA_CSV = "ekstraksi_fitur_204_gabungan.csv"
COORD_CSV = "koordinat_kecamatan.csv"
K_LIST = [2, 3, 4]          # k terbaik (2) + dua pembanding
JATIM_BBOX = (-8.9, -5.9, 110.8, 114.8)   # lat_min, lat_max, lon_min, lon_max

CHART_DIR = Path("_static/charts/clustering")
CHART_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR = Path("_static")

# Palet warna beda tiap cluster (hex untuk matplotlib, nama untuk folium)
HEX_COLORS = ["#1F6F78", "#C97B2E", "#7A4B9E", "#B23A48", "#4F772D", "#3D5A80"]
FOLIUM_COLORS = ["#1F6F78", "#C97B2E", "#7A4B9E", "#B23A48", "#4F772D", "#3D5A80"]

# ------------------------------------------------------------------
# 1. LOAD DATA, STANDARISASI, PCA
# ------------------------------------------------------------------
df = pd.read_csv(DATA_CSV)
feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
X = df[feature_cols].copy()
X = X.fillna(X.mean())

X_scaled = StandardScaler().fit_transform(X)
n_comp = min(37, len(df) - 1)
pca = PCA(n_components=n_comp)
X_pca = pca.fit_transform(X_scaled)
var1, var2 = pca.explained_variance_ratio_[:2] * 100
print(f"Sampel: {len(df)} | fitur: {len(feature_cols)} | komponen PCA: {n_comp}")
print(f"PCA1 menjelaskan {var1:.1f}% varians, PCA2 {var2:.1f}%")

# ------------------------------------------------------------------
# 2. SCATTER PLOT PCA1 vs PCA2 (untuk tiap k)
# ------------------------------------------------------------------
def short_name(daerah):
    return str(daerah).split(",")[0].strip()


# Batas "zoom": buang titik ekstrem (|z| > 2.5) supaya kumpulan titik utama terlihat jelas
z1 = (X_pca[:, 0] - X_pca[:, 0].mean()) / X_pca[:, 0].std()
z2 = (X_pca[:, 1] - X_pca[:, 1].mean()) / X_pca[:, 1].std()
zoom_mask = (np.abs(z1) < 2.5) & (np.abs(z2) < 2.5)
print(f"Titik ekstrem di PCA1/PCA2 (di luar panel zoom): {int((~zoom_mask).sum())}")

labels_by_k = {}
for k in K_LIST:
    labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X_pca)
    labels_by_k[k] = labels

    # cluster "minoritas" (anggota sedikit) diberi label nama, biar tidak penuh tulisan
    sizes = np.bincount(labels)
    minority_clusters = np.where(sizes <= max(2, 0.1 * len(df)))[0]
    minority = np.isin(labels, minority_clusters)

    fig, axes = plt.subplots(1, 2, figsize=(15, 6.5))
    titles = ["Tampilan penuh", "Zoom (tanpa titik ekstrem)"]
    for ax_i, (ax, title) in enumerate(zip(axes, titles)):
        for c in range(k):
            mask = labels == c
            ax.scatter(X_pca[mask, 0], X_pca[mask, 1],
                       s=90, color=HEX_COLORS[c % len(HEX_COLORS)],
                       edgecolor="white", linewidth=0.8,
                       label=f"Cluster {c} ({mask.sum()} kecamatan)")
        for i, name in enumerate(df["daerah"]):
            if minority[i] and (ax_i == 0 or zoom_mask[i]):
                ax.annotate(short_name(name), (X_pca[i, 0], X_pca[i, 1]),
                            fontsize=8, xytext=(6, 5), textcoords="offset points")
        ax.set_xlabel(f"PCA1 ({var1:.1f}% varians)")
        ax.set_ylabel(f"PCA2 ({var2:.1f}% varians)")
        ax.set_title(f"{title} - K-Means (k = {k})")
        ax.grid(alpha=0.25)
    axes[0].legend()

    pts = X_pca[zoom_mask, :2]
    pad_x = (pts[:, 0].max() - pts[:, 0].min()) * 0.15 + 0.2
    pad_y = (pts[:, 1].max() - pts[:, 1].min()) * 0.15 + 0.2
    axes[1].set_xlim(pts[:, 0].min() - pad_x, pts[:, 0].max() + pad_x)
    axes[1].set_ylim(pts[:, 1].min() - pad_y, pts[:, 1].max() + pad_y)

    fig.tight_layout()
    fig.savefig(CHART_DIR / f"scatter-cluster-k{k}.png", dpi=150)
    plt.close(fig)
    print(f"Tersimpan: scatter-cluster-k{k}.png")

# ------------------------------------------------------------------
# 3. KOORDINAT KECAMATAN (geocoding sekali, disimpan ke CSV)
# ------------------------------------------------------------------
daerah_unik = df["daerah"].astype(str).str.strip().unique().tolist()

if os.path.exists(COORD_CSV):
    coords = pd.read_csv(COORD_CSV)
    print(f"\nMemakai koordinat dari {COORD_CSV}")
else:
    from geopy.geocoders import Nominatim

    geolocator = Nominatim(user_agent="psd-tugas4-peta-cluster")
    rows = []
    print(f"\nGeocoding {len(daerah_unik)} kecamatan (butuh internet, +/- 1 menit)...")
    for d in daerah_unik:
        # "Kerek, Tuban" -> "Kecamatan Kerek, Tuban, Indonesia"
        # (tidak dipaksa "Jawa Timur" karena ada data kelas dari luar Jatim)
        queries = [f"Kecamatan {d}, Indonesia",
                   f"{d}, Indonesia"]
        lat = lon = np.nan
        for q in queries:
            try:
                loc = geolocator.geocode(q, timeout=10)
            except Exception:
                loc = None
            time.sleep(1.1)      # aturan Nominatim: maks 1 permintaan/detik
            if loc:
                lat, lon = loc.latitude, loc.longitude
                break
        print(f"  {d:35s} -> {lat}, {lon}")
        rows.append({"daerah": d, "lat": lat, "lon": lon})
    coords = pd.DataFrame(rows)
    coords.to_csv(COORD_CSV, index=False)
    print(f"\nTersimpan: {COORD_CSV}  <- CEK & perbaiki koordinat yang aneh, lalu jalankan ulang")

missing = coords[coords["lat"].isna()]
if len(missing):
    print("\nPERINGATAN: koordinat kosong untuk:", missing["daerah"].tolist())
    print("Isi manual lat/lon di", COORD_CSV, "lalu jalankan ulang script ini.")

# ------------------------------------------------------------------
# 4. PETA CLUSTER (statis PNG + interaktif HTML) untuk tiap k
# ------------------------------------------------------------------
import folium

base = df[["nama", "daerah"]].copy()
base["daerah"] = base["daerah"].astype(str).str.strip()
base = base.merge(coords, on="daerah", how="left")

# Kecamatan yang sama dipakai >1 mahasiswa -> geser sedikit biar titik tidak menumpuk
dup_idx = base.groupby("daerah").cumcount()
base["lat"] = base["lat"] + dup_idx * 0.004
base["lon"] = base["lon"] + dup_idx * 0.004

for k in K_LIST:
    base_k = base.copy()
    base_k["cluster"] = labels_by_k[k]
    valid = base_k.dropna(subset=["lat", "lon"])

    # Fokus tampilan ke Jawa Timur; titik di luar Jatim tetap ada tapi tidak ikut membingkai peta
    lat_min, lat_max, lon_min, lon_max = JATIM_BBOX
    in_jatim = valid["lat"].between(lat_min, lat_max) & valid["lon"].between(lon_min, lon_max)
    focus = valid[in_jatim] if in_jatim.any() else valid
    luar = valid[~in_jatim]
    if k == K_LIST[0] and len(luar):
        print("\nKecamatan di LUAR Jawa Timur (tidak masuk bingkai peta):",
              luar["daerah"].tolist())

    # ---- PNG statis (lon-lat) ----
    fig, ax = plt.subplots(figsize=(9, 7))
    for c in range(k):
        sub = valid[valid["cluster"] == c]
        ax.scatter(sub["lon"], sub["lat"], s=110,
                   color=HEX_COLORS[c % len(HEX_COLORS)],
                   edgecolor="white", linewidth=0.9,
                   label=f"Cluster {c} ({len(sub)} kecamatan)")
    for _, r in valid.iterrows():
        ax.annotate(short_name(r["daerah"]), (r["lon"], r["lat"]),
                    fontsize=6.5, alpha=0.75, xytext=(5, 4),
                    textcoords="offset points")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Peta Sebaran Cluster K-Means (k = {k})")
    ax.set_xlim(focus["lon"].min() - 0.15, focus["lon"].max() + 0.15)
    ax.set_ylim(focus["lat"].min() - 0.15, focus["lat"].max() + 0.15)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHART_DIR / f"peta-cluster-k{k}.png", dpi=150)
    plt.close(fig)

    # ---- HTML interaktif (folium, ada peta dasar OpenStreetMap) ----
    center = [focus["lat"].mean(), focus["lon"].mean()]
    m = folium.Map(location=center, zoom_start=8, tiles="OpenStreetMap")
    for _, r in valid.iterrows():
        color = FOLIUM_COLORS[int(r["cluster"]) % len(FOLIUM_COLORS)]
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=9, color="white", weight=1.5,
            fill=True, fill_color=color, fill_opacity=0.9,
            tooltip=f"{r['daerah']} - Cluster {int(r['cluster'])}",
            popup=folium.Popup(
                f"<b>{r['daerah']}</b><br>Cluster: {int(r['cluster'])}<br>{r['nama']}",
                max_width=250),
        ).add_to(m)

    m.fit_bounds([[focus["lat"].min(), focus["lon"].min()],
                  [focus["lat"].max(), focus["lon"].max()]])

    legend_items = "".join(
        f'<div><span style="background:{FOLIUM_COLORS[c % len(FOLIUM_COLORS)]};'
        f'display:inline-block;width:12px;height:12px;border-radius:50%;'
        f'margin-right:6px;"></span>Cluster {c}</div>'
        for c in range(k))
    legend_html = (
        '<div style="position:fixed;bottom:30px;left:30px;z-index:9999;'
        'background:white;padding:10px 14px;border:1px solid #bbb;'
        'border-radius:6px;font-size:13px;font-family:sans-serif;">'
        f'<b>K-Means (k = {k})</b>{legend_items}</div>')
    m.get_root().html.add_child(folium.Element(legend_html))

    html_path = STATIC_DIR / f"peta-cluster-k{k}.html"
    m.save(str(html_path))
    print(f"Tersimpan: peta-cluster-k{k}.png dan {html_path.name}")

# ------------------------------------------------------------------
# 5. RINGKASAN: anggota tiap cluster (bahan interpretasi)
# ------------------------------------------------------------------
print("\n" + "=" * 60)
for k in K_LIST:
    print(f"\nAnggota cluster untuk k = {k}:")
    tmp = df[["daerah"]].copy()
    tmp["cluster"] = labels_by_k[k]
    for c in range(k):
        names = tmp[tmp["cluster"] == c]["daerah"].tolist()
        print(f"  Cluster {c} ({len(names)}): {', '.join(names)}")
print("\nSelesai!")

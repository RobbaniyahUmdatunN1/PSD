"""
Bagian C: PCA (Reduksi Dimensi) + Penentuan Jumlah Cluster Terbaik (K-Means)

Dilakukan 2x:
  1. Pada data yang sudah direduksi PCA (37 komponen)
  2. Pada data 68 fitur asli (tanpa reduksi)
Untuk dibandingkan mana yang menghasilkan cluster lebih baik.

Cara pakai:
    pip install pandas scikit-learn matplotlib
    python pca_clustering_tugas4.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

OUTPUT_DIR = Path("_static/charts/clustering")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 1. LOAD DATA & STANDARISASI
#    (WAJIB standarisasi dulu sebelum PCA/K-Means, karena skala tiap
#    fitur TSFEL sangat berbeda-beda -- misal abs_energy bisa jutaan,
#    sedangkan skewness cuma sekitar -3 sampai 3)
df = pd.read_csv("ekstraksi_fitur_204_gabungan.csv")

# Ambil HANYA kolom bertipe angka sebagai fitur (otomatis buang kolom teks
# seperti 'nama', 'daerah', 'id' -- lebih aman daripada menebak nama kolom persis)
feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
print("Kolom yang dipakai sebagai fitur:", feature_cols[:5], "... dst")
print("Kolom yang di-exclude (bukan angka):",
      [c for c in df.columns if c not in feature_cols])

X = df[feature_cols].values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print(f"Jumlah sampel (kecamatan): {X.shape[0]}")
print(f"Jumlah fitur asli: {X.shape[1]}")

# 2. PCA: REDUKSI DIMENSI KE 36 KOMPONEN
#    Catatan: karena cuma ada 36 sampel, jumlah komponen PCA maksimal
#    yang bermakna secara matematis adalah min(n_sampel, n_fitur) = 36.
#    Jadi "reduksi ke 36" di sini artinya PCA penuh (tidak ada informasi
#    varians yang hilang, cuma diputar ke basis baru yang lebih efisien).
N_COMPONENTS = 36
pca = PCA(n_components=N_COMPONENTS)
X_pca = pca.fit_transform(X_scaled)

explained_var = pca.explained_variance_ratio_
cum_var = np.cumsum(explained_var)

print(f"\nVarians dijelaskan oleh 36 komponen PCA: {cum_var[-1]*100:.2f}%")
print(f"Varians dijelaskan oleh 10 komponen pertama: {cum_var[9]*100:.2f}%")

# Grafik scree plot (varians per komponen)
fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(range(1, N_COMPONENTS + 1), explained_var * 100, color="#1F6F78", label="Per komponen")
ax.plot(range(1, N_COMPONENTS + 1), cum_var * 100, color="#C97B2E", marker="o", label="Kumulatif")
ax.set_xlabel("Komponen PCA ke-")
ax.set_ylabel("Persentase Varians Dijelaskan (%)")
ax.set_title("Scree Plot: Varians Dijelaskan oleh Tiap Komponen PCA")
ax.legend()
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "scree-plot-pca.png", dpi=150)
plt.close(fig)
print("Tersimpan: scree-plot-pca.png")

# Simpan hasil PCA sebagai CSV (PCA1...PCA36)
pca_cols = [f"PCA{i+1}" for i in range(N_COMPONENTS)]
df_pca = pd.DataFrame(X_pca, columns=pca_cols)
df_pca.insert(0, "daerah", df["daerah"])
df_pca.insert(0, "nama", df["nama"])
df_pca.to_csv("hasil_pca_36komponen.csv", index=False)
print("Tersimpan: hasil_pca_36komponen.csv")

# 3. TENTUKAN JUMLAH CLUSTER TERBAIK
#    Dilakukan pada 2 dataset: (a) hasil PCA, (b) fitur asli (68, discaled)
#    Metode: Elbow Method (Inertia/WCSS) + Silhouette Score
def analisis_cluster(data, nama_dataset, k_range=range(2, 11)):
    inertias = []
    silhouettes = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(data)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(data, labels))

    # Grafik Elbow
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].plot(list(k_range), inertias, marker="o", color="#1F6F78")
    axes[0].set_xlabel("Jumlah Cluster (k)")
    axes[0].set_ylabel("Inertia (WCSS)")
    axes[0].set_title(f"Elbow Method - {nama_dataset}")

    axes[1].plot(list(k_range), silhouettes, marker="o", color="#C97B2E")
    axes[1].set_xlabel("Jumlah Cluster (k)")
    axes[1].set_ylabel("Silhouette Score")
    axes[1].set_title(f"Silhouette Score - {nama_dataset}")
    fig.tight_layout()
    filename = OUTPUT_DIR / f"cluster-analysis-{nama_dataset.lower().replace(' ', '-')}.png"
    fig.savefig(filename, dpi=150)
    plt.close(fig)

    best_k = list(k_range)[int(np.argmax(silhouettes))]
    print(f"\n[{nama_dataset}] Grafik tersimpan: {filename}")
    print(f"[{nama_dataset}] k terbaik berdasarkan Silhouette Score tertinggi: k = {best_k} "
          f"(silhouette = {max(silhouettes):.4f})")

    return best_k, inertias, silhouettes


print("\n" + "=" * 70)
print("ANALISIS CLUSTER PADA DATA HASIL PCA (36 KOMPONEN)")
print("=" * 70)
best_k_pca, _, _ = analisis_cluster(X_pca, "Data PCA (36 komponen)")

print("\n" + "=" * 70)
print("ANALISIS CLUSTER PADA 68 FITUR ASLI (TANPA PCA)")
print("=" * 70)
best_k_raw, _, _ = analisis_cluster(X_scaled, "68 Fitur Asli")

# 4. JALANKAN K-MEANS FINAL DENGAN k TERBAIK, SIMPAN HASIL LABEL CLUSTER
km_pca = KMeans(n_clusters=best_k_pca, random_state=42, n_init=10)
labels_pca = km_pca.fit_predict(X_pca)

km_raw = KMeans(n_clusters=best_k_raw, random_state=42, n_init=10)
labels_raw = km_raw.fit_predict(X_scaled)

df_result = df[["nama", "daerah"]].copy()
df_result["cluster_pca"] = labels_pca
df_result["cluster_68fitur"] = labels_raw
df_result.to_csv("hasil_clustering.csv", index=False)
print("\nTersimpan: hasil_clustering.csv (label cluster per kecamatan)")

print("\n" + "=" * 70)
print("RINGKASAN")
print("=" * 70)
print(f"Jumlah cluster terbaik (data PCA 37 komponen): k = {best_k_pca}")
print(f"Jumlah cluster terbaik (68 fitur asli)        : k = {best_k_raw}")

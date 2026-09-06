"""
Generate grafik tren polutan dari gresik_pollutant_data.csv
untuk ditempel di halaman tugas1-crawling-polutan.md

Cara pakai:
    pip install matplotlib pandas
    python generate_charts.py

Hasil: file-file gambar .png akan tersimpan di folder _static/charts/
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

CSV_PATH = "gresik_pollutant_data.csv"
OUTPUT_DIR = Path("_static/charts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(CSV_PATH, parse_dates=["date"])

pollutants = ["CO", "NO2", "HCHO", "O3", "SO2", "CH4"]

# ---- 1. Grafik gabungan (grid 2x3), buat overview ----
fig, axes = plt.subplots(2, 3, figsize=(15, 7))
for ax, pol in zip(axes.flatten(), pollutants):
    if pol in df.columns:
        ax.plot(df["date"], df[pol], linewidth=1, color="#1F6F78")
        ax.set_title(pol)
        ax.tick_params(axis="x", rotation=45)
fig.suptitle("Tren Konsentrasi Polutan di Gresik (Sept 2024 - Agu 2025)")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "overview-semua-polutan.png", dpi=150)
plt.close(fig)
print(f"Tersimpan: {OUTPUT_DIR / 'overview-semua-polutan.png'}")

# ---- 2. Grafik terpisah tiap polutan (lebih detail) ----
for pol in pollutants:
    if pol not in df.columns:
        continue
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(df["date"], df[pol], linewidth=1.2, color="#1F6F78")
    ax.set_title(f"Tren {pol} di Gresik")
    ax.set_xlabel("Tanggal")
    ax.set_ylabel(pol)
    fig.tight_layout()
    filename = OUTPUT_DIR / f"tren-{pol.lower()}.png"
    fig.savefig(filename, dpi=150)
    plt.close(fig)
    print(f"Tersimpan: {filename}")

# ---- 3. Cetak contoh tabel markdown (5 baris pertama) buat ditempel manual ----
print("\n--- Contoh tabel markdown (copy-paste ke tugas1-crawling-polutan.md) ---\n")
sample = df.head(5)
cols = sample.columns.tolist()
print("| " + " | ".join(cols) + " |")
print("|" + "|".join(["---"] * len(cols)) + "|")
for _, row in sample.iterrows():
    print("| " + " | ".join(str(v) for v in row.values) + " |")

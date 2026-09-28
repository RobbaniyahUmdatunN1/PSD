"""
Generate aset (tabel & grafik) dari hasil ekstraksi fitur TSFEL
untuk ditampilkan di halaman Tugas 3 (Jupyter Book).

Cara pakai:
    pip install pandas matplotlib
    Taruh file 'NO2_Cerme_TSFEL.csv' dan 'ekstraksi_fitur_no2_psd-a.csv'
    di folder yang sama, lalu jalankan:
    python generate_tugas3_assets.py

Hasil:
    - Tabel markdown hasil sendiri (di-print ke terminal, tinggal copy-paste)
    - Grafik perbandingan sekelas -> _static/charts/perbandingan-kelas-*.png
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

OUTPUT_DIR = Path("_static/charts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MY_KECAMATAN = "Cerme"  # ganti sesuai kecamatan kamu

# ------------------------------------------------------------------
# 1. TABEL HASIL SENDIRI (dibalik jadi vertikal: fitur | nilai)
# ------------------------------------------------------------------
df_mine = pd.read_csv("NO2_Cerme_TSFEL.csv")
transposed = df_mine.T.reset_index()
transposed.columns = ["Fitur", "Nilai"]
transposed["Nilai"] = transposed["Nilai"].apply(lambda x: f"{x:.6g}")

print(f"\n--- Tabel markdown hasil ekstraksi kamu ({len(transposed)} fitur) ---\n")
print("| Fitur | Nilai |")
print("|---|---|")
for _, row in transposed.iterrows():
    print(f"| {row['Fitur']} | {row['Nilai']} |")

# ------------------------------------------------------------------
# 2. DATA SEKELAS: TABEL RINGKAS (kolom kunci saja, biar tidak kepanjangan)
# ------------------------------------------------------------------
df_class = pd.read_csv("ekstraksi_fitur_no2_psd-a.csv")

key_cols = ["nama", "daerah", "calc_mean", "calc_std", "spectral_entropy", "autocorr"]
summary = df_class[key_cols].round(6)

print(f"\n--- Tabel ringkas perbandingan sekelas ({len(summary)} mahasiswa) ---\n")
print("| " + " | ".join(summary.columns) + " |")
print("|" + "|".join(["---"] * len(summary.columns)) + "|")
for _, row in summary.iterrows():
    print("| " + " | ".join(str(v) for v in row.values) + " |")

# ------------------------------------------------------------------
# 3. GRAFIK PERBANDINGAN: calc_mean (rata-rata NO2) per daerah, urut dari tertinggi
# ------------------------------------------------------------------
df_sorted = df_class.sort_values("calc_mean", ascending=True)
colors = ["#C97B2E" if MY_KECAMATAN.lower() in str(d).lower() else "#1F6F78"
          for d in df_sorted["daerah"]]

fig, ax = plt.subplots(figsize=(9, 12))
ax.barh(df_sorted["daerah"] + " (" + df_sorted["nama"].str.split().str[0] + ")",
        df_sorted["calc_mean"], color=colors)
ax.set_xlabel("calc_mean (rata-rata NO2)")
ax.set_title("Perbandingan Rata-rata NO2 Antar Kecamatan (Sekelas)")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "perbandingan-kelas-mean.png", dpi=150)
plt.close(fig)
print(f"\nTersimpan: {OUTPUT_DIR / 'perbandingan-kelas-mean.png'}")

# ------------------------------------------------------------------
# 4. GRAFIK PERBANDINGAN: spectral_entropy (pola acak vs periodik) per daerah
# ------------------------------------------------------------------
df_sorted2 = df_class.sort_values("spectral_entropy", ascending=True)
colors2 = ["#C97B2E" if MY_KECAMATAN.lower() in str(d).lower() else "#1F6F78"
           for d in df_sorted2["daerah"]]

fig, ax = plt.subplots(figsize=(9, 12))
ax.barh(df_sorted2["daerah"] + " (" + df_sorted2["nama"].str.split().str[0] + ")",
        df_sorted2["spectral_entropy"], color=colors2)
ax.set_xlabel("spectral_entropy")
ax.set_title("Perbandingan Spectral Entropy NO2 Antar Kecamatan (Sekelas)")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "perbandingan-kelas-entropy.png", dpi=150)
plt.close(fig)
print(f"Tersimpan: {OUTPUT_DIR / 'perbandingan-kelas-entropy.png'}")

print("\nSelesai! Warna oranye pada grafik = kecamatan kamu sendiri, biru = teman sekelas.")

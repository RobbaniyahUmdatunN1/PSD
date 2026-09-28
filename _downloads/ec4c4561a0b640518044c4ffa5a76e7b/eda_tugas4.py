import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

OUTPUT_DIR = Path("_static/charts/eda")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# BAGIAN 1: TIME SERIES NO2 HARIAN (DATA MENTAH, SEBELUM EKSTRAKSI FITUR)
df_raw = pd.read_csv("mystorage/NO2-Cerme.csv", parse_dates=["date"])

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df_raw["date"], df_raw["NO2"], color="#1F6F78", linewidth=1)
ax.set_title("Time Series NO2 Harian - Kecamatan Cerme (31 Agu 2025 - 31 Agu 2026)")
ax.set_xlabel("Tanggal")
ax.set_ylabel("NO2 (mol/m²)")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "timeseries-no2-cerme.png", dpi=150)
plt.close(fig)
print("Tersimpan: timeseries-no2-cerme.png")

# Rolling average (7 hari) untuk melihat tren tanpa noise harian
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df_raw["date"], df_raw["NO2"], color="#D8DED9", linewidth=0.8, label="Data harian")
ax.plot(df_raw["date"], df_raw["NO2"].rolling(7, min_periods=1).mean(),
        color="#C97B2E", linewidth=2, label="Rata-rata bergerak 7 hari")
ax.set_title("Tren NO2 Cerme dengan Rolling Average")
ax.set_xlabel("Tanggal")
ax.set_ylabel("NO2 (mol/m²)")
ax.legend()
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "timeseries-no2-cerme-trend.png", dpi=150)
plt.close(fig)
print("Tersimpan: timeseries-no2-cerme-trend.png")

# BAGIAN 2: EKSPLORASI CROSS-SECTIONAL DATA SEKELAS (37 kecamatan x 68 fitur)
df_class = pd.read_csv("ekstraksi_fitur_no2_psd-a.csv")
feature_cols = [c for c in df_class.columns if c not in ("nama", "daerah")]

print(f"\nJumlah kecamatan: {len(df_class)}")
print(f"Jumlah fitur: {len(feature_cols)}")

# --- Distribusi beberapa fitur kunci (boxplot) ---
key_features = ["calc_mean", "calc_std", "skewness", "kurtosis", "spectral_entropy", "autocorr"]
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
for ax, feat in zip(axes.flatten(), key_features):
    sns.boxplot(y=df_class[feat], ax=ax, color="#1F6F78")
    ax.set_title(feat)
fig.suptitle("Distribusi Fitur Kunci di Seluruh Kelas (37 Kecamatan)")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "distribusi-fitur-kunci.png", dpi=150)
plt.close(fig)
print("Tersimpan: distribusi-fitur-kunci.png")

# Correlation heatmap antar fitur
corr = df_class[feature_cols].corr()
fig, ax = plt.subplots(figsize=(16, 14))
sns.heatmap(corr, cmap="coolwarm", center=0, ax=ax, cbar_kws={"label": "Korelasi"})
ax.set_title("Korelasi Antar 68 Fitur (Seluruh Kelas)")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "korelasi-68-fitur.png", dpi=150)
plt.close(fig)
print("Tersimpan: korelasi-68-fitur.png")

# Statistik ringkas seluruh fitur
summary_stats = df_class[feature_cols].describe().T[["mean", "std", "min", "max"]]
summary_stats.to_csv(OUTPUT_DIR.parent / "ringkasan-statistik-68-fitur.csv")
print("Tersimpan: ringkasan-statistik-68-fitur.csv")

print("\nSelesai EDA!")

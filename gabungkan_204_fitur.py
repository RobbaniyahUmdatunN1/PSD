import pandas as pd

co = pd.read_csv("ekstraksi_fitur_co.csv")
no2 = pd.read_csv("ekstraksi_fitur_no2.csv")
so2 = pd.read_csv("ekstraksi_fitur_so2.csv")

# Kolom fitur (68 kolom) = semua kolom kecuali id, nama, daerah
feature_cols_co = [c for c in co.columns if c not in ("id", "nama", "daerah")]
feature_cols_no2 = [c for c in no2.columns if c not in ("id", "nama", "daerah")]
feature_cols_so2 = [c for c in so2.columns if c not in ("id", "nama", "daerah")]

print(f"Jumlah fitur CO : {len(feature_cols_co)}")
print(f"Jumlah fitur NO2: {len(feature_cols_no2)}")
print(f"Jumlah fitur SO2: {len(feature_cols_so2)}")

# Beri prefix nama polutan supaya tidak bentrok saat digabung
co_renamed = co[["nama", "daerah"] + feature_cols_co].rename(
    columns={c: f"CO_{c}" for c in feature_cols_co}
)
no2_renamed = no2[["nama", "daerah"] + feature_cols_no2].rename(
    columns={c: f"NO2_{c}" for c in feature_cols_no2}
)
so2_renamed = so2[["nama", "daerah"] + feature_cols_so2].rename(
    columns={c: f"SO2_{c}" for c in feature_cols_so2}
)

# Merge berdasarkan kolom 'nama' (konsisten di ketiga file, beda dgn 'daerah')
merged = co_renamed.merge(no2_renamed, on="nama", how="inner")
merged = merged.merge(so2_renamed, on="nama", how="inner")

n_feature_cols = len([c for c in merged.columns if c not in ("nama", "daerah")])
print(f"\nJumlah mahasiswa dengan data lengkap 3 polutan: {len(merged)}")
print(f"Jumlah total kolom fitur (204 diharapkan): {n_feature_cols}")

merged.to_csv("ekstraksi_fitur_204_gabungan.csv", index=False)
print("\nTersimpan: ekstraksi_fitur_204_gabungan.csv")

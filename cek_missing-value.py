import pandas as pd
import numpy as np

# 1. Load data 3 polutan
df_no2 = pd.read_csv("mystorage/NO2-Cerme.csv")
df_so2 = pd.read_csv("mystorage/SO2-Cerme.csv")
df_co  = pd.read_csv("mystorage/CO-Cerme.csv")

# Ensure date format
for df in [df_no2, df_so2, df_co]:
    df['date'] = pd.to_datetime(df['date'])

# 2. Merge 3 data berdasarkan tanggal
df_all = df_so2.merge(df_no2, on='date', how='outer').merge(df_co, on='date', how='outer')
df_all = df_all.sort_values('date').reset_index(drop=True)

# 3. Buat timeline tanggal lengkap (daily)
full_dates = pd.date_range(start=df_all['date'].min(), end=df_all['date'].max(), freq='D')
df_all = df_all.set_index('date').reindex(full_dates).rename_axis('date').reset_index()

# 4. Cek persentase Missing Value
print("=== PERSENTASE MISSING VALUE ===")
print((df_all.isnull().sum() / len(df_all)) * 100)

# 5. Interpolasi Time Series (Jika missing value < 15%)
df_clean = df_all.copy()
df_clean[['SO2', 'NO2', 'CO']] = df_clean[['SO2', 'NO2', 'CO']].interpolate(method='linear').bfill().ffill()

# Simpan dataset time series yang sudah rapi
df_clean.to_csv("mystorage/timeseries_cerme_clean.csv", index=False)
print("\nData time-series berhasil dirapikan & disimpan!")
"""
Pembuktian Fitur negative_turning 3 Polutan (CO, NO2, SO2) Kecamatan Cerme
"""

import numpy as np
import pandas as pd
import tsfel.feature_extraction.features as tsfel_features

POLUTAN_FILES = {
    "CO": "mystorage/CO-Cerme.csv",
    "NO2": "mystorage/NO2-Cerme.csv",
    "SO2": "mystorage/SO2-Cerme.csv",
}


def hitung_manual(x):
    diffs = np.diff(x)
    count = 0
    for i in range(1, len(diffs)):
        if diffs[i - 1] < 0 and diffs[i] > 0:
            count += 1
    return count


for nama_pol, path in POLUTAN_FILES.items():
    print("=" * 70)
    print(f"POLUTAN: {nama_pol}")
    print("=" * 70)

    df = pd.read_csv(path, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    sample = df.head(10).copy()
    x = sample[nama_pol].values.astype(float)

    print(f"10 hari pertama data {nama_pol} Cerme:")
    print(sample[["date", nama_pol]].to_string(index=False))

    diffs = np.diff(x)
    print("\nSelisih antar hari (delta):")
    for i, d in enumerate(diffs):
        print(f"  Delta{i+1} = {x[i+1]:.6f} - {x[i]:.6f} = {d:.6f}")

    manual_count = hitung_manual(x)
    print(f"\nJumlah negative turning points (manual, 10 hari pertama): {manual_count}")

    tsfel_result = tsfel_features.negative_turning(x)
    if isinstance(tsfel_result, dict) and "values" in tsfel_result:
        tsfel_result = tsfel_result["values"]
    tsfel_value = float(np.asarray(tsfel_result, dtype=float).mean())
    print(f"Jumlah negative turning points (TSFEL, 10 hari pertama)  : {tsfel_value}")

    match = "COCOK" if np.isclose(manual_count, tsfel_value, atol=0.5) else "BEDA"
    print(f"Status: {match}")

    # Bonus: full data setahun
    x_full = df[nama_pol].values.astype(float)
    manual_full = hitung_manual(x_full)
    tsfel_full = tsfel_features.negative_turning(x_full)
    if isinstance(tsfel_full, dict) and "values" in tsfel_full:
        tsfel_full = tsfel_full["values"]
    tsfel_full_val = float(np.asarray(tsfel_full, dtype=float).mean())
    print(f"\n[Data setahun penuh, {len(x_full)} hari] Manual: {manual_full} | TSFEL: {tsfel_full_val}")
    print()
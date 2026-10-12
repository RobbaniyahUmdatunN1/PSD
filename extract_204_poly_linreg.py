import pandas as pd
import numpy as np
import inspect
import tsfel.feature_extraction.features as tsfel_features
from sklearn.linear_model import LinearRegression

# ---------- 1. Muat 1 file CSV utama yang berisi semua polutan ----------
df = pd.read_csv('gresik_pollutant_data.csv')

df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

pollutants = ['NO2', 'SO2', 'CO']
fs = 1

# ---------- 2. Daftar PERSIS 68 fitur yang diminta ----------
FEATURE_LIST = """abs_energy auc autocorr average_power calc_centroid calc_max calc_mean
calc_median calc_min calc_std calc_var dfa distance ecdf ecdf_percentile ecdf_percentile_count
ecdf_slope entropy fundamental_frequency higuchi_fractal_dimension hist_mode human_range_energy
hurst_exponent interq_range kurtosis lempel_ziv lpcc max_frequency max_power_spectrum
maximum_fractal_length mean_abs_deviation mean_abs_diff mean_diff median_abs_deviation
median_abs_diff median_diff median_frequency mfcc mse negative_turning neighbourhood_peaks
petrosian_fractal_dimension pk_pk_distance positive_turning power_bandwidth rms skewness slope
spectral_centroid spectral_decrease spectral_distance spectral_entropy spectral_kurtosis
spectral_positive_turning spectral_roll_off spectral_roll_on spectral_skewness spectral_slope
spectral_spread spectral_variation spectrogram_mean_coeff sum_abs_diff wavelet_abs_mean
wavelet_energy wavelet_entropy wavelet_std wavelet_var zero_cross""".split()

print(f"Jumlah fitur per polutan: {len(FEATURE_LIST)}")
print(f"Total target fitur keseluruhan: {len(FEATURE_LIST) * len(pollutants)}")


def to_scalar(result):
    if isinstance(result, dict) and "values" in result:
        result = result["values"]
    if isinstance(result, (list, tuple, np.ndarray)):
        arr = np.asarray(result, dtype=float)
        return float(np.nanmean(arr))
    return float(result)


def extract_one(fn_name, signal, fs):
    fn = getattr(tsfel_features, fn_name)
    params = inspect.signature(fn).parameters
    if "fs" in params:
        result = fn(signal, fs)
    else:
        result = fn(signal)
    return to_scalar(result)


# ---------- 3. Dictionary untuk menampung hasil, DIPISAH 2 METODE ----------
combined_row_polynomial = {}
combined_row_linreg = {}

# ---------- 4. Looping untuk membersihkan dan mengekstraksi tiap polutan ----------
for pollutant in pollutants:
    print(f"\n--- Memproses polutan: {pollutant} ---")

    df_poly = df[['date', pollutant]].copy()

    # Paksa kolom target jadi numerik
    df_poly[pollutant] = pd.to_numeric(df_poly[pollutant], errors='coerce')
    n_missing_before = df_poly[pollutant].isna().sum()
    print(f"Jumlah NaN/non-numerik pada {pollutant}: {n_missing_before}")

    # Handling outlier dengan IQR
    Q1 = df_poly[pollutant].quantile(0.25)
    Q3 = df_poly[pollutant].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    df_poly.loc[(df_poly[pollutant] < lower_bound) | (df_poly[pollutant] > upper_bound), pollutant] = np.nan

    n_total_nan = df_poly[pollutant].isna().sum()
    pct_nan = n_total_nan / len(df_poly) * 100
    print(f"Total NaN setelah deteksi outlier (missing + outlier): {n_total_nan} ({pct_nan:.2f}%)")
    if pct_nan > 15:
        print(f"PERINGATAN: missing+outlier {pct_nan:.2f}% melebihi batas 15%!")

    # ================== BAGIAN YANG DIUBAH: 2 METODE IMPUTASI ==================

    # ---- Metode A: Polynomial interpolation ----
    series_untuk_poly = df_poly.set_index('date')[pollutant].reset_index(drop=True)
    signal_polynomial = series_untuk_poly.interpolate(
        method='polynomial', order=2
    ).ffill().bfill().astype(float).values

    # ---- Metode B: Linear Regression (tren garis lurus dari seluruh data) ----
    series_untuk_linreg = df_poly.set_index('date')[pollutant].reset_index(drop=True)
    x_semua = np.arange(len(series_untuk_linreg)).reshape(-1, 1)
    valid_mask = series_untuk_linreg.notna()

    model = LinearRegression()
    model.fit(x_semua[valid_mask], series_untuk_linreg[valid_mask].values)
    prediksi_semua = model.predict(x_semua)

    signal_linreg = series_untuk_linreg.copy()
    signal_linreg[~valid_mask] = prediksi_semua[~valid_mask.values]
    signal_linreg = signal_linreg.astype(float).values

    # ================== AKHIR BAGIAN YANG DIUBAH ==================

    # Ekstraksi fitur dan beri prefix nama polutan, UNTUK MASING-MASING METODE
    for fn_name in FEATURE_LIST:
        feature_key = f"{pollutant}_{fn_name}"
        combined_row_polynomial[feature_key] = extract_one(fn_name, signal_polynomial, fs)
        combined_row_linreg[feature_key] = extract_one(fn_name, signal_linreg, fs)

# ---------- 5. Simpan ke DataFrame final (1 baris, 204 kolom) x 2 FILE ----------
extracted_features_polynomial = pd.DataFrame([combined_row_polynomial])
extracted_features_linreg = pd.DataFrame([combined_row_linreg])

print(f"\nBerhasil! Total kolom akhir (Polynomial): {extracted_features_polynomial.shape[1]}")
print(f"Berhasil! Total kolom akhir (Linear Regression): {extracted_features_linreg.shape[1]}")

output_filename_polynomial = 'All-Pollutants-Cerme-Polynomial-TSFEL.csv'
output_filename_linreg = 'All-Pollutants-Cerme-LinearRegression-TSFEL.csv'

extracted_features_polynomial.to_csv(output_filename_polynomial, index=False)
extracted_features_linreg.to_csv(output_filename_linreg, index=False)

print(f"File berhasil disimpan sebagai: {output_filename_polynomial}")
print(f"File berhasil disimpan sebagai: {output_filename_linreg}")

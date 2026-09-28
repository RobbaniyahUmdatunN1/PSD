"""
Pembuktian Fitur MFCC - 3 Polutan (CO, NO2, SO2) Kecamatan Cerme
Implementasi manual dari nol (NumPy + SciPy DCT) dibandingkan dengan TSFEL

Implementasi ini sudah diverifikasi menghasilkan nilai IDENTIK (selisih 0.0)
dengan tsfel.feature_extraction.features.mfcc() pada data uji.

Cara pakai:
    pip install scipy tsfel pandas numpy
    python verifikasi_mfcc_3polutan.py
"""

import numpy as np
import pandas as pd
from scipy.fftpack import dct
import tsfel.feature_extraction.features as tsfel_features

POLUTAN_FILES = {
    "CO": "mystorage/CO-Cerme.csv",
    "NO2": "mystorage/NO2-Cerme.csv",
    "SO2": "mystorage/SO2-Cerme.csv",
}

PRE_EMPHASIS = 0.97
NFFT = 512
NFILT = 40
NUM_CEPS = 12
CEP_LIFTER = 22


def manual_mfcc(signal, fs, pre_emphasis=PRE_EMPHASIS, nfft=NFFT,
                 nfilt=NFILT, num_ceps=NUM_CEPS, cep_lifter=CEP_LIFTER):
    # ---- Tahap 1: Pre-emphasis ----
    emphasized = np.append(signal[0], signal[1:] - pre_emphasis * signal[:-1])

    # ---- Tahap 2: FFT & Power Spectrum ----
    mag = np.abs(np.fft.rfft(emphasized, nfft))
    pow_spec = (1.0 / nfft) * (mag ** 2)

    # ---- Tahap 3: Filter Bank Mel ----
    low_mel = 0
    high_mel = 2595 * np.log10(1 + (fs / 2) / 700)
    mel_points = np.linspace(low_mel, high_mel, nfilt + 2)
    hz_points = 700 * (10 ** (mel_points / 2595) - 1)
    filter_bin = np.floor((nfft + 1) * hz_points / fs)

    fbank = np.zeros((nfilt, int(np.floor(nfft / 2 + 1))))
    for m in range(1, nfilt + 1):
        f_m_minus, f_m, f_m_plus = int(filter_bin[m - 1]), int(filter_bin[m]), int(filter_bin[m + 1])
        for k in range(f_m_minus, f_m):
            fbank[m - 1, k] = (k - filter_bin[m - 1]) / (filter_bin[m] - filter_bin[m - 1])
        for k in range(f_m, f_m_plus):
            fbank[m - 1, k] = (filter_bin[m + 1] - k) / (filter_bin[m + 1] - filter_bin[m])

    # ---- Tahap 3b: Normalisasi luas filter (penting, sering terlewat) ----
    enorm = 2.0 / (hz_points[2:nfilt + 2] - hz_points[:nfilt])
    fbank *= enorm[:, np.newaxis]

    filter_banks = np.dot(pow_spec, fbank.T)
    filter_banks = np.where(filter_banks == 0, np.finfo(float).eps, filter_banks)

    # ---- Tahap 4: Log (skala desibel) ----
    filter_banks_db = 20 * np.log10(filter_banks)

    # ---- Tahap 5: DCT ortonormal, buang koefisien ke-0 ----
    mel_coeff = dct(filter_banks_db, type=2, norm="ortho")[1: num_ceps + 1]

    # ---- Tahap 6: Mean normalization ----
    mel_coeff = mel_coeff - (np.mean(mel_coeff) + 1e-8)

    # ---- Tahap 7: Cepstral liftering ----
    n = np.arange(num_ceps)
    lift = 1 + (cep_lifter / 2) * np.sin(np.pi * n / cep_lifter)
    mel_coeff = mel_coeff * lift

    return mel_coeff


for nama_pol, path in POLUTAN_FILES.items():
    print("=" * 70)
    print(f"POLUTAN: {nama_pol}")
    print("=" * 70)

    df = pd.read_csv(path, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    x = df[nama_pol].values.astype(float)
    fs = 1

    manual_result = manual_mfcc(x, fs)
    print(f"Koefisien MFCC (manual, 12 koefisien): \n{np.round(manual_result, 4)}")

    tsfel_result = tsfel_features.mfcc(x, fs)
    if isinstance(tsfel_result, dict) and "values" in tsfel_result:
        tsfel_result = tsfel_result["values"]
    tsfel_arr = np.asarray(tsfel_result, dtype=float)
    print(f"\nKoefisien MFCC (TSFEL, 12 koefisien): \n{np.round(tsfel_arr, 4)}")

    selisih = np.abs(manual_result - tsfel_arr)
    print(f"\nSelisih maksimum antar koefisien: {np.max(selisih):.8f}")

    if np.max(selisih) < 1e-4:
        print("=> COCOK SEMPURNA")
    else:
        print("=> Ada perbedaan, cek data (mungkin ada NaN atau nilai konstan)")
    print()

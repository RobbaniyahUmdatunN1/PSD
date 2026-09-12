# Tugas 3: Preprocessing & Ekstraksi Fitur (TSFEL)

## Latar Belakang

Melanjutkan Tugas 1 dan 2, tugas ini fokus pada satu fitur polutan (**NO2**) di wilayah **Kecamatan Cerme, Kabupaten Gresik** — berbeda dengan Tugas 1-2 yang menggunakan boundary bebas di sekitar kawasan industri Manyar. Pemilihan kecamatan sesuai domisili masing-masing mahasiswa, sesuai instruksi kelas.

## Alur Kerja

1. Data NO2 di-crawl ulang khusus untuk boundary administratif **Kecamatan Cerme** (bukan gambar polygon manual, tapi batas resmi pemerintah), untuk rentang **31 Agustus 2025 – 31 Agustus 2026**.
2. Dilakukan **preprocessing**: deteksi outlier dan imputasi missing value.
3. Data bersih diekstraksi menjadi **68 fitur** menggunakan library **TSFEL** (Time Series Feature Extraction Library).
4. Fitur dikelompokkan berdasarkan domain: Statistical, Temporal, Spectral (dan Fractal).
5. Hasil ekstraksi diunggah ke sistem pengumpulan kelas.

## 1. Boundary Wilayah: Kecamatan Cerme

Boundary yang digunakan adalah batas administratif resmi Kecamatan Cerme, Kabupaten Gresik, Provinsi Jawa Timur — diunduh dari [batas-admin.geoit.dev](https://batas-admin.geoit.dev/) dalam format GeoJSON, berbeda dari Tugas 1 yang menggunakan polygon gambar bebas.

Kecamatan Cerme dipilih karena merupakan domisili penulis, dan karakternya berbeda dari kawasan industri di Tugas 1 — didominasi area pertanian dan permukiman, sehingga sumber NO2 di sini kemungkinan besar didominasi lalu lintas kendaraan dan aktivitas rumah tangga, bukan industri berat.

## 2. Preprocessing

### Deteksi Outlier (Metode IQR)

Outlier dideteksi menggunakan metode **Interquartile Range (IQR)**:

$$IQR = Q_3 - Q_1$$

Data dianggap outlier jika berada di luar rentang:

$$[\,Q_1 - 1.5 \times IQR,\ \ Q_3 + 1.5 \times IQR\,]$$

Nilai yang terdeteksi sebagai outlier diubah menjadi kosong (NaN) terlebih dahulu, untuk kemudian diisi ulang pada tahap imputasi.

### Imputasi Missing Value

Nilai kosong (baik dari data asli yang memang kosong — misal akibat tertutup awan pada citra satelit — maupun dari hasil deteksi outlier) diisi menggunakan:
1. **Interpolasi berbasis waktu** (`interpolate(method='time')`) — mengisi celah dengan estimasi berdasarkan tren nilai di sekitarnya.
2. **Forward-fill & backward-fill** — untuk mengisi sisa nilai kosong di ujung awal/akhir data yang tidak bisa diinterpolasi.

Hasil akhir: dataset NO2 tanpa nilai kosong dan tanpa outlier, siap diekstraksi fiturnya.

## 3. Ekstraksi 68 Fitur dengan TSFEL

**TSFEL (Time Series Feature Extraction Library)** adalah pustaka Python yang secara otomatis menghitung ratusan jenis fitur karakteristik dari data deret waktu (time series) hanya dengan memanggil fungsi-fungsi fitur yang tersedia.

Dari data NO2 Kecamatan Cerme (1 tahun, harian) yang sudah bersih, diekstraksi tepat **68 fitur** — setiap fitur meringkas satu karakteristik tertentu dari keseluruhan data setahun menjadi 1 angka (bukan lagi 1 angka per hari).

Source code ekstraksi: [`extract_features_cerme.py`](extract_features_cerme.py)
Hasil ekstraksi: [`NO2_Cerme_TSFEL.csv`](NO2_Cerme_TSFEL.csv)

## 4. Pengelompokan 68 Fitur Berdasarkan Domain

TSFEL mengelompokkan fitur ke dalam domain-domain berikut:

### Domain Statistical (20 fitur)

Fitur yang mendeskripsikan sebaran nilai data secara keseluruhan, tanpa memperhatikan urutan waktu.

`abs_energy, average_power, calc_max, calc_mean, calc_median, calc_min, calc_std, calc_var, ecdf, ecdf_percentile, ecdf_percentile_count, ecdf_slope, entropy, hist_mode, interq_range, kurtosis, mean_abs_deviation, median_abs_deviation, rms, skewness`

### Domain Temporal (16 fitur)

Fitur yang menangkap pola perubahan nilai dari waktu ke waktu.

`auc, autocorr, calc_centroid, distance, lempel_ziv, mean_abs_diff, mean_diff, median_abs_diff, median_diff, negative_turning, neighbourhood_peaks, pk_pk_distance, positive_turning, slope, sum_abs_diff, zero_cross`

### Domain Spectral (26 fitur)

Fitur berbasis transformasi frekuensi (FFT/wavelet), menangkap pola periodik/musiman dalam data.

`fundamental_frequency, human_range_energy, lpcc, max_frequency, max_power_spectrum, median_frequency, mfcc, power_bandwidth, spectral_centroid, spectral_decrease, spectral_distance, spectral_entropy, spectral_kurtosis, spectral_positive_turning, spectral_roll_off, spectral_roll_on, spectral_skewness, spectral_slope, spectral_spread, spectral_variation, spectrogram_mean_coeff, wavelet_abs_mean, wavelet_energy, wavelet_entropy, wavelet_std, wavelet_var`

### Domain Fractal (6 fitur — kategori tambahan di luar 3 domain utama)

Fitur yang mengukur kompleksitas/self-similarity sinyal.

`dfa, higuchi_fractal_dimension, hurst_exponent, maximum_fractal_length, mse, petrosian_fractal_dimension`

**Ringkasan:** Statistical (20) + Temporal (16) + Spectral (26) + Fractal (6) = **68 fitur**

## 5. Hasil & Interpretasi

- `calc_mean` (rata-rata NO2 setahun): 5.26e-05. Rata-rata konsentrasi NO₂ relatif rendah (sekitar 0.000052 unit, kemungkinan dalam skala normalisasi atau ppm/ppb tergantung preprocessing). Artinya baseline polusi NO₂ di Cerme tidak terlalu tinggi sepanjang tahun.
- `calc_std` (variasi NO2): 2.17e-05. Variasi cukup moderat. Ada fluktuasi, tapi tidak ekstrem. Jadi polusi NO₂ di Cerme cenderung stabil, meski tetap ada naik-turun harian/mingguan.
- `spectral_entropy`: 0.77. Nilai mendekati 1 untuk pola NO₂ lebih acak, tidak terlalu periodik. Artinya sumber emisi bercampur (transportasi, aktivitas rumah tangga, mungkin sedikit industri), sehingga tidak ada siklus harian/mingguan yang sangat kuat.
- `autocorr`: 3.0. Angka ini menunjukkan ada pola berulang, tapi tidak terlalu dominan. Bisa jadi ada sedikit pola mingguan (misalnya Senin–Jumat lebih tinggi, akhir pekan lebih rendah), tapi tidak sekuat kota besar dengan lalu lintas padat.

# Interpretasi:

- Transportasi: kemungkinan jadi faktor utama, tapi tidak terlalu padat. Oleh sebab itu mean rendah dan entropy tinggi (acak).
- Industri/pertanian: tidak tampak pola musiman kuat dari data ini.
- Kehidupan harian: ada sedikit pola berulang (autocorr), mungkin jam sibuk pagi–sore, tapi tidak konsisten sepanjang tahun.

## Pengumpulan

File `NO2_Cerme_TSFEL.csv` (tanpa modifikasi) telah diunggah ke sistem pengumpulan kelas: [psd.basisdata2-c.my.id](https://psd.basisdata2-c.my.id/index.php), atas nama [Nama Kamu], Kecamatan Cerme.

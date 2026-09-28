# Fitur: Negative Turning Points

**Nama:** Robbaniyah Umdatun Ni'mah
**Fitur yang dijelaskan:** `negative_turning(signal)`
**Domain TSFEL:** Temporal
**Data yang digunakan:** CO, NO2, SO2 Kecamatan Cerme (data pribadi)

## 1. Konsep Dasar

**Negative turning point** adalah titik pada sinyal di mana nilainya berubah dari **menurun** menjadi **naik**, dengan kata lain, titik tersebut adalah **local minimum (titik lembah lokal)** pada sinyal. Fitur ini menghitung **berapa kali** kejadian seperti ini muncul sepanjang keseluruhan data.

Fitur ini termasuk domain **Temporal** karena murni mengandalkan urutan nilai dari waktu ke waktu (bukan nilai absolutnya), untuk menangkap seberapa sering sinyal "berbalik arah dari turun ke naik". semakin banyak negative turning points, semakin sering/fluktuatif sinyalnya naik-turun (bukan tren yang mulus).

## 2. Rumus

Diberikan sinyal $x_1, x_2, ..., x_n$, hitung dulu selisih antar titik berurutan:

$$\Delta_i = x_{i+1} - x_i$$

Titik ke-$i$ (dengan $2 \le i \le n-1$) disebut **negative turning point** jika:

$$\Delta_{i-1} < 0 \quad \text{dan} \quad \Delta_i > 0$$

(artinya: sebelum titik ini sinyal sedang turun, setelah titik ini sinyal mulai naik — titik ini adalah lembahnya)

$$\text{negative\_turning} = \sum_{i=2}^{n-1} \mathbb{1}\left[\Delta_{i-1} < 0 \ \text{dan} \ \Delta_i > 0\right]$$

## 3. Contoh Perhitungan Manual CO

Menggunakan cuplikan 10 hari pertama data CO Kecamatan Cerme:


| Hari ke | Nilai CO (x) | Selisih (Δ) |
|---|---|---|
2025-08-31 | 0.026594 | - |
2025-09-01 | 0.024891 | Delta1 = 0.024891 - 0.026594 = -0.001702 |
2025-09-02 | 0.024403 | Delta2 = 0.024403 - 0.024891 = -0.000488 |
2025-09-03 | 0.024798 | Delta3 = 0.024798 - 0.024403 = 0.000395 |
2025-09-04 | 0.027628 | Delta4 = 0.027628 - 0.024798 = 0.002831 |
2025-09-05 | 0.032402 | Delta5 = 0.032402 - 0.027628 = 0.004774 |
2025-09-06 | 0.029381 | Delta6 = 0.029381 - 0.032402 = -0.003021 |
2025-09-09 | 0.032387 | Delta7 = 0.032387 - 0.029381 = 0.003005 |
2025-09-10 | 0.023247 | Delta8 = 0.023247 - 0.032387 = -0.009140 |
2025-09-12 | 0.032229 | Delta9 = 0.032229 - 0.023247 = 0.008981 |

**Jumlah negative turning points (manual, 10 hari pertama):** 3
**Hasil TSFEL:** 3.0
**Status:** Cocok

## 4. Contoh Perhitungan Manual NO2

| Hari ke | Nilai NO2 (x) | Selisih (Δ) |
|---|---|---|
2025-08-31 | 0.000046 | - |
2025-09-01 | 0.000036 | Delta1 = 0.000036 - 0.000046 = -0.000010 |
2025-09-02 | 0.000020 | Delta2 = 0.000020 - 0.000036 = -0.000016 |
2025-09-03 | 0.000038 | Delta3 = 0.000038 - 0.000020 = 0.000018 |
2025-09-04 | 0.000057 | Delta4 = 0.000057 - 0.000038 = 0.000018 |
2025-09-05 | 0.000086 | Delta5 = 0.000086 - 0.000057 = 0.000029 |
2025-09-07 | 0.000069 | Delta6 = 0.000069 - 0.000086 = -0.000017 |
2025-09-10 | 0.000080 | Delta7 = 0.000080 - 0.000069 = 0.000011 |
2025-09-11 | 0.000035 | Delta8 = 0.000035 - 0.000080 = -0.000045 |
2025-09-12 | 0.000066 | Delta9 = 0.000066 - 0.000035 = 0.000031 |

**Jumlah negative turning points (manual, 10 hari pertama):** 3
**Hasil TSFEL:** 3.0
**Status:** Cocok

## 5. Contoh Perhitungan Manual SO2


| Hari ke | Nilai SO2 (x) | Selisih (Δ) |
|---|---|---|
2025-08-31 | 0.000052 | - |
2025-09-01 | -0.000001 | Delta1 = -0.000001 - 0.000052 = -0.000053
2025-09-02 | 0.000021 | Delta2 = 0.000021 - -0.000001 = 0.000022
2025-09-03 | 0.000056 | Delta3 = 0.000056 - 0.000021 = 0.000035
2025-09-04 | 0.000038 | Delta4 = 0.000038 - 0.000056 = -0.000018
2025-09-05 | -0.000016 | Delta5 = -0.000016 - 0.000038 = -0.000054
2025-09-06 | -0.000012 | Delta6 = -0.000012 - -0.000016 = 0.000003
2025-09-07 | 0.000002 | Delta7 = 0.000002 - -0.000012 = 0.000015
2025-09-08 | 0.000061 | Delta8 = 0.000061 - 0.000002 = 0.000058
2025-09-09 | 0.000006 | Delta9 = 0.000006 - 0.000061 = -0.000055

**Jumlah negative turning points (manual, 10 hari pertama):** 2
**Hasil TSFEL:** 2.0
**Status:** Cocok

## 6. Ringkasan Perbandingan 3 Polutan

| Polutan | Jumlah negative_turning (setahun penuh) |
|---|---|
| CO | 77 (264 hari) |
| NO2 | 66 (232 hari)|
| SO2 | 118 (364 hari)|

## 7. Interpretasi

Nilai `negative_turning` yang tinggi pada suatu polutan mengindikasikan konsentrasinya **sering naik-turun secara tidak beraturan** (misalnya dipengaruhi variasi lalu lintas harian atau cuaca), bukan mengikuti tren yang mulus/musiman. Perbandingan antar polutan (CO vs NO2 vs SO2) di Kecamatan Cerme bisa menunjukkan mana yang sumbernya lebih "sporadis" (misal CO dari kendaraan, cenderung naik-turun harian) dibanding yang lebih stabil/musiman (misal SO2 dari sumber industri jauh yang pengaruhnya lebih konstan).

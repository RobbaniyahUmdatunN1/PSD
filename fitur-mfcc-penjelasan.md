# Fitur: MFCC (Mel-Frequency Cepstral Coefficients)

**Nama:** Robbaniyah Umdatun Ni'mah
**Fitur yang dijelaskan:** `mfcc(signal, fs[, pre_emphasis, nfft, ...])`
**Domain TSFEL:** Spectral

## 1. Konsep Dasar

MFCC (Mel-Frequency Cepstral Coefficients) adalah fitur yang awalnya dikembangkan untuk pengolahan sinyal suara/audio, yang menangkap **bentuk spektrum frekuensi sinyal dengan cara meniru persepsi pendengaran manusia**. Manusia lebih peka terhadap perbedaan frekuensi rendah dibanding frekuensi tinggi. MFCC mengakomodasi ini lewat **skala Mel**, sebuah transformasi frekuensi yang non-linear (lebih rapat di frekuensi rendah, lebih renggang di frekuensi tinggi).

Dalam konteks TSFEL, MFCC diterapkan pada sinyal time-series apa pun (bukan cuma audio) sebagai cara mengekstrak pola bentuk spektral yang ringkas dari sinyal tersebut.

## 2. Alur Perhitungan (Pipeline)

MFCC dihitung melalui 6 tahap berurutan:

### Tahap 1: Pre-emphasis (opsional)

Menguatkan komponen frekuensi tinggi pada sinyal, untuk menyeimbangkan spektrum:

$$y[n] = x[n] - \alpha \cdot x[n-1]$$

dengan $\alpha$ (pre_emphasis) biasanya bernilai 0,97.

### Tahap 2: Transformasi Fourier (FFT)

Mengubah sinyal dari domain waktu ke domain frekuensi:

$$X(k) = \sum_{n=0}^{N-1} y[n] \cdot e^{-j 2\pi kn/N}$$

### Tahap 3: Power Spectrum

$$P(k) = \frac{|X(k)|^2}{N}$$

### Tahap 4: Filter Bank Mel

Frekuensi (Hz) dikonversi ke skala Mel:

$$\text{mel}(f) = 2595 \cdot \log_{10}\left(1 + \frac{f}{700}\right)$$

Dipasang serangkaian **filter segitiga** (default 40 filter) yang tersebar merata pada skala Mel, lalu **dinormalisasi berdasarkan lebar filter** (supaya filter yang lebih lebar di frekuensi tinggi tidak "membesar-besarkan" energi secara tidak proporsional):

$$\text{enorm}_m = \frac{2}{f_{m+1} - f_{m-1}}$$

Energi spektrum di tiap filter (setelah dinormalisasi) dijumlahkan:

$$S(m) = \text{enorm}_m \cdot \sum_{k} P(k) \cdot H_m(k)$$

### Tahap 5: Logaritma (skala desibel)

$$20 \cdot \log_{10}(S(m))$$

### Tahap 6: Discrete Cosine Transform (DCT), tipe-2 ortonormal

Menghasilkan koefisien cepstral, mengambil koefisien ke-1 sampai ke-12 (koefisien ke-0 dibuang):

$$C(n) = \sqrt{\frac{2}{M}} \sum_{m=0}^{M-1} \log(S(m)) \cdot \cos\left(\frac{\pi(2m+1)n}{2M}\right), \quad n = 1, ..., 12$$

### Tahap 7: Mean Normalization

$$C'(n) = C(n) - \left(\overline{C} + 10^{-8}\right)$$

### Tahap 8: Cepstral Liftering

Langkah terakhir untuk mengurangi bobot koefisien orde tinggi:

$$\text{lift}(n) = 1 + \frac{L}{2}\sin\left(\frac{\pi n}{L}\right), \quad L = 22 \text{ (cep\_lifter)}$$

$$\text{MFCC}(n) = C'(n) \cdot \text{lift}(n)$$

**Catatan penting:** hasil akhir MFCC berupa **12 koefisien sekaligus** (bukan 1 angka), sehingga saat digunakan sebagai 1 kolom fitur, nilai-nilai koefisien tersebut dirata-ratakan menjadi 1 angka ringkasan.

## 3. Contoh Perhitungan (Dibuktikan dengan Kode)

Karena melibatkan FFT dan filter bank yang kompleks, perhitungan manual "di atas kertas" untuk data riil tidak praktis. Sebagai gantinya, dibuat **implementasi manual dari nol menggunakan NumPy** (tanpa memanggil fungsi MFCC bawaan library manapun), lalu hasilnya dibandingkan dengan fungsi `tsfel.feature_extraction.features.mfcc()` untuk membuktikan rumus di atas sudah diterapkan dengan benar.

Lihat script pembuktian: [`verifikasi_mfcc_3polutan.py`](verifikasi_mfcc_3polutan.py)

Ringkasan alur pembuktian:
1. Signal NO2/CO/SO2 Kecamatan Cerme (data harian setahun) digunakan sebagai input, untuk masing-masing dari 3 polutan.
2. Implementasi manual (pre-emphasis → FFT → power spectrum → filter bank Mel + normalisasi luas → log dB → DCT ortonormal → mean normalization → cepstral liftering) dijalankan menggunakan NumPy dan SciPy (`scipy.fftpack.dct`).
3. Hasil MFCC dari implementasi manual dibandingkan dengan hasil `tsfel_features.mfcc()` untuk data yang sama.
4. **Hasil: selisih = 0.0 (cocok sempurna)** untuk ketiga polutan, membuktikan rumus di atas sudah diterapkan dengan benar dan identik dengan implementasi asli TSFEL.

**Hasil bisa dilihat:**
**POLUTAN: CO**
Koefisien MFCC (manual, 12 koefisien): 
[-29.7058 -11.0509  -7.3303  20.3376  79.243  -27.4087  51.5839 -17.9131
  84.6548  26.1903  69.8192  53.535 ]

Koefisien MFCC (TSFEL, 12 koefisien):
[-29.7058 -11.0509  -7.3303  20.3376  79.243  -27.4087  51.5839 -17.9131
  84.6548  26.1903  69.8192  53.535 ]

Selisih maksimum antar koefisien: 0.00000000
=> COCOK SEMPURNA

**POLUTAN: NO2**
Koefisien MFCC (manual, 12 koefisien): 
[-29.862  -45.6672 -37.7367  16.6995 -24.4272  85.2586 138.91   119.0468
  60.8137  35.1996  51.2277  91.0484]

Koefisien MFCC (TSFEL, 12 koefisien): 
[-29.862  -45.6672 -37.7367  16.6995 -24.4272  85.2586 138.91   119.0468
  60.8137  35.1996  51.2277  91.0484]

Selisih maksimum antar koefisien: 0.00000000
=> COCOK SEMPURNA

**POLUTAN: SO2**
Koefisien MFCC (manual, 12 koefisien): 
[-48.9099 -50.4393 -30.8259  -5.0579  16.6457 117.9598  65.2982  77.0791
 117.3402 166.5438 181.576   64.1536]

Koefisien MFCC (TSFEL, 12 koefisien): 
[-48.9099 -50.4393 -30.8259  -5.0579  16.6457 117.9598  65.2982  77.0791
 117.3402 166.5438 181.576   64.1536]

Selisih maksimum antar koefisien: 0.00000000
=> COCOK SEMPURNA

## 4. Interpretasi

Nilai MFCC yang tinggi/rendah mengindikasikan bentuk spektrum frekuensi sinyal NO2 (atau polutan lain) secara keseluruhan, apakah energi sinyal terkonsentrasi di frekuensi rendah (perubahan lambat/musiman) atau tersebar ke frekuensi tinggi (fluktuasi harian yang tajam/tidak teratur).

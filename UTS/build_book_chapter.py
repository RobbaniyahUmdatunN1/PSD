"""Bangun bab Jupyter Book (klasifikasi_lulc.md) berisi seluruh PROSES analisis.
Hasilnya ditaruh di folder proyek ini; daftarkan di _toc.yml milik web statismu.

Pemakaian: python build_book_chapter.py [--streamlit-url https://xxx.streamlit.app]
"""
import argparse, json
import config as C


def md_table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(x).replace("|", "\\|") for x in r) + " |" for r in rows]
    return "\n".join(out) + "\n"


def img(name, caption):
    return f"![{caption}](results/{name})\n" if (C.RESULT_DIR / name).exists() else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--streamlit-url", default="")
    args = ap.parse_args()
    R = json.load(open(C.RESULTS_JSON)) if C.RESULTS_JSON.exists() else None
    M = json.load(open(C.MAP_META)) if C.MAP_META.exists() else None

    L = ["# Klasifikasi Penggunaan Lahan Jawa Timur (Sentinel-2A)\n"]
    if args.streamlit_url:
        L.append(f"**Sistem informasi (Streamlit):** <{args.streamlit_url}>\n")

    L.append("## 1. Data Understanding dan Tujuan Analisis\n")
    L += [f"- {t}" for t in C.TUJUAN]

    L.append("\n## 2. Pengumpulan Data\n")
    L.append(
        "1. **Label**: 6 file GeoJSON poligon sampel, masing-masing 60 poligon (total 360), tersebar di Jawa Timur.\n"
        "2. **Citra**: Sentinel-2A Level-2A (`COPERNICUS/S2_SR_HARMONIZED`) di Google Earth Engine, tahun 2025, "
        "filter `SPACECRAFT_NAME = Sentinel-2A`, masking awan Cloud Score+ (cs_cdf >= 0,6), komposit median, "
        "reflektansi dibagi 10.000.\n"
        "3. **Ekstraksi**: 50 titik acak per poligon (10 m), nilai 10 band dan 8 indeks per titik, diekspor ke CSV.\n"
        "4. **Pembersihan**: buang nilai kosong/tak hingga, batasi indeks rasio (EVI, MVI), seimbangkan jumlah titik per kelas.\n"
        "5. **Pembagian data**: train/test dipisah *per poligon* (80:20) untuk mencegah kebocoran spasial.\n")

    L.append("## 3. Band Sentinel-2A\n")
    L.append(md_table(["Band", "Nama", "Panjang gelombang (nm)", "Resolusi (m)", "Kegunaan", "Dipakai"],
                      [[b, n, w, r, u, "Ya" if used else "Tidak"] for b, n, w, r, u, used in C.S2_BANDS]))
    L.append("B1, B9, B10 tidak dipakai (koreksi atmosfer/deteksi awan, resolusi 60 m; B10 tidak ada di produk L2A).\n")

    L.append("## 4. Skema Kelas dan Acuan Klasifikasi Lahan Indonesia\n")
    L.append("Mengacu pada SNI 7645-1:2014 dan klasifikasi penutup lahan KLHK (23 kelas), diagregasi menjadi 6 kelas.\n")
    L.append(md_table(["ID", "Kelas", "Warna", "Padanan klasifikasi Indonesia"],
                      [[c, n, col, ref] for c, n, col, _, ref in C.CLASSES]))

    L.append("## 5. Fitur dan Rumus\n")
    L.append(f"Total {len(C.FEATURES)} fitur: {len(C.BANDS)} band ({', '.join(C.BANDS)}) dan {len(C.INDICES)} indeks.\n")
    L.append(md_table(["Fitur", "Rumus", "Keterangan"], [[n, f"`{f}`", k] for n, f, k in C.INDEX_INFO]))

    if R:
        L.append("## 6. Jumlah Data dan Kelas\n")
        L.append(f"Jumlah kelas **{R['n_classes']}**, data latih **{R['n_train']}**, data uji **{R['n_test']}**.\n")
        L.append(md_table(["Kelas", "Poligon", "Titik (bersih)", "Train", "Test"],
                          [[n, R["n_polygons"].get(n, "-"), R["clean_counts_per_class"].get(n, "-"),
                            R["train_per_class"].get(n, 0), R["test_per_class"].get(n, 0)] for n in R["class_names"]]))
        L.append("## 7. Perbandingan Model\n")
        L.append(md_table(["Model", "CV akurasi (%)", "Akurasi uji (%)", "F1-macro uji (%)", "Kappa"],
                          [[m["model"] + (" (terbaik)" if m["model"] == R["best_model"] else ""),
                            f"{m['cv_acc_mean']*100:.2f} ± {m['cv_acc_std']*100:.2f}", f"{m['test_acc']*100:.2f}",
                            f"{m['test_f1_macro']*100:.2f}", f"{m['test_kappa']:.4f}"] for m in R["models"]]))
        L.append(f"Model terbaik (dipilih dari CV data latih): **{R['best_model']}**, akurasi uji "
                 f"**{R['best_test_acc']*100:.2f}%**, kappa **{R['best_test_kappa']:.4f}**.\n")
        L.append(img("perbandingan_model.png", "Perbandingan model"))
        L.append("## 8. Evaluasi Model Terbaik\n")
        L.append(img("confusion_matrix.png", "Confusion matrix") + img("feature_importance.png", "Kepentingan fitur"))
        L.append("## 9. Eksperimen Jumlah Data\n")
        L.append(md_table(["Fraksi data latih", "Jumlah", "Akurasi uji (%)"],
                          [[f"{c['fraksi']*100:.0f}%", c["n_train"], f"{c['test_acc']*100:.2f}"]
                           for c in R["data_size_experiment"]]))
        L.append(img("eksperimen_jumlah_data.png", "Eksperimen jumlah data"))
    else:
        L.append("## 6-9. Hasil\n\n_Belum ada results.json. Jalankan `python train_models.py` lalu bangun ulang bab ini._\n")

    if M:
        L.append("## 10. Hasil Klasifikasi dan Luas Kelas\n")
        L.append(img("klasifikasi_jatim.png", "Hasil klasifikasi (overlay)"))
        L.append(md_table(["Kelas", "Luas (ha)"], [[n, f"{v['luas_ha']:,.0f}"] for n, v in M["class_stats"].items()]))
        L.append("Luas bersifat indikatif karena dihitung dari raster kasar.\n")

    L.append("## 11. Analisis Kebijakan\n\n_Tulis interpretasimu di sini (alih fungsi sawah, kawasan terbangun, "
             "perlindungan mangrove) dengan merujuk dokumen kebijakan terkait._\n")

    out = C.ROOT / "klasifikasi_lulc.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"Tersimpan: {out}")


if __name__ == "__main__":
    main()

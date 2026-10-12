"""Bangun static_web/proses.html (self-contained) dari config.py + results/results.json.
Halaman ini berisi seluruh PROSES: tujuan, pengumpulan data, band Sentinel-2A, kelas,
fitur & rumus, jumlah data train/test, perbandingan model, dan hasil.
Bisa ditautkan dari web statis kamu, dan otomatis di-embed oleh app.py.
"""
import base64, json
from html import escape
import config as C


def img64(path):
    if not path.exists():
        return ""
    return f'<img src="data:image/png;base64,{base64.b64encode(path.read_bytes()).decode()}" alt="{path.stem}">'


def table(head, rows):
    h = "".join(f"<th>{escape(str(x))}</th>" for x in head)
    b = "".join("<tr>" + "".join(f"<td>{x}</td>" for x in r) + "</tr>" for r in rows)
    return f"<div class='scroll'><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>"


def main():
    R = json.load(open(C.RESULTS_JSON)) if C.RESULTS_JSON.exists() else None
    M = json.load(open(C.MAP_META)) if C.MAP_META.exists() else None
    s = []

    s.append("<h2>1. Data Understanding &amp; Tujuan Analisis</h2><ul>" +
             "".join(f"<li>{escape(t)}</li>" for t in C.TUJUAN) + "</ul>")

    s.append("<h2>2. Pengumpulan Data</h2><ol>"
             "<li><b>Label (ground truth)</b>: 6 file GeoJSON poligon sampel, masing-masing 60 poligon "
             "(total 360) tersebar di Jawa Timur, hasil digitasi visual di atas citra satelit.</li>"
             "<li><b>Citra</b>: Sentinel-2A Level-2A (<code>COPERNICUS/S2_SR_HARMONIZED</code>) di Google Earth Engine, "
             "tahun 2025, difilter <code>SPACECRAFT_NAME = Sentinel-2A</code>, masking awan dengan Cloud Score+ "
             "(cs_cdf &ge; 0,6), lalu komposit <i>median</i>. Reflektansi dibagi 10.000 (skala 0-1).</li>"
             "<li><b>Ekstraksi</b>: 50 titik acak per poligon (resolusi 10 m) &rarr; nilai 10 band + 8 indeks "
             "per titik &rarr; CSV.</li>"
             "<li><b>Pembersihan</b>: buang nilai kosong/tak hingga, batasi indeks rasio (EVI, MVI), "
             "seimbangkan jumlah titik per kelas.</li>"
             "<li><b>Pembagian data</b>: train/test dipisah <b>per poligon</b> (80:20) agar piksel bertetangga "
             "dari satu poligon tidak muncul di kedua sisi (mencegah kebocoran spasial).</li></ol>")

    s.append("<h2>3. Band Sentinel-2A</h2>" + table(
        ["Band", "Nama", "Panjang gelombang (nm)", "Resolusi (m)", "Kegunaan", "Dipakai"],
        [[b, n, w, r, escape(u), "Ya" if used else "Tidak"] for b, n, w, r, u, used in C.S2_BANDS]) +
        "<p class='note'>B1, B9, B10 tidak dipakai: ditujukan untuk koreksi atmosfer/deteksi awan "
        "dan beresolusi 60 m (B10 tidak tersedia di produk L2A).</p>")

    s.append("<h2>4. Skema Kelas &amp; Acuan Klasifikasi Lahan Indonesia</h2>"
             "<p>Skema mengacu pada klasifikasi penutup lahan nasional: <b>SNI 7645-1:2014</b> "
             "(Klasifikasi penutup lahan) dan klasifikasi penutup lahan <b>KLHK</b> (23 kelas). "
             "Karena keterbatasan data sampel, 23 kelas itu diagregasi menjadi 6 kelas berikut.</p>" +
             table(["ID", "Kelas", "Warna", "Padanan klasifikasi Indonesia"],
                   [[cid, n, f"<span class='sw' style='background:{col}'></span> {col}", escape(ref)]
                    for cid, n, col, _, ref in C.CLASSES]))

    s.append("<h2>5. Fitur &amp; Rumus</h2><p>Total <b>%d fitur</b>: %d band reflektansi + %d indeks spektral.</p>" %
             (len(C.FEATURES), len(C.BANDS), len(C.INDICES)) +
             table(["Fitur", "Rumus", "Keterangan"],
                   [[f"<b>{n}</b>", f"<code>{escape(f)}</code>", escape(k)] for n, f, k in C.INDEX_INFO]) +
             "<p class='note'>Band reflektansi yang dipakai: " + ", ".join(C.BANDS) + ".</p>")

    if R:
        s.append("<h2>6. Jumlah Data &amp; Kelas</h2>"
                 f"<p>Jumlah kelas: <b>{R['n_classes']}</b> &nbsp;|&nbsp; Data latih: <b>{R['n_train']}</b> "
                 f"&nbsp;|&nbsp; Data uji: <b>{R['n_test']}</b></p>" +
                 table(["Kelas", "Poligon", "Titik (bersih)", "Train", "Test"],
                       [[n, R["n_polygons"].get(n, "-"), R["clean_counts_per_class"].get(n, "-"),
                         R["train_per_class"].get(n, 0), R["test_per_class"].get(n, 0)]
                        for n in R["class_names"]]))
        rows = [[escape(m["model"]) + (" &#9733;" if m["model"] == R["best_model"] else ""),
                 f"{m['cv_acc_mean']*100:.2f} &plusmn; {m['cv_acc_std']*100:.2f}", f"{m['test_acc']*100:.2f}",
                 f"{m['test_f1_macro']*100:.2f}", f"{m['test_kappa']:.4f}"] for m in R["models"]]
        s.append("<h2>7. Perbandingan Model</h2>" +
                 table(["Model", "CV akurasi (%)", "Akurasi uji (%)", "F1-macro uji (%)", "Kappa"], rows) +
                 f"<p>Model terbaik (dipilih dari akurasi CV data latih): <b>{escape(R['best_model'])}</b> "
                 f"&mdash; akurasi uji <b>{R['best_test_acc']*100:.2f}%</b>, kappa <b>{R['best_test_kappa']:.4f}</b>.</p>" +
                 img64(C.RESULT_DIR / "perbandingan_model.png"))
        s.append("<h2>8. Evaluasi Model Terbaik</h2>" + img64(C.RESULT_DIR / "confusion_matrix.png") +
                 img64(C.RESULT_DIR / "feature_importance.png"))
        s.append("<h2>9. Eksperimen Jumlah Data</h2>" +
                 table(["Fraksi data latih", "Jumlah", "Akurasi uji (%)"],
                       [[f"{c['fraksi']*100:.0f}%", c["n_train"], f"{c['test_acc']*100:.2f}"]
                        for c in R["data_size_experiment"]]) + img64(C.RESULT_DIR / "eksperimen_jumlah_data.png"))
    else:
        s.append("<h2>6-9. Hasil</h2><p class='note'>Belum ada results.json. Jalankan "
                 "<code>python train_models.py</code> lalu bangun ulang halaman ini.</p>")

    if M:
        s.append("<h2>10. Luas Hasil Klasifikasi</h2>" +
                 table(["Kelas", "Luas (ha)", "Piksel"],
                       [[n, f"{v['luas_ha']:,.0f}", v["piksel"]] for n, v in M["class_stats"].items()]) +
                 "<p class='note'>Luas dihitung dari raster berresolusi kasar sehingga bersifat indikatif.</p>")

    html = f"""<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Proses Klasifikasi LULC Jawa Timur</title><style>
body{{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:0;padding:24px;line-height:1.55;color:#1d2733;background:#fff}}
main{{max-width:980px;margin:auto}} h1{{margin-top:0}} h2{{border-bottom:2px solid #2e86c1;padding-bottom:4px;margin-top:34px}}
table{{border-collapse:collapse;width:100%;font-size:14px;margin:10px 0}}
th,td{{border:1px solid #d5dbe1;padding:6px 9px;text-align:left;vertical-align:top}} th{{background:#eef3f8}}
code{{background:#f1f4f7;padding:1px 5px;border-radius:4px}} img{{max-width:100%;height:auto;margin:8px 0}}
.sw{{display:inline-block;width:14px;height:14px;border:1px solid #888;vertical-align:middle}}
.scroll{{overflow-x:auto}} .note{{color:#5c6b7a;font-size:13px}}
@media (prefers-color-scheme:dark){{body{{background:#0e1117;color:#e6e9ee}}th{{background:#1b2430}}
th,td{{border-color:#344052}}code{{background:#1b2430}}img{{background:#fff}}}}
</style></head><body><main>
<h1>Klasifikasi Penggunaan Lahan Jawa Timur (Sentinel-2A)</h1>
<p class="note">UTS Proyek Sains Data &ndash; SIG berbasis analisis spasial penggunaan lahan &amp; kebijakan</p>
{''.join(s)}
</main></body></html>"""
    out = C.STATIC_DIR / "proses.html"
    C.STATIC_DIR.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Tersimpan: {out} ({out.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()

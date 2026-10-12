Taruh web statis kamu di sini (index.html).
- app.py akan menampilkan static_web/index.html di menu "Proses (Web Statis)".
- Kalau belum ada, dipakai static_web/proses.html (dibuat otomatis oleh build_static_web.py).
- Supaya tidak rusak saat di-embed, pakai file self-contained (CSS/JS/gambar inline), atau host web statis
  (mis. GitHub Pages) lalu isi STATIC_WEB_URL di app.py.
- Tambahkan tautan ke proses.html dari index.html kamu untuk memasukkan seluruh proses ke web statis.

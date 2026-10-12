"""SIG Klasifikasi Penggunaan Lahan Jawa Timur (Sentinel-2A) - Streamlit.
Jalankan:  streamlit run app.py
"""
import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import folium
from folium.raster_layers import ImageOverlay
from streamlit_folium import st_folium

import config as C

# Jika web statis sudah di-host (mis. GitHub Pages), isi URL-nya di sini; kosongkan untuk embed file lokal.
STATIC_WEB_URL = ""

st.set_page_config(page_title="SIG LULC Jawa Timur", page_icon="🗺️", layout="wide")


@st.cache_data
def load_json(path):
    return json.load(open(path)) if path.exists() else None


R = load_json(C.RESULTS_JSON)
M = load_json(C.MAP_META)
POLYS = load_json(C.POLYGON_FILE)

page = st.sidebar.radio("Menu", ["🗺️ Peta Klasifikasi", "📘 Data Understanding",
                                 "📊 Evaluasi Model", "🌐 Proses (Web Statis)"])
st.sidebar.caption("Klasifikasi LULC Jawa Timur · Sentinel-2A · 6 kelas")


# ------------------------------------------------------------------ PETA
def legend_html():
    items = "".join(f"<div><span style='background:{col};width:12px;height:12px;display:inline-block;"
                    f"border:1px solid #333;margin-right:6px'></span>{n}</div>"
                    for _, n, col, _, _ in C.CLASSES)
    return ("<div style='position:fixed;bottom:28px;left:12px;z-index:9999;background:white;color:#111;"
            "padding:8px 10px;border-radius:6px;font-size:12px;box-shadow:0 1px 4px rgba(0,0,0,.4)'>"
            f"<b>Kelas Lahan</b>{items}</div>")


if page.startswith("🗺️"):
    st.title("Peta Hasil Klasifikasi Penggunaan Lahan - Jawa Timur")
    if M is None or not C.MAP_PNG.exists():
        st.warning("Hasil klasifikasi belum ada. Jalankan `python predict_map.py` terlebih dahulu.")
    c1, c2, c3 = st.columns(3)
    basemap = c1.selectbox("Basemap", ["Google Satelit", "Google Hybrid (satelit + label)", "OpenStreetMap"])
    opacity = c2.slider("Transparansi hasil klasifikasi", 0.0, 1.0, 0.7, 0.05)
    show_poly = c3.checkbox("Tampilkan poligon training", value=False)

    center = [-7.7, 112.6]
    m = folium.Map(location=center, zoom_start=8, tiles=None, control_scale=True)
    google = {"Google Satelit": "s", "Google Hybrid (satelit + label)": "y"}
    if basemap in google:
        folium.TileLayer(tiles=f"https://mt1.google.com/vt/lyrs={google[basemap]}&x={{x}}&y={{y}}&z={{z}}",
                         attr="Google", name=basemap, max_zoom=20).add_to(m)
    else:
        folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m)

    if M is not None and C.MAP_PNG.exists():
        ImageOverlay(image=str(C.MAP_PNG), bounds=M["bounds"], opacity=opacity,
                     name="Hasil klasifikasi", interactive=False, zindex=2).add_to(m)
    if show_poly and POLYS:
        folium.GeoJson(
            POLYS, name="Poligon training",
            style_function=lambda f: {"color": C.CLASS_COLORS[f["properties"]["class_id"]],
                                      "weight": 2, "fillOpacity": 0.15},
            tooltip=folium.GeoJsonTooltip(fields=["class_name", "poly_id"], aliases=["Kelas", "ID"])).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    m.get_root().html.add_child(folium.Element(legend_html()))
    st_folium(m, height=650, returned_objects=[])

    if M:
        st.subheader("Luas per kelas (indikatif)")
        df = pd.DataFrame([{"Kelas": k, "Luas (ha)": v["luas_ha"]} for k, v in M["class_stats"].items()])
        df["Persen (%)"] = (df["Luas (ha)"] / df["Luas (ha)"].sum() * 100).round(2)
        st.dataframe(df, hide_index=True)
        st.caption(f"Resolusi peta ≈ {M['pixel_size_deg'] * 111320:.0f} m/piksel. Basemap: tile Google Maps; "
                   "periksa ketentuan penggunaan Google untuk pemakaian di luar tugas.")


# ------------------------------------------------------------------ DATA UNDERSTANDING
elif page.startswith("📘"):
    st.title("Data Understanding")
    st.header("Tujuan analisis")
    for t in C.TUJUAN:
        st.markdown(f"- {t}")

    st.header("Pengumpulan data")
    st.markdown(
        "- **Label**: 6 GeoJSON poligon sampel (60 poligon/kelas, total 360) di Jawa Timur.\n"
        "- **Citra**: Sentinel-2A L2A (`COPERNICUS/S2_SR_HARMONIZED`), 2025, mask awan Cloud Score+, komposit median.\n"
        "- **Ekstraksi**: titik acak per poligon (10 m) → 10 band + 8 indeks → CSV.\n"
        "- **Split**: train/test dipisah *per poligon* (80:20) untuk mencegah kebocoran spasial.")

    st.header("Band Sentinel-2A")
    st.dataframe(pd.DataFrame(
        [{"Band": b, "Nama": n, "λ pusat (nm)": w, "Resolusi (m)": r, "Kegunaan": u,
          "Dipakai": "Ya" if used else "Tidak"} for b, n, w, r, u, used in C.S2_BANDS]),
        hide_index=True)

    st.header("Skema kelas & acuan klasifikasi lahan Indonesia")
    st.caption("Mengacu pada SNI 7645-1:2014 dan klasifikasi penutup lahan KLHK (23 kelas), diagregasi menjadi 6 kelas.")
    st.dataframe(pd.DataFrame([{"ID": c, "Kelas": n, "Warna": col, "Padanan klasifikasi Indonesia": ref}
                               for c, n, col, _, ref in C.CLASSES]), hide_index=True)

    st.header("Fitur & rumus")
    st.markdown("**Band reflektansi:** " + ", ".join(C.BANDS))
    st.dataframe(pd.DataFrame([{"Fitur": n, "Rumus": f, "Keterangan": k} for n, f, k in C.INDEX_INFO]),
                 hide_index=True)

    st.header("Jumlah data & kelas")
    if R:
        a, b, c = st.columns(3)
        a.metric("Jumlah kelas", R["n_classes"]); b.metric("Data latih", R["n_train"]); c.metric("Data uji", R["n_test"])
        st.dataframe(pd.DataFrame([{"Kelas": n, "Poligon": R["n_polygons"].get(n),
                                    "Train": R["train_per_class"].get(n, 0), "Test": R["test_per_class"].get(n, 0)}
                                   for n in R["class_names"]]), hide_index=True)
    else:
        st.info("Jalankan `python train_models.py` untuk menampilkan jumlah data latih/uji.")
        if POLYS:
            n = pd.Series([f["properties"]["class_name"] for f in POLYS["features"]]).value_counts()
            st.dataframe(n.rename("Jumlah poligon"))


# ------------------------------------------------------------------ EVALUASI
elif page.startswith("📊"):
    st.title("Evaluasi & Perbandingan Model")
    if not R:
        st.warning("Belum ada results.json. Jalankan `python train_models.py`.")
        st.stop()
    a, b, c = st.columns(3)
    a.metric("Model terbaik", R["best_model"])
    b.metric("Akurasi uji", f"{R['best_test_acc'] * 100:.2f}%")
    c.metric("Kappa", f"{R['best_test_kappa']:.4f}")

    df = pd.DataFrame(R["models"]).rename(columns={
        "model": "Model", "cv_acc_mean": "CV akurasi", "cv_acc_std": "CV std",
        "test_acc": "Akurasi uji", "test_f1_macro": "F1-macro uji", "test_kappa": "Kappa", "seconds": "Waktu (s)"})
    st.dataframe(df.sort_values("CV akurasi", ascending=False), hide_index=True)
    st.caption("Model terbaik dipilih dari akurasi cross-validation (GroupKFold per poligon) pada data latih, "
               "sehingga data uji tidak ikut menentukan pilihan.")

    left, right = st.columns(2)
    for col, f in ((left, "perbandingan_model.png"), (right, "confusion_matrix.png"),
                   (left, "feature_importance.png"), (right, "eksperimen_jumlah_data.png")):
        if (C.RESULT_DIR / f).exists():
            col.image(str(C.RESULT_DIR / f))

    st.subheader("Laporan per kelas")
    rep = pd.DataFrame(R["classification_report"]).T.round(4)
    st.dataframe(rep)


# ------------------------------------------------------------------ WEB STATIS
else:
    st.title("Proses Analisis (Web Statis)")
    if STATIC_WEB_URL:
        components.iframe(STATIC_WEB_URL, height=900, scrolling=True)
    else:
        index = C.STATIC_DIR / "index.html"
        proses = C.STATIC_DIR / "proses.html"
        target = index if index.exists() else proses
        if target.exists():
            if index.exists():
                st.caption("Menampilkan static_web/index.html. Pakai file yang self-contained "
                           "(CSS/JS/gambar inline) atau isi STATIC_WEB_URL di app.py jika tampilan rusak.")
            components.html(target.read_text(encoding="utf-8"), height=900, scrolling=True)
        else:
            st.warning("static_web/proses.html belum ada. Jalankan `python build_static_web.py`.")

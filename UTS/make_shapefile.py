"""Ubah data/training_polygons.geojson menjadi data/training_polygons_shp.zip
(Shapefile WGS84) agar bisa di-upload ke Google Earth Engine lewat
Assets > NEW > Table Upload > Shape files.

Murni Python standar, tidak butuh geopandas/fiona.
Pemakaian: python make_shapefile.py
"""
import json, struct, zipfile
import config as C

PRJ = ('GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],'
       'PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]')


def signed_area(ring):
    return sum((x1 * y2 - x2 * y1) for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1])) / 2.0


def orient(ring, clockwise):
    """Shapefile: ring luar searah jarum jam, lubang berlawanan."""
    is_cw = signed_area(ring) < 0
    return ring if is_cw == clockwise else ring[::-1]


def build(features):
    shp_recs, shx_recs, dbf_rows = [], [], []
    xs, ys, offset = [], [], 50                      # offset dalam satuan word 16-bit (header = 50)
    for i, ft in enumerate(features, 1):
        rings = ft["geometry"]["coordinates"]
        rings = [orient([tuple(p[:2]) for p in r[:-1]] if r[0] == r[-1] else [tuple(p[:2]) for p in r], k == 0)
                 for k, r in enumerate(rings)]
        rings = [r + [r[0]] for r in rings]          # tutup ring
        pts = [p for r in rings for p in r]
        px, py = [p[0] for p in pts], [p[1] for p in pts]
        xs += px; ys += py
        starts, n = [], 0
        for r in rings:
            starts.append(n); n += len(r)
        body = struct.pack("<i4d2i", 5, min(px), min(py), max(px), max(py), len(rings), len(pts))
        body += struct.pack(f"<{len(starts)}i", *starts)
        body += b"".join(struct.pack("<2d", x, y) for x, y in pts)
        words = len(body) // 2
        shp_recs.append(struct.pack(">2i", i, words) + body)
        shx_recs.append(struct.pack(">2i", offset, words))
        offset += 4 + words
        p = ft["properties"]
        dbf_rows.append((int(p["class_id"]), str(p["class_name"]), str(p["poly_id"])))

    def header(file_words):
        h = struct.pack(">i5ii", 9994, 0, 0, 0, 0, 0, file_words)
        h += struct.pack("<2i", 1000, 5)
        h += struct.pack("<8d", min(xs), min(ys), max(xs), max(ys), 0, 0, 0, 0)
        return h

    shp = header(offset) + b"".join(shp_recs)
    shx = header(50 + 4 * len(shx_recs)) + b"".join(shx_recs)

    # --- DBF
    fields = [("class_id", "N", 4), ("class_name", "C", 30), ("poly_id", "C", 10)]
    rec_len = 1 + sum(f[2] for f in fields)
    head_len = 32 + 32 * len(fields) + 1
    dbf = struct.pack("<4BIHH20x", 3, 126, 1, 1, len(dbf_rows), head_len, rec_len)
    for name, typ, ln in fields:
        dbf += name.encode().ljust(11, b"\0") + typ.encode() + b"\0" * 4 + bytes([ln, 0]) + b"\0" * 14
    dbf += b"\r"
    for cid, cname, pid in dbf_rows:
        dbf += b" " + str(cid).rjust(4).encode() + cname.encode("utf-8").ljust(30)[:30] + pid.encode().ljust(10)[:10]
    dbf += b"\x1a"
    return shp, shx, dbf


def main():
    feats = json.load(open(C.POLYGON_FILE))["features"]
    shp, shx, dbf = build(feats)
    out = C.DATA_DIR / "training_polygons_shp.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("training_polygons.shp", shp)
        z.writestr("training_polygons.shx", shx)
        z.writestr("training_polygons.dbf", dbf)
        z.writestr("training_polygons.prj", PRJ)
        z.writestr("training_polygons.cpg", "UTF-8")
    print(f"{len(feats)} poligon -> {out}")


if __name__ == "__main__":
    main()

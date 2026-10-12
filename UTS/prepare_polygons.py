"""Gabungkan 6 GeoJSON mentah menjadi satu file dengan atribut class_id, class_name, poly_id.
Pemakaian: python prepare_polygons.py <folder_geojson_mentah>"""
import json, sys
from pathlib import Path
from config import CLASSES, POLYGON_FILE

src = Path(sys.argv[1] if len(sys.argv) > 1 else "raw_geojson")
features = []
for cid, name, _, fname, _ in CLASSES:
    fc = json.load(open(src / fname))
    for i, ft in enumerate(fc["features"], 1):
        geom = ft["geometry"]
        assert geom["type"] == "Polygon" and len(geom["coordinates"][0]) >= 4, (fname, i)
        features.append({"type": "Feature", "geometry": geom,
                         "properties": {"class_id": cid, "class_name": name,
                                        "poly_id": f"{cid}_{i:03d}"}})
POLYGON_FILE.parent.mkdir(exist_ok=True)
json.dump({"type": "FeatureCollection", "features": features}, open(POLYGON_FILE, "w"))
print(f"{len(features)} poligon -> {POLYGON_FILE}")

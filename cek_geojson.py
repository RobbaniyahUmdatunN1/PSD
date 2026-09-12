import json

with open("cerme-boundary.geojson", "r") as f:
    data = json.load(f)

print("Tipe utama:", data.get("type"))

if data["type"] == "FeatureCollection":
    features = data["features"]
    print(f"Jumlah features: {len(features)}")
    for i, feat in enumerate(features[:5]):
        geom = feat.get("geometry", {})
        print(f"  Feature {i}: geometry type = {geom.get('type')}, "
              f"jumlah koordinat level-1 = {len(geom.get('coordinates', []))}")
        props = feat.get("properties", {})
        print(f"    properties: {props}")
else:
    print("Geometry type:", data.get("type"))
    print("Jumlah koordinat level-1:", len(data.get("coordinates", [])))

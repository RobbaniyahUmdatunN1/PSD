/**
 * UTS Proyek Sains Data - Klasifikasi LULC Jawa Timur (Sentinel-2A)
 * Jalankan di https://code.earthengine.google.com
 *
 * LANGKAH SEBELUM RUN:
 *  1. Assets > NEW > Table upload > Shape files -> pilih data/training_polygons_shp.zip
 *  2. Ganti ASSET_POLYGON di bawah dengan path asset hasil upload tadi.
 *  3. Run, lalu buka tab Tasks (kanan atas) dan klik RUN untuk 2 task export:
 *       - training_samples_jatim  (CSV)
 *       - fitur_jatim_250m        (GeoTIFF)
 *  4. Unduh dari Google Drive (folder GEE_UTS) ke:
 *       data/training_samples.csv   dan   data/raster/*.tif
 */

// ======================= 1. PARAMETER =======================
var ASSET_POLYGON = 'projects/NAMA-PROJECT/assets/training_polygons'; // <-- GANTI
var DATE_START = '2025-01-01';
var DATE_END   = '2026-01-01';
var N_PER_POLY = 50;      // titik acak per poligon -> 60 poligon x 50 = 3000 titik/kelas (EKSPERIMEN: 25/50/100)
var SAMPLE_SCALE = 10;    // meter
var SEED = 42;
var PREDICT_SCALE = 250;  // resolusi raster peta hasil (makin halus = file makin besar)
var CS_THRESHOLD = 0.6;   // ambang Cloud Score+ (makin tinggi makin ketat)

// Bounding box Jawa Timur + perairan sekitarnya (Selat Madura, Laut Jawa, Samudra Hindia, P. Bawean)
var AOI = ee.Geometry.Rectangle([110.9, -8.9, 114.6, -5.6]);

var BANDS = ['B2','B3','B4','B5','B6','B7','B8','B8A','B11','B12'];
// URUTAN INI HARUS SAMA DENGAN config.FEATURES di Python
var FEATURES = BANDS.concat(['NDVI','NDWI','MNDWI','NDBI','NDMI','EVI','SAVI','MVI']);

// ======================= 2. KOMPOSIT SENTINEL-2A =======================
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(AOI)
  .filterDate(DATE_START, DATE_END)
  .filter(ee.Filter.eq('SPACECRAFT_NAME', 'Sentinel-2A'));

var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');
var s2Clean = s2
  .linkCollection(csPlus, ['cs_cdf'])
  .map(function (img) { return img.updateMask(img.select('cs_cdf').gte(CS_THRESHOLD)); });

print('Jumlah scene Sentinel-2A:', s2.size());

// reflektansi L2A dikali 10000 -> skala 0-1
var base = s2Clean.select(BANDS).median().divide(10000);

function addIndices(img) {
  var b = {BLUE: img.select('B2'), GREEN: img.select('B3'), RED: img.select('B4'),
           NIR: img.select('B8'), SWIR: img.select('B11')};
  return img.addBands([
    img.normalizedDifference(['B8','B4']).rename('NDVI'),
    img.normalizedDifference(['B3','B8']).rename('NDWI'),
    img.normalizedDifference(['B3','B11']).rename('MNDWI'),
    img.normalizedDifference(['B11','B8']).rename('NDBI'),
    img.normalizedDifference(['B8','B11']).rename('NDMI'),
    img.expression('2.5 * (NIR - RED) / (NIR + 6*RED - 7.5*BLUE + 1)', b).rename('EVI'),
    img.expression('1.5 * (NIR - RED) / (NIR + RED + 0.5)', b).rename('SAVI'),
    img.expression('(NIR - GREEN) / (SWIR - GREEN)', b).rename('MVI')
  ]);
}
var comp = addIndices(base).select(FEATURES).toFloat();

// ======================= 3. POLIGON & TITIK SAMPEL =======================
var polys = ee.FeatureCollection(ASSET_POLYGON);
print('Poligon per kelas:', polys.aggregate_histogram('class_name'));

var points = polys.map(function (f) {
  var pts = ee.FeatureCollection.randomPoints({region: f.geometry(), points: N_PER_POLY, seed: SEED});
  return pts.map(function (p) {
    return p.set({class_id: f.get('class_id'), class_name: f.get('class_name'), poly_id: f.get('poly_id')});
  });
}).flatten();

var samples = comp.sampleRegions({collection: points, scale: SAMPLE_SCALE, geometries: true, tileScale: 8})
  .map(function (f) {
    var c = f.geometry().coordinates();
    return f.set({lon: c.get(0), lat: c.get(1)});
  });

print('Titik sampel per kelas:', samples.aggregate_histogram('class_name'));

// ======================= 4. VISUALISASI CEK =======================
Map.centerObject(AOI, 8);
Map.addLayer(comp, {bands: ['B4','B3','B2'], min: 0.0, max: 0.3}, 'True color');
Map.addLayer(comp.select('NDVI'), {min: -0.2, max: 0.9, palette: ['blue','white','green']}, 'NDVI', false);
Map.addLayer(polys, {color: 'red'}, 'Poligon training', false);

// ======================= 5. EXPORT =======================
Export.table.toDrive({
  collection: samples,
  description: 'training_samples_jatim',
  folder: 'GEE_UTS',
  fileFormat: 'CSV',
  selectors: ['class_id', 'class_name', 'poly_id', 'lon', 'lat'].concat(FEATURES)
});

Export.image.toDrive({
  image: comp.unmask(-9999),          // -9999 = nodata
  description: 'fitur_jatim_' + PREDICT_SCALE + 'm',
  folder: 'GEE_UTS',
  region: AOI,
  scale: PREDICT_SCALE,
  crs: 'EPSG:4326',
  maxPixels: 1e10,
  fileFormat: 'GeoTIFF'
});

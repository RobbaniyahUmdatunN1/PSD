"""
Migrasi data gresik_pollutant_data.csv ke PostgreSQL (Aiven)

Cara pakai:
    pip install psycopg2-binary pandas sqlalchemy python-dotenv
    Buat file '.env' (copy dari '.env.example'), isi kredensial asli kamu di situ.
    Jalankan: python migrate_csv_to_postgres.py

PENTING: File '.env' JANGAN pernah di-push ke GitHub (sudah otomatis
di-ignore lewat .gitignore). Yang di-push cukup '.env.example' sebagai
contoh format, tanpa data asli.
"""

import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# ------------------------------------------------------------------
# 1. BACA KREDENSIAL DARI FILE .env (BUKAN ditulis langsung di kode!)
# ------------------------------------------------------------------
load_dotenv()

AIVEN_CONFIG = {
    "host": os.getenv("AIVEN_HOST"),
    "port": os.getenv("AIVEN_PORT"),
    "database": os.getenv("AIVEN_DATABASE"),
    "user": os.getenv("AIVEN_USER"),
    "password": os.getenv("AIVEN_PASSWORD"),
}

if not all(AIVEN_CONFIG.values()):
    raise RuntimeError(
        "Kredensial belum lengkap. Pastikan file '.env' sudah dibuat "
        "dan berisi AIVEN_HOST, AIVEN_PORT, AIVEN_DATABASE, AIVEN_USER, AIVEN_PASSWORD."
    )

TABLE_NAME = "polutan_gresik"
CSV_PATH = "gresik_pollutant_data.csv"

# ------------------------------------------------------------------
# 2. BUAT KONEKSI KE POSTGRESQL
#    sslmode=require WAJIB untuk Aiven (mereka mewajibkan koneksi terenkripsi)
# ------------------------------------------------------------------
connection_string = (
    f"postgresql+psycopg2://{AIVEN_CONFIG['user']}:{AIVEN_CONFIG['password']}"
    f"@{AIVEN_CONFIG['host']}:{AIVEN_CONFIG['port']}/{AIVEN_CONFIG['database']}"
    f"?sslmode=require"
)
engine = create_engine(connection_string)

# ------------------------------------------------------------------
# 3. BACA CSV
# ------------------------------------------------------------------
print(f"Membaca {CSV_PATH} ...")
df = pd.read_csv(CSV_PATH, parse_dates=["date"])
print(f"Ditemukan {len(df)} baris, {len(df.columns)} kolom: {list(df.columns)}")

# ------------------------------------------------------------------
# 4. UPLOAD KE POSTGRESQL
#    if_exists="replace" -> kalau tabel sudah ada, akan ditimpa (biar bisa dijalankan ulang)
#    Ganti ke "append" kalau mau nambah data tanpa menghapus yang lama
# ------------------------------------------------------------------
print(f"Mengupload ke tabel '{TABLE_NAME}' di PostgreSQL Aiven ...")
df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False)
print("Selesai! Data berhasil dipindahkan ke PostgreSQL.")

# ------------------------------------------------------------------
# 5. VERIFIKASI: BACA ULANG BEBERAPA BARIS DARI DATABASE
# ------------------------------------------------------------------
check = pd.read_sql(f"SELECT * FROM {TABLE_NAME} LIMIT 5", engine)
print("\nContoh data dari database (5 baris pertama):")
print(check)

print(f"\nTotal baris di database: {pd.read_sql(f'SELECT COUNT(*) FROM {TABLE_NAME}', engine).iloc[0, 0]}")

"""
Convert data/sekolah_lengkap.csv (hasil 08_scrape_sekolah_lengkap.py) jadi
GeoJSON titik per kabupaten, formatnya dibikin sama persis dengan pola nama file
yang sudah dipakai di folder public/data/geojson/desa/.

Jalankan ini SETELAH 08_scrape_sekolah_lengkap.py selesai (atau minimal Tahap A
selesai kalau mau lihat sekolah tanpa titik dulu).

Cara pakai:
    python 09_build_sekolah_geojson.py

Output:
    public/data/geojson/sekolah/kabupaten_<nama>_sekolah.geojson
    public/data/geojson/sekolah/kota_<nama>_sekolah.geojson
"""

import os
import json
import pandas as pd

INPUT_CSV = "data/sekolah_lengkap.csv"
OUTPUT_DIR = "public/data/geojson/sekolah"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def tentukan_bentuk(nama_sekolah):
    n = nama_sekolah.upper()
    if n.startswith(("SD", "MI")):
        return "SD"
    if n.startswith(("SMP", "MTS")):
        return "SMP"
    if n.startswith(("SMA", "MA")):
        return "SMA"
    if n.startswith("SMK"):
        return "SMK"
    return "LAINNYA"


def slug_kabupaten(nama_kab):
    nama = nama_kab.strip()
    is_kota = nama.upper().startswith("KOTA")
    nama_bersih = nama.replace("KOTA ", "").replace("Kota ", "")
    slug = nama_bersih.lower().replace(" ", "_")
    prefix = "kota" if is_kota else "kabupaten"
    return f"{prefix}_{slug}_sekolah.geojson"


def main():
    if not os.path.exists(INPUT_CSV):
        print(f"File {INPUT_CSV} belum ada. Jalankan 08_scrape_sekolah_lengkap.py dulu.")
        return

    df = pd.read_csv(INPUT_CSV, dtype=str)
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    total = len(df)
    ada_koordinat = df["latitude"].notna().sum()
    print(f"Total baris: {total}, punya koordinat: {ada_koordinat} ({ada_koordinat/total*100:.1f}%)")

    df_valid = df.dropna(subset=["latitude", "longitude"]).copy()
    df_valid["bentuk"] = df_valid["nama_sekolah"].apply(tentukan_bentuk)

    jumlah_file = 0
    for kabupaten, grup in df_valid.groupby("kabupaten"):
        features = []
        for _, row in grup.iterrows():
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [row["longitude"], row["latitude"]],
                },
                "properties": {
                    "npsn": row["npsn"],
                    "nama_sekolah": row["nama_sekolah"],
                    "bentuk": row["bentuk"],
                    "status": row["status"],
                    "alamat": row["alamat"],
                    "kelurahan": row["kelurahan"],
                    "kecamatan": row["kecamatan"],
                    "kabupaten": row["kabupaten"],
                },
            })

        fc = {"type": "FeatureCollection", "features": features}
        nama_file = slug_kabupaten(kabupaten)
        with open(os.path.join(OUTPUT_DIR, nama_file), "w", encoding="utf-8") as f:
            json.dump(fc, f, ensure_ascii=False)
        jumlah_file += 1
        print(f"  {kabupaten}: {len(features)} sekolah -> {nama_file}")

    print(f"\nSelesai. {jumlah_file} file GeoJSON tersimpan di {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()

import os
import pandas as pd
import json

def main():
    csv_path = "data/sekolah_lengkap_final.csv"
    out_dir = "public/data/geojson/sekolah"
    
    if not os.path.exists(csv_path):
        print(f"File {csv_path} tidak ditemukan!")
        return

    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(csv_path, dtype=str)

    # Filter yang punya koordinat saja untuk peta
    df_map = df[df["latitude"].notna() & df["longitude"].notna()].copy()
    df_map["latitude"] = pd.to_numeric(df_map["latitude"], errors="coerce")
    df_map["longitude"] = pd.to_numeric(df_map["longitude"], errors="coerce")
    df_map = df_map[df_map["latitude"].notna() & df_map["longitude"].notna()]

    # Kelompokkan per kabupaten
    grouped = df_map.groupby("kabupaten")

    for kab, group in grouped:
        features = []
        for _, row in group.iterrows():
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [row["longitude"], row["latitude"]]
                },
                "properties": {
                    "npsn": row["npsn"],
                    "nama_sekolah": row["nama_sekolah"],
                    "alamat": row.get("alamat", ""),
                    "kelurahan": row.get("kelurahan", ""),
                    "kecamatan": row.get("kecamatan", ""),
                    "kabupaten": row.get("kabupaten", ""),
                    "status": row.get("status", ""),
                    "bentuk": row.get("bentuk", "")
                }
            }
            features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }

        # Nama file mengikuti format yang diharapkan di Sekolah_layer.jsx
        kab_str = str(kab).lower()
        is_kota = kab_str.startswith("kota ")
        
        # Bersihkan "kota " atau "kab. " dari nama
        nama_slug = kab_str.replace("kota ", "").replace("kab. ", "").strip().replace(" ", "_")
        
        prefix = "kota" if is_kota else "kabupaten"
        filename = f"{prefix}_{nama_slug}_sekolah.geojson"
        
        filepath = os.path.join(out_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(geojson, f, ensure_ascii=False)
            
        print(f"Berhasil membuat {filename} dengan {len(features)} sekolah.")

if __name__ == "__main__":
    main()

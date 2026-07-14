# Panduan Pemetaan Data Sekolah

1. **Pasang dependency Python**
   Buka terminal di folder project (`map_ziswaf` atau `PROJEK-ZISWAF`), jalankan: 
   `pip install requests beautifulsoup4 pandas --break-system-packages`

2. **Taruh script 08 di folder yang benar**
   Copy `08_scrape_sekolah_lengkap.py` ke root folder `PROJEK-ZISWAF` (sejajar folder `public/` dan `src/`), karena script ini nanti nyimpen hasil ke folder `data/` relatif dari situ.

3. **Jalankan scraping (paling lama)**
   `python 08_scrape_sekolah_lengkap.py` — ini bisa jalan berjam-jam karena ambil data puluhan ribu sekolah. Biarkan jalan di background, bisa dihentikan (Ctrl+C) dan dilanjut lagi kapan saja tanpa mengulang dari awal.

4. **Convert hasil scraping jadi GeoJSON**
   Setelah 08 selesai (atau sudah cukup banyak progresnya), jalankan: `python 09_build_sekolah_geojson.py` — ini bikin file GeoJSON per kabupaten di `public/data/geojson/sekolah/`

5. **Timpa data GeoJSON lama dengan yang sudah disederhanakan**
   Ekstrak `data-simplified.zip` yang sudah dibuat sebelumnya, timpa folder `public/data/` di project (ini bikin loading peta jauh lebih cepat, dari ~290MB jadi ~40MB).

6. **Pasang komponen Sekolah_layer.jsx**
   Copy file `Sekolah_layer.jsx` ke `src/components/map/`, lalu timpa `src/components/map/MapView.jsx` dengan isi `MapView_updated.jsx`.

7. **Jalankan & tes aplikasinya**
   `npm run dev`, buka di browser. Klik kabupaten → kecamatan → titik sekolah harusnya muncul otomatis begitu kecamatan dipilih.

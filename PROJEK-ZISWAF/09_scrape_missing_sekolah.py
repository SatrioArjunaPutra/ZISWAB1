import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler("log_scrape_missing.txt", encoding="utf-8"), logging.StreamHandler()],
)
log = logging.getLogger(__name__)

BASE = "https://referensi.data.kemendikdasmen.go.id"
JENJANG = ["dikdas", "dikmen"]
KODE_PROVINSI_JABAR = "020000"
JEDA_TAHAP_A = 3.0
JUMLAH_THREAD_TAHAP_B = 8
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

def ambil_html_dengan_validasi(url, butuh_tabel=True, retries=5):
    """
    Mengambil HTML dan memvalidasi apakah isinya diblokir (Cloudflare/Rate Limit).
    Jika butuh_tabel=True, memastikan ada tag <table>.
    """
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            html = r.text
            
            # Validasi isi (jika kosong atau diblokir)
            if butuh_tabel:
                if "<table" not in html and "Data tidak ditemukan" not in html and "Tidak ada data" not in html:
                    log.warning(f"  [!] Halaman kosong/diblokir di percobaan {i+1} untuk {url}. Menunggu...")
                    time.sleep(5 + i*2)
                    continue
            return html
        except requests.RequestException as e:
            log.warning(f"  [!] Error koneksi di percobaan {i+1} untuk {url}: {e}")
            time.sleep(5 + i*2)
    
    log.error(f"GAGAL TOTAL mengambil {url} setelah {retries} percobaan.")
    return None

def ekstrak_link_tabel(html, jenjang):
    soup = BeautifulSoup(html, "html.parser")
    hasil = []
    tabel = soup.find("table")
    if not tabel:
        return []
    for a in tabel.find_all("a"):
        href = a.get("href", "")
        if f"/{jenjang}/" in href:
            kode = href.rstrip("/").split("/")[-2]
            hasil.append({"kode": kode, "nama": a.text.strip()})
    return hasil

def ambil_daftar_sekolah_di_kecamatan(jenjang, kode_kec):
    url = f"{BASE}/pendidikan/{jenjang}/{kode_kec}/3"
    html = ambil_html_dengan_validasi(url, butuh_tabel=True)
    if not html:
        return []
        
    soup = BeautifulSoup(html, "html.parser")
    tabel = soup.find("table")
    if not tabel:
        return []
        
    hasil = []
    baris = tabel.find_all("tr")[1:]  # skip header
    for row in baris:
        kolom = row.find_all("td")
        if len(kolom) < 5:
            continue
        npsn_tag = kolom[1].find("a")
        if not npsn_tag:
            npsn_tag = kolom[2].find("a") # fallback jika npsn pindah kolom
            
        npsn = npsn_tag.text.strip() if npsn_tag else kolom[1].text.strip()
        # pastikan npsn berupa angka
        if not npsn.isdigit():
            continue
            
        hasil.append({
            "npsn": npsn,
            "nama_sekolah": kolom[2].text.strip(),
            "alamat": kolom[3].text.strip(),
            "kelurahan": kolom[4].text.strip(),
            "status": kolom[5].text.strip() if len(kolom) > 5 else "",
        })
    return hasil

def tahap_a_kumpulkan_missing():
    path_lama = "data/sekolah_daftar.csv"
    path_baru = "data/sekolah_daftar_lengkap.csv"
    
    df_lama = pd.DataFrame()
    if os.path.exists(path_lama):
        df_lama = pd.read_csv(path_lama, dtype=str)
        log.info(f"Memuat {len(df_lama)} sekolah dari scraping sebelumnya.")
    else:
        log.error("File data/sekolah_daftar.csv tidak ditemukan!")
        return
        
    # Kumpulkan kecamatan yang sudah ada agar tidak di-scrape ulang (optional, tapi aman nya scrape semua kec dan filter npsn)
    # Kita akan scrape semua dan gabungkan, agar yang kemarin gagal dapat ditarik.
    semua_sekolah = []
    
    for jenjang in JENJANG:
        url_prov = f"{BASE}/pendidikan/{jenjang}/{KODE_PROVINSI_JABAR}/1"
        html_prov = ambil_html_dengan_validasi(url_prov, butuh_tabel=True)
        daftar_kab = ekstrak_link_tabel(html_prov, jenjang) if html_prov else []
        log.info(f"[{jenjang}] Ditemukan {len(daftar_kab)} kabupaten/kota")
        time.sleep(JEDA_TAHAP_A)
        
        for kab in daftar_kab:
            url_kab = f"{BASE}/pendidikan/{jenjang}/{kab['kode']}/2"
            html_kab = ambil_html_dengan_validasi(url_kab, butuh_tabel=True)
            daftar_kec = ekstrak_link_tabel(html_kab, jenjang) if html_kab else []
            log.info(f"[{jenjang}] {kab['nama']}: Ditemukan {len(daftar_kec)} kecamatan")
            time.sleep(JEDA_TAHAP_A)
            
            for kec in daftar_kec:
                # Cek apakah kita sudah punya data dari kecamatan ini di df_lama secara lengkap?
                # Cukup lama kalau di-scrape semua, mari kita scrape saja dan filter npsn nanti.
                list_sek = ambil_daftar_sekolah_di_kecamatan(jenjang, kec["kode"])
                
                for s in list_sek:
                    s["kecamatan"] = kec["nama"]
                    s["kabupaten"] = kab["nama"]
                    s["jenjang"] = jenjang
                    
                semua_sekolah.extend(list_sek)
                log.info(f"[{jenjang}] {kab['nama']} / {kec['nama']}: ditarik {len(list_sek)} sekolah. (Total ditarik skrg: {len(semua_sekolah)})")
                time.sleep(JEDA_TAHAP_A)
                
    # Gabungkan dengan yang lama
    df_baru = pd.DataFrame(semua_sekolah)
    df_gabung = pd.concat([df_lama, df_baru], ignore_index=True)
    df_gabung = df_gabung.drop_duplicates(subset="npsn")
    
    log.info(f"Total unik setelah digabung: {len(df_gabung)} sekolah (Sebelumnya {len(df_lama)}).")
    df_gabung.to_csv(path_baru, index=False)
    log.info(f"Tersimpan ke {path_baru}")
    return df_gabung

if __name__ == "__main__":
    tahap_a_kumpulkan_missing()

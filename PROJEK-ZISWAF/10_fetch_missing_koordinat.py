import os
import time
import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("log_koordinat_missing.txt", encoding="utf-8"), logging.StreamHandler()],
)
log = logging.getLogger(__name__)

BASE = "https://referensi.data.kemendikdasmen.go.id"
JUMLAH_THREAD_TAHAP_B = 8
HEADERS = {"User-Agent": "Mozilla/5.0 (riset akademik non-komersial)"}

def ambil_html(url, max_retry=3):
    for percobaan in range(1, max_retry + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            if "Data tidak ditemukan" in r.text or "<table" not in r.text:
                pass
            return r.text
        except Exception as e:
            log.warning(f"Percobaan {percobaan}/{max_retry} gagal untuk {url}: {e}")
            time.sleep(4 * percobaan)
    log.error(f"GAGAL total: {url}")
    return None

def ambil_latlong(npsn):
    html = ambil_html(f"{BASE}/pendidikan/npsn/{npsn}", max_retry=2)
    if html is None:
        return npsn, None, None
    soup = BeautifulSoup(html, "html.parser")
    teks = soup.get_text()
    lat, lon = None, None
    for baris in teks.splitlines():
        baris = baris.strip()
        if baris.lower().startswith("lintang"):
            try:
                lat = float(baris.split(":")[-1].strip())
            except ValueError:
                pass
        if baris.lower().startswith("bujur"):
            try:
                lon = float(baris.split(":")[-1].strip())
            except ValueError:
                pass
    return npsn, lat, lon

def simpan_gabungan(df_sekolah, hasil_koordinat, path_out):
    df = df_sekolah.copy()
    df["latitude"] = df["npsn"].map(lambda n: hasil_koordinat.get(n, (None, None))[0])
    df["longitude"] = df["npsn"].map(lambda n: hasil_koordinat.get(n, (None, None))[1])
    df.to_csv(path_out, index=False)

def main():
    path_in = "data/sekolah_daftar_lengkap.csv"
    path_lama = "data/sekolah_lengkap.csv" # untuk resume yang sudah ditarik
    path_out = "data/sekolah_lengkap_final.csv"

    df_sekolah = pd.read_csv(path_in, dtype=str)
    
    sudah_selesai = {}
    
    # Ambil koordinat yang sudah pernah didownload sebelumnya (dari 25k)
    if os.path.exists(path_lama):
        df_lama = pd.read_csv(path_lama, dtype=str)
        for _, row in df_lama.iterrows():
            sudah_selesai[row["npsn"]] = (row.get("latitude"), row.get("longitude"))
        log.info(f"Mengambil resume dari {path_lama} ({len(sudah_selesai)} sekolah).")

    # Ambil koordinat yang mungkin sudah didownload di run ini jika terhenti
    if os.path.exists(path_out):
        df_out = pd.read_csv(path_out, dtype=str)
        for _, row in df_out.iterrows():
            if pd.notna(row.get("latitude")) and pd.notna(row.get("longitude")):
                sudah_selesai[row["npsn"]] = (row.get("latitude"), row.get("longitude"))
        log.info(f"Resume tambahan dari {path_out} total sudah ada koordinat {len(sudah_selesai)}.")

    npsn_belum = [n for n in df_sekolah["npsn"].unique() if n not in sudah_selesai]
    log.info(f"Sisa yang perlu ditarik koordinatnya: {len(npsn_belum)} sekolah (Total {df_sekolah['npsn'].nunique()}).")

    hasil_koordinat = dict(sudah_selesai)
    selesai_counter = 0

    with ThreadPoolExecutor(max_workers=JUMLAH_THREAD_TAHAP_B) as executor:
        futures = {executor.submit(ambil_latlong, npsn): npsn for npsn in npsn_belum}
        for future in as_completed(futures):
            npsn, lat, lon = future.result()
            hasil_koordinat[npsn] = (lat, lon)
            selesai_counter += 1

            if selesai_counter % 50 == 0:
                log.info(f"  Progres tarik koordinat tambahan: {selesai_counter}/{len(npsn_belum)}")
                simpan_gabungan(df_sekolah, hasil_koordinat, path_out)

    simpan_gabungan(df_sekolah, hasil_koordinat, path_out)
    
    df_final = pd.read_csv(path_out, dtype=str)
    ada_koordinat = df_final["latitude"].notna().sum()
    log.info(f"SELESAI TOTAL KOORDINAT. {ada_koordinat} dari {len(df_final)} sekolah berhasil memiliki Lintang/Bujur.")

if __name__ == "__main__":
    main()

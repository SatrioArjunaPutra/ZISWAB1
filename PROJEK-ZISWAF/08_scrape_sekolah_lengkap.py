"""
Scraping LENGKAP data sekolah se-Jawa Barat (SD/SMP/SMA/sederajat) dari
referensi.data.kemendikdasmen.go.id, TERMASUK koordinat lat/long tiap sekolah.

2 tahap dalam 1 script:
  Tahap A: kumpulkan daftar sekolah per kecamatan (NPSN, nama, alamat, kelurahan, dst)
  Tahap B: untuk tiap NPSN, ambil lat/long dari halaman detailnya (pakai beberapa
           thread paralel supaya lebih cepat, ada di kisaran puluhan ribu sekolah)

RESUMABLE: kalau terhenti di tengah jalan (internet putus, dihentikan manual, dll),
tinggal jalanin lagi -> otomatis lanjut dari yang belum selesai, tidak mengulang
dari awal.

Cara pakai:
    pip install requests beautifulsoup4 pandas --break-system-packages
    python 08_scrape_sekolah_lengkap.py

Output:
    data/sekolah_daftar.csv       <- hasil Tahap A (bisa dipakai duluan kalau perlu)
    data/sekolah_lengkap.csv      <- hasil akhir, sudah termasuk lat/long
    log_scrape_sekolah.txt
"""

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
    handlers=[logging.FileHandler("log_scrape_sekolah.txt", encoding="utf-8"), logging.StreamHandler()],
)
log = logging.getLogger(__name__)

BASE = "https://referensi.data.kemendikdasmen.go.id"
JENJANG = ["dikdas", "dikmen"]
KODE_PROVINSI_JABAR = "020000"
JEDA_TAHAP_A = 3.0        # jeda antar-request di tahap A (list per kecamatan)
JUMLAH_THREAD_TAHAP_B = 8  # jumlah request paralel di tahap B (ambil lat/long)
HEADERS = {"User-Agent": "Mozilla/5.0 (riset akademik non-komersial)"}

os.makedirs("data", exist_ok=True)


def ambil_html(url, max_retry=3):
    for percobaan in range(1, max_retry + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            return r.text
        except Exception as e:
            log.warning(f"Percobaan {percobaan}/{max_retry} gagal untuk {url}: {e}")
            time.sleep(4 * percobaan)
    log.error(f"GAGAL total: {url}")
    return None


def ekstrak_link_tabel(html, jenjang):
    soup = BeautifulSoup(html, "html.parser")
    hasil = []
    for a in soup.select("table a"):
        href = a.get("href", "")
        if f"/{jenjang}/" in href:
            kode = href.rstrip("/").split("/")[-2]
            hasil.append({"kode": kode, "nama": a.text.strip()})
    return hasil


def ambil_daftar_sekolah_di_kecamatan(jenjang, kode_kec):
    html = ambil_html(f"{BASE}/pendidikan/{jenjang}/{kode_kec}/3")
    if html is None:
        return []
    soup = BeautifulSoup(html, "html.parser")
    tabel = soup.find("table")
    if tabel is None:
        return []
    hasil = []
    for row in tabel.find_all("tr")[1:]:
        kolom = row.find_all("td")
        if len(kolom) < 5:
            continue
        npsn_tag = kolom[1].find("a")
        hasil.append({
            "npsn": npsn_tag.text.strip() if npsn_tag else kolom[1].text.strip(),
            "nama_sekolah": kolom[2].text.strip(),
            "alamat": kolom[3].text.strip(),
            "kelurahan": kolom[4].text.strip(),
            "status": kolom[5].text.strip() if len(kolom) > 5 else "",
        })
    return hasil


def tahap_a_kumpulkan_daftar():
    path_out = "data/sekolah_daftar.csv"
    if os.path.exists(path_out):
        log.info(f"[skip Tahap A] {path_out} sudah ada, pakai yang ada")
        return pd.read_csv(path_out, dtype=str)

    semua = []
    for jenjang in JENJANG:
        html = ambil_html(f"{BASE}/pendidikan/{jenjang}/{KODE_PROVINSI_JABAR}/1")
        daftar_kab = ekstrak_link_tabel(html, jenjang) if html else []
        log.info(f"[{jenjang}] {len(daftar_kab)} kabupaten/kota")
        time.sleep(JEDA_TAHAP_A)

        for kab in daftar_kab:
            html = ambil_html(f"{BASE}/pendidikan/{jenjang}/{kab['kode']}/2")
            daftar_kec = ekstrak_link_tabel(html, jenjang) if html else []
            time.sleep(JEDA_TAHAP_A)

            for kec in daftar_kec:
                sekolah_list = ambil_daftar_sekolah_di_kecamatan(jenjang, kec["kode"])
                for s in sekolah_list:
                    s.update({"kecamatan": kec["nama"], "kabupaten": kab["nama"], "jenjang": jenjang})
                semua.extend(sekolah_list)
                log.info(f"[{jenjang}] {kab['nama']} / {kec['nama']}: {len(sekolah_list)} sekolah "
                         f"(total: {len(semua)})")
                time.sleep(JEDA_TAHAP_A)

    df = pd.DataFrame(semua).drop_duplicates(subset="npsn")
    df.to_csv(path_out, index=False)
    log.info(f"Tahap A selesai: {len(df)} sekolah unik -> {path_out}")
    return df


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


def tahap_b_ambil_koordinat(df_sekolah):
    path_out = "data/sekolah_lengkap.csv"

    sudah_selesai = {}
    if os.path.exists(path_out):
        df_ada = pd.read_csv(path_out, dtype=str)
        for _, row in df_ada.iterrows():
            sudah_selesai[row["npsn"]] = (row.get("latitude"), row.get("longitude"))
        log.info(f"[resume] {len(sudah_selesai)} sekolah sudah punya koordinat dari run sebelumnya")

    npsn_belum = [n for n in df_sekolah["npsn"].unique() if n not in sudah_selesai]
    log.info(f"Tahap B: {len(npsn_belum)} sekolah perlu diambil koordinatnya "
             f"(dari total {df_sekolah['npsn'].nunique()} unik)")

    hasil_koordinat = dict(sudah_selesai)
    selesai_counter = 0

    with ThreadPoolExecutor(max_workers=JUMLAH_THREAD_TAHAP_B) as executor:
        futures = {executor.submit(ambil_latlong, npsn): npsn for npsn in npsn_belum}
        for future in as_completed(futures):
            npsn, lat, lon = future.result()
            hasil_koordinat[npsn] = (lat, lon)
            selesai_counter += 1

            if selesai_counter % 50 == 0:
                log.info(f"  progres Tahap B: {selesai_counter}/{len(npsn_belum)}")
                # simpan checkpoint setiap 50 sekolah, biar aman kalau terhenti
                simpan_gabungan(df_sekolah, hasil_koordinat, path_out)

    simpan_gabungan(df_sekolah, hasil_koordinat, path_out)
    log.info(f"Tahap B selesai -> {path_out}")


def simpan_gabungan(df_sekolah, hasil_koordinat, path_out):
    df = df_sekolah.copy()
    df["latitude"] = df["npsn"].map(lambda n: hasil_koordinat.get(n, (None, None))[0])
    df["longitude"] = df["npsn"].map(lambda n: hasil_koordinat.get(n, (None, None))[1])
    df.to_csv(path_out, index=False)


def main():
    df_sekolah = tahap_a_kumpulkan_daftar()
    tahap_b_ambil_koordinat(df_sekolah)

    df_final = pd.read_csv("data/sekolah_lengkap.csv", dtype=str)
    ada_koordinat = df_final["latitude"].notna().sum()
    log.info(f"\nSELESAI TOTAL. {ada_koordinat} dari {len(df_final)} sekolah punya koordinat.")


if __name__ == "__main__":
    main()

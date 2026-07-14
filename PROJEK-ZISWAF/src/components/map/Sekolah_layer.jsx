import { useEffect, useMemo, useState } from "react";
import { CircleMarker, Popup } from "react-leaflet";

export default function Sekolah_layer({ selectedKabupaten, selectedKecamatan, selectedDesa }) {
  const [sekolah, setSekolah] = useState(null);

  // Nama file mengikuti pola yang sama dengan Desa_Kelurahan_layer.jsx,
  // supaya konsisten dengan slug kabupaten yang sudah ada.
  useEffect(() => {
    if (!selectedKabupaten) {
      setSekolah(null);
      return;
    }

    let nama = selectedKabupaten.properties.WADMKK;
    const isKota = selectedKabupaten.properties.TIPADM === 5;
    nama = nama.replace(/^Kota\s+/i, "").toLowerCase().replace(/\s+/g, "_");
    const fileName = isKota ? `kota_${nama}_sekolah.geojson` : `kabupaten_${nama}_sekolah.geojson`;

    fetch(`/data/geojson/sekolah/${fileName}`)
      .then((res) => {
        if (!res.ok) throw new Error("File sekolah tidak ditemukan: " + fileName);
        return res.json();
      })
      .then((data) => setSekolah(data))
      .catch((err) => {
        console.error(err);
        setSekolah(null);
      });
  }, [selectedKabupaten]);

  // Titik sekolah cuma tampil kalau sudah masuk level desa,
  // dan difilter cuma yang kelurahannya sama dengan nama desa
  const filteredSekolah = useMemo(() => {
    if (!sekolah || !selectedDesa) return null;
    const namaDesa = selectedDesa.properties.NAMOBJ;
    const namaKec = selectedKecamatan?.properties?.WADMKC;
    return sekolah.features.filter(
      (f) => {
         const kelurahanStr = (f.properties.kelurahan || "").toUpperCase().replace(/\s+/g, '');
         const desaStr = (namaDesa || "").toUpperCase().replace(/\s+/g, '');
         const kecamatanStr = (f.properties.kecamatan || "").toUpperCase().replace(/\s+/g, '');
         const kecStr = (namaKec || "").toUpperCase().replace(/\s+/g, '');
         
         const matchDesa = kelurahanStr === desaStr;
         const matchKec = kecamatanStr === kecStr;
         // Kemdikbud kadang kelurahannya sedikit beda nama (spasi), untuk itu spasi dihilangkan
         return matchDesa && matchKec;
      }
    );
  }, [sekolah, selectedKecamatan, selectedDesa]);

  const warnaPerJenjang = {
    SD: "#2E7D32",   // hijau
    SMP: "#F9A825",  // kuning
    SMA: "#C62828",  // merah
    SMK: "#6A1B9A",  // ungu
  };

  if (!selectedDesa || !filteredSekolah) return null;

  return (
    <>
      {filteredSekolah.map((f) => {
        if (!f || !f.geometry || !f.geometry.coordinates) return null;
        const [lon, lat] = f.geometry.coordinates;
        if (lon == null || lat == null) return null;
        
        const p = f.properties || {};
        const warna = warnaPerJenjang[p.bentuk] || "#455A64";

        return (
          <CircleMarker
            key={p.npsn || Math.random().toString()}
            center={[lat, lon]}
            radius={5}
            pathOptions={{ color: "#fff", weight: 1, fillColor: warna, fillOpacity: 0.9 }}
          >
            <Popup>
              <div style={{ fontSize: 13 }}>
                <b>{p.nama_sekolah || "Sekolah"}</b>
                <br />
                {p.bentuk} &middot; {p.status}
                <br />
                {p.alamat}
                <br />
                Desa/Kel. {p.kelurahan}
                <br />
                NPSN: {p.npsn}
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </>
  );
}

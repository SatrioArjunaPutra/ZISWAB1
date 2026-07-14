import { useEffect, useMemo, useState } from "react";
import { GeoJSON } from "react-leaflet";

export default function Desa_Kelurahan_layer({
  selectedKabupaten,
  selectedKecamatan,
  selectedDesa,
  setSelectedDesa,
  setHoverInfo
}) {
  const [desa, setDesa] = useState(null);

  const fileMap = {
    "Bandung": "kabupaten_bandung_desa_kelurahan.geojson",
    "Bandung Barat": "kabupaten_bandung_barat_desa_kelurahan.geojson",
    "Bekasi": "kabupaten_bekasi_desa_kelurahan.geojson",
    "Bogor": "kabupaten_bogor_desa_kelurahan.geojson",
    "Ciamis": "kabupaten_ciamis_desa_kelurahan.geojson",
    "Cianjur": "kabupaten_cianjur_desa_kelurahan.geojson",
    "Cirebon": "kabupaten_cirebon_desa_kelurahan.geojson",
    "Garut": "kabupaten_garut_desa_kelurahan.geojson",
    "Indramayu": "kabupaten_indramayu_desa_kelurahan.geojson",
    "Karawang": "kabupaten_karawang_desa_kelurahan.geojson",
    "Kuningan": "kabupaten_kuningan_desa_kelurahan.geojson",
    "Majalengka": "kabupaten_majalengka_desa_kelurahan.geojson",
    "Pangandaran": "kabupaten_pangandaran_desa_kelurahan.geojson",
    "Purwakarta": "kabupaten_purwakarta_desa_kelurahan.geojson",
    "Subang": "kabupaten_subang_desa_kelurahan.geojson",
    "Sukabumi": "kabupaten_sukabumi_desa_kelurahan.geojson",
    "Sumedang": "kabupaten_sumedang_desa_kelurahan.geojson",
    "Tasikmalaya": "kabupaten_tasikmalaya_desa_kelurahan.geojson",

    "Kota Bandung": "kota_bandung_desa_kelurahan.geojson",
    "Kota Banjar": "kota_banjar_desa_kelurahan.geojson",
    "Kota Bekasi": "kota_bekasi_desa_kelurahan.geojson",
    "Kota Bogor": "kota_bogor_desa_kelurahan.geojson",
    "Kota Cimahi": "kota_cimahi_desa_kelurahan.geojson",
    "Kota Cirebon": "kota_cirebon_desa_kelurahan.geojson",
    "Kota Depok": "kota_depok_desa_kelurahan.geojson",
    "Kota Sukabumi": "kota_sukabumi_desa_kelurahan.geojson",
    "Kota Tasikmalaya": "kota_tasikmalaya_desa_kelurahan.geojson",
  };

  useEffect(() => {
    if (!selectedKabupaten) {
      setDesa(null);
      return;
    }

    const namaWilayah = selectedKabupaten.properties.WADMKK;

    const fileName = fileMap[namaWilayah];

    if (!fileName) {
      console.log("File GeoJSON tidak ditemukan:", namaWilayah);
      return;
    }

    console.log("Load GeoJSON Desa:", fileName);

    fetch(`/data/geojson/desa/${fileName}`)
      .then((res) => {
        if (!res.ok) {
          throw new Error("File tidak ditemukan");
        }
        return res.json();
      })
      .then((json) => {
        console.log("Jumlah Desa:", json.features.length);
        setDesa(json);
      })
      .catch((err) => {
        console.error(err);
        setDesa(null);
      });
  }, [selectedKabupaten]);

    const filteredDesa = useMemo(() => {
    if (!desa) return null;

    if (!selectedKecamatan) return null;

    const hasil = desa.features.filter(
      (feature) =>
        feature.properties.WADMKC ===
        selectedKecamatan.properties.WADMKC
    );

    console.log(
      "Kecamatan:",
      selectedKecamatan.properties.WADMKC
    );

    console.log(
      "Jumlah desa:",
      hasil.length
    );

    return {
      type: "FeatureCollection",
      features: hasil,
    };
  }, [desa, selectedKecamatan]);

  const defaultStyle = {
    color: "#1565C0",
    weight: 1,
    fillColor: "#42A5F5",
    fillOpacity: 0.35,
  };

  const hoverStyle = {
    color: "#FF9800",
    weight: 3,
    fillColor: "#FFEB3B",
    fillOpacity: 0.6,
  };

  const styleFunction = (feature) => {
    if (selectedDesa && selectedDesa.properties.NAMOBJ === feature.properties.NAMOBJ) {
      return hoverStyle;
    }
    return defaultStyle;
  };

  const onEachFeature = (feature, layer) => {
    const p = feature.properties || {};

    layer.on({
      mouseover(e) {
        if (selectedDesa?.properties?.NAMOBJ === p.NAMOBJ) return;
        e.target.setStyle(hoverStyle);
        e.target.openTooltip();
        if (setHoverInfo) {
          setHoverInfo({
            nama: p.NAMOBJ || "Tidak Diketahui",
            level: "Desa/Kelurahan",
            kabupaten: p.WADMKK || "Tidak Diketahui",
            provinsi: p.WADMPR || "Jawa Barat",
          });
        }
      },

      mouseout(e) {
        if (selectedDesa?.properties?.NAMOBJ === p.NAMOBJ) return;
        e.target.setStyle(defaultStyle);
        e.target.closeTooltip();
        if (setHoverInfo) setHoverInfo(null);
      },

      click(e) {
        if (setSelectedDesa) {
          setSelectedDesa(feature);
        }
      },
    });
  };

    if (!selectedKabupaten) return null;

  if (!selectedKecamatan) return null;

  if (!filteredDesa) return null;

  return (
    <GeoJSON
      key={
        selectedKabupaten.properties.WADMKK +
        "-" +
        selectedKecamatan.properties.WADMKC
      }
      data={filteredDesa}
      style={styleFunction}
      onEachFeature={onEachFeature}
    />
  );
}
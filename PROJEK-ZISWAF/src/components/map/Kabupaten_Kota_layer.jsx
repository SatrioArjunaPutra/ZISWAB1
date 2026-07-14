import { useEffect, useState } from "react";
import { GeoJSON } from "react-leaflet";

export default function Kabupaten_Kota_Layer({
  selectedKabupaten,
  setSelectedKabupaten,
  setHoverInfo,
}) {
  const [kabupaten, setKabupaten] = useState(null);

  useEffect(() => {
    fetch("/data/geojson/kabupaten_kota.geojson")
      .then((res) => res.json())
      .then((data) => setKabupaten(data))
      .catch((err) => console.log(err));
  }, []);

  const defaultStyle = {
    color: "#1976D2",
    weight: 2,
    fillColor: "#64B5F6",
    fillOpacity: 0.25,
  };

  const hoverStyle = {
    color: "#FB8C00",
    weight: 3,
    fillOpacity: 0.45,
  };

  const selectedStyle = {
    color: "#2E7D32",
    weight: 4,
    fillColor: "#4CAF50",
    fillOpacity: 0.5,
  };

  const styleFunction = (feature) => {
    if (!selectedKabupaten) return defaultStyle;

    if (feature.properties.WADMKK === selectedKabupaten.properties.WADMKK) {
      return selectedStyle;
    }

    return {
      opacity: 0,
      fillOpacity: 0,
    };
  };

  const onEachFeature = (feature, layer) => {
    const p = feature.properties;

    layer.on({
      mouseover(e){

    if(selectedKabupaten?.properties?.WADMKK === p.WADMKK)
        return;

    e.target.setStyle(hoverStyle);

    setHoverInfo({

        level: "Kabupaten/Kota",

        nama: p.WADMKK,

        kabupaten: p.WADMKK,

        provinsi: p.WADMPR

    });

},

      mouseout(e){

    if(selectedKabupaten?.properties?.WADMKK === p.WADMKK)
        return;

    e.target.setStyle(defaultStyle);

    setHoverInfo(null);

},

      click() {
        setSelectedKabupaten(feature);
      },
    });
  };

  if (!kabupaten) return null;

  return (
    <GeoJSON
      key={selectedKabupaten?.properties?.WADMKK || "kabupaten"}
      data={kabupaten}
      style={styleFunction}
      onEachFeature={onEachFeature}
    />
  );
}
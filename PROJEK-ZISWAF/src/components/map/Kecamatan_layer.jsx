import { useEffect, useMemo, useState } from "react";
import { GeoJSON } from "react-leaflet";

export default function Kecamatan_Layer({

    selectedKabupaten,
    selectedKecamatan,
    setSelectedKecamatan,
    setHoverInfo,
}) {

    const [kecamatan, setKecamatan] = useState(null);

    const [desaGeojson, setDesaGeojson] = useState(null);

    useEffect(() => {

        fetch("/data/geojson/kecamatan.geojson")

            .then(res => res.json())
            .then(data => setKecamatan(data))
            .catch(console.error);

    }, []);

    useEffect(() => {

        if (!selectedKabupaten) {

            setDesaGeojson(null);
            return;

        }

        const p = selectedKabupaten.properties;

let nama = p.WADMKK;

// hilangkan kata "Kota "
nama = nama.replace(/^Kota\s+/i, "");

nama = nama
    .toLowerCase()
    .replace(/\s+/g, "_");

let fileName;

if (p.TIPADM === 5) {

    fileName = `kota_${nama}_desa_kelurahan.geojson`;

} else {

    fileName = `kabupaten_${nama}_desa_kelurahan.geojson`;

}

console.log(fileName);

        fetch(`/data/geojson/desa/${fileName}`)

            .then(res => {

                if (!res.ok)
                    throw new Error("GeoJSON desa tidak ditemukan");

                return res.json();

            })

            .then(data => {

                console.log("GeoJSON Desa :", fileName);

                setDesaGeojson(data);

            })

            .catch(err => {

                console.error(err);

                setDesaGeojson(null);

            });

    }, [selectedKabupaten]);

        const filteredKecamatan = useMemo(() => {

        if (!kecamatan) return null;

        if (!selectedKabupaten) return null;

        return {

            type: "FeatureCollection",

            features: kecamatan.features.filter(

                feature =>

                    feature.properties.WADMKK ===
                    selectedKabupaten.properties.WADMKK

            )

        };

    }, [

        kecamatan,
        selectedKabupaten

    ]);

    const filteredDesa = useMemo(() => {

        if (!desaGeojson) return null;

        if (!selectedKecamatan) return null;

        return {

            type: "FeatureCollection",

            features: desaGeojson.features.filter(

                feature =>

                    feature.properties.WADMKC ===
                    selectedKecamatan.properties.WADMKC

            )

        };

    }, [

        desaGeojson,
        selectedKecamatan

    ]);

    const defaultStyle = {

        color: "#E53935",
        weight: 1.5,
        fillColor: "#EF5350",
        fillOpacity: 0.15,

    };

    const hoverStyle = {

        color: "#FB8C00",
        weight: 3,
        fillColor: "#FFB74D",
        fillOpacity: 0.45,

    };

    const selectedStyle = {

        color: "#2E7D32",
        weight: 3,
        fillColor: "#66BB6A",
        fillOpacity: 0.5,

    };

    const styleFunction = (feature) => {
  if (selectedKecamatan) {
    return {
      color: "transparent",
      weight: 0,
      opacity: 0,
      fillOpacity: 0,
    };
  }

  return defaultStyle;
};

        const onEachFeature = (feature, layer) => {

        const p = feature.properties;


        layer.on({

            mouseover(e) {

    if(selectedKecamatan?.properties?.WADMKC === p.WADMKC)
        return;

    e.target.setStyle(hoverStyle);

    setHoverInfo({

        level: "Kecamatan",

        nama: p.WADMKC,

        kabupaten: p.WADMKK,

        provinsi: p.WADMPR

    });

},

            mouseout(e){

    if(selectedKecamatan?.properties?.WADMKC === p.WADMKC)
        return;

    e.target.setStyle(defaultStyle);

    setHoverInfo(null);

},

            click(){

                setSelectedKecamatan(feature);

            }

        });

    };

    const desaStyle = {

        color: "#1565C0",
        weight: 1,
        fillColor: "#42A5F5",
        fillOpacity: 0.35,

    };

    const onEachDesa = (feature, layer) => {

    const p = feature.properties;

    layer.on({

        mouseover(e){

            setHoverInfo({

                nama: p.WADMKD,
                level: "Desa/Kelurahan",
                kabupaten: p.WADMKK,
                provinsi: p.WADMPR,

            });

            e.target.setStyle({

                color:"#FF9800",
                weight:2,
                fillOpacity:0.6

            });

        },

        mouseout(e){

            setHoverInfo(null);

            e.target.setStyle(desaStyle);

        }

    });

};

    if (!filteredKecamatan)
        return null;

    return (

        <>

            <GeoJSON

                key={
                    selectedKabupaten?.properties?.WADMKK || "kecamatan"
                }

                data={filteredKecamatan}

                style={styleFunction}

                onEachFeature={onEachFeature}

            />

            {filteredDesa && (

                <GeoJSON

                    key={
                        selectedKecamatan?.properties?.WADMKC || "desa"
                    }

                    data={filteredDesa}

                    style={desaStyle}

                    onEachFeature={onEachDesa}

                />

            )}

        </>

    );

}
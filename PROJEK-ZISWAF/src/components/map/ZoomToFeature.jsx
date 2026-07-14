import { useEffect } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";

export default function ZoomToFeature({ feature }) {
  const map = useMap();

  useEffect(() => {
    if (!feature) return;

    const layer = L.geoJSON(feature);

    map.fitBounds(layer.getBounds(), {
      padding: [40, 40],
      animate: true,
    });
  }, [feature, map]);

  return null;
}
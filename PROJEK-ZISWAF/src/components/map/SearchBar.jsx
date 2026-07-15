import React, { useState, useEffect, useRef } from "react";
import { useMap, Marker, Popup } from "react-leaflet";
import L from "leaflet";

// Fix icon issue for default leaflet marker
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

export default function SearchBar() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [data, setData] = useState(null);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedResult, setSelectedResult] = useState(null);
  
  const map = useMap();
  const searchContainerRef = useRef(null);

  // Load index data on mount
  useEffect(() => {
    fetch("/data/search_index.json")
      .then(res => res.json())
      .then(json => setData(json))
      .catch(err => console.error("Gagal load search index", err));
  }, []);

  // Handle outside clicks to close dropdown
  useEffect(() => {
    function handleClickOutside(event) {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Prevent map dragging when interacting with search bar
  useEffect(() => {
    const el = searchContainerRef.current;
    if (el) {
      const stop = (e) => e.stopPropagation();
      el.addEventListener('mousedown', stop);
      el.addEventListener('dblclick', stop);
      el.addEventListener('wheel', stop);
      return () => {
        el.removeEventListener('mousedown', stop);
        el.removeEventListener('dblclick', stop);
        el.removeEventListener('wheel', stop);
      };
    }
  }, []);

  const handleSearch = (e) => {
    const val = e.target.value;
    setQuery(val);
    setSelectedResult(null);
    
    if (val.trim().length < 3 || !data) {
      setResults([]);
      setIsOpen(false);
      return;
    }
    
    const lowerVal = val.toLowerCase();
    
    // Filter data (limit to 10 results for performance)
    const filtered = data
      .filter(item => item.n.toLowerCase().includes(lowerVal))
      .slice(0, 10);
      
    setResults(filtered);
    setIsOpen(true);
  };

  const handleSelect = (item) => {
    setQuery(item.n);
    setIsOpen(false);
    setSelectedResult(item);
    
    // Terbang ke lokasi
    if (item.lt && item.lg) {
      map.flyTo([item.lt, item.lg], 17, {
        duration: 2
      });
    }
  };

  return (
    <>
      <div 
        ref={searchContainerRef}
        style={{
          position: "absolute",
          top: "20px",
          left: "50%",
          transform: "translateX(-50%)",
          zIndex: 1000,
          width: "90%",
          maxWidth: "400px",
          fontFamily: "Arial, sans-serif"
        }}
      >
        <div style={{ position: "relative" }}>
          <input
            type="text"
            value={query}
            onChange={handleSearch}
            placeholder="Cari Sekolah atau Kampus..."
            style={{
              width: "100%",
              padding: "12px 20px",
              fontSize: "15px",
              borderRadius: "24px",
              border: "none",
              outline: "none",
              boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
              backgroundColor: "white",
              boxSizing: "border-box"
            }}
            onFocus={() => {
              if (results.length > 0) setIsOpen(true);
            }}
          />
          
          {/* Dropdown Results */}
          {isOpen && results.length > 0 && (
            <div style={{
              position: "absolute",
              top: "100%",
              left: 0,
              right: 0,
              marginTop: "8px",
              backgroundColor: "white",
              borderRadius: "12px",
              boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
              maxHeight: "300px",
              overflowY: "auto",
              overflowX: "hidden"
            }}>
              {results.map((item, idx) => (
                <div 
                  key={idx}
                  onClick={() => handleSelect(item)}
                  style={{
                    padding: "12px 16px",
                    borderBottom: idx === results.length - 1 ? "none" : "1px solid #eee",
                    cursor: "pointer",
                    transition: "background-color 0.2s"
                  }}
                  onMouseEnter={(e) => e.target.style.backgroundColor = "#f5f5f5"}
                  onMouseLeave={(e) => e.target.style.backgroundColor = "white"}
                >
                  <div style={{ fontWeight: "bold", fontSize: "14px", color: "#333", pointerEvents: "none" }}>
                    {item.t === "PT" ? "🎓" : "🏫"} {item.n}
                  </div>
                  <div style={{ fontSize: "12px", color: "#666", marginTop: "4px", pointerEvents: "none" }}>
                    {item.c}, {item.k}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Render Marker jika ada hasil yang dipilih */}
      {selectedResult && selectedResult.lt && selectedResult.lg && (
        <Marker position={[selectedResult.lt, selectedResult.lg]}>
          <Popup autoPan={false}>
            <div style={{ textAlign: "center", minWidth: "150px" }}>
              <div style={{ fontSize: "16px", marginBottom: "5px" }}>
                {selectedResult.t === "PT" ? "🎓" : "🏫"}
              </div>
              <strong style={{ color: "#d32f2f" }}>{selectedResult.n}</strong>
              <div style={{ fontSize: "12px", marginTop: "5px", color: "#555" }}>
                {selectedResult.c}, {selectedResult.k}
              </div>
            </div>
          </Popup>
        </Marker>
      )}
    </>
  );
}

"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { ComposableMap, Geographies, Geography, ZoomableGroup } from "react-simple-maps"
import { scaleLinear } from "d3-scale"
import { useTranslation } from "@/utils/translation"

// World map topojson
const remoteGeoUrl = "https://raw.githubusercontent.com/deldersveld/topojson/master/world-countries.json"
const localGeoUrl = "/world-countries.json"

export function MapChart({ countryStats, onSelectCountry, selectedCountry, disabled = false }) {
  const { t } = useTranslation();
  const [position, setPosition] = useState({ coordinates: [0, 0], zoom: 1 })
  const [mapData, setMapData] = useState(null)
  const [error, setError] = useState(null)
  const [tooltipVisible, setTooltipVisible] = useState(false)
  const [tooltipContent, setTooltipContent] = useState("")
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 })
  const [countryMatches, setCountryMatches] = useState({ total: 0, matched: 0 })
  const mapContainerRef = useRef(null)

  useEffect(() => {
    const fetchMapData = async () => {
      try {
        let response;
        try {
          response = await fetch(localGeoUrl);
          if (!response.ok) throw new Error("Local file not found");
          console.log("Successfully loaded local map file");
        } catch (localError) {
          console.warn("Failed to load local map file, trying remote URL");
          response = await fetch(remoteGeoUrl);
          if (!response.ok) throw new Error(`Remote fetch failed: ${response.status}`);
          console.log("Successfully loaded remote map file");
        }
        
        const data = await response.json();
        setMapData(data);
      } catch (error) {
        console.error("Error loading map data:", error);
        setError(`Failed to load map data: ${error.message}`);
      }
    };

    fetchMapData();
  }, []);

  // Calculate matches when map data changes
  useEffect(() => {
    if (mapData && Object.keys(countryStats).length > 0) {
      setTimeout(() => {
        let matches = 0;
        let total = 0;
        
        // Safely count matches
        try {
          const geographies = document.querySelectorAll('[class*="rsm-geography"]');
          total = geographies.length;
          
          Object.keys(countryStats).forEach(countryCode => {
            if (document.querySelector(`[aria-label*="${countryCode}"]`)) {
              matches++;
            }
          });
        } catch (e) {
          console.warn("Error counting map matches:", e);
        }
        
        setCountryMatches({ total, matched: matches });
      }, 1000);
    }
  }, [mapData, countryStats]);

  // Reset zoom when selected country is cleared
  useEffect(() => {
    if (!selectedCountry) {
      setPosition({ coordinates: [0, 0], zoom: 1 });
    }
  }, [selectedCountry]);

  const handleCountryClick = useCallback((geo) => {
    if (disabled) return; // Skip if map is disabled
    
    const countryId = geo.id;
    const countryName = geo.properties?.name || t("unknown");
    
    console.log(`Country clicked: ${countryName} (${countryId})`);
    console.log(`Has data: ${countryStats[countryId] ? 'Yes' : 'No'}`);
    
    if (countryStats[countryId]) {
      if (selectedCountry === countryId) {
        // Reset if clicking the same country
        onSelectCountry(null);
        setPosition({ coordinates: [0, 0], zoom: 1 });
      } else {
        // Select the country and zoom in
        onSelectCountry(countryId);
      }
    }
  }, [countryStats, onSelectCountry, selectedCountry, disabled, t]);

  const handleReset = useCallback(() => {
    setPosition({ coordinates: [0, 0], zoom: 1 });
    onSelectCountry(null);
  }, [onSelectCountry]);

  const handleMouseMove = useCallback((e) => {
    if (disabled) return; // Skip if map is disabled
    
    if (tooltipVisible && mapContainerRef.current) {
      const containerRect = mapContainerRef.current.getBoundingClientRect();
      const x = e.clientX - containerRect.left;
      const y = e.clientY - containerRect.top;
      
      setTooltipPosition({
        x: x,
        y: y
      });
    }
  }, [tooltipVisible, disabled]);

  const handleMouseHover = useCallback((geo) => {
    if (disabled) return; // Skip if map is disabled
    
    if (!geo || !geo.id) return;
    
    const countryId = geo.id;
    const countryName = geo.properties?.name || t("unknown");
    const hasData = countryStats[countryId] ? true : false;
    const count = hasData ? countryStats[countryId]?.count || 0 : 0;
    
    const tooltipText = hasData 
      ? `${countryName}: ${count} ${t(count === 1 ? 'incident' : 'incidents')}` 
      : `${countryName}: ${t("no_data")}`;
      
    setTooltipContent(tooltipText);
    setTooltipVisible(true);
  }, [countryStats, disabled, t]);

  if (error) {
    return <div className="text-center text-red-500 p-4">{error}</div>;
  }

  if (!mapData) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <div className="animate-pulse text-center">
          <div className="h-8 w-8 mx-auto rounded-full bg-primary/20 mb-2"></div>
          <p>{t("loading_map_data")}</p>
        </div>
      </div>
    );
  }

  // Create a color scale based on incident counts
  const maxCount = Object.values(countryStats || {}).reduce((max, country) => Math.max(max, country?.count || 0), 1);
  const colorScale = scaleLinear().domain([0, maxCount]).range(["#f1f5f9", "hsl(var(--primary))"]);

  return (
    <div 
      className={`relative h-full w-full ${disabled ? 'pointer-events-none' : ''}`}
      ref={mapContainerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setTooltipVisible(false)}
    >
      {/* Custom tooltip */}
      {tooltipVisible && (
        <div 
          className="absolute z-50 pointer-events-none bg-background border rounded-md shadow-md px-3 py-2 text-sm transition-opacity"
          style={{ 
            left: `${tooltipPosition.x}px`, 
            top: `${tooltipPosition.y - 40}px`,
            opacity: tooltipVisible ? 1 : 0
          }}
        >
          {tooltipContent}
        </div>
      )}
      
      <ComposableMap
        projection="geoMercator"
        projectionConfig={{
          scale: 150,
        }}
        className="h-full w-full"
      >
        <ZoomableGroup 
          zoom={position.zoom} 
          center={position.coordinates} 
          onMoveEnd={setPosition}
          onMoveStart={() => setTooltipVisible(false)}
        >
          <Geographies geography={mapData}>
            {({ geographies }) => 
              geographies.map((geo) => {
                const countryId = geo.id;
                const hasData = countryStats[countryId] ? true : false;
                const count = hasData ? countryStats[countryId]?.count || 0 : 0;
                const isSelected = selectedCountry === countryId;

                return (
                  <Geography
                    key={geo.rsmKey || `geo-${countryId}`}
                    geography={geo}
                    fill={hasData ? colorScale(count) : "#f1f5f9"}
                    stroke={isSelected ? "hsl(var(--primary))" : "#D6D6DA"}
                    strokeWidth={isSelected ? 2 : 0.5}
                    style={{
                      default: {
                        outline: "none",
                        cursor: disabled ? "default" : (hasData ? "pointer" : "default")
                      },
                      hover: {
                        fill: hasData ? "hsl(var(--primary) / 0.7)" : "#F5F5F5",
                        outline: "none",
                        cursor: disabled ? "default" : (hasData ? "pointer" : "default")
                      },
                      pressed: {
                        outline: "none",
                        cursor: disabled ? "default" : (hasData ? "pointer" : "default")
                      },
                    }}
                    onClick={() => handleCountryClick(geo)}
                    onMouseEnter={() => handleMouseHover(geo)}
                    onMouseLeave={() => setTooltipVisible(false)}
                  />
                );
              })
            }
          </Geographies>
        </ZoomableGroup>
      </ComposableMap>

      {position.zoom > 1 && (
        <button
          onClick={handleReset}
          className="absolute bottom-4 right-4 rounded-full bg-primary p-2 text-primary-foreground shadow-md hover:bg-primary/90"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
            <polyline points="9 22 9 12 15 12 15 22"></polyline>
          </svg>
        </button>
      )}

      <div className="absolute bottom-4 left-4 flex items-center gap-2 rounded-md bg-background/80 p-2 text-xs backdrop-blur">
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded-sm bg-slate-200"></div>
          <span>{t("no_data")}</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded-sm bg-primary/30"></div>
          <span>{t("low")}</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded-sm bg-primary"></div>
          <span>{t("high")}</span>
        </div>
      </div>
    </div>
  );
}
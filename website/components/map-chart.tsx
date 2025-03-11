"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { ComposableMap, Geographies, Geography, ZoomableGroup } from "react-simple-maps"
import { scaleLinear } from "d3-scale"
import { feature } from "topojson-client"

// World map topojson
const remoteGeoUrl = "https://raw.githubusercontent.com/deldersveld/topojson/master/world-countries.json"
const localGeoUrl = "/world-countries.json"

export function MapChart({ countryStats, onSelectCountry, selectedCountry }) {
  const [position, setPosition] = useState({ coordinates: [0, 0], zoom: 1 })
  const [mapData, setMapData] = useState(null)
  const [error, setError] = useState(null)
  const [tooltipVisible, setTooltipVisible] = useState(false)
  const [tooltipContent, setTooltipContent] = useState("")
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 })
  const [countryMatches, setCountryMatches] = useState({ total: 0, matched: 0 })
  const [countryFeatures, setCountryFeatures] = useState({})
  const mapContainerRef = useRef(null)
  const mapBounds = useRef({})

  // Fetch map data on component mount
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
        
        // Process geographies to extract features and bounding boxes
        if (data && data.objects) {
          const countries = {};
          const features = feature(data, data.objects.countries).features;
          
          features.forEach(geo => {
            if (geo.id) {
              // Calculate country bounds (bounding box)
              let bounds = { x: [Infinity, -Infinity], y: [Infinity, -Infinity] };
              
              if (geo.geometry && geo.geometry.coordinates) {
                const coords = geo.geometry.coordinates;
                
                // Handle different geometry types
                if (geo.geometry.type === "Polygon") {
                  coords[0].forEach(([x, y]) => {
                    bounds.x[0] = Math.min(bounds.x[0], x);
                    bounds.x[1] = Math.max(bounds.x[1], x);
                    bounds.y[0] = Math.min(bounds.y[0], y);
                    bounds.y[1] = Math.max(bounds.y[1], y);
                  });
                } 
                else if (geo.geometry.type === "MultiPolygon") {
                  coords.forEach(poly => {
                    poly[0].forEach(([x, y]) => {
                      bounds.x[0] = Math.min(bounds.x[0], x);
                      bounds.x[1] = Math.max(bounds.x[1], x);
                      bounds.y[0] = Math.min(bounds.y[0], y);
                      bounds.y[1] = Math.max(bounds.y[1], y);
                    });
                  });
                }
              }
              
              // Store country with its bounds
              countries[geo.id] = {
                feature: geo,
                bounds: bounds,
                center: [
                  (bounds.x[0] + bounds.x[1]) / 2,
                  (bounds.y[0] + bounds.y[1]) / 2
                ],
                name: geo.properties.name
              };
            }
          });
          
          setCountryFeatures(countries);
          mapBounds.current = countries;
        }
      } catch (error) {
        console.error("Error loading map data:", error);
        setError(`Failed to load map data: ${error.message}`);
      }
    };

    fetchMapData();
  }, []);

  // Calculate matches when country features and stats are available
  useEffect(() => {
    if (Object.keys(countryFeatures).length > 0 && Object.keys(countryStats).length > 0) {
      let matches = 0;
      for (const countryId in countryFeatures) {
        if (countryStats[countryId]) {
          matches++;
        }
      }
      
      setCountryMatches({
        total: Object.keys(countryFeatures).length,
        matched: matches
      });
    }
  }, [countryFeatures, countryStats]);

  // Handle country selection and zoom effect
  useEffect(() => {
    if (selectedCountry && countryFeatures[selectedCountry]) {
      // Get the selected country's data
      const country = countryFeatures[selectedCountry];
      
      // Calculate best zoom level based on country size
      const bounds = country.bounds;
      const width = Math.abs(bounds.x[1] - bounds.x[0]);
      const height = Math.abs(bounds.y[1] - bounds.y[0]);
      
      // Adjust zoom based on country size (larger countries need less zoom)
      let zoomLevel = 4;
      if (width > 50 || height > 50) zoomLevel = 3;
      if (width > 90 || height > 90) zoomLevel = 2;
      
      // Apply zoom with animation delay for better UX
      setTimeout(() => {
        setPosition({
          coordinates: country.center,
          zoom: zoomLevel
        });
      }, 100);
    }
  }, [selectedCountry, countryFeatures]);

  // Handle country click
  const handleCountryClick = useCallback((geo) => {
    if (!geo || !geo.id) return;
    
    const countryId = geo.id;
    const countryName = geo.properties?.name || 'Unknown';
    
    console.log(`Country clicked: ${countryName} (${countryId})`);
    
    if (countryStats[countryId]) {
      if (selectedCountry === countryId) {
        // Reset if clicking the same country
        onSelectCountry(null);
        setPosition({ coordinates: [0, 0], zoom: 1 });
      } else {
        // Select the country
        onSelectCountry(countryId);
      }
    } else {
      console.log(`No data for ${countryName}`);
    }
  }, [countryStats, onSelectCountry, selectedCountry]);

  // Handle reset button click
  const handleReset = useCallback(() => {
    setPosition({ coordinates: [0, 0], zoom: 1 });
    onSelectCountry(null);
  }, [onSelectCountry]);

  // Handle mouse move for tooltip positioning
  const handleMouseMove = useCallback((e) => {
    if (tooltipVisible && mapContainerRef.current) {
      const containerRect = mapContainerRef.current.getBoundingClientRect();
      const x = e.clientX - containerRect.left;
      const y = e.clientY - containerRect.top;
      
      setTooltipPosition({
        x: x,
        y: y
      });
    }
  }, [tooltipVisible]);

  // Handle mouse hover on country
  const handleCountryHover = useCallback((geo) => {
    if (!geo || !geo.id) return;
    
    const countryId = geo.id;
    const countryName = geo.properties?.name || 'Unknown';
    const hasData = countryStats[countryId] ? true : false;
    const count = hasData ? countryStats[countryId]?.count || 0 : 0;
    
    const tooltipText = hasData 
      ? `${countryName}: ${count} incidents` 
      : `${countryName}: No data`;
      
    setTooltipContent(tooltipText);
    setTooltipVisible(true);
  }, [countryStats]);

  if (error) {
    return <div className="text-center text-red-500 p-4">{error}</div>;
  }

  if (!mapData) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <div className="animate-pulse text-center">
          <div className="h-8 w-8 mx-auto rounded-full bg-primary/20 mb-2"></div>
          <p>Loading map data...</p>
        </div>
      </div>
    );
  }

  // Create a color scale based on incident counts
  const maxCount = Object.values(countryStats || {}).reduce((max, country) => Math.max(max, country?.count || 0), 1);
  const colorScale = scaleLinear().domain([0, maxCount]).range(["#f1f5f9", "hsl(var(--primary))"]);

  return (
    <div 
      className="relative h-full w-full overflow-hidden rounded-lg"
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
          translateExtent={[[-Infinity, -Infinity], [Infinity, Infinity]]}
        >
          <Geographies geography={mapData}>
            {({ geographies }) => {
              return geographies.map((geo) => {
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
                        cursor: hasData ? "pointer" : "default"
                      },
                      hover: {
                        fill: hasData ? "hsl(var(--primary) / 0.7)" : "#F5F5F5",
                        outline: "none",
                        cursor: hasData ? "pointer" : "default"
                      },
                      pressed: {
                        outline: "none",
                        cursor: hasData ? "pointer" : "default"
                      },
                    }}
                    onClick={() => handleCountryClick(geo)}
                    onMouseEnter={() => handleCountryHover(geo)}
                    onMouseLeave={() => setTooltipVisible(false)}
                  />
                );
              });
            }}
          </Geographies>
        </ZoomableGroup>
      </ComposableMap>

      {position.zoom > 1 && (
        <button
          onClick={handleReset}
          className="absolute bottom-4 right-4 rounded-full bg-primary p-2 text-primary-foreground shadow-md hover:bg-primary/90 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
            <polyline points="9 22 9 12 15 12 15 22"></polyline>
          </svg>
        </button>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 left-4 flex items-center gap-2 rounded-md bg-background/90 p-2 text-xs backdrop-blur">
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded-sm bg-slate-200"></div>
          <span>No data</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded-sm bg-primary/30"></div>
          <span>Low</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded-sm bg-primary"></div>
          <span>High</span>
        </div>
      </div>
    </div>
  );
}
"use client"

import { useState, useRef, useEffect } from "react"
import { ComposableMap, Geographies, Geography, ZoomableGroup } from "react-simple-maps"
import { scaleLinear } from "d3-scale"
import { Tooltip } from "react-tooltip"
import { useTheme } from "next-themes"

interface WorldMapProps {
  countryData: Record<string, number>
  language: string
}

const WorldMap = ({ countryData, language }: WorldMapProps) => {
  const [tooltipContent, setTooltipContent] = useState("")
  const [isMapActive, setIsMapActive] = useState(false)
  const mapRef = useRef<HTMLDivElement>(null)
  const { theme } = useTheme()

  // Find the maximum count for scaling
  const maxCount = Math.max(...Object.values(countryData), 1)

  // Create a color scale
  const colorScale = scaleLinear<string>().domain([0, maxCount]).range(["#e6f2ff", "#0066cc"])

  // Handle clicks outside the map to deactivate it
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (mapRef.current && !mapRef.current.contains(event.target as Node)) {
        setIsMapActive(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [])

  // Prevent wheel events when map is not active
  useEffect(() => {
    const handleWheel = (e: WheelEvent) => {
      if (!isMapActive && mapRef.current?.contains(e.target as Node)) {
        e.preventDefault()
      }
    }

    // Use passive: false to allow preventDefault
    document.addEventListener("wheel", handleWheel, { passive: false })
    return () => {
      document.removeEventListener("wheel", handleWheel)
    }
  }, [isMapActive])

  return (
    <div
      ref={mapRef}
      className={`relative border rounded-lg p-2 ${
        isMapActive ? "cursor-grab" : "cursor-pointer"
      } ${theme === "dark" ? "bg-gray-800" : "bg-white"}`}
      onClick={() => !isMapActive && setIsMapActive(true)}
    >
      {!isMapActive && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/10 rounded-lg z-10">
          <div className="bg-white dark:bg-gray-800 p-2 rounded-md shadow-md">
            {language === "en" ? "Click to activate map" : "Cliquez pour activer la carte"}
          </div>
        </div>
      )}

      <ComposableMap projection="geoMercator" style={{ width: "100%", height: "500px" }}>
        <ZoomableGroup
          zoom={1}
          center={[0, 0]}
          translateExtent={[
            [-100, -200],
            [1000, 600],
          ]}
        >
          <Geographies geography="/world-countries.json">
            {({ geographies }) =>
              geographies.map((geo) => {
                const id = geo.id
                const count = countryData[id] || 0
                const name = geo.properties.name

                return (
                  <Geography
                    key={geo.rsmKey}
                    geography={geo}
                    fill={count > 0 ? colorScale(count) : "#F5F4F6"}
                    stroke="#D6D6DA"
                    strokeWidth={0.5}
                    onMouseEnter={() => {
                      const tooltipText = `${name}: ${count} ${language === "en" ? "entities" : "entités"}`
                      setTooltipContent(tooltipText)
                    }}
                    onMouseLeave={() => {
                      setTooltipContent("")
                    }}
                    style={{
                      default: { outline: "none" },
                      hover: { outline: "none", fill: "#F53" },
                      pressed: { outline: "none" },
                    }}
                    data-tooltip-id="geo-tooltip"
                  />
                )
              })
            }
          </Geographies>
        </ZoomableGroup>
      </ComposableMap>

      <Tooltip id="geo-tooltip" content={tooltipContent} />
    </div>
  )
}

export default WorldMap


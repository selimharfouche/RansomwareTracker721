"use client"

import { useState, useEffect } from "react"
import { MapChart } from "@/components/map-chart"
import { StatsPanel } from "@/components/stats-panel"
import { ThemeToggle } from "@/components/theme-toggle"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Shield, Globe, Building, AlertTriangle } from "lucide-react"
import ErrorBoundary from "@/components/error-boundary"
import { EnhancedBarChart } from "@/components/enhanced-bar-chart"
import { EnhancedPieChart } from "@/components/enhanced-pie-chart"
import { CountryDetailCard } from "@/components/country-detail-card"

// API route path
const DATA_PATH = "/api/data"

export default function Home() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedCountry, setSelectedCountry] = useState(null)
  const [countryStats, setCountryStats] = useState({})
  const [industryStats, setIndustryStats] = useState([])
  const [groupStats, setGroupStats] = useState([])
  const [selectedCountryData, setSelectedCountryData] = useState([])
  const [debugInfo, setDebugInfo] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log("Fetching data from:", DATA_PATH);
        const response = await fetch(DATA_PATH)
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const jsonData = await response.json()
        console.log("Data fetched successfully", {
          hasEntities: !!jsonData.entities,
          entitiesCount: jsonData.entities?.length || 0
        });

        // Check if the data has an entities array
        if (!jsonData.entities || jsonData.entities.length === 0) {
          console.warn("No entities found in the data");
          setDebugInfo({
            dataFormat: JSON.stringify(jsonData).substring(0, 200) + "...",
            error: "No entities array found or empty entities array"
          });
        }

        // Process the data
        processData(jsonData.entities || []);
      } catch (error) {
        console.error("Error loading data:", error)
        setError(error.message)
        setDebugInfo({
          error: error.message,
          stack: error.stack
        });
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const processData = (entities) => {
    // Process country statistics with country code normalization
    const countries = {};
    const industries = {};
    const groups = {};

    // ISO-2 to ISO-3 conversion map for common countries
    const iso2ToIso3 = {
      'US': 'USA', 'GB': 'GBR', 'CA': 'CAN', 'AU': 'AUS',
      'DE': 'DEU', 'FR': 'FRA', 'IT': 'ITA', 'JP': 'JPN',
      'CN': 'CHN', 'IN': 'IND', 'RU': 'RUS', 'BR': 'BRA',
    };

    // Function to normalize country codes
    const normalizeCountryCode = (code) => {
      if (!code) return "UNK"; // Unknown
      
      // Handle various formats
      if (code.length === 2) {
        return iso2ToIso3[code.toUpperCase()] || `UNK_${code}`;
      }
      
      // Ensure 3-letter code is uppercase
      return code.toUpperCase();
    };

    // Process each entity
    entities.forEach((item) => {
      // Skip items with missing essential data
      if (!item) return;
      
      // Normalize and handle country stats
      let countryCode = "UNK";
      
      if (item.geography && item.geography.country_code) {
        countryCode = normalizeCountryCode(item.geography.country_code);
      }
      
      if (!countries[countryCode]) {
        countries[countryCode] = { 
          count: 0, 
          cities: {}, 
          entities: [],
          name: item.geography?.country || "Unknown Country" 
        };
      }
      
      countries[countryCode].count++;
      countries[countryCode].entities.push(item);

      // City stats
      const city = item.geography?.city || "Unknown";
      if (!countries[countryCode].cities[city]) {
        countries[countryCode].cities[city] = 0;
      }
      countries[countryCode].cities[city]++;

      // Industry stats
      const industry = item.organization?.industry || "Unknown";
      if (!industries[industry]) {
        industries[industry] = 0;
      }
      industries[industry]++;

      // Ransomware group stats
      const group = item.ransomware_group || "Unknown";
      if (!groups[group]) {
        groups[group] = 0;
      }
      groups[group]++;
    });

    // Format for charts
    const industryData = Object.entries(industries)
      .map(([name, count]) => ({
        name,
        value: count,
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10);

    const groupData = Object.entries(groups)
      .map(([name, count]) => ({
        name,
        value: count,
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10);

    setData(entities);
    setCountryStats(countries);
    setIndustryStats(industryData);
    setGroupStats(groupData);
  };

  const handleCountrySelect = (countryCode) => {
    if (countryCode === selectedCountry) {
      // If the same country is selected twice, clear the selection
      setSelectedCountry(null)
      setSelectedCountryData([])
    } else {
      setSelectedCountry(countryCode)
      if (countryStats[countryCode]) {
        setSelectedCountryData(countryStats[countryCode].entities || [])
      }
    }
  }

  // Calculate industry statistics for the selected country
  const calculateCountryIndustryStats = () => {
    if (!selectedCountry || !selectedCountryData.length) return []
    
    const industries = {}
    selectedCountryData.forEach(item => {
      const industry = item.organization?.industry || "Unknown"
      if (!industries[industry]) {
        industries[industry] = 0
      }
      industries[industry]++
    })
    
    return Object.entries(industries)
      .map(([name, count]) => ({
        name,
        value: count,
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 8)
  }

  const selectedCountryIndustries = calculateCountryIndustryStats()

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-bold">Ransomware Intelligence</h1>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="container py-6">
        {loading ? (
          <div className="space-y-4">
            <Skeleton className="h-[500px] w-full rounded-lg" />
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <Skeleton className="h-[200px] rounded-lg" />
              <Skeleton className="h-[200px] rounded-lg" />
              <Skeleton className="h-[200px] rounded-lg" />
            </div>
          </div>
        ) : error ? (
          <div className="text-center text-red-500 p-4 bg-red-100 rounded-lg">
            <h2 className="text-xl font-bold mb-2">Error loading data</h2>
            <p>{error}</p>
            <p className="mt-4 text-sm">
              There was an error loading the data. Please try refreshing the page. If the problem persists, there might
              be a server configuration issue.
            </p>
            {debugInfo && (
              <div className="mt-4 p-4 bg-white rounded text-left text-xs overflow-auto max-h-60">
                <pre>{JSON.stringify(debugInfo, null, 2)}</pre>
              </div>
            )}
          </div>
        ) : (
          <ErrorBoundary>
            <>
              <div className="mb-8">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center gap-2">
                      <Globe className="h-5 w-5" />
                      Geographic Distribution
                    </CardTitle>
                    <CardDescription>
                      {selectedCountry 
                        ? `Showing data for ${selectedCountry} - Click the country again or use the reset button to return to global view` 
                        : `Click on countries to see detailed statistics`}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[500px] w-full">
                      <MapChart
                        countryStats={countryStats}
                        onSelectCountry={handleCountrySelect}
                        selectedCountry={selectedCountry}
                      />
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                <StatsPanel
                  title="Total Incidents"
                  value={selectedCountry ? (countryStats[selectedCountry]?.count || 0) : data.length}
                  icon={<AlertTriangle className="h-5 w-5" />}
                  description={selectedCountry ? `Incidents in ${selectedCountry}` : "Total recorded ransomware incidents"}
                />
                <StatsPanel
                  title={selectedCountry ? "Affected Cities" : "Affected Countries"}
                  value={selectedCountry 
                    ? Object.keys(countryStats[selectedCountry]?.cities || {}).length 
                    : Object.keys(countryStats).length}
                  icon={<Globe className="h-5 w-5" />}
                  description={selectedCountry ? `Cities with incidents in ${selectedCountry}` : "Number of countries with incidents"}
                />
                <StatsPanel
                  title="Ransomware Groups"
                  value={groupStats.length}
                  icon={<Shield className="h-5 w-5" />}
                  description="Active ransomware groups"
                />
              </div>

              <div className="mt-8 grid gap-6 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Building className="h-5 w-5" />
                      {selectedCountry 
                        ? `Industries Affected in ${selectedCountry}` 
                        : "Top Industries Targeted"}
                    </CardTitle>
                    <CardDescription>Distribution of attacks by industry</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[300px]">
                      <EnhancedBarChart
                        data={selectedCountry ? selectedCountryIndustries : industryStats}
                        index="name"
                        categories={["value"]}
                        colors={["hsl(var(--chart-1))"]}
                        valueFormatter={(value) => `${value} incidents`}
                        yAxisWidth={120}
                      />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Shield className="h-5 w-5" />
                      Ransomware Groups
                    </CardTitle>
                    <CardDescription>Distribution of attacks by group</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[300px]">
                      <EnhancedPieChart
                        data={groupStats}
                        index="name"
                        category="value"
                        valueFormatter={(value) => `${value} incidents`}
                        colors={[
                          "hsl(var(--chart-1))",
                          "hsl(var(--chart-2))",
                          "hsl(var(--chart-3))",
                          "hsl(var(--chart-4))",
                          "hsl(var(--chart-5))",
                          "hsl(var(--chart-6))",
                        ]}
                      />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {selectedCountry && countryStats[selectedCountry] && (
                <CountryDetailCard
                  country={selectedCountry}
                  countryStats={countryStats}
                  onClose={() => {
                    setSelectedCountry(null);
                    setSelectedCountryData([]);
                  }}
                />
              )}
            </>
          </ErrorBoundary>
        )}
      </main>
    </div>
  );
}
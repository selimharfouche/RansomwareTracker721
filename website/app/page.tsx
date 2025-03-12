"use client"

import { useState, useEffect, useRef } from "react"
import { useTranslation } from "@/utils/translation"
import { MapChart } from "@/components/map-chart"
import { StatsPanel } from "@/components/stats-panel"
import { ThemeToggle } from "@/components/theme-toggle"
import { LanguageSwitcher } from "@/components/language-switcher"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Progress } from "@/components/ui/progress"
import { 
  Shield, 
  Globe, 
  Building, 
  AlertTriangle, 
  MapPin, 
  Users, 
  DollarSign, 
  Building2, 
  PieChart 
} from "lucide-react"
import ErrorBoundary from "@/components/error-boundary"
import { EnhancedBarChart } from "@/components/enhanced-bar-chart"
import { EnhancedPieChart } from "@/components/enhanced-pie-chart"
import { CountryDetailCard } from "@/components/country-detail-card"
import { CityListCard } from "@/components/city-list-card"

// Configuration constants
const SCROLL_ANIMATION_DURATION = 4000; // Duration in milliseconds (4 seconds)
const SCROLL_ANIMATION_DELAY = 100; // Delay before starting the animation (milliseconds)

// API route path
const DATA_PATH = "/api/data"

// Organization status colors
const statusColors = {
  "Private": "hsl(var(--chart-1))",
  "Public": "hsl(var(--chart-2))",
  "Government": "hsl(var(--chart-3))",
  "Non-profit": "hsl(var(--chart-4))",
  "Educational": "hsl(var(--chart-5))"
};

// Employee range order
const employeeRangeOrder = [
  "1-9",
  "10-49", 
  "50-99", 
  "100-499", 
  "500-999", 
  "1000-4999", 
  "5000+"
];

// Revenue range order
const revenueRangeOrder = [
  "<$1M",
  "$1M-$5M",
  "$5M-$10M",
  "$10M-$50M",
  "$50M-$100M",
  "$100M-$500M",
  "$500M-$1B",
  ">$1B"
];

export default function Home() {
  const { t, language } = useTranslation()
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedCountry, setSelectedCountry] = useState(null)
  const [countryStats, setCountryStats] = useState({})
  const [industryStats, setIndustryStats] = useState([])
  const [groupStats, setGroupStats] = useState([])
  const [globalCities, setGlobalCities] = useState([])
  const [employeeStats, setEmployeeStats] = useState([])
  const [revenueStats, setRevenueStats] = useState([])
  const [statusStats, setStatusStats] = useState([])
  const [selectedCountryData, setSelectedCountryData] = useState([])
  const [headerVisible, setHeaderVisible] = useState(true)
  const [lastScrollY, setLastScrollY] = useState(0)
  const [mapActive, setMapActive] = useState(false)
  const [isScrolling, setIsScrolling] = useState(false)
  const [chartAnimationKey, setChartAnimationKey] = useState(0)
  const [debugInfo, setDebugInfo] = useState(null)
  
  // Refs
  const chartsRef = useRef(null)
  const headerRef = useRef(null)
  const mapRef = useRef(null)
  const pieChartRef = useRef(null)
  const scrollTimeout = useRef(null)

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

  // Handle scrolling header and chart animations
  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      // Set scrolling state to true
      setIsScrolling(true);
      
      // Clear any existing timeout
      if (scrollTimeout.current) {
        clearTimeout(scrollTimeout.current);
      }
      
      // Set a timeout to detect when scrolling stops
      scrollTimeout.current = setTimeout(() => {
        setIsScrolling(false);
        // When scrolling stops, update the animation key to trigger a fresh animation
        setChartAnimationKey(prev => prev + 1);
      }, 150); // Wait for 150ms of no scroll events to consider scrolling stopped
      
      if (currentScrollY > lastScrollY && currentScrollY > 100) {
        // Scrolling down & past header
        setHeaderVisible(false);
      } else {
        // Scrolling up or at top
        setHeaderVisible(true);
      }
      
      setLastScrollY(currentScrollY);
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
      if (scrollTimeout.current) {
        clearTimeout(scrollTimeout.current);
      }
    };
  }, [lastScrollY]);

  // Effect to scroll to charts section when a country is selected - with configurable duration
  useEffect(() => {
    if (selectedCountry && chartsRef.current) {
      // Function to perform slow scrolling with configurable duration
      const scrollWithAnimation = () => {
        const targetElement = chartsRef.current;
        const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - 20;
        const startPosition = window.pageYOffset;
        const distance = targetPosition - startPosition;
        
        // Use the duration from our constant
        const duration = SCROLL_ANIMATION_DURATION;
        const startTime = performance.now();
        
        const animateScroll = (currentTime) => {
          const elapsedTime = currentTime - startTime;
          const progress = Math.min(elapsedTime / duration, 1);
          
          // Easing function for smoother animation
          const easeInOutQuad = t => t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
          const easedProgress = easeInOutQuad(progress);
          
          window.scrollTo(0, startPosition + distance * easedProgress);
          
          if (progress < 1) {
            requestAnimationFrame(animateScroll);
          } else {
            // When scroll animation completes, update the chart animation key
            setChartAnimationKey(prev => prev + 1);
          }
        };
        
        requestAnimationFrame(animateScroll);
      };
      
      // Start the scrolling animation with a configurable delay
      setTimeout(scrollWithAnimation, SCROLL_ANIMATION_DELAY);
    }
  }, [selectedCountry]);
  
  // Process organization statistics
  const processOrgStats = (entities) => {
    // Process employee ranges
    const employeeRanges = {};
    employeeRangeOrder.forEach(range => {
      employeeRanges[range] = 0;
    });
    
    // Process revenue ranges
    const revenueRanges = {};
    revenueRangeOrder.forEach(range => {
      revenueRanges[range] = 0;
    });
    
    // Process organization status
    const orgStatuses = {};
    
    entities.forEach(entity => {
      // Employee range statistics
      const employeeRange = entity.organization?.size?.employees_range || "Unknown";
      if (employeeRanges.hasOwnProperty(employeeRange)) {
        employeeRanges[employeeRange]++;
      } else if (employeeRange !== "Unknown") {
        employeeRanges["Unknown"] = (employeeRanges["Unknown"] || 0) + 1;
      }
      
      // Revenue range statistics
      const revenueRange = entity.organization?.size?.revenue_range || "Unknown";
      if (revenueRanges.hasOwnProperty(revenueRange)) {
        revenueRanges[revenueRange]++;
      } else if (revenueRange !== "Unknown") {
        revenueRanges["Unknown"] = (revenueRanges["Unknown"] || 0) + 1;
      }
      
      // Organization status statistics
      const status = entity.organization?.status || "Unknown";
      orgStatuses[status] = (orgStatuses[status] || 0) + 1;
    });
    
    // Format for charts - employee ranges
    const formattedEmployeeRanges = Object.keys(employeeRanges)
      .filter(range => employeeRanges[range] > 0)
      .map(range => ({
        name: range,
        value: employeeRanges[range],
        order: employeeRangeOrder.indexOf(range)
      }))
      .sort((a, b) => {
        if (a.name === "Unknown") return 1;
        if (b.name === "Unknown") return -1;
        return a.order - b.order;
      });
    
    // Format for charts - revenue ranges
    const formattedRevenueRanges = Object.keys(revenueRanges)
      .filter(range => revenueRanges[range] > 0)
      .map(range => ({
        name: range,
        value: revenueRanges[range],
        order: revenueRangeOrder.indexOf(range)
      }))
      .sort((a, b) => {
        if (a.name === "Unknown") return 1;
        if (b.name === "Unknown") return -1;
        return a.order - b.order;
      });
    
    // Format for charts - organization status
    const formattedStatuses = Object.keys(orgStatuses)
      .map(status => ({
        name: status,
        value: orgStatuses[status]
      }))
      .sort((a, b) => b.value - a.value);
    
    return {
      employeeStats: formattedEmployeeRanges,
      revenueStats: formattedRevenueRanges,
      statusStats: formattedStatuses
    };
  };

  const processData = (entities) => {
    // Process country statistics with country code normalization
    const countries = {};
    const industries = {};
    const groups = {};
    const allCities = {};

    // Process each entity
    entities.forEach((item) => {
      // Skip items with missing essential data
      if (!item) return;
      
      // Normalize and handle country stats
      let countryCode = "UNK";
      
      if (item.geography && item.geography.country_code) {
        countryCode = item.geography.country_code.toUpperCase();
      }
      
      if (!countries[countryCode]) {
        const countryName = (item.geography && item.geography.country) || 
                          (countryCode === "UNK" ? t("global") : countryCode);
        
        countries[countryCode] = { 
          count: 0, 
          cities: {}, 
          entities: [],
          name: countryName
        };
      }
      
      countries[countryCode].count++;
      countries[countryCode].entities.push(item);

      // City stats - both for countries and global
      const city = item.geography?.city || t("unknown");
      // Country city stats
      if (!countries[countryCode].cities[city]) {
        countries[countryCode].cities[city] = 0;
      }
      countries[countryCode].cities[city]++;
      
      // Global city stats
      if (!allCities[city]) {
        allCities[city] = {
          count: 0,
          countryCode: countryCode,
          countryName: countries[countryCode].name
        };
      }
      allCities[city].count++;

      // Industry stats
      const industry = item.organization?.industry || t("unknown");
      if (!industries[industry]) {
        industries[industry] = 0;
      }
      industries[industry]++;

      // Ransomware group stats
      const group = item.ransomware_group || t("unknown");
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
      
    // Format global city data
    const formattedGlobalCities = Object.entries(allCities)
      .map(([name, data]) => ({
        city: name,
        count: data.count,
        countryCode: data.countryCode,
        countryName: data.countryName
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 20);
    
    // Process organization statistics
    const { employeeStats, revenueStats, statusStats } = processOrgStats(entities);

    setData(entities);
    setCountryStats(countries);
    setIndustryStats(industryData);
    setGroupStats(groupData);
    setGlobalCities(formattedGlobalCities);
    setEmployeeStats(employeeStats);
    setRevenueStats(revenueStats);
    setStatusStats(statusStats);
  };

  const handleCountrySelect = (countryCode) => {
    if (countryCode === selectedCountry) {
      // If the same country is selected twice, clear the selection
      setSelectedCountry(null)
      setSelectedCountryData([])
      
      // Reset to global organization stats
      const { employeeStats, revenueStats, statusStats } = processOrgStats(data);
      setEmployeeStats(employeeStats);
      setRevenueStats(revenueStats);
      setStatusStats(statusStats);

      // Increment animation key for a fresh animation
      setChartAnimationKey(prev => prev + 1);
    } else {
      setSelectedCountry(countryCode)
      if (countryStats[countryCode]) {
        const countryEntities = countryStats[countryCode].entities || [];
        setSelectedCountryData(countryEntities);
        
        // Update organization stats for selected country
        const { employeeStats, revenueStats, statusStats } = processOrgStats(countryEntities);
        setEmployeeStats(employeeStats);
        setRevenueStats(revenueStats);
        setStatusStats(statusStats);

        // Increment animation key for a fresh animation
        setChartAnimationKey(prev => prev + 1);
      }
    }
  }

  // Calculate industry statistics for the selected country
  const calculateCountryIndustryStats = () => {
    if (!selectedCountry || !selectedCountryData.length) return []
    
    const industries = {}
    selectedCountryData.forEach(item => {
      const industry = item.organization?.industry || t("unknown")
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
  
  // Handle map activation
  const activateMap = () => {
    setMapActive(true);
  };

  // Create a component for organization size stats visualization
  const OrgSizeStats = ({ employeeData, revenueData }) => {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            {t("organization_size")}
          </CardTitle>
          <CardDescription>{t("distribution_by_size")}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-medium mb-2">{t("employees_range")}</h3>
              <div className="space-y-2">
                {employeeData.map((range) => (
                  <div key={range.name} className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">{range.name}</span>
                      <span className="text-sm text-muted-foreground">{range.value}</span>
                    </div>
                    <Progress 
                      value={(range.value / Math.max(...employeeData.map(r => r.value))) * 100} 
                      className="h-2" 
                      indicatorClassName="bg-primary" 
                    />
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h3 className="text-sm font-medium mb-2">{t("revenue_range")}</h3>
              <div className="space-y-2">
                {revenueData.map((range) => (
                  <div key={range.name} className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">{range.name}</span>
                      <span className="text-sm text-muted-foreground">{range.value}</span>
                    </div>
                    <Progress 
                      value={(range.value / Math.max(...revenueData.map(r => r.value))) * 100} 
                      className="h-2" 
                      indicatorClassName="bg-primary" 
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  // Create a component for organization status visualization
  const OrgStatusStats = ({ statusData }) => {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            {t("organization_status")}
          </CardTitle>
          <CardDescription>{t("distribution_by_status")}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]" ref={pieChartRef}>
            {/* Use the animation key to control when the chart re-renders with animation */}
            <EnhancedPieChart
              key={`status-chart-${chartAnimationKey}`}
              data={statusData}
              index="name"
              category="value"
              valueFormatter={(value) => `${value} ${t(value === 1 ? "incident" : "incidents")}`}
              colors={Object.values(statusColors)}
            />
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="min-h-screen bg-background">
      <header 
        ref={headerRef}
        className={`sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 transition-transform duration-300 ${
          headerVisible ? 'translate-y-0' : '-translate-y-full'
        }`}
      >
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-bold">{t("ransomware_intelligence")}</h1>
          </div>
          <div className="flex items-center gap-4">
            <LanguageSwitcher />
            <ThemeToggle />
          </div>
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
            <h2 className="text-xl font-bold mb-2">{t("error_loading_data")}</h2>
            <p>{error}</p>
            <p className="mt-4 text-sm">
              {t("error_description")}
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
                      {t("geographic_distribution")}
                    </CardTitle>
                    <CardDescription>
                      {!mapActive ? 
                        t("click_to_activate_map") : 
                        selectedCountry 
                          ? t("showing_data_for", {country: countryStats[selectedCountry]?.name || selectedCountry})
                          : t("click_countries_for_stats")
                      }
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div 
                      ref={mapRef}
                      className="h-[500px] w-full relative" 
                      onClick={!mapActive ? activateMap : undefined}
                    >
                      {/* Overlay to prevent map interaction until activated */}
                      {!mapActive && (
                        <div className="absolute inset-0 bg-black/5 backdrop-blur-[1px] flex items-center justify-center z-10 cursor-pointer">
                          <div className="bg-background rounded-lg p-4 shadow-lg">
                            <p className="text-center font-medium">{t("click_to_activate_map")}</p>
                          </div>
                        </div>
                      )}
                      <MapChart
                        countryStats={countryStats}
                        onSelectCountry={handleCountrySelect}
                        selectedCountry={selectedCountry}
                        disabled={!mapActive}
                      />
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                <StatsPanel
                  title={t("total_incidents")}
                  value={selectedCountry ? (countryStats[selectedCountry]?.count || 0) : data.length}
                  icon={<AlertTriangle className="h-5 w-5" />}
                  description={selectedCountry ? t("incidents_in_country", {country: countryStats[selectedCountry]?.name || selectedCountry}) : t("total_recorded_incidents")}
                />
                <StatsPanel
                  title={selectedCountry ? t("affected_cities") : t("affected_countries")}
                  value={selectedCountry 
                    ? Object.keys(countryStats[selectedCountry]?.cities || {}).length 
                    : Object.keys(countryStats).length}
                  icon={<Globe className="h-5 w-5" />}
                  description={selectedCountry ? t("cities_with_incidents_in", {country: countryStats[selectedCountry]?.name || selectedCountry}) : t("countries_with_incidents")}
                />
                <StatsPanel
                  title={t("ransomware_groups")}
                  value={groupStats.length}
                  icon={<Shield className="h-5 w-5" />}
                  description={t("active_ransomware_groups")}
                />
              </div>

              {/* Charts Section with Ref for scrolling */}
              <div ref={chartsRef} className="mt-8 grid gap-6 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Building className="h-5 w-5" />
                      {selectedCountry 
                        ? t("industries_affected_in", {country: countryStats[selectedCountry]?.name || selectedCountry})
                        : t("top_industries_targeted")}
                    </CardTitle>
                    <CardDescription>{t("distribution_by_industry")}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[300px]">
                      <EnhancedBarChart
                        key={`industry-chart-${chartAnimationKey}`}
                        data={selectedCountry ? selectedCountryIndustries : industryStats}
                        index="name"
                        categories={["value"]}
                        colors={["hsl(var(--chart-1))"]}
                        valueFormatter={(value) => `${value} ${t(value === 1 ? "incident" : "incidents")}`}
                        yAxisWidth={120}
                      />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Shield className="h-5 w-5" />
                      {t("ransomware_groups")}
                    </CardTitle>
                    <CardDescription>{t("distribution_by_group")}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[300px]">
                      <EnhancedPieChart
                        key={`group-chart-${chartAnimationKey}`}
                        data={groupStats}
                        index="name"
                        category="value"
                        valueFormatter={(value) => `${value} ${t(value === 1 ? "incident" : "incidents")}`}
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
              
              {/* Organization Statistics Section */}
              <div className="mt-8 grid gap-6 md:grid-cols-2">
                <OrgSizeStats employeeData={employeeStats} revenueData={revenueStats} />
                <OrgStatusStats statusData={statusStats} />
              </div>

              {/* City Detail Section - Country or Global */}
              <div className="mt-8">
                {selectedCountry && countryStats[selectedCountry] ? (
                  <CountryDetailCard
                    country={selectedCountry}
                    countryStats={countryStats}
                    onClose={() => {
                      setSelectedCountry(null);
                      setSelectedCountryData([]);
                      
                      // Reset to global organization stats
                      const { employeeStats, revenueStats, statusStats } = processOrgStats(data);
                      setEmployeeStats(employeeStats);
                      setRevenueStats(revenueStats);
                      setStatusStats(statusStats);
                      
                      // Increment animation key for a fresh animation
                      setChartAnimationKey(prev => prev + 1);
                    }}
                  />
                ) : (
                  globalCities.length > 0 && (
                    <CityListCard
                      title={t("top_affected_cities_worldwide")}
                      cities={globalCities}
                      showCountry={true}
                    />
                  )
                )}
              </div>
            </>
          </ErrorBoundary>
        )}
      </main>
    </div>
  );
}
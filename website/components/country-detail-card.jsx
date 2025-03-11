"use client"

import { useState } from "react"
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Building, MapPin, Shield, X, BarChart3 } from "lucide-react"
import { EnhancedPieChart } from "@/components/enhanced-pie-chart"

export function CountryDetailCard({ country, countryStats, onClose }) {
  const [activeTab, setActiveTab] = useState("cities")

  // No data check
  if (!country || !countryStats || !countryStats[country]) {
    return null;
  }

  const countryData = countryStats[country];
  const { count, cities, entities = [], name = country } = countryData;

  // Format city data for display
  const cityEntries = Object.entries(cities || {})
    .sort(([, a], [, b]) => b - a)
    .map(([city, count]) => ({ city, count }));

  // Calculate incident counts by industry
  const industryMap = {};
  entities.forEach(entity => {
    const industry = entity.organization?.industry || "Unknown";
    industryMap[industry] = (industryMap[industry] || 0) + 1;
  });

  const industryData = Object.entries(industryMap)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8);

  // Calculate incident counts by group
  const groupMap = {};
  entities.forEach(entity => {
    const group = entity.ransomware_group || "Unknown";
    groupMap[group] = (groupMap[group] || 0) + 1;
  });

  const groupData = Object.entries(groupMap)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 5);

  return (
    <Card className="mt-8 rounded-lg border shadow-md overflow-hidden">
      <CardHeader className="relative pb-2 bg-muted/20">
        <div className="flex justify-between items-center">
          <CardTitle className="flex items-center gap-2 text-xl">
            <MapPin className="h-5 w-5 text-primary" />
            {name}
          </CardTitle>
          <button
            onClick={onClose}
            className="rounded-full p-1 hover:bg-muted transition-colors"
            aria-label="Close country details"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <CardDescription className="flex items-center gap-1.5">
          <Shield className="h-4 w-4 text-primary/80" />
          <span>{count} ransomware incidents recorded</span>
        </CardDescription>
      </CardHeader>
      <CardContent className="p-0">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid grid-cols-3 p-0 bg-muted/20 rounded-none">
            <TabsTrigger 
              value="cities" 
              className="data-[state=active]:bg-background rounded-none border-b-2 border-transparent data-[state=active]:border-primary"
            >
              <div className="flex items-center gap-1.5 py-1">
                <MapPin className="h-4 w-4" />
                <span>Cities</span>
              </div>
            </TabsTrigger>
            <TabsTrigger 
              value="industries" 
              className="data-[state=active]:bg-background rounded-none border-b-2 border-transparent data-[state=active]:border-primary"
            >
              <div className="flex items-center gap-1.5 py-1">
                <Building className="h-4 w-4" />
                <span>Industries</span>
              </div>
            </TabsTrigger>
            <TabsTrigger 
              value="groups" 
              className="data-[state=active]:bg-background rounded-none border-b-2 border-transparent data-[state=active]:border-primary"
            >
              <div className="flex items-center gap-1.5 py-1">
                <Shield className="h-4 w-4" />
                <span>Groups</span>
              </div>
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="cities" className="mt-0">
            {cityEntries.length > 0 ? (
              <ScrollArea className="h-[350px] px-4 py-3">
                <div className="space-y-2">
                  {cityEntries.map(({ city, count }, index) => (
                    <div 
                      key={city} 
                      className="flex items-center justify-between p-2 rounded hover:bg-muted/30 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
                          {index + 1}
                        </div>
                        <span className="font-medium truncate max-w-[150px]">{city}</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-sm text-muted-foreground">{count} incidents</span>
                        <div 
                          className="ml-2 h-2 bg-primary/80 rounded-full" 
                          style={{ 
                            width: `${Math.max(16, (count / cityEntries[0].count) * 80)}px`
                          }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            ) : (
              <div className="flex h-[350px] items-center justify-center text-muted-foreground">
                No city data available
              </div>
            )}
          </TabsContent>
          
          <TabsContent value="industries" className="mt-0">
            <div className="h-[350px] p-4">
              {industryData.length > 0 ? (
                <div className="h-full flex flex-col">
                  <h3 className="text-sm font-medium mb-1 flex items-center gap-1.5">
                    <Building className="h-4 w-4 text-primary/80" />
                    <span>Most Targeted Industries in {name}</span>
                  </h3>
                  <div className="grow">
                    <div className="h-full max-h-[300px]">
                      <ScrollArea className="h-full">
                        <div className="space-y-2 py-2">
                          {industryData.map((industry, idx) => (
                            <div key={industry.name} className="flex items-center justify-between p-2 rounded hover:bg-muted/30 transition-colors">
                              <div className="flex items-center gap-3">
                                <div 
                                  className="h-2 w-2 rounded-full" 
                                  style={{ backgroundColor: `hsl(var(--chart-${(idx % 6) + 1}))` }}
                                ></div>
                                <span className="font-medium truncate max-w-[150px]">{industry.name}</span>
                              </div>
                              <div className="flex items-center">
                                <span className="text-sm text-muted-foreground">{industry.value} incidents</span>
                                <div 
                                  className="ml-2 h-2 bg-primary/80 rounded-full" 
                                  style={{ 
                                    width: `${Math.max(16, (industry.value / industryData[0].value) * 80)}px`
                                  }}
                                ></div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </ScrollArea>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex h-full items-center justify-center text-muted-foreground">
                  No industry data available
                </div>
              )}
            </div>
          </TabsContent>
          
          <TabsContent value="groups" className="mt-0">
            <div className="h-[350px] p-4">
              {groupData.length > 0 ? (
                <div className="h-full">
                  <h3 className="text-sm font-medium mb-3 flex items-center gap-1.5">
                    <Shield className="h-4 w-4 text-primary/80" />
                    <span>Ransomware Groups Active in {name}</span>
                  </h3>
                  <div className="h-[300px]">
                    <EnhancedPieChart 
                      data={groupData}
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
                </div>
              ) : (
                <div className="flex h-full items-center justify-center text-muted-foreground">
                  No group data available
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
"use client"

import { useState } from "react"
import { useTranslation } from "@/utils/translation"
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card"
import { MapPin, ChevronDown, ChevronUp } from "lucide-react"

export function CityListCard({ title, cities, showCountry = false }) {
  const { t } = useTranslation()
  const [showAllCities, setShowAllCities] = useState(false)

  // Toggle showing all cities
  const toggleAllCities = () => {
    setShowAllCities(!showAllCities)
  }

  // Format city data for display
  const allCityEntries = cities || [];
    
  // Display 10 cities by default, or all if expanded
  const cityEntries = showAllCities 
    ? allCityEntries 
    : allCityEntries.slice(0, 10);

  return (
    <Card className="rounded-lg border shadow-md overflow-hidden">
      <CardHeader className="pb-2 bg-muted/20">
        <CardTitle className="flex items-center gap-2">
          <MapPin className="h-5 w-5 text-primary" />
          {title}
        </CardTitle>
        <CardDescription>
          {t("top_cities_by_incidents")}
        </CardDescription>
      </CardHeader>
      <CardContent className="p-4">
        {cityEntries.length > 0 ? (
          <div>
            <table className="w-full mb-2">
              <tbody>
                {cityEntries.map(({ city, count, countryName }, index) => (
                  <tr key={`${city}-${index}`} className="border-b last:border-b-0">
                    <td className="py-3">
                      <div className="flex items-center gap-3">
                        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
                          {index + 1}
                        </div>
                        <div>
                          <span className="font-medium">{city}</span>
                          {showCountry && countryName && (
                            <div className="text-xs text-muted-foreground">
                              {countryName}
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="py-3 text-right text-sm text-muted-foreground whitespace-nowrap">
                      {count} {t(count === 1 ? "incident" : "incidents")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {allCityEntries.length > 10 && (
              <button 
                onClick={toggleAllCities}
                className="w-full text-center py-2 text-sm text-primary hover:underline flex items-center justify-center gap-1"
              >
                {showAllCities ? (
                  <>
                    <span>{t("show_fewer_cities")}</span>
                    <ChevronUp className="h-3 w-3" />
                  </>
                ) : (
                  <>
                    <span>{t("more_cities", {count: allCityEntries.length - 10})}</span>
                    <ChevronDown className="h-3 w-3" />
                  </>
                )}
              </button>
            )}
          </div>
        ) : (
          <div className="text-center py-6 text-muted-foreground">
            {t("no_city_data")}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
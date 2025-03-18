"use client"

import { useState, useEffect } from "react"
import WorldMap from "./world-map"
import LanguageSwitcher from "./language-switcher" // Fixed import
import { ThemeToggle } from "./theme-toggle"
import { IndustryChart } from "./charts/industry-chart"
import { RevenueChart } from "./charts/revenue-chart"
import { EmployeeChart } from "./charts/employee-chart"
import { fetchData, getCountryData, getTopIndustries, getRevenueRanges, getEmployeeRanges } from "@/lib/data-utils"

export default function WorldMapDashboard() {
  const [language, setLanguage] = useState<string>("en")
  const [countryData, setCountryData] = useState<Record<string, number>>({})
  const [topIndustries, setTopIndustries] = useState<Array<{ name: string; count: number }>>([])
  const [revenueRanges, setRevenueRanges] = useState<Array<{ name: string; value: number }>>([])
  const [employeeRanges, setEmployeeRanges] = useState<Array<{ name: string; count: number }>>([])
  const [totalEntities, setTotalEntities] = useState<number>(0)

  useEffect(() => {
    const loadData = async () => {
      const entities = await fetchData()
      setTotalEntities(entities.length)
      setCountryData(getCountryData(entities))
      setTopIndustries(getTopIndustries(entities))
      setRevenueRanges(getRevenueRanges(entities))
      setEmployeeRanges(getEmployeeRanges(entities))
    }

    loadData()
  }, [])

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">
          {language === "en" ? "Global Entity Dashboard" : "Tableau de Bord des Entités Mondiales"}
        </h1>
        <div className="flex items-center gap-4">
          <LanguageSwitcher currentLanguage={language} onLanguageChange={setLanguage} />
          <ThemeToggle language={language} />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-lg border bg-card text-card-foreground shadow-sm">
          <div className="text-2xl font-bold">{totalEntities}</div>
          <div className="text-sm text-muted-foreground">
            {language === "en" ? "Total Entities" : "Total des Entités"}
          </div>
        </div>
        <div className="p-4 rounded-lg border bg-card text-card-foreground shadow-sm">
          <div className="text-2xl font-bold">{Object.keys(countryData).length}</div>
          <div className="text-sm text-muted-foreground">
            {language === "en" ? "Countries Affected" : "Pays Affectés"}
          </div>
        </div>
        <div className="p-4 rounded-lg border bg-card text-card-foreground shadow-sm">
          <div className="text-2xl font-bold">{topIndustries.length > 0 ? topIndustries[0].name : "-"}</div>
          <div className="text-sm text-muted-foreground">
            {language === "en" ? "Top Industry" : "Industrie Principale"}
          </div>
        </div>
      </div>

      <WorldMap countryData={countryData} language={language} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <IndustryChart data={topIndustries} language={language} />
        <RevenueChart data={revenueRanges} language={language} />
        <EmployeeChart data={employeeRanges} language={language} />
      </div>
    </div>
  )
}


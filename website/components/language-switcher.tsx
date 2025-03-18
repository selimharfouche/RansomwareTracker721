"use client"

import { Button } from "@/components/ui/button"
import { Globe } from "lucide-react"

const LanguageSwitcher = ({ currentLanguage, onLanguageChange }) => {
  const toggleLanguage = () => {
    const newLanguage = currentLanguage === "en" ? "fr" : "en"
    onLanguageChange(newLanguage)
  }

  return (
    <Button variant="outline" size="sm" onClick={toggleLanguage} className="flex items-center gap-2">
      <Globe className="h-4 w-4" />
      <span>{currentLanguage === "en" ? "FR" : "EN"}</span>
    </Button>
  )
}

export default LanguageSwitcher


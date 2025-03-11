"use client"

import { useState, useEffect } from "react"
import { useTranslation } from "@/utils/translation"
import { Button } from "@/components/ui/button"
import { Globe } from "lucide-react"

export function LanguageSwitcher() {
  const { language, setLanguage } = useTranslation()
  
  const toggleLanguage = () => {
    const newLanguage = language === 'en' ? 'fr' : 'en'
    setLanguage(newLanguage)
    localStorage.setItem('language', newLanguage)
  }
  
  return (
    <Button 
      variant="ghost" 
      size="icon"
      onClick={toggleLanguage}
      aria-label={`Switch to ${language === 'en' ? 'French' : 'English'}`}
      className="flex items-center gap-1"
    >
      <Globe className="h-5 w-5" />
      <span className="ml-1 text-xs font-bold">{language.toUpperCase()}</span>
    </Button>
  )
}
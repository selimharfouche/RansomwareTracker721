// src/contexts/LanguageContext.tsx
'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

type Language = 'en' | 'fr';

interface LanguageContextType {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: string) => string;
}

// Simple translations - expand as needed
const translations = {
  en: {
    'ransomware_tracker': 'Ransomware Tracker',
    'monitor_latest': 'Monitor the latest targets from various ransomware groups',
    'latest_target': 'Latest Target',
    'no_targets': 'No targets found',
    'status': 'Status',
    'updated': 'Updated',
    'entities': 'entities',
    'theme': 'Theme',
    'language': 'Language',
    'light': 'Light',
    'dark': 'Dark',
    'no_data': 'No data available',
    'no_data_description': 'No ransomware data has been found. Make sure the data directory exists and has JSON files.',
    'unknown': 'Unknown',
    'loading': 'Loading data...',
  },
  fr: {
    'ransomware_tracker': 'Suivi des Ransomwares',
    'monitor_latest': 'Suivez les dernières cibles de divers groupes de ransomware',
    'latest_target': 'Dernière Cible',
    'no_targets': 'Aucune cible trouvée',
    'status': 'Statut',
    'updated': 'Mis à jour',
    'entities': 'entités',
    'theme': 'Thème',
    'language': 'Langue',
    'light': 'Clair',
    'dark': 'Sombre',
    'no_data': 'Aucune donnée disponible',
    'no_data_description': 'Aucune donnée de ransomware n\'a été trouvée. Assurez-vous que le répertoire de données existe et contient des fichiers JSON.',
    'unknown': 'Inconnu',
    'loading': 'Chargement des données...',
  }
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState<Language>('en');

  // Translation function
  const t = (key: string): string => {
    return (translations[language] as Record<string, string>)[key] || key;
  };

  // Load saved language preference
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedLanguage = localStorage.getItem('language') as Language | null;
      if (savedLanguage && (savedLanguage === 'en' || savedLanguage === 'fr')) {
        setLanguage(savedLanguage);
      }
    }
  }, []);

  // Save language preference when it changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('language', language);
      document.documentElement.lang = language;
    }
  }, [language]);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
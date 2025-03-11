"use client"

import { createContext, useContext, useState, useEffect } from "react"

// Translation dictionaries
const translations = {
  en: {
    // General
    ransomware_intelligence: "Ransomware Intelligence",
    unknown: "Unknown",
    global: "Global",
    incident: "incident",
    incidents: "incidents",
    of_total: "of total",
    no_data: "No data",
    low: "Low",
    high: "High",
    loading_map_data: "Loading map data...",
    
    // Map and navigation
    geographic_distribution: "Geographic Distribution",
    click_to_activate_map: "Click to activate map",
    showing_data_for: "Showing data for {{country}} - Click the country again or use the reset button to return to global view",
    click_countries_for_stats: "Click on countries to see detailed statistics",
    close_country_details: "Close country details",
    
    // Stats and metrics
    total_incidents: "Total Incidents",
    total_recorded_incidents: "Total recorded ransomware incidents",
    incidents_in_country: "Incidents in {{country}}",
    affected_cities: "Affected Cities",
    affected_countries: "Affected Countries",
    cities_with_incidents_in: "Cities with incidents in {{country}}",
    countries_with_incidents: "Number of countries with incidents",
    ransomware_groups: "Ransomware Groups",
    active_ransomware_groups: "Active ransomware groups",
    
    // Charts and data visualization
    top_industries_targeted: "Top Industries Targeted",
    industries_affected_in: "Industries Affected in {{country}}",
    distribution_by_industry: "Distribution of attacks by industry",
    distribution_by_group: "Distribution of attacks by group",
    
    // Cities
    top_affected_cities_worldwide: "Top Affected Cities Worldwide",
    top_cities: "Top Cities",
    top_cities_by_incidents: "Top cities by number of ransomware incidents",
    ransomware_incidents_recorded: "{{count}} ransomware incidents recorded",
    show_fewer_cities: "Show fewer cities",
    more_cities: "+ {{count}} more cities",
    no_city_data: "No city data available",
    
    // Errors
    error_loading_data: "Error loading data",
    error_description: "There was an error loading the data. Please try refreshing the page. If the problem persists, there might be a server configuration issue."
  },
  fr: {
    // General
    ransomware_intelligence: "Intelligence Rançongiciel",
    unknown: "Inconnu",
    global: "Mondial",
    incident: "incident",
    incidents: "incidents",
    of_total: "du total",
    no_data: "Pas de données",
    low: "Faible",
    high: "Élevé",
    loading_map_data: "Chargement des données cartographiques...",
    
    // Map and navigation
    geographic_distribution: "Distribution Géographique",
    click_to_activate_map: "Cliquez pour activer la carte",
    showing_data_for: "Affichage des données pour {{country}} - Cliquez à nouveau sur le pays ou utilisez le bouton de réinitialisation pour revenir à la vue globale",
    click_countries_for_stats: "Cliquez sur les pays pour voir les statistiques détaillées",
    close_country_details: "Fermer les détails du pays",
    
    // Stats and metrics
    total_incidents: "Total des Incidents",
    total_recorded_incidents: "Total des incidents de rançongiciel enregistrés",
    incidents_in_country: "Incidents en {{country}}",
    affected_cities: "Villes Affectées",
    affected_countries: "Pays Affectés",
    cities_with_incidents_in: "Villes avec incidents en {{country}}",
    countries_with_incidents: "Nombre de pays avec incidents",
    ransomware_groups: "Groupes de Rançongiciel",
    active_ransomware_groups: "Groupes de rançongiciel actifs",
    
    // Charts and data visualization
    top_industries_targeted: "Principales Industries Ciblées",
    industries_affected_in: "Industries Affectées en {{country}}",
    distribution_by_industry: "Distribution des attaques par industrie",
    distribution_by_group: "Distribution des attaques par groupe",
    
    // Cities
    top_affected_cities_worldwide: "Principales Villes Affectées Mondiales",
    top_cities: "Principales Villes",
    top_cities_by_incidents: "Principales villes par nombre d'incidents de rançongiciel",
    ransomware_incidents_recorded: "{{count}} incidents de rançongiciel enregistrés",
    show_fewer_cities: "Afficher moins de villes",
    more_cities: "+ {{count}} villes supplémentaires",
    no_city_data: "Aucune donnée de ville disponible",
    
    // Errors
    error_loading_data: "Erreur de chargement des données",
    error_description: "Une erreur est survenue lors du chargement des données. Veuillez actualiser la page. Si le problème persiste, il pourrait y avoir un problème de configuration du serveur."
  }
};

// Translation context
const TranslationContext = createContext();

export function TranslationProvider({ children }) {
  // Check localStorage or default to English
  const [language, setLanguage] = useState('en');
  
  useEffect(() => {
    const savedLanguage = localStorage.getItem('language');
    if (savedLanguage && ['en', 'fr'].includes(savedLanguage)) {
      setLanguage(savedLanguage);
    } else {
      // Try to detect browser language
      const browserLang = navigator.language.split('-')[0];
      if (browserLang === 'fr') {
        setLanguage('fr');
      }
    }
  }, []);
  
  // Translation function with template support
  const t = (key, params = {}) => {
    const translation = translations[language][key] || key;
    
    if (Object.keys(params).length === 0) {
      return translation;
    }
    
    // Replace template variables
    return translation.replace(/\{\{(\w+)\}\}/g, (_, match) => {
      return params[match] !== undefined ? params[match] : `{{${match}}}`;
    });
  };
  
  return (
    <TranslationContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </TranslationContext.Provider>
  );
}

export function useTranslation() {
  const context = useContext(TranslationContext);
  if (context === undefined) {
    throw new Error('useTranslation must be used within a TranslationProvider');
  }
  return context;
}

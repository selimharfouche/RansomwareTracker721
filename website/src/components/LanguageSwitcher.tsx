// src/components/LanguageSwitcher.tsx
'use client';

import React from 'react';
import { useLanguage } from '../contexts/LanguageContext';

export default function LanguageSwitcher() {
  const { language, setLanguage } = useLanguage();

  const toggleLanguage = () => {
    setLanguage(language === 'en' ? 'fr' : 'en');
  };

  return (
    <div className="flex items-center space-x-2">
      {/* English label */}
      <span 
        className={`text-sm font-medium ${language === 'en' ? 'text-ransomware-600 dark:text-ransomware-400' : 'text-gray-400'}`}
      >
        EN
      </span>
      
      {/* Toggle Switch */}
      <div 
        onClick={toggleLanguage}
        className="relative inline-flex items-center cursor-pointer"
      >
        <div className="w-12 h-6 bg-gray-300 dark:bg-gray-600 rounded-full px-1 flex items-center transition-colors">
          <div 
            className={`w-4 h-4 rounded-full transform transition-transform duration-300 ease-in-out bg-white
              ${language === 'en' ? 'translate-x-0' : 'translate-x-6'}
            `}
          ></div>
        </div>
      </div>
      
      {/* French label */}
      <span 
        className={`text-sm font-medium ${language === 'fr' ? 'text-ransomware-600 dark:text-ransomware-400' : 'text-gray-400'}`}
      >
        FR
      </span>
    </div>
  );
}
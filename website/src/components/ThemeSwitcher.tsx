// src/components/ThemeSwitcher.tsx
'use client';

import React from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { useLanguage } from '../contexts/LanguageContext';

export default function ThemeSwitcher() {
  const { theme, setTheme } = useTheme();
  const { t } = useLanguage();

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  return (
    <div className="flex items-center space-x-2">
      {/* Sun Icon */}
      <svg 
        xmlns="http://www.w3.org/2000/svg" 
        className={`h-5 w-5 ${theme === 'light' ? 'text-yellow-500' : 'text-gray-400'}`} 
        fill="none" 
        viewBox="0 0 24 24" 
        stroke="currentColor"
      >
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth={2} 
          d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" 
        />
      </svg>
      
      {/* Toggle Switch */}
      <div 
        onClick={toggleTheme}
        className="relative inline-flex items-center cursor-pointer"
      >
        <div className={`w-12 h-6 rounded-full px-1 flex items-center transition-colors ${theme === 'dark' ? 'bg-gray-600' : 'bg-gray-300'}`}>
          <div 
            className={`w-4 h-4 rounded-full transform transition-transform duration-300 ease-in-out bg-white
              ${theme === 'light' ? 'translate-x-0' : 'translate-x-6'}
            `}
          ></div>
        </div>
      </div>
      
      {/* Moon Icon */}
      <svg 
        xmlns="http://www.w3.org/2000/svg" 
        className={`h-5 w-5 ${theme === 'dark' ? 'text-indigo-300' : 'text-gray-400'}`} 
        fill="none" 
        viewBox="0 0 24 24" 
        stroke="currentColor"
      >
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth={2} 
          d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" 
        />
      </svg>
    </div>
  );
}
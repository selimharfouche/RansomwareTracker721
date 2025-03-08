// src/components/NavBar.tsx
'use client';

import React from 'react';
import ThemeSwitcher from './ThemeSwitcher';
import LanguageSwitcher from './LanguageSwitcher';
import { useLanguage } from '../contexts/LanguageContext';

export default function NavBar() {
  const { t } = useLanguage();

  return (
    <nav className="bg-card shadow-sm theme-transition">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <span className="text-xl font-bold text-ransomware theme-transition">
              {t('ransomware_tracker')}
            </span>
          </div>
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-secondary mr-1 theme-transition">{t('theme')}:</span>
              <ThemeSwitcher />
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-secondary mr-1 theme-transition">{t('language')}:</span>
              <LanguageSwitcher />
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
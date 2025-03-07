'use client';

import React from 'react';
import RansomwareCard from './RansomwareCard';
import { RansomwareSite } from '../lib/ransomware';
import { useLanguage } from '../contexts/LanguageContext';

interface RansomwareGridProps {
  sites: RansomwareSite[];
}

export default function RansomwareGrid({ sites }: RansomwareGridProps) {
  const { t } = useLanguage();

  if (!sites || sites.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-100 dark:bg-gray-900 rounded-xl">
        <div className="text-center">
          <h3 className="text-xl font-medium text-gray-700 dark:text-gray-300">{t('no_data')}</h3>
          <p className="mt-2 text-gray-500 dark:text-gray-400">
            {t('no_data_description')}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {sites.map((site) => (
        <RansomwareCard key={site.key} site={site} />
      ))}
    </div>
  );
}
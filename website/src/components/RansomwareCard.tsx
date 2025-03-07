'use client';

import React from 'react';
import { RansomwareSite } from '../lib/ransomware';
import { useLanguage } from '../contexts/LanguageContext';

interface RansomwareCardProps {
  site: RansomwareSite;
}

export default function RansomwareCard({ site }: RansomwareCardProps) {
  const { name, data, latestTarget } = site;
  const { t } = useLanguage();
  
  // Calculate time since update if available
  const getTimeSinceUpdate = () => {
    if (!data.last_updated) return t('unknown');
    
    const updateTime = new Date(data.last_updated);
    const now = new Date();
    const diffMs = now.getTime() - updateTime.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    
    if (diffHours < 1) {
      const diffMinutes = Math.floor(diffMs / (1000 * 60));
      return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
      return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else {
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    }
  };
  
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden transition-transform transform hover:scale-105 hover:shadow-xl">
      <div className="p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-2">{name}</h2>
          <span className="px-3 py-1 text-sm rounded-full bg-ransomware-600 text-white font-medium">
            {data.total_count} {t('entities')}
          </span>
        </div>
        
        <div className="mt-4 space-y-3">
          <div>
            <div className="text-sm text-gray-500 dark:text-gray-400">{t('latest_target')}</div>
            {latestTarget ? (
              <div className="font-mono text-lg font-semibold text-ransomware-700 dark:text-ransomware-300">
                {latestTarget.domain}
              </div>
            ) : (
              <div className="font-mono text-lg text-gray-400 dark:text-gray-500">{t('no_targets')}</div>
            )}
          </div>
          
          <div className="flex justify-between items-center border-t border-gray-200 dark:border-gray-700 pt-3 mt-3">
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {t('status')}: {latestTarget?.status || t('unknown')}
            </div>
            <div className="text-xs text-gray-400 dark:text-gray-500">
              {t('updated')}: {getTimeSinceUpdate()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
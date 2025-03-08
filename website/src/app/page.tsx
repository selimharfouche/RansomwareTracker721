// src/app/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { RansomwareSite, fetchRansomwareSites } from '../lib/ransomware';
import RansomwareGrid from '../components/RansomwareGrid';
import { useLanguage } from '../contexts/LanguageContext';
import NavBar from '../components/NavBar';
import DirectThemeController from '../components/DirectThemeController';

export default function Home() {
  const [sites, setSites] = useState<RansomwareSite[]>([]);
  const [loading, setLoading] = useState(true);
  const { t } = useLanguage();
  
  // Fetch ransomware data
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const data = await fetchRansomwareSites();
      setSites(data);
      setLoading(false);
    }
    
    loadData();
  }, []);
  
  return (
    <main className="min-h-screen theme-transition">
      <DirectThemeController />
      <NavBar />
      <div className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-extrabold text-primary sm:text-5xl sm:tracking-tight theme-transition">
              <span className="text-ransomware">{t('ransomware_tracker')}</span>
            </h1>
            <p className="mt-3 max-w-2xl mx-auto text-xl text-secondary sm:mt-4 theme-transition">
              {t('monitor_latest')}
            </p>
          </div>
          
          <div className="mt-10">
            {loading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-pulse-slow text-ransomware text-xl theme-transition">
                  {t('loading')}
                </div>
              </div>
            ) : (
              <RansomwareGrid sites={sites} />
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
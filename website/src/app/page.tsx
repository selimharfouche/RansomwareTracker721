'use client';

import { useEffect, useState } from 'react';
import { RansomwareSite, fetchRansomwareSites } from '../lib/ransomware';
import RansomwareGrid from '../components/RansomwareGrid';
import { useLanguage } from '../contexts/LanguageContext';
import NavBar from '../components/NavBar';

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
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <NavBar />
      <div className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-extrabold text-gray-900 dark:text-white sm:text-5xl sm:tracking-tight">
              <span className="text-ransomware-600 dark:text-ransomware-400">{t('ransomware_tracker')}</span>
            </h1>
            <p className="mt-3 max-w-2xl mx-auto text-xl text-gray-500 dark:text-gray-300 sm:mt-4">
              {t('monitor_latest')}
            </p>
          </div>
          
          <div className="mt-10">
            {loading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-pulse-slow text-ransomware-500 dark:text-ransomware-400 text-xl">
                  Loading data...
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
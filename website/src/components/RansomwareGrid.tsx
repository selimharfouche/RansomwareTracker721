import React from 'react';
import RansomwareCard from './RansomwareCard';
import { RansomwareSite } from '../lib/ransomware';

interface RansomwareGridProps {
  sites: RansomwareSite[];
}

export default function RansomwareGrid({ sites }: RansomwareGridProps) {
  if (!sites || sites.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-100 dark:bg-gray-900 rounded-xl">
        <div className="text-center">
          <h3 className="text-xl font-medium text-gray-700 dark:text-gray-300">No data available</h3>
          <p className="mt-2 text-gray-500 dark:text-gray-400">
            No ransomware data has been found. Make sure the data directory exists and has JSON files.
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
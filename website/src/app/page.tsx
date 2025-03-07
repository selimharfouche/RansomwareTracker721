import { getAllRansomwareSites } from '../lib/ransomware';
import RansomwareGrid from '../components/RansomwareGrid';

export const dynamic = "force-dynamic"; // This ensures the page is not statically generated

export default function Home() {
  // Get all ransomware sites data
  const sites = getAllRansomwareSites();
  
  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-extrabold text-gray-900 dark:text-white sm:text-5xl sm:tracking-tight">
            <span className="text-ransomware-600 dark:text-ransomware-400">Ransomware</span> Tracker
          </h1>
          <p className="mt-3 max-w-2xl mx-auto text-xl text-gray-500 dark:text-gray-300 sm:mt-4">
            Monitor the latest targets from various ransomware groups
          </p>
        </div>
        
        <div className="mt-10">
          <RansomwareGrid sites={sites} />
        </div>
      </div>
    </main>
  );
}
import { useEffect, useState } from 'react';
import { OwnerMapping } from './components/OwnerMapping';

interface ApiStatus {
  name: string;
  version: string;
  status: string;
}

type TabType = 'dashboard' | 'owners';

function App() {
  const [apiStatus, setApiStatus] = useState<ApiStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('owners');

  useEffect(() => {
    fetch('http://localhost:8000/')
      .then((res) => res.json())
      .then((data) => setApiStatus(data))
      .catch(() => setError('Could not connect to API'));
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-800/50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-white">
                Fantasy League History Tracker
              </h1>
              <p className="text-slate-400 text-sm">
                Unified stats from Yahoo Fantasy and Sleeper
              </p>
            </div>
            {apiStatus ? (
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                <span className="text-slate-400 text-sm">API Connected</span>
              </div>
            ) : error ? (
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 bg-red-400 rounded-full"></span>
                <span className="text-red-400 text-sm">{error}</span>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></span>
                <span className="text-slate-400 text-sm">Connecting...</span>
              </div>
            )}
          </div>

          {/* Navigation */}
          <nav className="mt-4 flex gap-1">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-4 py-2 rounded-t-lg text-sm font-medium transition-colors ${
                activeTab === 'dashboard'
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab('owners')}
              className={`px-4 py-2 rounded-t-lg text-sm font-medium transition-colors ${
                activeTab === 'owners'
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              Owner Mapping
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto">
        {activeTab === 'dashboard' && (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-white mb-4">Dashboard</h2>
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <p className="text-slate-400">
                Welcome to the Fantasy League History Tracker. Use the Owner
                Mapping tab to link your Yahoo and Sleeper accounts.
              </p>
              {apiStatus && (
                <div className="mt-4 text-sm text-slate-500">
                  <p>API Version: {apiStatus.version}</p>
                  <p>Status: {apiStatus.status}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'owners' && <OwnerMapping />}
      </main>
    </div>
  );
}

export default App;

/**
 * Dashboard Page
 *
 * Main landing page showing:
 * - League overview stats
 * - API connection status
 * - Quick links to other sections
 * - Import functionality
 */

import { useEffect, useState } from 'react';

interface ApiStatus {
  name: string;
  version: string;
  status: string;
}

interface DashboardProps {
  apiStatus: ApiStatus | null;
  leagueName: string;
}

export function Dashboard({ apiStatus, leagueName }: DashboardProps) {
  const [stats, setStats] = useState<{
    totalOwners: number;
    totalSeasons: number;
    totalTrades: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Import modal state
  const [showImportModal, setShowImportModal] = useState(false);
  const [leagueId, setLeagueId] = useState('');
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<{success: boolean; message: string} | null>(null);

  const loadStats = async () => {
    try {
      const [ownersRes, seasonsRes, tradesRes] = await Promise.all([
        fetch('http://localhost:8000/api/history/owners').then(r => r.ok ? r.json() : []),
        fetch('http://localhost:8000/api/history/seasons').then(r => r.ok ? r.json() : []),
        fetch('http://localhost:8000/api/trades/stats').then(r => r.ok ? r.json() : { total_trades: 0 }),
      ]);
      setStats({
        totalOwners: Array.isArray(ownersRes) ? ownersRes.length : 0,
        totalSeasons: Array.isArray(seasonsRes) ? seasonsRes.length : 0,
        totalTrades: tradesRes.total_trades ?? 0,
      });
    } catch {
      // Stats not available, that's ok
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  const handleImport = async () => {
    if (!leagueId.trim()) return;
    
    setImporting(true);
    setImportResult(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/sleeper/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ league_id: leagueId.trim() }),
      });
      
      if (response.ok) {
        const data = await response.json();
        setImportResult({
          success: true,
          message: `Imported "${data.league_name}" (${data.season_year}): ${data.teams_imported} teams, ${data.matchups_imported} matchups, ${data.trades_imported} trades`
        });
        // Refresh stats
        loadStats();
      } else {
        const error = await response.json();
        setImportResult({
          success: false,
          message: error.detail || 'Failed to import league'
        });
      }
    } catch (err) {
      setImportResult({
        success: false,
        message: 'Network error - is the backend running?'
      });
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Welcome to {leagueName}</h2>
        <p className="text-slate-400 dark:text-slate-400">
          Your unified fantasy football history from Yahoo Fantasy and Sleeper
        </p>
      </div>

      {/* Quick Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-slate-800 dark:bg-slate-800 rounded-lg p-6 border border-slate-700 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-blue-600/20 flex items-center justify-center">
              <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <div>
              <p className="text-slate-400 text-sm">Owners</p>
              <p className="text-2xl font-bold text-white">
                {loading ? '...' : stats?.totalOwners ?? 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-slate-800 dark:bg-slate-800 rounded-lg p-6 border border-slate-700 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-green-600/20 flex items-center justify-center">
              <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <p className="text-slate-400 text-sm">Seasons</p>
              <p className="text-2xl font-bold text-white">
                {loading ? '...' : stats?.totalSeasons ?? 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-slate-800 dark:bg-slate-800 rounded-lg p-6 border border-slate-700 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-purple-600/20 flex items-center justify-center">
              <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
            </div>
            <div>
              <p className="text-slate-400 text-sm">Trades</p>
              <p className="text-2xl font-bold text-white">
                {loading ? '...' : stats?.totalTrades ?? 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-slate-800 dark:bg-slate-800 rounded-lg p-6 border border-slate-700 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-yellow-600/20 flex items-center justify-center">
              <svg className="w-6 h-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="text-slate-400 text-sm">API Status</p>
              <p className="text-lg font-semibold text-white flex items-center gap-2">
                {apiStatus ? (
                  <>
                    <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                    Connected
                  </>
                ) : (
                  <>
                    <span className="w-2 h-2 bg-red-400 rounded-full"></span>
                    Disconnected
                  </>
                )}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Import Section */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 mb-8">
        <h3 className="text-xl font-bold text-white mb-4">Import League</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Sleeper Import */}
          <div 
            onClick={() => setShowImportModal(true)}
            className="p-6 bg-slate-700/50 rounded-lg border-2 border-dashed border-slate-600 hover:border-blue-500 cursor-pointer transition-colors"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-blue-600/20 flex items-center justify-center">
                <span className="text-2xl">🌙</span>
              </div>
              <div>
                <div className="text-white font-semibold">Import from Sleeper</div>
                <p className="text-slate-400 text-sm">Enter your Sleeper league ID</p>
              </div>
            </div>
          </div>
          
          {/* Yahoo Import - Coming Soon */}
          <div className="p-6 bg-slate-700/30 rounded-lg border-2 border-dashed border-slate-700 opacity-60">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-purple-600/20 flex items-center justify-center">
                <span className="text-2xl">🏈</span>
              </div>
              <div>
                <div className="text-white font-semibold">Import from Yahoo</div>
                <p className="text-slate-400 text-sm">Coming soon - requires OAuth setup</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Getting Started Section */}
      <div className="bg-slate-800 dark:bg-slate-800 rounded-lg p-6 border border-slate-700 dark:border-slate-700 mb-8">
        <h3 className="text-xl font-bold text-white mb-4">Getting Started</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-slate-700/50 rounded-lg">
            <div className="text-blue-400 font-semibold mb-2">1. Import Leagues</div>
            <p className="text-slate-400 text-sm">
              Connect your Sleeper and Yahoo Fantasy leagues to import historical data.
            </p>
          </div>
          <div className="p-4 bg-slate-700/50 rounded-lg">
            <div className="text-blue-400 font-semibold mb-2">2. Map Owners</div>
            <p className="text-slate-400 text-sm">
              Link the same person across platforms to combine their stats.
            </p>
          </div>
          <div className="p-4 bg-slate-700/50 rounded-lg">
            <div className="text-blue-400 font-semibold mb-2">3. Explore History</div>
            <p className="text-slate-400 text-sm">
              View head-to-head records, trade analytics, and league records.
            </p>
          </div>
        </div>
      </div>

      {/* API Info */}
      {apiStatus && (
        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
          <div className="flex items-center gap-4 text-sm text-slate-400">
            <span>API: {apiStatus.name}</span>
            <span>Version: {apiStatus.version}</span>
            <span>Status: {apiStatus.status}</span>
          </div>
        </div>
      )}

      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-lg p-6 w-full max-w-md mx-4 border border-slate-700">
            <h3 className="text-xl font-bold text-white mb-4">Import Sleeper League</h3>
            
            <div className="mb-4">
              <label className="block text-slate-400 text-sm mb-2">
                Sleeper League ID
              </label>
              <input
                type="text"
                value={leagueId}
                onChange={(e) => setLeagueId(e.target.value)}
                placeholder="e.g. 123456789012345678"
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
              />
              <p className="text-slate-500 text-xs mt-2">
                Find this in your Sleeper app URL: sleeper.app/leagues/[LEAGUE_ID]
              </p>
            </div>

            {importResult && (
              <div className={`p-3 rounded-lg mb-4 ${importResult.success ? 'bg-green-600/20 text-green-400' : 'bg-red-600/20 text-red-400'}`}>
                {importResult.message}
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowImportModal(false);
                  setLeagueId('');
                  setImportResult(null);
                }}
                className="flex-1 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleImport}
                disabled={importing || !leagueId.trim()}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {importing ? 'Importing...' : 'Import'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;

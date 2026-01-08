/**
 * Dashboard Page
 *
 * Main landing page showing:
 * - League overview stats
 * - API connection status
 * - Quick links to other sections
 * - Import functionality
 */

import { useEffect, useState, useCallback } from 'react';
import { ImportModal } from '../components/ImportModal';
import { ImportedLeagues } from '../components/ImportedLeagues';
import { YahooAuthModal } from '../components/YahooAuthModal';
import { YahooImportModal } from '../components/YahooImportModal';

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
  const [importLeagueId, setImportLeagueId] = useState('');
  const [leagueRefreshTrigger, setLeagueRefreshTrigger] = useState(0);

  // Yahoo auth/import state
  const [showYahooAuthModal, setShowYahooAuthModal] = useState(false);
  const [showYahooImportModal, setShowYahooImportModal] = useState(false);
  const [yahooAuthStatus, setYahooAuthStatus] = useState<'unknown' | 'authenticated' | 'unauthenticated'>('unknown');
  const [yahooImportLeagueKey, setYahooImportLeagueKey] = useState('');

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

  // Check Yahoo authentication status
  const checkYahooAuth = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/yahoo/auth/status');
      if (response.ok) {
        const data = await response.json();
        setYahooAuthStatus(data.authenticated ? 'authenticated' : 'unauthenticated');
      } else {
        setYahooAuthStatus('unauthenticated');
      }
    } catch {
      setYahooAuthStatus('unauthenticated');
    }
  }, []);

  useEffect(() => {
    loadStats();
    checkYahooAuth();
  }, [checkYahooAuth]);

  const handleReimport = (leagueId: string, platform: string) => {
    if (platform === 'sleeper') {
      setImportLeagueId(leagueId);
      setShowImportModal(true);
    } else if (platform === 'yahoo') {
      // For Yahoo, check auth status first
      if (yahooAuthStatus === 'authenticated') {
        setYahooImportLeagueKey(leagueId);
        setShowYahooImportModal(true);
      } else {
        // Need to authenticate first
        setYahooImportLeagueKey(leagueId);
        setShowYahooAuthModal(true);
      }
    }
  };

  const handleImportSuccess = () => {
    loadStats();
    setLeagueRefreshTrigger((prev) => prev + 1);
    setImportLeagueId('');
  };

  const handleDeleteLeague = () => {
    loadStats();
    setLeagueRefreshTrigger((prev) => prev + 1);
  };

  const handleCloseModal = () => {
    setShowImportModal(false);
    setImportLeagueId('');
  };

  // Yahoo auth/import handlers
  const handleYahooClick = () => {
    if (yahooAuthStatus === 'authenticated') {
      setShowYahooImportModal(true);
    } else {
      setShowYahooAuthModal(true);
    }
  };

  const handleYahooAuthSuccess = () => {
    setYahooAuthStatus('authenticated');
    setShowYahooAuthModal(false);
    // Open import modal after successful auth
    setShowYahooImportModal(true);
  };

  const handleYahooAuthClose = () => {
    setShowYahooAuthModal(false);
    setYahooImportLeagueKey('');
  };

  const handleYahooImportSuccess = () => {
    loadStats();
    setLeagueRefreshTrigger((prev) => prev + 1);
  };

  const handleYahooImportClose = () => {
    setShowYahooImportModal(false);
    setYahooImportLeagueKey('');
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
          
          {/* Yahoo Import */}
          <div
            onClick={handleYahooClick}
            className="p-6 bg-slate-700/50 rounded-lg border-2 border-dashed border-slate-600 hover:border-purple-500 cursor-pointer transition-colors"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-purple-600/20 flex items-center justify-center">
                <span className="text-2xl">🏈</span>
              </div>
              <div>
                <div className="text-white font-semibold flex items-center gap-2">
                  Import from Yahoo
                  {yahooAuthStatus === 'authenticated' && (
                    <span className="text-xs bg-green-600/20 text-green-400 px-2 py-0.5 rounded">
                      Connected
                    </span>
                  )}
                </div>
                <p className="text-slate-400 text-sm">
                  {yahooAuthStatus === 'authenticated'
                    ? 'Click to import a Yahoo Fantasy league'
                    : 'Login to Yahoo to import your leagues'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Imported Leagues Section */}
      <div className="mb-8">
        <ImportedLeagues
          onReimport={handleReimport}
          onDelete={handleDeleteLeague}
          refreshTrigger={leagueRefreshTrigger}
        />
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
      <ImportModal
        isOpen={showImportModal}
        onClose={handleCloseModal}
        onSuccess={handleImportSuccess}
        initialLeagueId={importLeagueId}
      />

      {/* Yahoo Auth Modal */}
      <YahooAuthModal
        isOpen={showYahooAuthModal}
        onClose={handleYahooAuthClose}
        onSuccess={handleYahooAuthSuccess}
      />

      {/* Yahoo Import Modal */}
      <YahooImportModal
        isOpen={showYahooImportModal}
        onClose={handleYahooImportClose}
        onSuccess={handleYahooImportSuccess}
        initialLeagueKey={yahooImportLeagueKey}
      />
    </div>
  );
}

export default Dashboard;

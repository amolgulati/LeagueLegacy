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
        <h2 className="text-3xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>Welcome to {leagueName}</h2>
        <p style={{ color: 'var(--text-secondary)' }}>
          Your unified fantasy football history from Yahoo Fantasy and Sleeper
        </p>
      </div>

      {/* Quick Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="rounded-lg p-6" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-primary)' }}>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'rgba(59, 130, 246, 0.2)' }}>
              <svg className="w-6 h-6" style={{ color: 'var(--chart-1)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <div>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Owners</p>
              <p className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
                {loading ? '...' : stats?.totalOwners ?? 0}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-lg p-6" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-primary)' }}>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'var(--success-muted)' }}>
              <svg className="w-6 h-6" style={{ color: 'var(--success)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Seasons</p>
              <p className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
                {loading ? '...' : stats?.totalSeasons ?? 0}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-lg p-6" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-primary)' }}>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'rgba(139, 92, 246, 0.2)' }}>
              <svg className="w-6 h-6" style={{ color: 'var(--accent-secondary)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
            </div>
            <div>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Trades</p>
              <p className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
                {loading ? '...' : stats?.totalTrades ?? 0}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-lg p-6" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-primary)' }}>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'var(--warning-muted)' }}>
              <svg className="w-6 h-6" style={{ color: 'var(--warning)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>API Status</p>
              <p className="text-lg font-semibold flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                {apiStatus ? (
                  <>
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--success)' }}></span>
                    Connected
                  </>
                ) : (
                  <>
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--error)' }}></span>
                    Disconnected
                  </>
                )}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Import Section */}
      <div className="rounded-lg p-6 mb-8" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-primary)' }}>
        <h3 className="text-xl font-bold mb-4" style={{ color: 'var(--text-primary)' }}>Import League</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Sleeper Import */}
          <div
            onClick={() => setShowImportModal(true)}
            className="p-6 rounded-lg border-2 border-dashed cursor-pointer transition-colors hover:border-blue-500"
            style={{ backgroundColor: 'var(--bg-tertiary)', borderColor: 'var(--border-secondary)' }}
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'rgba(59, 130, 246, 0.2)' }}>
                <span className="text-2xl">🌙</span>
              </div>
              <div>
                <div className="font-semibold" style={{ color: 'var(--text-primary)' }}>Import from Sleeper</div>
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Enter your Sleeper league ID</p>
              </div>
            </div>
          </div>

          {/* Yahoo Import */}
          <div
            onClick={handleYahooClick}
            className="p-6 rounded-lg border-2 border-dashed cursor-pointer transition-colors hover:border-purple-500"
            style={{ backgroundColor: 'var(--bg-tertiary)', borderColor: 'var(--border-secondary)' }}
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'rgba(139, 92, 246, 0.2)' }}>
                <span className="text-2xl">🏈</span>
              </div>
              <div>
                <div className="font-semibold flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                  Import from Yahoo
                  {yahooAuthStatus === 'authenticated' && (
                    <span className="text-xs px-2 py-0.5 rounded" style={{ backgroundColor: 'var(--success-muted)', color: 'var(--success)' }}>
                      Connected
                    </span>
                  )}
                </div>
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
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
      <div className="rounded-lg p-6 mb-8" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-primary)' }}>
        <h3 className="text-xl font-bold mb-4" style={{ color: 'var(--text-primary)' }}>Getting Started</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
            <div className="font-semibold mb-2" style={{ color: 'var(--accent-primary)' }}>1. Import Leagues</div>
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              Connect your Sleeper and Yahoo Fantasy leagues to import historical data.
            </p>
          </div>
          <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
            <div className="font-semibold mb-2" style={{ color: 'var(--accent-primary)' }}>2. Map Owners</div>
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              Link the same person across platforms to combine their stats.
            </p>
          </div>
          <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
            <div className="font-semibold mb-2" style={{ color: 'var(--accent-primary)' }}>3. Explore History</div>
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              View head-to-head records, trade analytics, and league records.
            </p>
          </div>
        </div>
      </div>

      {/* API Info */}
      {apiStatus && (
        <div className="rounded-lg p-4" style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-primary)' }}>
          <div className="flex items-center gap-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
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

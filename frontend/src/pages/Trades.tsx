/**
 * Trades Page
 *
 * Displays trade history visualization with:
 * - Timeline view of all trades
 * - Filter by owner or season
 * - Trade partners network graph
 * - Trade frequency stats
 */

import { useState, useEffect, useCallback } from 'react';
import { TradeTimeline } from '../components/TradeTimeline';
import { TradeFilters } from '../components/TradeFilters';
import { TradeNetwork } from '../components/TradeNetwork';

interface Team {
  id: number;
  name: string;
  owner: {
    id: number;
    name: string;
    display_name: string | null;
    avatar_url: string | null;
  };
}

interface TeamTradeDetails {
  team_id: number;
  owner_name: string;
  received: string[];
  sent: string[];
}

interface Trade {
  id: number;
  week: number | null;
  trade_date: string;
  season_id: number;
  season_year: number;
  league_id: number;
  league_name: string;
  assets_exchanged: string | null;
  trade_details: TeamTradeDetails[] | null;
  trade_summary: string | null;
  status: string;
  teams: Team[];
}

interface TraderStats {
  owner: {
    id: number;
    name: string;
    display_name: string | null;
    avatar_url: string | null;
  };
  trade_count: number;
}

interface SeasonTradeStats {
  season_id: number;
  year: number;
  league_name: string;
  trade_count: number;
}

interface TradeStats {
  total_trades: number;
  most_active_traders: TraderStats[];
  trades_by_season: SeasonTradeStats[];
  avg_trades_per_season: number;
}

interface Owner {
  id: number;
  name: string;
  display_name: string | null;
}

interface Season {
  id: number;
  year: number;
  league_name: string;
}

type ViewMode = 'timeline' | 'network';

export function Trades() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [allTrades, setAllTrades] = useState<Trade[]>([]);
  const [stats, setStats] = useState<TradeStats | null>(null);
  const [owners, setOwners] = useState<Owner[]>([]);
  const [seasons, setSeasons] = useState<Season[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('timeline');

  // Filter states
  const [selectedOwnerId, setSelectedOwnerId] = useState<number | null>(null);
  const [selectedSeasonId, setSelectedSeasonId] = useState<number | null>(null);

  // Load initial data
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Load all data in parallel
        const [tradesRes, statsRes, ownersRes, seasonsRes] = await Promise.all([
          fetch('http://localhost:8000/api/trades?limit=100').then((r) =>
            r.ok ? r.json() : { trades: [], total: 0 }
          ),
          fetch('http://localhost:8000/api/trades/stats').then((r) => (r.ok ? r.json() : null)),
          fetch('http://localhost:8000/api/history/owners').then((r) => (r.ok ? r.json() : [])),
          fetch('http://localhost:8000/api/history/seasons').then((r) => (r.ok ? r.json() : [])),
        ]);

        const tradesList = tradesRes.trades || [];
        setAllTrades(tradesList);
        setTrades(tradesList);
        setStats(statsRes);

        // Extract unique owners from trades or use history endpoint
        if (Array.isArray(ownersRes)) {
          setOwners(
            ownersRes.map((o: { id: number; name: string; display_name: string | null }) => ({
              id: o.id,
              name: o.name,
              display_name: o.display_name,
            }))
          );
        }

        // Extract unique seasons
        if (Array.isArray(seasonsRes)) {
          setSeasons(
            seasonsRes.map((s: { id: number; year: number; league: { name: string } }) => ({
              id: s.id,
              year: s.year,
              league_name: s.league?.name || 'Unknown League',
            }))
          );
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load trades');
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  // Filter trades when filters change
  const filterTrades = useCallback(() => {
    let filtered = [...allTrades];

    if (selectedOwnerId !== null) {
      filtered = filtered.filter((trade) =>
        trade.teams.some((team) => team.owner.id === selectedOwnerId)
      );
    }

    if (selectedSeasonId !== null) {
      filtered = filtered.filter((trade) => trade.season_id === selectedSeasonId);
    }

    setTrades(filtered);
  }, [allTrades, selectedOwnerId, selectedSeasonId]);

  useEffect(() => {
    filterTrades();
  }, [filterTrades]);

  const handleOwnerChange = (ownerId: number | null) => {
    setSelectedOwnerId(ownerId);
  };

  const handleSeasonChange = (seasonId: number | null) => {
    setSelectedSeasonId(seasonId);
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-white">Trade History</h2>
          <p className="text-slate-400">Trade visualization and analytics</p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-white">Trade History</h2>
          <p className="text-slate-400">Trade visualization and analytics</p>
        </div>
        <div className="bg-red-900/30 border border-red-600 rounded-lg p-4">
          <p className="text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Trade History</h2>
          <p className="text-slate-400">Trade visualization and analytics across all leagues</p>
        </div>

        {/* View Mode Toggle */}
        <div className="flex bg-slate-800 rounded-lg p-1 border border-slate-700">
          <button
            onClick={() => setViewMode('timeline')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'timeline'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
            }`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Timeline
          </button>
          <button
            onClick={() => setViewMode('network')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'network'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
            }`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            Network
          </button>
        </div>
      </div>

      {/* Filters */}
      <TradeFilters
        owners={owners}
        seasons={seasons}
        selectedOwnerId={selectedOwnerId}
        selectedSeasonId={selectedSeasonId}
        onOwnerChange={handleOwnerChange}
        onSeasonChange={handleSeasonChange}
        loading={loading}
      />

      {/* No Data State */}
      {allTrades.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-slate-700 flex items-center justify-center">
            <svg className="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">No Trades Found</h3>
          <p className="text-slate-400 max-w-md mx-auto">
            Import league data from Sleeper or Yahoo Fantasy to see trade history and analytics here.
          </p>
        </div>
      ) : (
        <>
          {/* View Content */}
          {viewMode === 'timeline' ? (
            <TradeTimeline
              trades={trades}
              tradesBySeasonData={stats?.trades_by_season || []}
              loading={loading}
            />
          ) : (
            <TradeNetwork
              trades={trades}
              mostActiveTraders={stats?.most_active_traders || []}
              avgTradesPerSeason={stats?.avg_trades_per_season || 0}
              loading={loading}
            />
          )}

          {/* Results Count */}
          {(selectedOwnerId !== null || selectedSeasonId !== null) && (
            <div className="text-center py-4">
              <p className="text-slate-400 text-sm">
                Showing {trades.length} of {allTrades.length} trades
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default Trades;

/**
 * Trades Page
 *
 * Displays trade history and analytics.
 */

import { useState, useEffect } from 'react';

interface Trade {
  id: number;
  season_id: number;
  week: number;
  transaction_id: string | null;
  executed_at: string | null;
  teams: Array<{
    id: number;
    name: string;
    owner_id: number;
    owner_name: string;
  }>;
}

interface TradeStats {
  total_trades: number;
  most_active_traders: Array<{
    owner_id: number;
    owner_name: string;
    trade_count: number;
  }>;
  trades_by_season: Array<{
    season_id: number;
    year: number;
    league_name: string;
    trade_count: number;
  }>;
}

export function Trades() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [stats, setStats] = useState<TradeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [tradesRes, statsRes] = await Promise.all([
          fetch(`http://localhost:8000/api/trades?page=${page}&page_size=${pageSize}`).then(r => r.ok ? r.json() : { trades: [], total_count: 0 }),
          fetch('http://localhost:8000/api/trades/stats').then(r => r.ok ? r.json() : null),
        ]);
        setTrades(tradesRes.trades || []);
        setTotalCount(tradesRes.total_count || 0);
        setStats(statsRes);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load trades');
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [page]);

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white">Trades</h2>
        <p className="text-slate-400">Trade history and analytics across all leagues</p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <p className="text-slate-400 text-sm">Total Trades</p>
            <p className="text-2xl font-bold text-white">{stats.total_trades}</p>
          </div>

          {stats.most_active_traders.slice(0, 3).map((trader, index) => (
            <div key={trader.owner_id} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <p className="text-slate-400 text-sm flex items-center gap-1">
                {index === 0 ? (
                  <>
                    <svg className="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M5 2a2 2 0 00-2 2v1a2 2 0 002 2h1v1H5a3 3 0 00-3 3v6a3 3 0 003 3h10a3 3 0 003-3v-6a3 3 0 00-3-3h-1V7h1a2 2 0 002-2V4a2 2 0 00-2-2H5z" clipRule="evenodd" />
                    </svg>
                    Trade King
                  </>
                ) : (
                  `#${index + 1} Trader`
                )}
              </p>
              <p className="text-lg font-bold text-white truncate">{trader.owner_name}</p>
              <p className="text-sm text-slate-400">{trader.trade_count} trades</p>
            </div>
          ))}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
        </div>
      ) : error ? (
        <div className="bg-red-900/30 border border-red-600 rounded-lg p-4">
          <p className="text-red-400">{error}</p>
        </div>
      ) : trades.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-700 flex items-center justify-center">
            <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">No Trades Found</h3>
          <p className="text-slate-400 max-w-md mx-auto">
            Import league data from Sleeper or Yahoo Fantasy to see trades here.
          </p>
        </div>
      ) : (
        <>
          <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-700 bg-slate-800">
                    <th className="text-left py-3 px-4 text-slate-400 font-medium text-sm">Week</th>
                    <th className="text-left py-3 px-4 text-slate-400 font-medium text-sm">Teams Involved</th>
                    <th className="text-left py-3 px-4 text-slate-400 font-medium text-sm hidden sm:table-cell">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.map(trade => (
                    <tr
                      key={trade.id}
                      className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors"
                    >
                      <td className="py-4 px-4">
                        <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-purple-600/20 text-purple-400 text-sm font-bold">
                          {trade.week}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex flex-wrap items-center gap-2">
                          {trade.teams.map((team, index) => (
                            <span key={team.id}>
                              <span className="text-white font-medium">{team.owner_name}</span>
                              {index < trade.teams.length - 1 && (
                                <svg className="w-4 h-4 text-slate-500 inline mx-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                                </svg>
                              )}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="py-4 px-4 text-slate-400 hidden sm:table-cell">
                        {trade.executed_at
                          ? new Date(trade.executed_at).toLocaleDateString()
                          : '-'
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-slate-400 text-sm">
                Page {page} of {totalPages} ({totalCount} total trades)
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed rounded text-white text-sm"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed rounded text-white text-sm"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default Trades;

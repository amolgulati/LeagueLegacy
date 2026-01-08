/**
 * TradeTimeline Component
 *
 * Displays trades in a vertical timeline view with filtering options.
 * Shows trade details, participants, and date in an engaging visual format.
 */

import { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

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

interface SeasonTradeStats {
  season_id: number;
  year: number;
  league_name: string;
  trade_count: number;
}

interface TradeTimelineProps {
  trades: Trade[];
  tradesBySeasonData: SeasonTradeStats[];
  loading?: boolean;
}

// Color palette for the chart bars
const COLORS = ['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#6366f1'];

export function TradeTimeline({ trades, tradesBySeasonData, loading }: TradeTimelineProps) {
  // Group trades by season year for the timeline
  const groupedTrades = useMemo(() => {
    const groups: { [key: string]: Trade[] } = {};
    trades.forEach((trade) => {
      const key = `${trade.season_year}`;
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(trade);
    });

    // Sort trades within each group by week (newest first)
    Object.keys(groups).forEach((key) => {
      groups[key].sort((a, b) => (b.week || 0) - (a.week || 0));
    });

    return groups;
  }, [trades]);

  // Sort years for display (newest first)
  const sortedYears = useMemo(() => {
    return Object.keys(groupedTrades).sort((a, b) => parseInt(b) - parseInt(a));
  }, [groupedTrades]);

  // Prepare chart data for trades by season
  const chartData = useMemo(() => {
    return tradesBySeasonData
      .sort((a, b) => a.year - b.year)
      .map((s) => ({
        year: s.year,
        trades: s.trade_count,
        league: s.league_name,
      }));
  }, [tradesBySeasonData]);

  const getOwnerDisplayName = (team: Team) => {
    return team.owner.display_name || team.owner.name;
  };

  const formatTradeDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
      </div>
    );
  }

  if (trades.length === 0) {
    return (
      <div className="text-center py-12 text-slate-400">
        <svg className="w-16 h-16 mx-auto mb-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
        </svg>
        <p className="text-lg font-medium">No trades found</p>
        <p className="text-sm">Try adjusting your filters</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Trades by Season Chart */}
      {chartData.length > 0 && (
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Trades by Season
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <XAxis
                  dataKey="year"
                  tick={{ fill: '#94a3b8', fontSize: 12 }}
                  axisLine={{ stroke: '#475569' }}
                  tickLine={{ stroke: '#475569' }}
                />
                <YAxis
                  tick={{ fill: '#94a3b8', fontSize: 12 }}
                  axisLine={{ stroke: '#475569' }}
                  tickLine={{ stroke: '#475569' }}
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px',
                    color: '#f8fafc'
                  }}
                  formatter={(value) => [`${value} trades`, 'Count']}
                  labelFormatter={(label) => `Season ${label}`}
                />
                <Bar dataKey="trades" radius={[4, 4, 0, 0]}>
                  {chartData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Timeline View */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
          <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Trade Timeline
        </h3>

        <div className="relative">
          {/* Vertical Timeline Line */}
          <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gradient-to-b from-purple-500 via-blue-500 to-cyan-500"></div>

          {sortedYears.map((year) => (
            <div key={year} className="mb-8 last:mb-0">
              {/* Year Header */}
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center text-white font-bold text-sm z-10 shadow-lg">
                  {year.slice(-2)}
                </div>
                <div>
                  <h4 className="text-xl font-bold text-white">{year} Season</h4>
                  <p className="text-slate-400 text-sm">
                    {groupedTrades[year].length} trade{groupedTrades[year].length !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>

              {/* Trades for this year */}
              <div className="ml-6 pl-10 border-l border-slate-700 space-y-4">
                {groupedTrades[year].map((trade) => (
                  <div
                    key={trade.id}
                    className="bg-slate-700/50 rounded-lg p-4 hover:bg-slate-700 transition-colors relative"
                  >
                    {/* Timeline dot */}
                    <div className="absolute -left-[2.875rem] top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-blue-400 border-2 border-slate-800"></div>

                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      {/* Trade Participants */}
                      <div className="flex items-center gap-2 flex-wrap">
                        {trade.teams.map((team, idx) => (
                          <span key={team.id} className="flex items-center gap-1">
                            <span className="px-3 py-1 rounded-full bg-slate-600/50 text-white font-medium text-sm">
                              {getOwnerDisplayName(team)}
                            </span>
                            {idx < trade.teams.length - 1 && (
                              <svg className="w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                              </svg>
                            )}
                          </span>
                        ))}
                      </div>

                      {/* Trade Metadata */}
                      <div className="flex items-center gap-3 text-sm">
                        {trade.week && (
                          <span className="px-2 py-1 rounded bg-purple-600/30 text-purple-300 font-medium">
                            Week {trade.week}
                          </span>
                        )}
                        <span className="text-slate-400">
                          {formatTradeDate(trade.trade_date)}
                        </span>
                      </div>
                    </div>

                    {/* Trade Details - Player Names */}
                    {trade.trade_details && trade.trade_details.length > 0 ? (
                      <div className="mt-3 space-y-2">
                        {trade.trade_details.map((detail) => (
                          <div key={detail.team_id} className="text-sm">
                            <span className="text-slate-300 font-medium">{detail.owner_name}</span>
                            {detail.received.length > 0 && (
                              <span className="text-slate-400">
                                {' '}receives{' '}
                                <span className="text-green-400">
                                  {detail.received.join(', ')}
                                </span>
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : trade.trade_summary ? (
                      <p className="text-slate-400 text-sm mt-2">
                        {trade.trade_summary}
                      </p>
                    ) : null}

                    {/* League Name */}
                    <p className="text-slate-500 text-xs mt-2">
                      {trade.league_name}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default TradeTimeline;

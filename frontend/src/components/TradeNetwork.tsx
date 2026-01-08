/**
 * TradeNetwork Component
 *
 * Displays a network graph visualization of trade relationships between owners.
 * Shows who trades with whom and how frequently.
 */

import { useMemo, useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { useTheme } from '../hooks/useTheme';

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

interface Trade {
  id: number;
  week: number | null;
  trade_date: string;
  season_id: number;
  season_year: number;
  league_id: number;
  league_name: string;
  assets_exchanged: string | null;
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

interface TradeNetworkProps {
  trades: Trade[];
  mostActiveTraders: TraderStats[];
  avgTradesPerSeason: number;
  loading?: boolean;
}

interface TradePartnership {
  owner1Name: string;
  owner2Name: string;
  owner1Id: number;
  owner2Id: number;
  count: number;
}

// Get theme-aware colors from CSS variables
const getThemeColors = (): string[] => {
  const computedStyle = getComputedStyle(document.documentElement);
  return [
    computedStyle.getPropertyValue('--chart-1').trim() || '#3b82f6',
    computedStyle.getPropertyValue('--chart-2').trim() || '#8b5cf6',
    computedStyle.getPropertyValue('--chart-3').trim() || '#22c55e',
    computedStyle.getPropertyValue('--chart-4').trim() || '#f97316',
    computedStyle.getPropertyValue('--accent-primary').trim() || '#3b82f6',
    computedStyle.getPropertyValue('--accent-secondary').trim() || '#8b5cf6',
    computedStyle.getPropertyValue('--success').trim() || '#22c55e',
    computedStyle.getPropertyValue('--warning').trim() || '#eab308',
    computedStyle.getPropertyValue('--error').trim() || '#ef4444',
    computedStyle.getPropertyValue('--trophy-gold').trim() || '#fbbf24',
  ];
};

// Get theme-aware axis/tooltip colors
const getChartThemeStyles = () => {
  const computedStyle = getComputedStyle(document.documentElement);
  return {
    tickFill: computedStyle.getPropertyValue('--text-secondary').trim() || '#94a3b8',
    axisStroke: computedStyle.getPropertyValue('--border-secondary').trim() || '#475569',
    tooltipBg: computedStyle.getPropertyValue('--bg-secondary').trim() || '#1e293b',
    tooltipBorder: computedStyle.getPropertyValue('--border-secondary').trim() || '#475569',
    tooltipText: computedStyle.getPropertyValue('--text-primary').trim() || '#f8fafc',
  };
};

export function TradeNetwork({ trades, mostActiveTraders, avgTradesPerSeason, loading }: TradeNetworkProps) {
  const { theme } = useTheme();
  const [chartColors, setChartColors] = useState<string[]>(getThemeColors());
  const [chartStyles, setChartStyles] = useState(getChartThemeStyles());

  // Update colors when theme changes
  useEffect(() => {
    // Small delay to ensure CSS variables are applied
    const timer = setTimeout(() => {
      setChartColors(getThemeColors());
      setChartStyles(getChartThemeStyles());
    }, 50);
    return () => clearTimeout(timer);
  }, [theme]);

  // Get color for owner avatar based on index
  const getOwnerColor = (index: number) => {
    return chartColors[index % chartColors.length];
  };
  // Calculate trade partnerships (who trades with whom)
  const partnerships = useMemo(() => {
    const partnershipMap = new Map<string, TradePartnership>();

    trades.forEach((trade) => {
      // For each pair of participants in the trade
      for (let i = 0; i < trade.teams.length; i++) {
        for (let j = i + 1; j < trade.teams.length; j++) {
          const owner1 = trade.teams[i].owner;
          const owner2 = trade.teams[j].owner;

          // Create consistent key (smaller ID first)
          const key = owner1.id < owner2.id ? `${owner1.id}-${owner2.id}` : `${owner2.id}-${owner1.id}`;

          const existing = partnershipMap.get(key);
          if (existing) {
            existing.count++;
          } else {
            partnershipMap.set(key, {
              owner1Name: owner1.id < owner2.id ? owner1.display_name || owner1.name : owner2.display_name || owner2.name,
              owner2Name: owner1.id < owner2.id ? owner2.display_name || owner2.name : owner1.display_name || owner1.name,
              owner1Id: Math.min(owner1.id, owner2.id),
              owner2Id: Math.max(owner1.id, owner2.id),
              count: 1,
            });
          }
        }
      }
    });

    return Array.from(partnershipMap.values()).sort((a, b) => b.count - a.count);
  }, [trades]);

  // Prepare data for the most active traders chart
  const traderChartData = useMemo(() => {
    return mostActiveTraders.slice(0, 10).map((t) => ({
      name: t.owner.display_name || t.owner.name,
      trades: t.trade_count,
      id: t.owner.id,
    }));
  }, [mostActiveTraders]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Trade Frequency Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-blue-600/20 flex items-center justify-center">
              <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
            </div>
            <div>
              <p className="text-slate-400 text-sm">Total Trades</p>
              <p className="text-2xl font-bold text-white">{trades.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-purple-600/20 flex items-center justify-center">
              <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <p className="text-slate-400 text-sm">Avg per Season</p>
              <p className="text-2xl font-bold text-white">{avgTradesPerSeason.toFixed(1)}</p>
            </div>
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-emerald-600/20 flex items-center justify-center">
              <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <div>
              <p className="text-slate-400 text-sm">Trade Partners</p>
              <p className="text-2xl font-bold text-white">{partnerships.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Most Active Traders Chart */}
      {traderChartData.length > 0 && (
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M5 2a2 2 0 00-2 2v1a2 2 0 002 2h1v1H5a3 3 0 00-3 3v6a3 3 0 003 3h10a3 3 0 003-3v-6a3 3 0 00-3-3h-1V7h1a2 2 0 002-2V4a2 2 0 00-2-2H5z" clipRule="evenodd" />
            </svg>
            Most Active Traders
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={traderChartData}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 60, bottom: 5 }}
              >
                <XAxis
                  type="number"
                  tick={{ fill: chartStyles.tickFill, fontSize: 12 }}
                  axisLine={{ stroke: chartStyles.axisStroke }}
                  tickLine={{ stroke: chartStyles.axisStroke }}
                  allowDecimals={false}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fill: chartStyles.tickFill, fontSize: 12 }}
                  axisLine={{ stroke: chartStyles.axisStroke }}
                  tickLine={{ stroke: chartStyles.axisStroke }}
                  width={80}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: chartStyles.tooltipBg,
                    border: `1px solid ${chartStyles.tooltipBorder}`,
                    borderRadius: '8px',
                    color: chartStyles.tooltipText,
                  }}
                  formatter={(value) => [`${value} trades`, 'Total']}
                />
                <Bar dataKey="trades" radius={[0, 4, 4, 0]}>
                  {traderChartData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={chartColors[index % chartColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Trade Partners Network */}
      {partnerships.length > 0 && (
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            Trade Partner Network
          </h3>

          {/* Network Visualization as Connected Pairs */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {partnerships.slice(0, 12).map((partnership, index) => (
              <div
                key={`${partnership.owner1Id}-${partnership.owner2Id}`}
                className="bg-slate-700/50 rounded-lg p-4 hover:bg-slate-700/70 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    {/* Owner 1 */}
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0"
                        style={{ backgroundColor: getOwnerColor(index) }}
                      >
                        {partnership.owner1Name.charAt(0).toUpperCase()}
                      </div>
                      <span className="font-medium truncate" style={{ color: 'var(--text-primary)' }}>
                        {partnership.owner1Name}
                      </span>
                    </div>

                    {/* Connection Line */}
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <div className="w-8 h-0.5" style={{ backgroundColor: 'var(--border-secondary)' }}></div>
                      <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                        <svg className="w-3 h-3" style={{ color: 'var(--text-secondary)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                        </svg>
                      </div>
                      <div className="w-8 h-0.5" style={{ backgroundColor: 'var(--border-secondary)' }}></div>
                    </div>

                    {/* Owner 2 */}
                    <div className="flex items-center gap-2 flex-1 min-w-0 justify-end">
                      <span className="font-medium truncate text-right" style={{ color: 'var(--text-primary)' }}>
                        {partnership.owner2Name}
                      </span>
                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0"
                        style={{ backgroundColor: getOwnerColor(index + 5) }}
                      >
                        {partnership.owner2Name.charAt(0).toUpperCase()}
                      </div>
                    </div>
                  </div>

                  {/* Trade Count Badge */}
                  <div className="ml-4 flex-shrink-0">
                    <span className={`inline-flex items-center justify-center px-3 py-1 rounded-full text-sm font-bold ${
                      partnership.count >= 5
                        ? 'bg-amber-500/20 text-amber-300'
                        : partnership.count >= 3
                        ? 'bg-blue-500/20 text-blue-300'
                        : 'bg-slate-600/50 text-slate-300'
                    }`}>
                      {partnership.count}x
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {partnerships.length > 12 && (
            <p className="text-slate-500 text-sm text-center mt-4">
              + {partnerships.length - 12} more trade partnerships
            </p>
          )}
        </div>
      )}

      {/* No Trades Message */}
      {trades.length === 0 && (
        <div className="text-center py-12 text-slate-400">
          <svg className="w-16 h-16 mx-auto mb-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          <p className="text-lg font-medium">No trade network data</p>
          <p className="text-sm">Import some trades to see the network</p>
        </div>
      )}
    </div>
  );
}

export default TradeNetwork;

import { useEffect, useState } from 'react';
import { RecordsPageSkeleton } from '../components/LoadingStates';
import { useTheme } from '../hooks/useTheme';

interface WeeklyScoreRecord {
  score: number;
  owner_id: number;
  owner_name: string;
  team_name: string;
  year: number;
  week: number;
  opponent_name?: string;
}

interface SeasonPointsRecord {
  points: number;
  owner_id: number;
  owner_name: string;
  team_name: string;
  year: number;
}

interface WinStreakRecord {
  streak: number;
  owner_id: number;
  owner_name: string;
  team_name: string;
  year: number;
}

interface SeasonTradesRecord {
  trade_count: number;
  owner_id: number;
  owner_name: string;
  year: number;
}

interface PlacementRecord {
  count: number;
  owner_id: number;
  owner_name: string;
  years: number[];
}

interface AllRecords {
  highest_single_week_score: WeeklyScoreRecord | null;
  most_points_in_season: SeasonPointsRecord | null;
  longest_win_streak: WinStreakRecord | null;
  most_trades_in_season: SeasonTradesRecord | null;
  most_runner_up_finishes: PlacementRecord | null;
  most_third_place_finishes: PlacementRecord | null;
  top_weekly_scores: WeeklyScoreRecord[];
  top_season_points: SeasonPointsRecord[];
  top_win_streaks: WinStreakRecord[];
  top_runner_up_finishes: PlacementRecord[];
  top_third_place_finishes: PlacementRecord[];
}

// Get theme-aware colors from CSS variables
const getRecordColors = () => {
  const computedStyle = getComputedStyle(document.documentElement);
  const trophyGold = computedStyle.getPropertyValue('--trophy-gold').trim() || '#fbbf24';
  return {
    gold: trophyGold,
    goldDark: adjustColor(trophyGold, -30),
    silver: computedStyle.getPropertyValue('--trophy-silver').trim() || '#9ca3af',
    bronze: computedStyle.getPropertyValue('--trophy-bronze').trim() || '#f97316',
    chart1: computedStyle.getPropertyValue('--chart-1').trim() || '#3b82f6',
    chart2: computedStyle.getPropertyValue('--chart-2').trim() || '#8b5cf6',
    chart3: computedStyle.getPropertyValue('--chart-3').trim() || '#22c55e',
    chart4: computedStyle.getPropertyValue('--chart-4').trim() || '#f97316',
  };
};

// Simple function to adjust a hex color brightness
const adjustColor = (hex: string, amount: number): string => {
  const clamp = (val: number) => Math.min(255, Math.max(0, val));
  let color = hex.replace('#', '');
  if (color.length === 3) {
    color = color.split('').map(c => c + c).join('');
  }
  const r = clamp(parseInt(color.substring(0, 2), 16) + amount);
  const g = clamp(parseInt(color.substring(2, 4), 16) + amount);
  const b = clamp(parseInt(color.substring(4, 6), 16) + amount);
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
};

// Trophy icon SVG - theme-aware
const TrophyIcon = ({ className = "w-6 h-6", style }: { className?: string; style?: React.CSSProperties }) => (
  <svg className={className} style={style} fill="currentColor" viewBox="0 0 20 20">
    <path fillRule="evenodd" d="M5 2a2 2 0 00-2 2v1a2 2 0 002 2h1v1H5a3 3 0 00-3 3v6a3 3 0 003 3h10a3 3 0 003-3v-6a3 3 0 00-3-3h-1V7h1a2 2 0 002-2V4a2 2 0 00-2-2H5zm0 2h10v1H5V4zm3 4h4v1H8V8z" clipRule="evenodd" />
  </svg>
);

// Medal component for rankings - theme-aware
const RankMedal = ({ rank, colors }: { rank: number; colors: ReturnType<typeof getRecordColors> }) => {
  const getMedalStyle = () => {
    switch (rank) {
      case 1:
        return {
          background: `linear-gradient(135deg, ${colors.gold} 0%, ${colors.goldDark} 100%)`,
          color: '#1a1a1a',
        };
      case 2:
        return {
          background: `linear-gradient(135deg, ${colors.silver} 0%, ${adjustColor(colors.silver, -30)} 100%)`,
          color: '#1a1a1a',
        };
      case 3:
        return {
          background: `linear-gradient(135deg, ${colors.bronze} 0%, ${adjustColor(colors.bronze, -30)} 100%)`,
          color: '#fff',
        };
      default:
        return {
          background: 'var(--bg-tertiary)',
          color: 'var(--text-primary)',
        };
    }
  };

  const style = getMedalStyle();

  return (
    <span
      className="inline-flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm"
      style={{
        background: style.background,
        color: style.color,
      }}
    >
      {rank}
    </span>
  );
};

// Record Card Component for individual record display - theme-aware
const RecordCard = ({
  title,
  icon,
  value,
  ownerName,
  year,
  subtitle,
  color,
}: {
  title: string;
  icon: React.ReactNode;
  value: string;
  ownerName: string;
  year: number;
  subtitle?: string;
  color: string; // Now accepts actual color value
}) => {
  return (
    <div className="rounded-xl overflow-hidden shadow-lg hover:shadow-xl transition-shadow" style={{ backgroundColor: 'var(--bg-secondary)' }}>
      <div className="p-4" style={{ background: `linear-gradient(to right, ${color}, ${adjustColor(color, -20)})` }}>
        <div className="flex items-center gap-3">
          <div className="rounded-lg p-2" style={{ backgroundColor: 'rgba(255, 255, 255, 0.2)' }}>
            {icon}
          </div>
          <h3 className="text-white font-bold text-lg">{title}</h3>
        </div>
      </div>
      <div className="p-5">
        <div className="text-4xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>{value}</div>
        <div className="text-xl font-semibold" style={{ color: 'var(--text-secondary)' }}>{ownerName}</div>
        <div className="flex items-center gap-2 mt-2">
          <span style={{ color: 'var(--text-secondary)' }}>{year}</span>
          {subtitle && <span style={{ color: 'var(--text-muted)' }}>• {subtitle}</span>}
        </div>
      </div>
    </div>
  );
};

// Placement Record Card for runner-up and third place - shows multiple years
const PlacementRecordCard = ({
  title,
  icon,
  count,
  ownerName,
  years,
  color,
}: {
  title: string;
  icon: React.ReactNode;
  count: number;
  ownerName: string;
  years: number[];
  color: string;
}) => {
  return (
    <div className="rounded-xl overflow-hidden shadow-lg hover:shadow-xl transition-shadow" style={{ backgroundColor: 'var(--bg-secondary)' }}>
      <div className="p-4" style={{ background: `linear-gradient(to right, ${color}, ${adjustColor(color, -20)})` }}>
        <div className="flex items-center gap-3">
          <div className="rounded-lg p-2" style={{ backgroundColor: 'rgba(255, 255, 255, 0.2)' }}>
            {icon}
          </div>
          <h3 className="text-white font-bold text-lg">{title}</h3>
        </div>
      </div>
      <div className="p-5">
        <div className="text-4xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>{count}x</div>
        <div className="text-xl font-semibold" style={{ color: 'var(--text-secondary)' }}>{ownerName}</div>
        <div className="flex items-center gap-2 mt-2 flex-wrap">
          <span style={{ color: 'var(--text-muted)' }}>Years: {years.slice(0, 5).join(', ')}{years.length > 5 ? '...' : ''}</span>
        </div>
      </div>
    </div>
  );
};

// Leaderboard Table Component - theme-aware
const LeaderboardTable = ({
  title,
  icon,
  data,
  columns,
  colors,
}: {
  title: string;
  icon: React.ReactNode;
  data: Array<Record<string, unknown>>;
  columns: Array<{
    key: string;
    label: string;
    render?: (value: unknown, row: Record<string, unknown>) => React.ReactNode;
  }>;
  colors: ReturnType<typeof getRecordColors>;
}) => {
  return (
    <div className="rounded-xl overflow-hidden shadow-lg" style={{ backgroundColor: 'var(--bg-secondary)' }}>
      <div className="p-4 flex items-center gap-3" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
        <div style={{ color: colors.chart1 }}>{icon}</div>
        <h3 className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>{title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr style={{ borderBottomWidth: '1px', borderColor: 'var(--border-primary)' }}>
              <th className="px-4 py-3 text-left text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Rank</th>
              {columns.map((col) => (
                <th key={col.key} className="px-4 py-3 text-left text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <tr
                key={index}
                className="transition-colors"
                style={{
                  borderBottomWidth: '1px',
                  borderColor: 'var(--border-primary)',
                  backgroundColor: index < 3 ? 'var(--bg-tertiary)' : 'transparent',
                }}
              >
                <td className="px-4 py-3">
                  <RankMedal rank={index + 1} colors={colors} />
                </td>
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-3" style={{ color: 'var(--text-primary)' }}>
                    {col.render ? col.render(row[col.key], row) : String(row[col.key] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export function Records() {
  const { theme } = useTheme();
  const [records, setRecords] = useState<AllRecords | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recordColors, setRecordColors] = useState(getRecordColors());

  // Update colors when theme changes
  useEffect(() => {
    const timer = setTimeout(() => {
      setRecordColors(getRecordColors());
    }, 50);
    return () => clearTimeout(timer);
  }, [theme]);

  useEffect(() => {
    const fetchRecords = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/records');
        if (!response.ok) throw new Error('Failed to fetch records');
        const data = await response.json();
        setRecords(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchRecords();
  }, []);

  if (loading) {
    return (
      <div className="p-4 sm:p-6">
        <RecordsPageSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 sm:p-6">
        <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-6 text-center">
          <p className="text-red-400">Error: {error}</p>
        </div>
      </div>
    );
  }

  const hasRecords = records && (
    records.highest_single_week_score ||
    records.most_points_in_season ||
    records.longest_win_streak ||
    records.most_trades_in_season ||
    records.most_runner_up_finishes ||
    records.most_third_place_finishes
  );

  return (
    <div className="p-4 sm:p-6 space-y-8">
      {/* Page Header */}
      <div className="text-center">
        <div
          className="inline-flex items-center justify-center w-16 h-16 rounded-full mb-4 shadow-lg"
          style={{ background: `linear-gradient(135deg, ${recordColors.gold} 0%, ${recordColors.bronze} 100%)` }}
        >
          <TrophyIcon className="w-8 h-8" style={{ color: 'white' }} />
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>League Records</h1>
        <p style={{ color: 'var(--text-secondary)' }}>The greatest achievements in league history</p>
      </div>

      {!hasRecords ? (
        <div className="rounded-xl p-8 text-center" style={{ backgroundColor: 'var(--bg-secondary)', opacity: 0.8 }}>
          <p className="text-lg" style={{ color: 'var(--text-secondary)' }}>No records yet. Import your league data to see the records!</p>
        </div>
      ) : (
        <>
          {/* Top Records Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {records?.highest_single_week_score && (
              <RecordCard
                title="Highest Week Score"
                icon={
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                }
                value={records.highest_single_week_score.score.toFixed(1)}
                ownerName={records.highest_single_week_score.owner_name}
                year={records.highest_single_week_score.year}
                subtitle={`Week ${records.highest_single_week_score.week}`}
                color={recordColors.chart1}
              />
            )}

            {records?.most_points_in_season && (
              <RecordCard
                title="Most Season Points"
                icon={
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                }
                value={records.most_points_in_season.points.toFixed(1)}
                ownerName={records.most_points_in_season.owner_name}
                year={records.most_points_in_season.year}
                color={recordColors.chart3}
              />
            )}

            {records?.longest_win_streak && (
              <RecordCard
                title="Longest Win Streak"
                icon={
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" />
                  </svg>
                }
                value={`${records.longest_win_streak.streak} Games`}
                ownerName={records.longest_win_streak.owner_name}
                year={records.longest_win_streak.year}
                color={recordColors.chart4}
              />
            )}

            {records?.most_trades_in_season && (
              <RecordCard
                title="Most Trades (Season)"
                icon={
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                  </svg>
                }
                value={`${records.most_trades_in_season.trade_count} Trades`}
                ownerName={records.most_trades_in_season.owner_name}
                year={records.most_trades_in_season.year}
                color={recordColors.chart2}
              />
            )}
          </div>

          {/* Podium Records (Runner-up and Third Place) */}
          {(records?.most_runner_up_finishes || records?.most_third_place_finishes) && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {records?.most_runner_up_finishes && (
                <PlacementRecordCard
                  title="Most Runner-Up Finishes"
                  icon={<TrophyIcon className="w-6 h-6 text-white" />}
                  count={records.most_runner_up_finishes.count}
                  ownerName={records.most_runner_up_finishes.owner_name}
                  years={records.most_runner_up_finishes.years}
                  color={recordColors.silver}
                />
              )}

              {records?.most_third_place_finishes && (
                <PlacementRecordCard
                  title="Most Third Place Finishes"
                  icon={<TrophyIcon className="w-6 h-6 text-white" />}
                  count={records.most_third_place_finishes.count}
                  ownerName={records.most_third_place_finishes.owner_name}
                  years={records.most_third_place_finishes.years}
                  color={recordColors.bronze}
                />
              )}
            </div>
          )}

          {/* Leaderboard Tables */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Weekly Scores */}
            {records?.top_weekly_scores && records.top_weekly_scores.length > 0 && (
              <LeaderboardTable
                title="Top Weekly Scores"
                icon={
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                }
                data={records.top_weekly_scores as unknown as Array<Record<string, unknown>>}
                columns={[
                  { key: 'owner_name', label: 'Owner' },
                  {
                    key: 'score',
                    label: 'Score',
                    render: (value) => (
                      <span className="font-bold" style={{ color: recordColors.chart1 }}>{(value as number).toFixed(1)}</span>
                    ),
                  },
                  {
                    key: 'year',
                    label: 'Year/Week',
                    render: (value, row) => (
                      <span style={{ color: 'var(--text-secondary)' }}>
                        {value as number} • Wk {row.week as number}
                      </span>
                    ),
                  },
                ]}
                colors={recordColors}
              />
            )}

            {/* Top Season Points */}
            {records?.top_season_points && records.top_season_points.length > 0 && (
              <LeaderboardTable
                title="Top Season Point Totals"
                icon={
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                }
                data={records.top_season_points as unknown as Array<Record<string, unknown>>}
                columns={[
                  { key: 'owner_name', label: 'Owner' },
                  {
                    key: 'points',
                    label: 'Points',
                    render: (value) => (
                      <span className="font-bold" style={{ color: recordColors.chart3 }}>{(value as number).toFixed(1)}</span>
                    ),
                  },
                  {
                    key: 'year',
                    label: 'Year',
                    render: (value) => <span style={{ color: 'var(--text-secondary)' }}>{value as number}</span>,
                  },
                ]}
                colors={recordColors}
              />
            )}

            {/* Top Win Streaks */}
            {records?.top_win_streaks && records.top_win_streaks.length > 0 && (
              <LeaderboardTable
                title="Top Win Streaks"
                icon={
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" />
                  </svg>
                }
                data={records.top_win_streaks as unknown as Array<Record<string, unknown>>}
                columns={[
                  { key: 'owner_name', label: 'Owner' },
                  {
                    key: 'streak',
                    label: 'Streak',
                    render: (value) => (
                      <span className="font-bold" style={{ color: recordColors.chart4 }}>{value as number} wins</span>
                    ),
                  },
                  {
                    key: 'year',
                    label: 'Year',
                    render: (value) => <span style={{ color: 'var(--text-secondary)' }}>{value as number}</span>,
                  },
                ]}
                colors={recordColors}
              />
            )}
          </div>
        </>
      )}
    </div>
  );
}

import { useEffect, useState } from 'react';
import { RecordsPageSkeleton } from '../components/LoadingStates';

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

interface AllRecords {
  highest_single_week_score: WeeklyScoreRecord | null;
  most_points_in_season: SeasonPointsRecord | null;
  longest_win_streak: WinStreakRecord | null;
  most_trades_in_season: SeasonTradesRecord | null;
  top_weekly_scores: WeeklyScoreRecord[];
  top_season_points: SeasonPointsRecord[];
  top_win_streaks: WinStreakRecord[];
}

// Trophy icon SVG
const TrophyIcon = ({ className = "w-6 h-6" }: { className?: string }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 20 20">
    <path fillRule="evenodd" d="M5 2a2 2 0 00-2 2v1a2 2 0 002 2h1v1H5a3 3 0 00-3 3v6a3 3 0 003 3h10a3 3 0 003-3v-6a3 3 0 00-3-3h-1V7h1a2 2 0 002-2V4a2 2 0 00-2-2H5zm0 2h10v1H5V4zm3 4h4v1H8V8z" clipRule="evenodd" />
  </svg>
);

// Medal component for rankings
const RankMedal = ({ rank }: { rank: number }) => {
  const colors: Record<number, string> = {
    1: 'bg-yellow-500 text-yellow-900',
    2: 'bg-gray-300 text-gray-700',
    3: 'bg-amber-600 text-amber-100',
  };

  const bgColor = colors[rank] || 'bg-slate-600 text-slate-200';

  return (
    <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full ${bgColor} font-bold text-sm`}>
      {rank}
    </span>
  );
};

// Record Card Component for individual record display
const RecordCard = ({
  title,
  icon,
  value,
  ownerName,
  year,
  subtitle,
  color = 'blue',
}: {
  title: string;
  icon: React.ReactNode;
  value: string;
  ownerName: string;
  year: number;
  subtitle?: string;
  color?: 'blue' | 'green' | 'orange' | 'purple';
}) => {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    orange: 'from-orange-500 to-orange-600',
    purple: 'from-purple-500 to-purple-600',
  };

  return (
    <div className="bg-slate-800 rounded-xl overflow-hidden shadow-lg hover:shadow-xl transition-shadow">
      <div className={`bg-gradient-to-r ${colorClasses[color]} p-4`}>
        <div className="flex items-center gap-3">
          <div className="bg-white/20 rounded-lg p-2">
            {icon}
          </div>
          <h3 className="text-white font-bold text-lg">{title}</h3>
        </div>
      </div>
      <div className="p-5">
        <div className="text-4xl font-bold text-white mb-2">{value}</div>
        <div className="text-xl font-semibold text-slate-200">{ownerName}</div>
        <div className="flex items-center gap-2 mt-2">
          <span className="text-slate-400">{year}</span>
          {subtitle && <span className="text-slate-500">• {subtitle}</span>}
        </div>
      </div>
    </div>
  );
};

// Leaderboard Table Component
const LeaderboardTable = ({
  title,
  icon,
  data,
  columns,
}: {
  title: string;
  icon: React.ReactNode;
  data: Array<Record<string, unknown>>;
  columns: Array<{
    key: string;
    label: string;
    render?: (value: unknown, row: Record<string, unknown>) => React.ReactNode;
  }>;
}) => {
  return (
    <div className="bg-slate-800 rounded-xl overflow-hidden shadow-lg">
      <div className="bg-slate-700 p-4 flex items-center gap-3">
        <div className="text-blue-400">{icon}</div>
        <h3 className="text-white font-bold text-lg">{title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="px-4 py-3 text-left text-slate-400 text-sm font-medium">Rank</th>
              {columns.map((col) => (
                <th key={col.key} className="px-4 py-3 text-left text-slate-400 text-sm font-medium">
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <tr
                key={index}
                className={`border-b border-slate-700/50 ${index < 3 ? 'bg-slate-700/30' : ''} hover:bg-slate-700/50 transition-colors`}
              >
                <td className="px-4 py-3">
                  <RankMedal rank={index + 1} />
                </td>
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-3 text-white">
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
  const [records, setRecords] = useState<AllRecords | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
    records.most_trades_in_season
  );

  return (
    <div className="p-4 sm:p-6 space-y-8">
      {/* Page Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-yellow-500 to-orange-600 mb-4 shadow-lg">
          <TrophyIcon className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2">League Records</h1>
        <p className="text-slate-400">The greatest achievements in league history</p>
      </div>

      {!hasRecords ? (
        <div className="bg-slate-800/50 rounded-xl p-8 text-center">
          <p className="text-slate-400 text-lg">No records yet. Import your league data to see the records!</p>
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
                color="blue"
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
                color="green"
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
                color="orange"
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
                color="purple"
              />
            )}
          </div>

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
                      <span className="font-bold text-blue-400">{(value as number).toFixed(1)}</span>
                    ),
                  },
                  {
                    key: 'year',
                    label: 'Year/Week',
                    render: (value, row) => (
                      <span className="text-slate-300">
                        {value as number} • Wk {row.week as number}
                      </span>
                    ),
                  },
                ]}
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
                      <span className="font-bold text-green-400">{(value as number).toFixed(1)}</span>
                    ),
                  },
                  {
                    key: 'year',
                    label: 'Year',
                    render: (value) => <span className="text-slate-300">{value as number}</span>,
                  },
                ]}
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
                      <span className="font-bold text-orange-400">{value as number} wins</span>
                    ),
                  },
                  {
                    key: 'year',
                    label: 'Year',
                    render: (value) => <span className="text-slate-300">{value as number}</span>,
                  },
                ]}
              />
            )}
          </div>
        </>
      )}
    </div>
  );
}

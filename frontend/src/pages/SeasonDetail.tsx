/**
 * SeasonDetail Page
 *
 * Displays detailed view of a specific season including:
 * - Season info and configuration
 * - Final standings
 * - Playoff bracket
 * - Notable trades
 */

import { useState, useEffect } from 'react';

interface OwnerBrief {
  id: number;
  name: string;
  display_name: string | null;
  avatar_url: string | null;
}

interface TeamStanding {
  team_id: number;
  team_name: string;
  owner_id: number;
  owner_name: string;
  owner_display_name: string | null;
  owner_avatar_url: string | null;
  wins: number;
  losses: number;
  ties: number;
  points_for: number;
  points_against: number;
  regular_season_rank: number | null;
  final_rank: number | null;
  made_playoffs: boolean;
}

interface PlayoffMatchup {
  id: number;
  week: number;
  home_team_id: number;
  home_team_name: string;
  home_owner_id: number;
  home_owner_name: string;
  away_team_id: number;
  away_team_name: string;
  away_owner_id: number;
  away_owner_name: string;
  home_score: number;
  away_score: number;
  winner_team_id: number | null;
  winner_owner_name: string | null;
  is_championship: boolean;
  is_consolation: boolean;
  is_tie: boolean;
}

interface TradeTeamBrief {
  id: number;
  name: string;
  owner_id: number;
  owner_name: string;
}

interface TradeSummary {
  id: number;
  week: number | null;
  trade_date: string;
  assets_exchanged: string | null;
  teams: TradeTeamBrief[];
}

interface SeasonDetail {
  id: number;
  year: number;
  league_id: number;
  league_name: string;
  platform: string;
  is_complete: boolean;
  regular_season_weeks: number | null;
  playoff_weeks: number | null;
  playoff_team_count: number | null;
  team_count: number;
  champion: OwnerBrief | null;
  runner_up: OwnerBrief | null;
  standings: TeamStanding[];
  playoff_bracket: PlayoffMatchup[];
  trades: TradeSummary[];
}

interface SeasonDetailProps {
  seasonId: number;
  onBack: () => void;
}

function getOwnerInitial(name: string): string {
  return name.charAt(0).toUpperCase();
}

function getGradientColors(name: string): string {
  const gradients = [
    'from-blue-500 to-purple-600',
    'from-green-500 to-teal-600',
    'from-orange-500 to-red-600',
    'from-pink-500 to-rose-600',
    'from-indigo-500 to-blue-600',
    'from-yellow-500 to-orange-600',
    'from-cyan-500 to-blue-600',
    'from-purple-500 to-pink-600',
  ];
  const index = name.charCodeAt(0) % gradients.length;
  return gradients[index];
}

export function SeasonDetail({ seasonId, onBack }: SeasonDetailProps) {
  const [season, setSeason] = useState<SeasonDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<'standings' | 'playoffs' | 'trades'>('standings');

  useEffect(() => {
    const loadSeason = async () => {
      try {
        setLoading(true);
        const res = await fetch(`http://localhost:8000/api/seasons/${seasonId}`);
        if (!res.ok) throw new Error('Failed to load season details');
        const data = await res.json();
        setSeason(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load season');
      } finally {
        setLoading(false);
      }
    };
    loadSeason();
  }, [seasonId]);

  if (loading) {
    return (
      <div className="p-6">
        <button onClick={onBack} className="mb-4 text-blue-400 hover:text-blue-300 flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Seasons
        </button>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
        </div>
      </div>
    );
  }

  if (error || !season) {
    return (
      <div className="p-6">
        <button onClick={onBack} className="mb-4 text-blue-400 hover:text-blue-300 flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Seasons
        </button>
        <div className="bg-red-900/30 border border-red-600 rounded-lg p-4">
          <p className="text-red-400">{error || 'Season not found'}</p>
        </div>
      </div>
    );
  }

  // Group playoff matchups by week
  const playoffsByWeek = season.playoff_bracket.reduce((acc, matchup) => {
    if (!acc[matchup.week]) {
      acc[matchup.week] = [];
    }
    acc[matchup.week].push(matchup);
    return acc;
  }, {} as Record<number, PlayoffMatchup[]>);

  const playoffWeeks = Object.keys(playoffsByWeek).map(Number).sort((a, b) => a - b);

  return (
    <div className="p-6">
      {/* Back Button */}
      <button onClick={onBack} className="mb-4 text-blue-400 hover:text-blue-300 flex items-center gap-2">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        Back to Seasons
      </button>

      {/* Season Header */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-white text-xl font-bold">
                {season.year.toString().slice(-2)}
              </span>
              <div>
                <h2 className="text-2xl font-bold text-white">{season.year} Season</h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-slate-400">{season.league_name}</span>
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    season.platform === 'SLEEPER'
                      ? 'bg-purple-600/20 text-purple-400'
                      : 'bg-blue-600/20 text-blue-400'
                  }`}>
                    {season.platform}
                  </span>
                </div>
              </div>
            </div>

            {/* Season Stats */}
            <div className="flex flex-wrap gap-4 mt-4 text-sm text-slate-400">
              <span>{season.team_count} teams</span>
              {season.regular_season_weeks && (
                <span>{season.regular_season_weeks} regular season weeks</span>
              )}
              {season.playoff_team_count && (
                <span>{season.playoff_team_count} playoff teams</span>
              )}
              <span className={season.is_complete ? 'text-green-400' : 'text-yellow-400'}>
                {season.is_complete ? 'Completed' : 'In Progress'}
              </span>
            </div>
          </div>

          {/* Champion Info */}
          {season.champion && (
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 md:text-right">
              <div className="flex items-center gap-3 md:flex-row-reverse">
                <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${getGradientColors(season.champion.name)} flex items-center justify-center text-white font-bold text-lg ring-2 ring-yellow-400`}>
                  {getOwnerInitial(season.champion.name)}
                </div>
                <div>
                  <p className="text-yellow-400 text-xs font-medium">CHAMPION</p>
                  <p className="text-white font-bold text-lg">{season.champion.name}</p>
                  {season.runner_up && (
                    <p className="text-slate-400 text-sm">defeated {season.runner_up.name}</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* View Toggle */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveView('standings')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeView === 'standings'
              ? 'bg-blue-600 text-white'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          Final Standings
        </button>
        <button
          onClick={() => setActiveView('playoffs')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeView === 'playoffs'
              ? 'bg-blue-600 text-white'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          Playoff Bracket
        </button>
        <button
          onClick={() => setActiveView('trades')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeView === 'trades'
              ? 'bg-blue-600 text-white'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          Trades ({season.trades.length})
        </button>
      </div>

      {/* Standings View */}
      {activeView === 'standings' && (
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-700">
                <tr>
                  <th className="text-left px-4 py-3 text-slate-300 font-medium text-sm">Rank</th>
                  <th className="text-left px-4 py-3 text-slate-300 font-medium text-sm">Owner</th>
                  <th className="text-left px-4 py-3 text-slate-300 font-medium text-sm">Team</th>
                  <th className="text-center px-4 py-3 text-slate-300 font-medium text-sm">Record</th>
                  <th className="text-right px-4 py-3 text-slate-300 font-medium text-sm">Points For</th>
                  <th className="text-right px-4 py-3 text-slate-300 font-medium text-sm">Points Against</th>
                  <th className="text-center px-4 py-3 text-slate-300 font-medium text-sm">Playoffs</th>
                </tr>
              </thead>
              <tbody>
                {season.standings.map((team, index) => (
                  <tr
                    key={team.team_id}
                    className={`border-t border-slate-700 ${
                      team.final_rank === 1 ? 'bg-yellow-500/10' :
                      team.final_rank === 2 ? 'bg-slate-600/20' : ''
                    }`}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {team.final_rank === 1 && (
                          <svg className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M5 2a2 2 0 00-2 2v1a2 2 0 002 2h1v1H5a3 3 0 00-3 3v6a3 3 0 003 3h10a3 3 0 003-3v-6a3 3 0 00-3-3h-1V7h1a2 2 0 002-2V4a2 2 0 00-2-2H5zm0 2h10v1H5V4zm3 4h4v1H8V8z" clipRule="evenodd" />
                          </svg>
                        )}
                        {team.final_rank === 2 && (
                          <span className="text-slate-400 text-sm">2nd</span>
                        )}
                        {team.final_rank === 3 && (
                          <span className="text-amber-600 text-sm">3rd</span>
                        )}
                        {team.final_rank && team.final_rank > 3 && (
                          <span className="text-slate-400 text-sm">{team.final_rank}th</span>
                        )}
                        {!team.final_rank && (
                          <span className="text-slate-500 text-sm">{index + 1}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-full bg-gradient-to-br ${getGradientColors(team.owner_name)} flex items-center justify-center text-white font-bold text-sm`}>
                          {getOwnerInitial(team.owner_name)}
                        </div>
                        <span className="text-white font-medium">{team.owner_name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-slate-400">{team.team_name}</td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-white font-medium">
                        {team.wins}-{team.losses}{team.ties > 0 ? `-${team.ties}` : ''}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-green-400">{team.points_for.toFixed(1)}</td>
                    <td className="px-4 py-3 text-right text-red-400">{team.points_against.toFixed(1)}</td>
                    <td className="px-4 py-3 text-center">
                      {team.made_playoffs ? (
                        <span className="inline-flex items-center gap-1 text-green-400">
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                          Yes
                        </span>
                      ) : (
                        <span className="text-slate-500">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Playoffs View */}
      {activeView === 'playoffs' && (
        <div>
          {season.playoff_bracket.length === 0 ? (
            <div className="bg-slate-800 rounded-xl border border-slate-700 p-8 text-center">
              <p className="text-slate-400">No playoff data available for this season.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {playoffWeeks.map(week => {
                const weekMatchups = playoffsByWeek[week];
                const hasChampionship = weekMatchups.some(m => m.is_championship);

                return (
                  <div key={week}>
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                      {hasChampionship ? (
                        <>
                          <svg className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M5 2a2 2 0 00-2 2v1a2 2 0 002 2h1v1H5a3 3 0 00-3 3v6a3 3 0 003 3h10a3 3 0 003-3v-6a3 3 0 00-3-3h-1V7h1a2 2 0 002-2V4a2 2 0 00-2-2H5zm0 2h10v1H5V4zm3 4h4v1H8V8z" clipRule="evenodd" />
                          </svg>
                          Championship Week (Week {week})
                        </>
                      ) : (
                        <>Week {week}</>
                      )}
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {weekMatchups.map(matchup => (
                        <div
                          key={matchup.id}
                          className={`rounded-xl border overflow-hidden ${
                            matchup.is_championship
                              ? 'bg-gradient-to-br from-yellow-500/20 to-orange-500/20 border-yellow-500/50'
                              : matchup.is_consolation
                                ? 'bg-slate-700 border-slate-600'
                                : 'bg-slate-800 border-slate-700'
                          }`}
                        >
                          {matchup.is_championship && (
                            <div className="bg-yellow-500/30 px-4 py-2 text-center border-b border-yellow-500/50">
                              <span className="text-yellow-400 font-bold text-sm">CHAMPIONSHIP</span>
                            </div>
                          )}
                          {matchup.is_consolation && (
                            <div className="bg-slate-600 px-4 py-2 text-center border-b border-slate-500">
                              <span className="text-slate-300 font-medium text-sm">Consolation</span>
                            </div>
                          )}

                          <div className="p-4">
                            {/* Home Team */}
                            <div className={`flex items-center justify-between p-3 rounded-lg mb-2 ${
                              matchup.winner_team_id === matchup.home_team_id
                                ? 'bg-green-500/20 border border-green-500/30'
                                : 'bg-slate-700/50'
                            }`}>
                              <div className="flex items-center gap-3">
                                <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${getGradientColors(matchup.home_owner_name)} flex items-center justify-center text-white font-bold`}>
                                  {getOwnerInitial(matchup.home_owner_name)}
                                </div>
                                <div>
                                  <p className="text-white font-medium">{matchup.home_owner_name}</p>
                                  <p className="text-slate-400 text-sm">{matchup.home_team_name}</p>
                                </div>
                              </div>
                              <span className={`text-2xl font-bold ${
                                matchup.winner_team_id === matchup.home_team_id
                                  ? 'text-green-400'
                                  : 'text-slate-400'
                              }`}>
                                {matchup.home_score.toFixed(1)}
                              </span>
                            </div>

                            {/* Away Team */}
                            <div className={`flex items-center justify-between p-3 rounded-lg ${
                              matchup.winner_team_id === matchup.away_team_id
                                ? 'bg-green-500/20 border border-green-500/30'
                                : 'bg-slate-700/50'
                            }`}>
                              <div className="flex items-center gap-3">
                                <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${getGradientColors(matchup.away_owner_name)} flex items-center justify-center text-white font-bold`}>
                                  {getOwnerInitial(matchup.away_owner_name)}
                                </div>
                                <div>
                                  <p className="text-white font-medium">{matchup.away_owner_name}</p>
                                  <p className="text-slate-400 text-sm">{matchup.away_team_name}</p>
                                </div>
                              </div>
                              <span className={`text-2xl font-bold ${
                                matchup.winner_team_id === matchup.away_team_id
                                  ? 'text-green-400'
                                  : 'text-slate-400'
                              }`}>
                                {matchup.away_score.toFixed(1)}
                              </span>
                            </div>

                            {/* Winner indicator */}
                            {matchup.winner_owner_name && matchup.is_championship && (
                              <div className="mt-4 text-center">
                                <span className="inline-flex items-center gap-2 text-yellow-400 font-bold">
                                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M5 2a2 2 0 00-2 2v1a2 2 0 002 2h1v1H5a3 3 0 00-3 3v6a3 3 0 003 3h10a3 3 0 003-3v-6a3 3 0 00-3-3h-1V7h1a2 2 0 002-2V4a2 2 0 00-2-2H5zm0 2h10v1H5V4zm3 4h4v1H8V8z" clipRule="evenodd" />
                                  </svg>
                                  {matchup.winner_owner_name} wins the championship!
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Trades View */}
      {activeView === 'trades' && (
        <div>
          {season.trades.length === 0 ? (
            <div className="bg-slate-800 rounded-xl border border-slate-700 p-8 text-center">
              <svg className="w-12 h-12 mx-auto mb-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
              <p className="text-slate-400">No trades recorded for this season.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {season.trades.map(trade => (
                <div key={trade.id} className="bg-slate-800 rounded-xl border border-slate-700 p-4">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-3">
                    <div className="flex items-center gap-2">
                      <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                      </svg>
                      <span className="text-white font-medium">Trade</span>
                      {trade.week && (
                        <span className="text-slate-400 text-sm">Week {trade.week}</span>
                      )}
                    </div>
                    <span className="text-slate-500 text-sm">
                      {new Date(trade.trade_date).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric'
                      })}
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-3">
                    {trade.teams.map((team, index) => (
                      <div key={team.id} className="flex items-center gap-2">
                        <div className={`w-8 h-8 rounded-full bg-gradient-to-br ${getGradientColors(team.owner_name)} flex items-center justify-center text-white font-bold text-sm`}>
                          {getOwnerInitial(team.owner_name)}
                        </div>
                        <span className="text-white">{team.owner_name}</span>
                        {index < trade.teams.length - 1 && (
                          <svg className="w-5 h-5 text-slate-500 mx-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                          </svg>
                        )}
                      </div>
                    ))}
                  </div>

                  {trade.assets_exchanged && (
                    <div className="mt-3 p-3 bg-slate-700/50 rounded-lg">
                      <p className="text-slate-300 text-sm font-mono">{trade.assets_exchanged}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default SeasonDetail;

/**
 * ImportedLeagues Component
 *
 * Displays a list of imported leagues with:
 * - League info (name, platform, seasons)
 * - Import date
 * - Re-import and delete actions
 */

import { useState, useEffect } from 'react';
import { LoadingSpinner } from './LoadingStates';

interface LeagueSeason {
  id: number;
  year: number;
  champion_name: string | null;
}

interface ImportedLeague {
  id: number;
  name: string;
  platform: string;
  platform_league_id: string;
  team_count: number | null;
  scoring_type: string | null;
  created_at: string;
  seasons_count: number;
  seasons: LeagueSeason[];
  latest_season_year: number | null;
  total_teams: number;
  total_matchups: number;
  total_trades: number;
}

interface ImportedLeaguesProps {
  onReimport: (leagueId: string, platform: string) => void;
  onDelete: (leagueId: number) => void;
  refreshTrigger?: number;
}

export function ImportedLeagues({ onReimport, onDelete, refreshTrigger }: ImportedLeaguesProps) {
  const [leagues, setLeagues] = useState<ImportedLeague[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);

  const loadLeagues = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('http://localhost:8000/api/leagues');
      if (response.ok) {
        const data = await response.json();
        setLeagues(data);
      } else {
        setError('Failed to load leagues');
      }
    } catch {
      setError('Network error - please ensure the backend is running');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLeagues();
  }, [refreshTrigger]);

  const handleDelete = async (leagueId: number) => {
    if (confirmDelete !== leagueId) {
      setConfirmDelete(leagueId);
      return;
    }

    setDeletingId(leagueId);
    setConfirmDelete(null);

    try {
      const response = await fetch(`http://localhost:8000/api/leagues/${leagueId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setLeagues((prev) => prev.filter((l) => l.id !== leagueId));
        onDelete(leagueId);
      } else {
        const error = await response.json();
        setError(error.detail || 'Failed to delete league');
      }
    } catch {
      setError('Network error while deleting league');
    } finally {
      setDeletingId(null);
    }
  };

  const getPlatformIcon = (platform: string) => {
    return platform === 'sleeper' ? '🌙' : '🏈';
  };

  const getPlatformColor = (platform: string) => {
    return platform === 'sleeper' ? 'bg-blue-600/20 text-blue-400' : 'bg-purple-600/20 text-purple-400';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (loading) {
    return (
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-xl font-bold text-white mb-4">Imported Leagues</h3>
        <div className="flex justify-center py-8">
          <LoadingSpinner size="md" color="blue" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-xl font-bold text-white mb-4">Imported Leagues</h3>
        <div className="text-red-400 text-center py-4">{error}</div>
        <button
          onClick={loadLeagues}
          className="w-full py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (leagues.length === 0) {
    return (
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-xl font-bold text-white mb-4">Imported Leagues</h3>
        <div className="text-slate-400 text-center py-8">
          <div className="text-4xl mb-2">📊</div>
          <p>No leagues imported yet.</p>
          <p className="text-sm mt-2">Use the Import League section above to get started!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-white">Imported Leagues</h3>
        <span className="text-slate-400 text-sm">{leagues.length} league{leagues.length !== 1 ? 's' : ''}</span>
      </div>

      <div className="space-y-4">
        {leagues.map((league) => (
          <div
            key={league.id}
            className="bg-slate-700/50 rounded-lg p-4 border border-slate-600/50 hover:border-slate-500/50 transition-colors"
          >
            {/* Header Row */}
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3 min-w-0">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${getPlatformColor(league.platform)}`}>
                  <span className="text-xl">{getPlatformIcon(league.platform)}</span>
                </div>
                <div className="min-w-0">
                  <div className="text-white font-semibold truncate">{league.name}</div>
                  <div className="flex items-center gap-2 text-slate-400 text-sm">
                    <span className="capitalize">{league.platform}</span>
                    {league.scoring_type && (
                      <>
                        <span className="text-slate-600">•</span>
                        <span>{league.scoring_type}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => onReimport(league.platform_league_id, league.platform)}
                  className={`px-3 py-1.5 rounded-lg transition-colors text-sm font-medium flex items-center gap-1.5 ${
                    league.platform === 'sleeper'
                      ? 'bg-blue-600/20 text-blue-400 hover:bg-blue-600/30'
                      : 'bg-purple-600/20 text-purple-400 hover:bg-purple-600/30'
                  }`}
                  title="Re-import league data"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Re-import
                </button>
                <button
                  onClick={() => handleDelete(league.id)}
                  disabled={deletingId === league.id}
                  className={`px-3 py-1.5 rounded-lg transition-colors text-sm font-medium flex items-center gap-1.5 ${
                    confirmDelete === league.id
                      ? 'bg-red-600 text-white hover:bg-red-500'
                      : 'bg-red-600/20 text-red-400 hover:bg-red-600/30'
                  } disabled:opacity-50`}
                  title={confirmDelete === league.id ? 'Click again to confirm' : 'Delete league'}
                >
                  {deletingId === league.id ? (
                    <LoadingSpinner size="sm" color="red" />
                  ) : (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  )}
                  {confirmDelete === league.id ? 'Confirm' : 'Delete'}
                </button>
              </div>
            </div>

            {/* Stats Row */}
            <div className="mt-3 pt-3 border-t border-slate-600/50 grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="text-center">
                <div className="text-white font-medium">{league.seasons_count}</div>
                <div className="text-slate-400 text-xs">Season{league.seasons_count !== 1 ? 's' : ''}</div>
              </div>
              <div className="text-center">
                <div className="text-white font-medium">{league.total_teams}</div>
                <div className="text-slate-400 text-xs">Teams</div>
              </div>
              <div className="text-center">
                <div className="text-white font-medium">{league.total_matchups}</div>
                <div className="text-slate-400 text-xs">Matchups</div>
              </div>
              <div className="text-center">
                <div className="text-white font-medium">{league.total_trades}</div>
                <div className="text-slate-400 text-xs">Trades</div>
              </div>
            </div>

            {/* Footer Row */}
            <div className="mt-3 pt-3 border-t border-slate-600/50 flex items-center justify-between text-sm">
              <div className="text-slate-400">
                {league.latest_season_year && (
                  <span>
                    {league.seasons_count > 1
                      ? `${Math.min(...league.seasons.map(s => s.year))} - ${league.latest_season_year}`
                      : league.latest_season_year
                    }
                  </span>
                )}
              </div>
              <div className="text-slate-500">
                Imported {formatDate(league.created_at)}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ImportedLeagues;

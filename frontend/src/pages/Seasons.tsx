/**
 * Seasons Page
 *
 * Displays all seasons with champions and key stats.
 */

import { useState, useEffect } from 'react';

interface Season {
  season_id: number;
  year: number;
  league_id: number;
  league_name: string;
  platform: string;
  champion_id: number | null;
  champion_name: string | null;
  team_count: number;
}

export function Seasons() {
  const [seasons, setSeasons] = useState<Season[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadSeasons = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/history/seasons');
        if (!res.ok) throw new Error('Failed to load seasons');
        const data = await res.json();
        setSeasons(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load seasons');
      } finally {
        setLoading(false);
      }
    };
    loadSeasons();
  }, []);

  // Group seasons by year
  const seasonsByYear = seasons.reduce((acc, season) => {
    if (!acc[season.year]) {
      acc[season.year] = [];
    }
    acc[season.year].push(season);
    return acc;
  }, {} as Record<number, Season[]>);

  const sortedYears = Object.keys(seasonsByYear)
    .map(Number)
    .sort((a, b) => b - a);

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white">Seasons</h2>
        <p className="text-slate-400">All seasons with champions and league info</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
        </div>
      ) : error ? (
        <div className="bg-red-900/30 border border-red-600 rounded-lg p-4">
          <p className="text-red-400">{error}</p>
        </div>
      ) : seasons.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-700 flex items-center justify-center">
            <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">No Seasons Found</h3>
          <p className="text-slate-400 max-w-md mx-auto">
            Import league data from Sleeper or Yahoo Fantasy to see seasons here.
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {sortedYears.map(year => (
            <div key={year}>
              <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-white text-sm font-bold">
                  {year.toString().slice(-2)}
                </span>
                {year} Season
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {seasonsByYear[year].map(season => (
                  <div
                    key={season.season_id}
                    className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden hover:border-slate-600 transition-colors"
                  >
                    <div className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-semibold text-white">{season.league_name}</h4>
                          <span className={`text-xs px-2 py-0.5 rounded ${
                            season.platform === 'SLEEPER'
                              ? 'bg-purple-600/20 text-purple-400'
                              : 'bg-blue-600/20 text-blue-400'
                          }`}>
                            {season.platform}
                          </span>
                        </div>
                        <span className="text-slate-400 text-sm">
                          {season.team_count} teams
                        </span>
                      </div>

                      {season.champion_name ? (
                        <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                          <div className="flex items-center gap-2">
                            <svg className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M5 2a2 2 0 00-2 2v1a2 2 0 002 2h1v1H5a3 3 0 00-3 3v6a3 3 0 003 3h10a3 3 0 003-3v-6a3 3 0 00-3-3h-1V7h1a2 2 0 002-2V4a2 2 0 00-2-2H5zm0 2h10v1H5V4zm3 4h4v1H8V8z" clipRule="evenodd" />
                            </svg>
                            <div>
                              <p className="text-yellow-400 text-xs font-medium">Champion</p>
                              <p className="text-white font-semibold">{season.champion_name}</p>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="mt-4 p-3 bg-slate-700/50 rounded-lg">
                          <p className="text-slate-400 text-sm text-center">No champion recorded</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Seasons;

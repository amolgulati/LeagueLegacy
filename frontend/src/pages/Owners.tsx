/**
 * Owners Page
 *
 * Lists all owners with their career stats.
 * Provides quick access to owner profiles and mapping.
 */

import { useState, useEffect } from 'react';
import { OwnerMapping } from '../components/OwnerMapping';

interface OwnerWithStats {
  owner_id: number;
  owner_name: string;
  total_wins: number;
  total_losses: number;
  total_ties: number;
  playoff_appearances: number;
  championships: number;
  win_percentage: number;
}

type ViewMode = 'list' | 'mapping';

export function Owners() {
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [owners, setOwners] = useState<OwnerWithStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadOwners = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/history/owners');
        if (!res.ok) throw new Error('Failed to load owners');
        const data = await res.json();
        setOwners(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load owners');
      } finally {
        setLoading(false);
      }
    };
    loadOwners();
  }, []);

  if (viewMode === 'mapping') {
    return (
      <div>
        <div className="p-6 pb-0">
          <button
            onClick={() => setViewMode('list')}
            className="text-blue-400 hover:text-blue-300 flex items-center gap-2 mb-4"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Owners List
          </button>
        </div>
        <OwnerMapping />
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white">Owners</h2>
          <p className="text-slate-400">Career statistics across all platforms</p>
        </div>
        <button
          onClick={() => setViewMode('mapping')}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white text-sm flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          Manage Mappings
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
        </div>
      ) : error ? (
        <div className="bg-red-900/30 border border-red-600 rounded-lg p-4">
          <p className="text-red-400">{error}</p>
        </div>
      ) : owners.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-700 flex items-center justify-center">
            <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">No Owners Found</h3>
          <p className="text-slate-400 max-w-md mx-auto">
            Import league data from Sleeper or Yahoo Fantasy to see owners here.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-4 text-slate-400 font-medium text-sm">Rank</th>
                <th className="text-left py-3 px-4 text-slate-400 font-medium text-sm">Owner</th>
                <th className="text-center py-3 px-4 text-slate-400 font-medium text-sm">Record</th>
                <th className="text-center py-3 px-4 text-slate-400 font-medium text-sm hidden sm:table-cell">Win %</th>
                <th className="text-center py-3 px-4 text-slate-400 font-medium text-sm hidden md:table-cell">Playoffs</th>
                <th className="text-center py-3 px-4 text-slate-400 font-medium text-sm">Titles</th>
              </tr>
            </thead>
            <tbody>
              {owners.map((owner, index) => (
                <tr
                  key={owner.owner_id}
                  className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors"
                >
                  <td className="py-4 px-4">
                    <span className={`
                      inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold
                      ${index === 0 ? 'bg-yellow-500/20 text-yellow-400' :
                        index === 1 ? 'bg-slate-400/20 text-slate-300' :
                        index === 2 ? 'bg-orange-500/20 text-orange-400' :
                        'bg-slate-700 text-slate-400'}
                    `}>
                      {index + 1}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                        {owner.owner_name.charAt(0).toUpperCase()}
                      </div>
                      <span className="font-medium text-white">{owner.owner_name}</span>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-center text-white font-mono">
                    {owner.total_wins}-{owner.total_losses}
                    {owner.total_ties > 0 && `-${owner.total_ties}`}
                  </td>
                  <td className="py-4 px-4 text-center text-slate-300 hidden sm:table-cell">
                    {(owner.win_percentage * 100).toFixed(1)}%
                  </td>
                  <td className="py-4 px-4 text-center text-slate-300 hidden md:table-cell">
                    {owner.playoff_appearances}
                  </td>
                  <td className="py-4 px-4 text-center">
                    {owner.championships > 0 ? (
                      <span className="inline-flex items-center gap-1 text-yellow-400 font-bold">
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M5 2a2 2 0 00-2 2v1a2 2 0 002 2h1v1H5a3 3 0 00-3 3v6a3 3 0 003 3h10a3 3 0 003-3v-6a3 3 0 00-3-3h-1V7h1a2 2 0 002-2V4a2 2 0 00-2-2H5zm0 2h10v1H5V4zm3 4h4v1H8V8z" clipRule="evenodd" />
                        </svg>
                        {owner.championships}
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
      )}
    </div>
  );
}

export default Owners;

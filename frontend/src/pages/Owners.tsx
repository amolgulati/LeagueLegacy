/**
 * Owners Page
 *
 * Lists all owners with their career stats.
 * Supports both card view (profile cards) and list view (table).
 * Provides quick access to owner profiles and mapping.
 */

import { useState, useEffect } from 'react';
import { OwnerMapping } from '../components/OwnerMapping';
import { OwnerProfileCard } from '../components/OwnerProfileCard';
import type { OwnerWithStats } from '../types/owner';

type ViewMode = 'cards' | 'list' | 'mapping';

export function Owners() {
  const [viewMode, setViewMode] = useState<ViewMode>('cards');
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
            onClick={() => setViewMode('cards')}
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
        <div className="flex items-center gap-3">
          {/* View Toggle */}
          <div className="flex items-center bg-slate-800 rounded-lg p-1">
            <button
              onClick={() => setViewMode('cards')}
              className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                viewMode === 'cards'
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
              title="Card View"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                viewMode === 'list'
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
              title="List View"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
            </button>
          </div>

          {/* Manage Mappings Button */}
          <button
            onClick={() => setViewMode('mapping')}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white text-sm flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            <span className="hidden sm:inline">Manage Mappings</span>
          </button>
        </div>
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
      ) : viewMode === 'cards' ? (
        /* Card View */
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {owners.map((owner, index) => (
            <OwnerProfileCard
              key={owner.id}
              owner={owner}
              rank={index + 1}
            />
          ))}
        </div>
      ) : (
        /* List View (Table) */
        <div className="overflow-x-auto rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)' }}>
          <table className="w-full espn-table">
            <thead>
              <tr style={{ borderBottom: '3px solid var(--border-primary)' }}>
                <th className="text-left py-3 px-4 font-medium text-sm" style={{ color: 'var(--text-muted)' }}>Rank</th>
                <th className="text-left py-3 px-4 font-medium text-sm" style={{ color: 'var(--text-muted)' }}>Owner</th>
                <th className="text-center py-3 px-4 font-medium text-sm" style={{ color: 'var(--text-muted)' }}>Record</th>
                <th className="text-center py-3 px-4 font-medium text-sm hidden sm:table-cell" style={{ color: 'var(--text-muted)' }}>Win %</th>
                <th className="text-center py-3 px-4 font-medium text-sm hidden md:table-cell" style={{ color: 'var(--text-muted)' }}>Playoffs</th>
                <th className="text-center py-3 px-4 font-medium text-sm" style={{ color: 'var(--text-muted)' }}>Titles</th>
              </tr>
            </thead>
            <tbody>
              {owners.map((owner, index) => (
                <tr
                  key={owner.id}
                  className={`transition-colors ${owner.championships > 0 ? 'champion-row' : ''}`}
                  style={{
                    borderBottom: '1px solid rgba(255,255,255,0.1)',
                    ...(owner.championships > 0 ? {
                      background: 'linear-gradient(90deg, rgba(255, 215, 0, 0.15) 0%, transparent 100%)',
                      borderLeft: '4px solid var(--trophy-gold)'
                    } : {})
                  }}
                >
                  <td className="py-4 px-4 rank-cell">
                    <span
                      className="inline-flex items-center justify-center w-8 h-8 text-sm font-bold"
                      style={{
                        borderRadius: '2px',
                        ...(index === 0 ? { backgroundColor: 'rgba(255, 215, 0, 0.2)', color: 'var(--trophy-gold)' } :
                          index === 1 ? { backgroundColor: 'rgba(192, 192, 192, 0.2)', color: 'var(--trophy-silver)' } :
                          index === 2 ? { backgroundColor: 'rgba(205, 127, 50, 0.2)', color: 'var(--trophy-bronze)' } :
                          { backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-secondary)' })
                      }}
                    >
                      {index + 1}
                    </span>
                  </td>
                  <td className="py-4 px-4 owner-cell">
                    <div className="flex items-center gap-3">
                      {owner.avatar_url ? (
                        <img
                          src={owner.avatar_url}
                          alt={owner.display_name || owner.name}
                          className="w-10 h-10 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                          {(owner.display_name || owner.name).charAt(0).toUpperCase()}
                        </div>
                      )}
                      <span className="font-medium espn-team-name" style={{ color: 'var(--text-primary)' }}>{owner.display_name || owner.name}</span>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-center points-cell" style={{ color: 'var(--text-primary)' }}>
                    {owner.total_wins}-{owner.total_losses}
                    {owner.total_ties > 0 && `-${owner.total_ties}`}
                  </td>
                  <td className="py-4 px-4 text-center hidden sm:table-cell" style={{ color: 'var(--text-secondary)' }}>
                    {owner.win_percentage.toFixed(1)}%
                  </td>
                  <td className="py-4 px-4 text-center hidden md:table-cell" style={{ color: 'var(--text-secondary)' }}>
                    {owner.playoff_appearances}
                  </td>
                  <td className="py-4 px-4 text-center">
                    {owner.championships > 0 ? (
                      <span className="inline-flex items-center gap-1 font-bold" style={{ color: 'var(--trophy-gold)' }}>
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 2a1 1 0 00-1 1v1H6a1 1 0 00-1 1v3a3 3 0 003 3h.17A5.986 5.986 0 0110 12.17V15H8a1 1 0 000 2h4a1 1 0 000-2h-2v-2.83A5.986 5.986 0 0011.83 11H12a3 3 0 003-3V5a1 1 0 00-1-1h-3V3a1 1 0 00-1-1zM7 5h6v3a1 1 0 01-1 1H8a1 1 0 01-1-1V5z" clipRule="evenodd" />
                        </svg>
                        {owner.championships}
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>-</span>
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

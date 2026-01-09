/**
 * Head-to-Head Rivalry View Page
 *
 * Allows users to select two owners and view:
 * - All-time record between them
 * - Average scores in matchups
 * - Historical matchup list with playoff highlights
 */

import { useState, useEffect } from 'react';
import type { OwnerWithStats, HeadToHeadResponse, MatchupDetail } from '../types/owner';

/**
 * Generates a consistent gradient based on owner name
 */
function getAvatarGradient(name: string): string {
  const gradients = [
    'from-blue-500 to-purple-600',
    'from-emerald-500 to-teal-600',
    'from-orange-500 to-red-600',
    'from-pink-500 to-rose-600',
    'from-indigo-500 to-blue-600',
    'from-amber-500 to-orange-600',
    'from-cyan-500 to-blue-600',
    'from-violet-500 to-purple-600',
  ];

  const hash = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return gradients[hash % gradients.length];
}

/**
 * OwnerSelect component for dropdown selection
 */
function OwnerSelect({
  owners,
  selectedId,
  onChange,
  excludeId,
  label,
}: {
  owners: OwnerWithStats[];
  selectedId: number | null;
  onChange: (id: number | null) => void;
  excludeId: number | null;
  label: string;
}) {
  const filteredOwners = owners.filter(o => o.id !== excludeId);

  return (
    <div className="flex-1">
      <label className="block text-sm font-medium text-slate-400 mb-2">{label}</label>
      <select
        value={selectedId ?? ''}
        onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
        className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      >
        <option value="">Select owner...</option>
        {filteredOwners.map((owner) => (
          <option key={owner.id} value={owner.id}>
            {owner.display_name || owner.name}
          </option>
        ))}
      </select>
    </div>
  );
}

/**
 * OwnerCard component for displaying selected owner in the comparison
 */
function OwnerCard({
  owner,
  wins,
  avgScore,
  isLeading,
  position,
}: {
  owner: { id: number; name: string; display_name: string | null; avatar_url: string | null };
  wins: number;
  avgScore: number | null;
  isLeading: boolean;
  position: 'left' | 'right';
}) {
  const displayName = owner.display_name || owner.name;
  const gradient = getAvatarGradient(owner.name);

  return (
    <div className={`
      flex-1 p-6 rounded-xl
      ${isLeading ? 'bg-gradient-to-br from-emerald-900/50 to-emerald-800/30 border-emerald-700/50' : 'bg-slate-800/50 border-slate-700/50'}
      border
      ${position === 'left' ? 'text-center' : 'text-center'}
    `}>
      {/* Leading badge */}
      {isLeading && (
        <div className="mb-3">
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-medium">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
            LEADING
          </span>
        </div>
      )}

      {/* Avatar */}
      <div className="flex justify-center mb-4">
        {owner.avatar_url ? (
          <img
            src={owner.avatar_url}
            alt={displayName}
            className="w-20 h-20 rounded-full object-cover ring-4 ring-slate-700 shadow-lg"
          />
        ) : (
          <div className={`
            w-20 h-20 rounded-full
            bg-gradient-to-br ${gradient}
            flex items-center justify-center
            text-3xl font-bold text-white
            ring-4 ring-slate-700 shadow-lg
          `}>
            {displayName.charAt(0).toUpperCase()}
          </div>
        )}
      </div>

      {/* Name */}
      <h3 className="text-xl font-bold text-white mb-4">{displayName}</h3>

      {/* Stats */}
      <div className="space-y-2">
        <div className={`text-4xl font-bold ${isLeading ? 'text-emerald-400' : 'text-white'}`}>
          {wins}
        </div>
        <div className="text-sm text-slate-400 uppercase tracking-wide">Wins</div>

        {avgScore !== null && (
          <div className="mt-4 pt-4 border-t border-slate-700/50">
            <div className="text-lg font-semibold text-slate-300">
              {avgScore.toFixed(1)}
            </div>
            <div className="text-xs text-slate-500 uppercase tracking-wide">Avg Score</div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * MatchupRow component for displaying individual matchup history
 */
function MatchupRow({
  matchup,
  owner1Name,
  owner2Name,
  owner1Id,
}: {
  matchup: MatchupDetail;
  owner1Name: string;
  owner2Name: string;
  owner1Id: number;
}) {
  const isOwner1Winner = matchup.winner_id === owner1Id;
  const isTie = matchup.winner_id === null && !matchup.is_playoff;

  return (
    <div className={`
      flex items-center gap-4 p-4 rounded-lg
      ${matchup.is_championship ? 'bg-yellow-900/20 border border-yellow-700/50' :
        matchup.is_playoff ? 'bg-purple-900/20 border border-purple-700/50' :
        'bg-slate-800/30'}
      hover:bg-slate-700/30 transition-colors
    `}>
      {/* Year/Week */}
      <div className="w-24 text-center">
        <div className="text-white font-semibold">{matchup.year}</div>
        <div className="text-xs text-slate-400">Week {matchup.week}</div>
      </div>

      {/* Badges */}
      <div className="w-24 flex flex-col items-center gap-1">
        {matchup.is_championship && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-400 text-xs font-medium">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 2a1 1 0 00-1 1v1H6a1 1 0 00-1 1v3a3 3 0 003 3h.17A5.986 5.986 0 0110 12.17V15H8a1 1 0 000 2h4a1 1 0 000-2h-2v-2.83A5.986 5.986 0 0011.83 11H12a3 3 0 003-3V5a1 1 0 00-1-1h-3V3a1 1 0 00-1-1zM7 5h6v3a1 1 0 01-1 1H8a1 1 0 01-1-1V5z" clipRule="evenodd" />
            </svg>
            SHIP
          </span>
        )}
        {matchup.is_playoff && !matchup.is_championship && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-400 text-xs font-medium">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            PLAYOFF
          </span>
        )}
      </div>

      {/* Scores */}
      <div className="flex-1 flex items-center justify-center gap-4">
        <div className={`flex-1 text-right ${isOwner1Winner ? 'text-emerald-400 font-bold' : 'text-slate-300'}`}>
          <span className="hidden sm:inline mr-2">{owner1Name}</span>
          <span className="text-xl font-mono">{matchup.owner1_score.toFixed(1)}</span>
        </div>

        <div className="text-slate-500 font-medium">vs</div>

        <div className={`flex-1 text-left ${!isOwner1Winner && !isTie ? 'text-emerald-400 font-bold' : 'text-slate-300'}`}>
          <span className="text-xl font-mono">{matchup.owner2_score.toFixed(1)}</span>
          <span className="hidden sm:inline ml-2">{owner2Name}</span>
        </div>
      </div>

      {/* Winner indicator */}
      <div className="w-16 text-center">
        {isTie ? (
          <span className="text-slate-400 text-sm">TIE</span>
        ) : isOwner1Winner ? (
          <span className="text-emerald-400 text-sm font-medium">W</span>
        ) : (
          <span className="text-red-400 text-sm font-medium">L</span>
        )}
      </div>
    </div>
  );
}

export function HeadToHead() {
  const [owners, setOwners] = useState<OwnerWithStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [owner1Id, setOwner1Id] = useState<number | null>(null);
  const [owner2Id, setOwner2Id] = useState<number | null>(null);

  const [headToHead, setHeadToHead] = useState<HeadToHeadResponse | null>(null);
  const [h2hLoading, setH2hLoading] = useState(false);
  const [h2hError, setH2hError] = useState<string | null>(null);

  // Load owners on mount
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

  // Load head-to-head data when both owners are selected
  useEffect(() => {
    if (owner1Id === null || owner2Id === null) {
      setHeadToHead(null);
      return;
    }

    const loadHeadToHead = async () => {
      setH2hLoading(true);
      setH2hError(null);
      try {
        const res = await fetch(`http://localhost:8000/api/history/head-to-head/${owner1Id}/${owner2Id}`);
        if (!res.ok) throw new Error('Failed to load head-to-head data');
        const data = await res.json();
        setHeadToHead(data);
      } catch (err) {
        setH2hError(err instanceof Error ? err.message : 'Failed to load head-to-head data');
      } finally {
        setH2hLoading(false);
      }
    };
    loadHeadToHead();
  }, [owner1Id, owner2Id]);

  // Swap owners
  const handleSwapOwners = () => {
    setOwner1Id(owner2Id);
    setOwner2Id(owner1Id);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-900/30 border border-red-600 rounded-lg p-4">
          <p className="text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  if (owners.length < 2) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-700 flex items-center justify-center">
            <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">Not Enough Owners</h3>
          <p className="text-slate-400 max-w-md mx-auto">
            You need at least 2 owners to compare head-to-head records. Import league data to get started.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white">Head-to-Head Rivalry</h2>
        <p className="text-slate-400">Compare all-time records between two owners</p>
      </div>

      {/* Owner Selection */}
      <div className="bg-slate-800/50 rounded-xl p-6 mb-6 border border-slate-700/50">
        <div className="flex flex-col sm:flex-row items-end gap-4">
          <OwnerSelect
            owners={owners}
            selectedId={owner1Id}
            onChange={setOwner1Id}
            excludeId={owner2Id}
            label="Select First Owner"
          />

          {/* Swap Button */}
          <button
            onClick={handleSwapOwners}
            disabled={owner1Id === null || owner2Id === null}
            className="p-3 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
            title="Swap owners"
          >
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
          </button>

          <OwnerSelect
            owners={owners}
            selectedId={owner2Id}
            onChange={setOwner2Id}
            excludeId={owner1Id}
            label="Select Second Owner"
          />
        </div>
      </div>

      {/* Loading State */}
      {h2hLoading && (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
        </div>
      )}

      {/* Error State */}
      {h2hError && (
        <div className="bg-red-900/30 border border-red-600 rounded-lg p-4">
          <p className="text-red-400">{h2hError}</p>
        </div>
      )}

      {/* No Selection State */}
      {!h2hLoading && !h2hError && !headToHead && (owner1Id === null || owner2Id === null) && (
        <div className="text-center py-12 bg-slate-800/30 rounded-xl border border-slate-700/50">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-700 flex items-center justify-center">
            <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">Select Two Owners</h3>
          <p className="text-slate-400 max-w-md mx-auto">
            Choose two owners from the dropdowns above to see their head-to-head rivalry history.
          </p>
        </div>
      )}

      {/* Head-to-Head Results */}
      {headToHead && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="flex flex-col sm:flex-row gap-4">
            <OwnerCard
              owner={headToHead.owner1}
              wins={headToHead.owner1_wins}
              avgScore={headToHead.owner1_avg_score}
              isLeading={headToHead.owner1_wins > headToHead.owner2_wins}
              position="left"
            />

            {/* VS Badge */}
            <div className="flex items-center justify-center">
              <div className="w-16 h-16 rounded-full bg-slate-800 border-2 border-slate-600 flex items-center justify-center">
                <span className="text-lg font-bold text-slate-400">VS</span>
              </div>
            </div>

            <OwnerCard
              owner={headToHead.owner2}
              wins={headToHead.owner2_wins}
              avgScore={headToHead.owner2_avg_score}
              isLeading={headToHead.owner2_wins > headToHead.owner1_wins}
              position="right"
            />
          </div>

          {/* Overall Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-slate-800/50 rounded-lg p-4 text-center border border-slate-700/50">
              <div className="text-2xl font-bold text-white">{headToHead.total_matchups}</div>
              <div className="text-xs text-slate-400 uppercase tracking-wide">Total Matchups</div>
            </div>

            <div className="bg-slate-800/50 rounded-lg p-4 text-center border border-slate-700/50">
              <div className="text-2xl font-bold text-slate-300">{headToHead.ties}</div>
              <div className="text-xs text-slate-400 uppercase tracking-wide">Ties</div>
            </div>

            <div className="bg-purple-900/30 rounded-lg p-4 text-center border border-purple-700/50">
              <div className="text-2xl font-bold text-purple-400">{headToHead.playoff_matchups}</div>
              <div className="text-xs text-slate-400 uppercase tracking-wide">Playoff Matchups</div>
            </div>

            <div className="bg-purple-900/30 rounded-lg p-4 text-center border border-purple-700/50">
              <div className="text-2xl font-bold text-white">
                {headToHead.owner1_playoff_wins}-{headToHead.owner2_playoff_wins}
              </div>
              <div className="text-xs text-slate-400 uppercase tracking-wide">Playoff Record</div>
            </div>
          </div>

          {/* Matchup History */}
          {headToHead.matchups.length > 0 ? (
            <div className="bg-slate-800/30 rounded-xl border border-slate-700/50 overflow-hidden">
              <div className="p-4 border-b border-slate-700/50">
                <h3 className="text-lg font-semibold text-white">Matchup History</h3>
                <p className="text-sm text-slate-400">
                  {headToHead.matchups.length} matchup{headToHead.matchups.length !== 1 ? 's' : ''} found
                </p>
              </div>

              <div className="max-h-96 overflow-y-auto">
                <div className="p-4 space-y-2">
                  {headToHead.matchups.map((matchup, index) => (
                    <MatchupRow
                      key={`${matchup.year}-${matchup.week}-${index}`}
                      matchup={matchup}
                      owner1Name={headToHead.owner1.display_name || headToHead.owner1.name}
                      owner2Name={headToHead.owner2.display_name || headToHead.owner2.name}
                      owner1Id={headToHead.owner1.id}
                    />
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 bg-slate-800/30 rounded-xl border border-slate-700/50">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-700 flex items-center justify-center">
                <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">No Matchups Found</h3>
              <p className="text-slate-400 max-w-md mx-auto">
                These owners haven't played against each other yet.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default HeadToHead;

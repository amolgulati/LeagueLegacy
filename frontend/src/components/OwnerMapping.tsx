/**
 * Owner Mapping Component
 *
 * Provides UI for:
 * - Viewing all owners and their platform mappings
 * - Linking Yahoo and Sleeper users as the same owner
 * - Merging two separate owners into one
 */

import { useState, useEffect } from 'react';
import type { Owner, OwnerStats } from '../types/owner';
import {
  fetchOwners,
  fetchUnmappedOwners,
  fetchOwnerStats,
  updateOwnerMapping,
  mergeOwners,
} from '../api/owners';

interface OwnerCardProps {
  owner: Owner;
  stats?: OwnerStats;
  isSelected?: boolean;
  onSelect?: (owner: Owner) => void;
  onViewStats?: (owner: Owner) => void;
}

function OwnerCard({ owner, stats, isSelected, onSelect, onViewStats }: OwnerCardProps) {
  const isMapped = owner.sleeper_user_id && owner.yahoo_user_id;

  return (
    <div
      className={`p-4 rounded-lg border transition-all cursor-pointer ${
        isSelected
          ? 'border-blue-500 bg-blue-900/30'
          : isMapped
          ? 'border-green-600 bg-slate-800'
          : 'border-yellow-600 bg-slate-800'
      }`}
      onClick={() => onSelect?.(owner)}
    >
      <div className="flex items-center gap-3 mb-3">
        {owner.avatar_url ? (
          <img
            src={owner.avatar_url}
            alt={owner.name}
            className="w-12 h-12 rounded-full"
          />
        ) : (
          <div className="w-12 h-12 rounded-full bg-slate-600 flex items-center justify-center">
            <span className="text-xl font-bold text-slate-300">
              {owner.name.charAt(0).toUpperCase()}
            </span>
          </div>
        )}
        <div>
          <h3 className="text-white font-semibold">{owner.name}</h3>
          {owner.display_name && (
            <p className="text-slate-400 text-sm">{owner.display_name}</p>
          )}
        </div>
      </div>

      <div className="space-y-1 text-sm">
        <div className="flex items-center gap-2">
          <span className={owner.sleeper_user_id ? 'text-green-400' : 'text-red-400'}>
            {owner.sleeper_user_id ? '✓' : '✗'}
          </span>
          <span className="text-slate-300">Sleeper:</span>
          <span className="text-slate-400 truncate">
            {owner.sleeper_user_id || 'Not linked'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className={owner.yahoo_user_id ? 'text-green-400' : 'text-red-400'}>
            {owner.yahoo_user_id ? '✓' : '✗'}
          </span>
          <span className="text-slate-300">Yahoo:</span>
          <span className="text-slate-400 truncate">
            {owner.yahoo_user_id || 'Not linked'}
          </span>
        </div>
      </div>

      {stats && (
        <div className="mt-3 pt-3 border-t border-slate-700 grid grid-cols-3 gap-2 text-center text-sm">
          <div>
            <p className="text-slate-400">Record</p>
            <p className="text-white font-semibold">
              {stats.total_wins}-{stats.total_losses}
            </p>
          </div>
          <div>
            <p className="text-slate-400">Playoffs</p>
            <p className="text-white font-semibold">{stats.playoff_appearances}</p>
          </div>
          <div>
            <p className="text-slate-400">Titles</p>
            <p className="text-yellow-400 font-semibold">{stats.championships}</p>
          </div>
        </div>
      )}

      {onViewStats && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onViewStats(owner);
          }}
          className="mt-3 w-full py-2 px-3 bg-slate-700 hover:bg-slate-600 rounded text-sm text-slate-300"
        >
          View Stats
        </button>
      )}
    </div>
  );
}

interface LinkPlatformModalProps {
  owner: Owner;
  platform: 'sleeper' | 'yahoo';
  onClose: () => void;
  onSave: (userId: string) => Promise<void>;
}

function LinkPlatformModal({ owner, platform, onClose, onSave }: LinkPlatformModalProps) {
  const [userId, setUserId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userId.trim()) return;

    setLoading(true);
    setError(null);

    try {
      await onSave(userId.trim());
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to link platform');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-bold text-white mb-4">
          Link {platform === 'sleeper' ? 'Sleeper' : 'Yahoo'} Account
        </h2>
        <p className="text-slate-400 mb-4">
          Link a {platform === 'sleeper' ? 'Sleeper' : 'Yahoo'} user ID to{' '}
          <strong className="text-white">{owner.name}</strong>
        </p>

        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder={`Enter ${platform} user ID`}
            className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
          />

          {error && (
            <p className="mt-2 text-red-400 text-sm">{error}</p>
          )}

          <div className="mt-4 flex gap-3 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-slate-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !userId.trim()}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded text-white disabled:opacity-50"
            >
              {loading ? 'Linking...' : 'Link Account'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

interface MergeOwnersModalProps {
  primaryOwner: Owner;
  secondaryOwner: Owner;
  onClose: () => void;
  onMerge: () => Promise<void>;
}

function MergeOwnersModal({
  primaryOwner,
  secondaryOwner,
  onClose,
  onMerge,
}: MergeOwnersModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleMerge = async () => {
    setLoading(true);
    setError(null);

    try {
      await onMerge();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to merge owners');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-lg p-6 max-w-lg w-full mx-4">
        <h2 className="text-xl font-bold text-white mb-4">Merge Owners</h2>
        <p className="text-slate-400 mb-4">
          This will merge <strong className="text-red-400">{secondaryOwner.name}</strong>{' '}
          into <strong className="text-green-400">{primaryOwner.name}</strong>.
        </p>

        <div className="bg-slate-700 rounded-lg p-4 mb-4">
          <h3 className="text-white font-semibold mb-2">What will happen:</h3>
          <ul className="text-slate-300 text-sm space-y-1">
            <li>
              • All teams from "{secondaryOwner.name}" will be transferred to "
              {primaryOwner.name}"
            </li>
            <li>
              • Platform IDs will be merged (primary's IDs take precedence)
            </li>
            <li>• "{secondaryOwner.name}" will be deleted</li>
          </ul>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="p-3 bg-green-900/30 border border-green-600 rounded">
            <p className="text-xs text-green-400 mb-1">Keep (Primary)</p>
            <p className="text-white font-semibold">{primaryOwner.name}</p>
          </div>
          <div className="p-3 bg-red-900/30 border border-red-600 rounded">
            <p className="text-xs text-red-400 mb-1">Delete (Secondary)</p>
            <p className="text-white font-semibold">{secondaryOwner.name}</p>
          </div>
        </div>

        {error && <p className="mb-4 text-red-400 text-sm">{error}</p>}

        <div className="flex gap-3 justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-slate-300"
          >
            Cancel
          </button>
          <button
            onClick={handleMerge}
            disabled={loading}
            className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded text-white disabled:opacity-50"
          >
            {loading ? 'Merging...' : 'Confirm Merge'}
          </button>
        </div>
      </div>
    </div>
  );
}

export function OwnerMapping() {
  const [owners, setOwners] = useState<Owner[]>([]);
  const [unmappedOwners, setUnmappedOwners] = useState<Owner[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selected owners for merging
  const [selectedOwners, setSelectedOwners] = useState<Owner[]>([]);
  const [showMergeModal, setShowMergeModal] = useState(false);

  // Link platform modal
  const [linkTarget, setLinkTarget] = useState<{
    owner: Owner;
    platform: 'sleeper' | 'yahoo';
  } | null>(null);

  // Stats modal
  const [statsOwner, setStatsOwner] = useState<Owner | null>(null);
  const [ownerStats, setOwnerStats] = useState<OwnerStats | null>(null);

  // Filter mode
  const [showOnlyUnmapped, setShowOnlyUnmapped] = useState(false);

  const loadOwners = async () => {
    setLoading(true);
    setError(null);
    try {
      const [allOwners, unmapped] = await Promise.all([
        fetchOwners(),
        fetchUnmappedOwners(),
      ]);
      setOwners(allOwners);
      setUnmappedOwners(unmapped);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load owners');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOwners();
  }, []);

  const handleSelectOwner = (owner: Owner) => {
    if (selectedOwners.find((o) => o.id === owner.id)) {
      setSelectedOwners(selectedOwners.filter((o) => o.id !== owner.id));
    } else if (selectedOwners.length < 2) {
      setSelectedOwners([...selectedOwners, owner]);
    }
  };

  const handleLinkPlatform = async (userId: string) => {
    if (!linkTarget) return;

    await updateOwnerMapping(linkTarget.owner.id, {
      [linkTarget.platform === 'sleeper' ? 'sleeper_user_id' : 'yahoo_user_id']:
        userId,
    });

    await loadOwners();
    setSelectedOwners([]);
  };

  const handleMergeOwners = async () => {
    if (selectedOwners.length !== 2) return;

    await mergeOwners({
      primary_owner_id: selectedOwners[0].id,
      secondary_owner_id: selectedOwners[1].id,
    });

    await loadOwners();
    setSelectedOwners([]);
  };

  const handleViewStats = async (owner: Owner) => {
    setStatsOwner(owner);
    try {
      const stats = await fetchOwnerStats(owner.id);
      setOwnerStats(stats);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const displayOwners = showOnlyUnmapped ? unmappedOwners : owners;

  if (loading && owners.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-slate-400">Loading owners...</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white mb-2">Owner Mapping</h1>
        <p className="text-slate-400">
          Link Yahoo and Sleeper accounts to the same owner to aggregate stats
          across platforms.
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-900/30 border border-red-600 rounded-lg">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Controls */}
      <div className="mb-6 flex flex-wrap gap-4 items-center">
        <label className="flex items-center gap-2 text-slate-300">
          <input
            type="checkbox"
            checked={showOnlyUnmapped}
            onChange={(e) => setShowOnlyUnmapped(e.target.checked)}
            className="rounded bg-slate-700 border-slate-600"
          />
          Show only unmapped owners ({unmappedOwners.length})
        </label>

        {selectedOwners.length === 2 && (
          <button
            onClick={() => setShowMergeModal(true)}
            className="ml-auto px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded text-white"
          >
            Merge Selected Owners
          </button>
        )}

        {selectedOwners.length > 0 && selectedOwners.length < 2 && (
          <p className="ml-auto text-slate-400 text-sm">
            Select another owner to merge
          </p>
        )}
      </div>

      {/* Owner Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {displayOwners.map((owner) => (
          <OwnerCard
            key={owner.id}
            owner={owner}
            isSelected={selectedOwners.some((o) => o.id === owner.id)}
            onSelect={handleSelectOwner}
            onViewStats={handleViewStats}
          />
        ))}
      </div>

      {displayOwners.length === 0 && (
        <div className="text-center py-12">
          <p className="text-slate-400">No owners found</p>
        </div>
      )}

      {/* Quick Actions for Selected Owner */}
      {selectedOwners.length === 1 && (
        <div className="fixed bottom-6 right-6 bg-slate-800 border border-slate-700 rounded-lg p-4 shadow-xl">
          <p className="text-white font-semibold mb-2">
            {selectedOwners[0].name}
          </p>
          <div className="flex gap-2">
            {!selectedOwners[0].sleeper_user_id && (
              <button
                onClick={() =>
                  setLinkTarget({ owner: selectedOwners[0], platform: 'sleeper' })
                }
                className="px-3 py-1 bg-purple-600 hover:bg-purple-500 rounded text-sm text-white"
              >
                Link Sleeper
              </button>
            )}
            {!selectedOwners[0].yahoo_user_id && (
              <button
                onClick={() =>
                  setLinkTarget({ owner: selectedOwners[0], platform: 'yahoo' })
                }
                className="px-3 py-1 bg-purple-600 hover:bg-purple-500 rounded text-sm text-white"
              >
                Link Yahoo
              </button>
            )}
          </div>
        </div>
      )}

      {/* Modals */}
      {linkTarget && (
        <LinkPlatformModal
          owner={linkTarget.owner}
          platform={linkTarget.platform}
          onClose={() => setLinkTarget(null)}
          onSave={handleLinkPlatform}
        />
      )}

      {showMergeModal && selectedOwners.length === 2 && (
        <MergeOwnersModal
          primaryOwner={selectedOwners[0]}
          secondaryOwner={selectedOwners[1]}
          onClose={() => setShowMergeModal(false)}
          onMerge={handleMergeOwners}
        />
      )}

      {/* Stats Modal */}
      {statsOwner && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold text-white mb-4">
              {statsOwner.name}'s Career Stats
            </h2>

            {ownerStats ? (
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-700 rounded p-3 text-center">
                  <p className="text-slate-400 text-sm">Total Record</p>
                  <p className="text-white text-xl font-bold">
                    {ownerStats.total_wins}-{ownerStats.total_losses}
                    {ownerStats.total_ties > 0 && `-${ownerStats.total_ties}`}
                  </p>
                </div>
                <div className="bg-slate-700 rounded p-3 text-center">
                  <p className="text-slate-400 text-sm">Seasons Played</p>
                  <p className="text-white text-xl font-bold">
                    {ownerStats.seasons_played}
                  </p>
                </div>
                <div className="bg-slate-700 rounded p-3 text-center">
                  <p className="text-slate-400 text-sm">Total Points</p>
                  <p className="text-white text-xl font-bold">
                    {ownerStats.total_points.toLocaleString()}
                  </p>
                </div>
                <div className="bg-slate-700 rounded p-3 text-center">
                  <p className="text-slate-400 text-sm">Playoff Apps</p>
                  <p className="text-white text-xl font-bold">
                    {ownerStats.playoff_appearances}
                  </p>
                </div>
                <div className="bg-yellow-900/30 border border-yellow-600 rounded p-3 text-center col-span-2">
                  <p className="text-yellow-400 text-sm">Championships</p>
                  <p className="text-yellow-300 text-2xl font-bold">
                    {ownerStats.championships}
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-slate-400">Loading stats...</p>
            )}

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => {
                  setStatsOwner(null);
                  setOwnerStats(null);
                }}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-slate-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default OwnerMapping;

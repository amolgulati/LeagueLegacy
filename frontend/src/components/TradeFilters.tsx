/**
 * TradeFilters Component
 *
 * Provides filter controls for trades by owner and season.
 */

interface Owner {
  id: number;
  name: string;
  display_name: string | null;
}

interface Season {
  id: number;
  year: number;
  league_name: string;
}

interface TradeFiltersProps {
  owners: Owner[];
  seasons: Season[];
  selectedOwnerId: number | null;
  selectedSeasonId: number | null;
  onOwnerChange: (ownerId: number | null) => void;
  onSeasonChange: (seasonId: number | null) => void;
  loading?: boolean;
}

export function TradeFilters({
  owners,
  seasons,
  selectedOwnerId,
  selectedSeasonId,
  onOwnerChange,
  onSeasonChange,
  loading,
}: TradeFiltersProps) {
  // Sort owners alphabetically
  const sortedOwners = [...owners].sort((a, b) =>
    (a.display_name || a.name).localeCompare(b.display_name || b.name)
  );

  // Sort seasons by year (newest first)
  const sortedSeasons = [...seasons].sort((a, b) => b.year - a.year);

  const hasActiveFilters = selectedOwnerId !== null || selectedSeasonId !== null;

  const clearFilters = () => {
    onOwnerChange(null);
    onSeasonChange(null);
  };

  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Owner Filter */}
        <div className="flex-1">
          <label htmlFor="owner-filter" className="block text-sm font-medium text-slate-400 mb-2">
            Filter by Owner
          </label>
          <select
            id="owner-filter"
            value={selectedOwnerId ?? ''}
            onChange={(e) => onOwnerChange(e.target.value ? parseInt(e.target.value) : null)}
            disabled={loading}
            className="w-full px-4 py-2 rounded-lg bg-slate-700 border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
          >
            <option value="">All Owners</option>
            {sortedOwners.map((owner) => (
              <option key={owner.id} value={owner.id}>
                {owner.display_name || owner.name}
              </option>
            ))}
          </select>
        </div>

        {/* Season Filter */}
        <div className="flex-1">
          <label htmlFor="season-filter" className="block text-sm font-medium text-slate-400 mb-2">
            Filter by Season
          </label>
          <select
            id="season-filter"
            value={selectedSeasonId ?? ''}
            onChange={(e) => onSeasonChange(e.target.value ? parseInt(e.target.value) : null)}
            disabled={loading}
            className="w-full px-4 py-2 rounded-lg bg-slate-700 border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
          >
            <option value="">All Seasons</option>
            {sortedSeasons.map((season) => (
              <option key={season.id} value={season.id}>
                {season.year} - {season.league_name}
              </option>
            ))}
          </select>
        </div>

        {/* Clear Filters Button */}
        {hasActiveFilters && (
          <div className="flex items-end">
            <button
              onClick={clearFilters}
              className="px-4 py-2 rounded-lg bg-slate-600 hover:bg-slate-500 text-white text-sm font-medium transition-colors flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              Clear
            </button>
          </div>
        )}
      </div>

      {/* Active Filters Display */}
      {hasActiveFilters && (
        <div className="mt-4 flex flex-wrap gap-2">
          {selectedOwnerId && (
            <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-blue-600/30 text-blue-300 text-sm">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              {sortedOwners.find((o) => o.id === selectedOwnerId)?.display_name ||
                sortedOwners.find((o) => o.id === selectedOwnerId)?.name ||
                'Unknown'}
              <button
                onClick={() => onOwnerChange(null)}
                className="ml-1 hover:text-white transition-colors"
                aria-label="Remove owner filter"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </span>
          )}
          {selectedSeasonId && (
            <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-purple-600/30 text-purple-300 text-sm">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              {sortedSeasons.find((s) => s.id === selectedSeasonId)?.year} -{' '}
              {sortedSeasons.find((s) => s.id === selectedSeasonId)?.league_name}
              <button
                onClick={() => onSeasonChange(null)}
                className="ml-1 hover:text-white transition-colors"
                aria-label="Remove season filter"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </span>
          )}
        </div>
      )}
    </div>
  );
}

export default TradeFilters;

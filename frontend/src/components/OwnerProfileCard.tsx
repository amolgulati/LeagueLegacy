/**
 * Owner Profile Card Component
 *
 * Displays an owner's profile with:
 * - Avatar and name
 * - Career record (W-L-T)
 * - Championships count with trophy icons
 * - Playoff appearances
 * - Win percentage
 *
 * Uses a visually appealing card design with gradients and animations.
 */

import type { OwnerWithStats } from '../types/owner';

interface OwnerProfileCardProps {
  owner: OwnerWithStats;
  rank: number;
  onClick?: () => void;
}

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

  // Use character codes to pick a consistent gradient
  const hash = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return gradients[hash % gradients.length];
}

/**
 * Formats the win percentage as a string
 */
function formatWinPercentage(percentage: number): string {
  return `${percentage.toFixed(1)}%`;
}

/**
 * Gets the rank badge style based on position
 */
function getRankBadgeStyle(rank: number): string {
  switch (rank) {
    case 1:
      return 'bg-gradient-to-br from-yellow-400 to-amber-500 text-yellow-900 shadow-yellow-500/30';
    case 2:
      return 'bg-gradient-to-br from-slate-300 to-slate-400 text-slate-700 shadow-slate-400/30';
    case 3:
      return 'bg-gradient-to-br from-orange-400 to-amber-600 text-orange-900 shadow-orange-400/30';
    default:
      return 'bg-slate-700 text-slate-300';
  }
}

export function OwnerProfileCard({ owner, rank, onClick }: OwnerProfileCardProps) {
  const displayName = owner.display_name || owner.name;
  const avatarGradient = getAvatarGradient(owner.name);
  const record = `${owner.total_wins}-${owner.total_losses}${owner.total_ties > 0 ? `-${owner.total_ties}` : ''}`;

  return (
    <div
      onClick={onClick}
      className={`
        relative overflow-hidden rounded-xl
        bg-gradient-to-br from-slate-800 to-slate-900
        border border-slate-700/50
        shadow-lg shadow-slate-900/50
        hover:shadow-xl hover:shadow-slate-900/70
        hover:border-slate-600/50
        transition-all duration-300 ease-out
        ${onClick ? 'cursor-pointer hover:scale-[1.02]' : ''}
      `}
    >
      {/* Championship banner for champions */}
      {owner.championships > 0 && (
        <div className="absolute top-0 right-0 w-24 h-24 overflow-hidden">
          <div className="absolute top-3 -right-8 w-32 transform rotate-45 bg-gradient-to-r from-yellow-500 to-amber-600 text-center py-1 text-xs font-bold text-yellow-900 shadow-lg">
            {owner.championships}x CHAMP
          </div>
        </div>
      )}

      {/* Rank badge */}
      <div className={`
        absolute top-4 left-4 w-8 h-8 rounded-full
        flex items-center justify-center text-sm font-bold
        shadow-lg ${getRankBadgeStyle(rank)}
      `}>
        {rank}
      </div>

      <div className="p-6 pt-8">
        {/* Avatar and Name */}
        <div className="flex flex-col items-center mb-6">
          {/* Avatar */}
          <div className="relative mb-4">
            {owner.avatar_url ? (
              <img
                src={owner.avatar_url}
                alt={displayName}
                className="w-20 h-20 rounded-full object-cover ring-4 ring-slate-700 shadow-lg"
              />
            ) : (
              <div className={`
                w-20 h-20 rounded-full
                bg-gradient-to-br ${avatarGradient}
                flex items-center justify-center
                text-3xl font-bold text-white
                ring-4 ring-slate-700 shadow-lg
              `}>
                {displayName.charAt(0).toUpperCase()}
              </div>
            )}

            {/* Trophy icon for champions */}
            {owner.championships > 0 && (
              <div className="absolute -bottom-1 -right-1 w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center shadow-lg border-2 border-slate-800">
                <svg className="w-4 h-4 text-yellow-900" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 2a1 1 0 00-1 1v1H6a1 1 0 00-1 1v3a3 3 0 003 3h.17A5.986 5.986 0 0110 12.17V15H8a1 1 0 000 2h4a1 1 0 000-2h-2v-2.83A5.986 5.986 0 0011.83 11H12a3 3 0 003-3V5a1 1 0 00-1-1h-3V3a1 1 0 00-1-1zM7 5h6v3a1 1 0 01-1 1H8a1 1 0 01-1-1V5z" clipRule="evenodd" />
                </svg>
              </div>
            )}
          </div>

          {/* Name */}
          <h3 className="text-xl font-bold text-white text-center truncate max-w-full">
            {displayName}
          </h3>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          {/* Record */}
          <div className="text-center p-3 rounded-lg bg-slate-800/50">
            <div className="text-2xl font-mono font-bold text-white">{record}</div>
            <div className="text-xs text-slate-400 uppercase tracking-wide">Record</div>
          </div>

          {/* Win Percentage */}
          <div className="text-center p-3 rounded-lg bg-slate-800/50">
            <div className="text-2xl font-bold text-white">{formatWinPercentage(owner.win_percentage)}</div>
            <div className="text-xs text-slate-400 uppercase tracking-wide">Win %</div>
          </div>
        </div>

        {/* Additional Stats */}
        <div className="grid grid-cols-3 gap-2">
          {/* Championships */}
          <div className="text-center p-2 rounded-lg bg-slate-800/50">
            <div className={`text-lg font-bold flex items-center justify-center gap-1 ${owner.championships > 0 ? 'text-yellow-400' : 'text-slate-400'}`}>
              {owner.championships > 0 && (
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 2a1 1 0 00-1 1v1H6a1 1 0 00-1 1v3a3 3 0 003 3h.17A5.986 5.986 0 0110 12.17V15H8a1 1 0 000 2h4a1 1 0 000-2h-2v-2.83A5.986 5.986 0 0011.83 11H12a3 3 0 003-3V5a1 1 0 00-1-1h-3V3a1 1 0 00-1-1zM7 5h6v3a1 1 0 01-1 1H8a1 1 0 01-1-1V5z" clipRule="evenodd" />
                </svg>
              )}
              {owner.championships}
            </div>
            <div className="text-xs text-slate-400 uppercase tracking-wide">Titles</div>
          </div>

          {/* Playoff Appearances */}
          <div className="text-center p-2 rounded-lg bg-slate-800/50">
            <div className={`text-lg font-bold ${owner.playoff_appearances > 0 ? 'text-emerald-400' : 'text-slate-400'}`}>
              {owner.playoff_appearances}
            </div>
            <div className="text-xs text-slate-400 uppercase tracking-wide">Playoffs</div>
          </div>

          {/* Seasons Played */}
          <div className="text-center p-2 rounded-lg bg-slate-800/50">
            <div className="text-lg font-bold text-blue-400">
              {owner.seasons_played}
            </div>
            <div className="text-xs text-slate-400 uppercase tracking-wide">Seasons</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default OwnerProfileCard;

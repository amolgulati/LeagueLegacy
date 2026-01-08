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
 * Supports theming via CSS variables.
 */

import type { OwnerWithStats } from '../types/owner';

interface OwnerProfileCardProps {
  owner: OwnerWithStats;
  rank: number;
  onClick?: () => void;
}

/**
 * Generates a consistent gradient style based on owner name
 * Uses CSS variables with fallback colors for theme-awareness
 */
function getAvatarGradientStyle(name: string): React.CSSProperties {
  // Array of gradient color pairs that work with all themes
  const gradients = [
    { from: 'var(--chart-1)', to: 'var(--accent-secondary)' },
    { from: 'var(--success)', to: '#14b8a6' },
    { from: 'var(--chart-4)', to: 'var(--error)' },
    { from: '#ec4899', to: '#f43f5e' },
    { from: '#6366f1', to: 'var(--chart-1)' },
    { from: 'var(--trophy-gold)', to: 'var(--chart-4)' },
    { from: '#06b6d4', to: 'var(--chart-1)' },
    { from: '#8b5cf6', to: 'var(--accent-secondary)' },
  ];

  // Use character codes to pick a consistent gradient
  const hash = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const gradient = gradients[hash % gradients.length];
  return {
    background: `linear-gradient(to bottom right, ${gradient.from}, ${gradient.to})`,
  };
}

/**
 * Formats the win percentage as a string
 */
function formatWinPercentage(percentage: number): string {
  return `${percentage.toFixed(1)}%`;
}

/**
 * Gets the rank badge inline style based on position
 * Uses CSS variables for theme-awareness
 */
function getRankBadgeStyle(rank: number): React.CSSProperties {
  switch (rank) {
    case 1:
      return {
        background: `linear-gradient(to bottom right, var(--trophy-gold), #f59e0b)`,
        color: 'var(--text-inverted)',
        boxShadow: '0 4px 6px -1px rgba(251, 191, 36, 0.3)',
      };
    case 2:
      return {
        background: `linear-gradient(to bottom right, var(--trophy-silver), #9ca3af)`,
        color: 'var(--text-inverted)',
        boxShadow: '0 4px 6px -1px rgba(156, 163, 175, 0.3)',
      };
    case 3:
      return {
        background: `linear-gradient(to bottom right, var(--trophy-bronze), #d97706)`,
        color: 'var(--text-inverted)',
        boxShadow: '0 4px 6px -1px rgba(249, 115, 22, 0.3)',
      };
    default:
      return {
        backgroundColor: 'var(--bg-tertiary)',
        color: 'var(--text-secondary)',
      };
  }
}

export function OwnerProfileCard({ owner, rank, onClick }: OwnerProfileCardProps) {
  const displayName = owner.display_name || owner.name;
  const avatarGradientStyle = getAvatarGradientStyle(owner.name);
  const record = `${owner.total_wins}-${owner.total_losses}${owner.total_ties > 0 ? `-${owner.total_ties}` : ''}`;

  return (
    <div
      onClick={onClick}
      className={`
        relative overflow-hidden rounded-xl
        shadow-lg
        hover:shadow-xl
        transition-all duration-300 ease-out
        ${onClick ? 'cursor-pointer hover:scale-[1.02]' : ''}
      `}
      style={{
        background: 'linear-gradient(to bottom right, var(--bg-card), var(--bg-primary))',
        border: '1px solid var(--border-primary)',
      }}
    >
      {/* Championship banner for champions */}
      {owner.championships > 0 && (
        <div className="absolute top-0 right-0 w-24 h-24 overflow-hidden">
          <div
            className="absolute top-3 -right-8 w-32 transform rotate-45 text-center py-1 text-xs font-bold shadow-lg"
            style={{
              background: 'linear-gradient(to right, var(--trophy-gold), #f59e0b)',
              color: 'var(--text-inverted)',
            }}
          >
            {owner.championships}x CHAMP
          </div>
        </div>
      )}

      {/* Rank badge */}
      <div
        className="absolute top-4 left-4 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shadow-lg"
        style={getRankBadgeStyle(rank)}
      >
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
                className="w-20 h-20 rounded-full object-cover shadow-lg"
                style={{ boxShadow: '0 0 0 4px var(--border-primary)' }}
              />
            ) : (
              <div
                className="w-20 h-20 rounded-full flex items-center justify-center text-3xl font-bold shadow-lg"
                style={{
                  ...avatarGradientStyle,
                  color: 'white',
                  boxShadow: '0 0 0 4px var(--border-primary)',
                }}
              >
                {displayName.charAt(0).toUpperCase()}
              </div>
            )}

            {/* Trophy icon for champions */}
            {owner.championships > 0 && (
              <div
                className="absolute -bottom-1 -right-1 w-8 h-8 rounded-full flex items-center justify-center shadow-lg"
                style={{
                  backgroundColor: 'var(--trophy-gold)',
                  border: '2px solid var(--bg-card)',
                }}
              >
                <svg className="w-4 h-4" style={{ color: 'var(--text-inverted)' }} fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 2a1 1 0 00-1 1v1H6a1 1 0 00-1 1v3a3 3 0 003 3h.17A5.986 5.986 0 0110 12.17V15H8a1 1 0 000 2h4a1 1 0 000-2h-2v-2.83A5.986 5.986 0 0011.83 11H12a3 3 0 003-3V5a1 1 0 00-1-1h-3V3a1 1 0 00-1-1zM7 5h6v3a1 1 0 01-1 1H8a1 1 0 01-1-1V5z" clipRule="evenodd" />
                </svg>
              </div>
            )}
          </div>

          {/* Name */}
          <h3 className="text-xl font-bold text-center truncate max-w-full" style={{ color: 'var(--text-primary)' }}>
            {displayName}
          </h3>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          {/* Record */}
          <div className="text-center p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
            <div className="text-2xl font-mono font-bold" style={{ color: 'var(--text-primary)' }}>{record}</div>
            <div className="text-xs uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>Record</div>
          </div>

          {/* Win Percentage */}
          <div className="text-center p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
            <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{formatWinPercentage(owner.win_percentage)}</div>
            <div className="text-xs uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>Win %</div>
          </div>
        </div>

        {/* Additional Stats */}
        <div className="grid grid-cols-3 gap-2">
          {/* Championships */}
          <div className="text-center p-2 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
            <div
              className="text-lg font-bold flex items-center justify-center gap-1"
              style={{ color: owner.championships > 0 ? 'var(--trophy-gold)' : 'var(--text-muted)' }}
            >
              {owner.championships > 0 && (
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 2a1 1 0 00-1 1v1H6a1 1 0 00-1 1v3a3 3 0 003 3h.17A5.986 5.986 0 0110 12.17V15H8a1 1 0 000 2h4a1 1 0 000-2h-2v-2.83A5.986 5.986 0 0011.83 11H12a3 3 0 003-3V5a1 1 0 00-1-1h-3V3a1 1 0 00-1-1zM7 5h6v3a1 1 0 01-1 1H8a1 1 0 01-1-1V5z" clipRule="evenodd" />
                </svg>
              )}
              {owner.championships}
            </div>
            <div className="text-xs uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>Titles</div>
          </div>

          {/* Playoff Appearances */}
          <div className="text-center p-2 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
            <div
              className="text-lg font-bold"
              style={{ color: owner.playoff_appearances > 0 ? 'var(--success)' : 'var(--text-muted)' }}
            >
              {owner.playoff_appearances}
            </div>
            <div className="text-xs uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>Playoffs</div>
          </div>

          {/* Seasons Played */}
          <div className="text-center p-2 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
            <div className="text-lg font-bold" style={{ color: 'var(--chart-1)' }}>
              {owner.seasons_played}
            </div>
            <div className="text-xs uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>Seasons</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default OwnerProfileCard;

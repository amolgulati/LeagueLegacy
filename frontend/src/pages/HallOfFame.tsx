import { useEffect, useState, useId } from 'react';
import { Confetti } from '../components/Confetti';
import { HeroSkeleton, CardSkeleton } from '../components/LoadingStates';
import { useTheme } from '../hooks/useTheme';

// ==================== Types ====================

interface ChampionOwner {
  id: number;
  name: string;
  display_name?: string;
  avatar_url?: string;
}

interface ChampionSeason {
  year: number;
  league_id: number;
  league_name: string;
  platform: string;
  team_name: string;
  record: string;
  points_for: number;
  champion: ChampionOwner;
  runner_up?: ChampionOwner;
}

interface ChampionshipCount {
  owner: ChampionOwner;
  championships: number;
  years: number[];
  leagues: string[];
}

interface PlacementCount {
  owner: ChampionOwner;
  count: number;
  years: number[];
  leagues: string[];
}

interface DynastyStreak {
  owner: ChampionOwner;
  streak: number;
  start_year: number;
  end_year: number;
  league_name: string;
}

interface HallOfFameData {
  champions_by_year: ChampionSeason[];
  championship_leaderboard: ChampionshipCount[];
  runner_up_leaderboard: PlacementCount[];
  third_place_leaderboard: PlacementCount[];
  dynasties: DynastyStreak[];
  total_seasons: number;
  unique_champions: number;
}

// ==================== Components ====================

// Get theme-aware trophy colors from CSS variables
const getTrophyColors = () => {
  const computedStyle = getComputedStyle(document.documentElement);
  const trophyGold = computedStyle.getPropertyValue('--trophy-gold').trim() || '#fbbf24';
  return {
    gold: trophyGold,
    goldDark: adjustColor(trophyGold, -30), // Darker gold for stroke
    goldMid: adjustColor(trophyGold, -15),  // Medium gold for gradient
    silver: computedStyle.getPropertyValue('--trophy-silver').trim() || '#9ca3af',
    bronze: computedStyle.getPropertyValue('--trophy-bronze').trim() || '#f97316',
    accentSecondary: computedStyle.getPropertyValue('--accent-secondary').trim() || '#8b5cf6',
  };
};

// Simple function to adjust a hex color brightness
const adjustColor = (hex: string, amount: number): string => {
  const clamp = (val: number) => Math.min(255, Math.max(0, val));
  let color = hex.replace('#', '');
  if (color.length === 3) {
    color = color.split('').map(c => c + c).join('');
  }
  const r = clamp(parseInt(color.substring(0, 2), 16) + amount);
  const g = clamp(parseInt(color.substring(2, 4), 16) + amount);
  const b = clamp(parseInt(color.substring(4, 6), 16) + amount);
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
};

// Large Trophy SVG for hero section - theme-aware
const LargeTrophyIcon = ({ className = "w-24 h-24", colors }: { className?: string; colors?: ReturnType<typeof getTrophyColors> }) => {
  const c = colors || getTrophyColors();
  const id = useId();
  const gradientId = `trophyGold-${id}`;
  const shineId = `trophyShine-${id}`;

  return (
    <svg className={className} viewBox="0 0 64 64" fill="none">
      <defs>
        <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={c.gold} />
          <stop offset="50%" stopColor={c.goldMid} />
          <stop offset="100%" stopColor={c.gold} />
        </linearGradient>
        <linearGradient id={shineId} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.5" />
          <stop offset="50%" stopColor="#FFFFFF" stopOpacity="0.2" />
          <stop offset="100%" stopColor="#FFFFFF" stopOpacity="0" />
        </linearGradient>
      </defs>
      {/* Trophy cup */}
      <path
        d="M16 12h32v4c0 12-6 22-16 24-10-2-16-12-16-24v-4z"
        fill={`url(#${gradientId})`}
        stroke={c.goldDark}
        strokeWidth="1"
      />
      {/* Shine effect */}
      <path
        d="M20 16h8v2c0 8-2 14-4 16-2-2-4-8-4-16v-2z"
        fill={`url(#${shineId})`}
      />
      {/* Handles */}
      <path
        d="M16 14h-4a8 8 0 0 0 0 16h4"
        fill="none"
        stroke={c.gold}
        strokeWidth="4"
        strokeLinecap="round"
      />
      <path
        d="M48 14h4a8 8 0 0 1 0 16h-4"
        fill="none"
        stroke={c.gold}
        strokeWidth="4"
        strokeLinecap="round"
      />
      {/* Base */}
      <path
        d="M28 40h8v4h-8z"
        fill={c.gold}
      />
      <path
        d="M24 44h16v2c0 2-2 4-4 4h-8c-2 0-4-2-4-4v-2z"
        fill={c.gold}
        stroke={c.goldDark}
        strokeWidth="1"
      />
      {/* Star on trophy */}
      <path
        d="M32 20l2 4 4 1-3 3 1 4-4-2-4 2 1-4-3-3 4-1z"
        fill={c.goldDark}
      />
    </svg>
  );
};

// Small trophy icon - theme-aware
const TrophyIcon = ({ className = "w-6 h-6", color = "text-yellow-500", style }: { className?: string; color?: string; style?: React.CSSProperties }) => (
  <svg className={`${className} ${color}`} style={style} fill="currentColor" viewBox="0 0 20 20">
    <path fillRule="evenodd" d="M5 2a2 2 0 00-2 2v1a2 2 0 002 2h1v1H5a3 3 0 00-3 3v6a3 3 0 003 3h10a3 3 0 003-3v-6a3 3 0 00-3-3h-1V7h1a2 2 0 002-2V4a2 2 0 00-2-2H5zm0 2h10v1H5V4zm3 4h4v1H8V8z" clipRule="evenodd" />
  </svg>
);

// Crown icon for champions - theme-aware
const CrownIcon = ({ className = "w-5 h-5", style }: { className?: string; style?: React.CSSProperties }) => (
  <svg className={className} style={style} viewBox="0 0 24 24" fill="currentColor">
    <path d="M5 16L3 5l5 5 4-6 4 6 5-5-2 11H5zm0 2h14v2H5v-2z" />
  </svg>
);

// Medal component for rankings - theme-aware
const RankMedal = ({ rank, colors }: { rank: number; colors?: ReturnType<typeof getTrophyColors> }) => {
  const c = colors || getTrophyColors();

  const getMedalStyle = () => {
    switch (rank) {
      case 1:
        return {
          background: `linear-gradient(135deg, ${c.gold} 0%, ${c.goldDark} 100%)`,
          color: '#1a1a1a',
          ring: c.gold,
        };
      case 2:
        return {
          background: `linear-gradient(135deg, ${c.silver} 0%, ${adjustColor(c.silver, -30)} 100%)`,
          color: '#1a1a1a',
          ring: c.silver,
        };
      case 3:
        return {
          background: `linear-gradient(135deg, ${c.bronze} 0%, ${adjustColor(c.bronze, -30)} 100%)`,
          color: '#fff',
          ring: c.bronze,
        };
      default:
        return {
          background: 'var(--bg-tertiary)',
          color: 'var(--text-primary)',
          ring: 'var(--border-secondary)',
        };
    }
  };

  const style = getMedalStyle();

  return (
    <span
      className="inline-flex items-center justify-center w-10 h-10 rounded-full font-bold text-lg shadow-lg ring-2"
      style={{
        background: style.background,
        color: style.color,
        ['--tw-ring-color' as string]: style.ring,
      }}
    >
      {rank}
    </span>
  );
};

// Avatar component with gradient fallback
const ChampionAvatar = ({ name, avatarUrl, size = "md" }: { name: string; avatarUrl?: string; size?: "sm" | "md" | "lg" }) => {
  const sizeClasses = {
    sm: "w-8 h-8 text-sm",
    md: "w-12 h-12 text-lg",
    lg: "w-20 h-20 text-3xl",
  };

  const initial = name.charAt(0).toUpperCase();
  const colorIndex = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % 8;
  const gradients = [
    'from-blue-500 to-purple-600',
    'from-green-500 to-teal-600',
    'from-orange-500 to-red-600',
    'from-pink-500 to-rose-600',
    'from-indigo-500 to-blue-600',
    'from-yellow-500 to-orange-600',
    'from-cyan-500 to-blue-600',
    'from-emerald-500 to-green-600',
  ];

  if (avatarUrl) {
    return (
      <img
        src={avatarUrl}
        alt={name}
        className={`${sizeClasses[size]} rounded-full object-cover ring-2 ring-yellow-500/50`}
      />
    );
  }

  return (
    <div
      className={`${sizeClasses[size]} rounded-full bg-gradient-to-br ${gradients[colorIndex]} flex items-center justify-center text-white font-bold ring-2 ring-yellow-500/50`}
    >
      {initial}
    </div>
  );
};

// Championship Year Card
const ChampionCard = ({ champion, isFirst, index }: { champion: ChampionSeason; isFirst: boolean; index: number }) => {
  return (
    <div
      className={`relative overflow-hidden rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-2xl hover-lift animate-card-entrance ${
        isFirst
          ? 'bg-gradient-to-br from-yellow-500/20 via-amber-500/10 to-orange-500/20 ring-2 ring-yellow-500/50'
          : 'bg-slate-800/80'
      }`}
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      {/* Decorative corner */}
      <div className="absolute top-0 right-0 w-16 h-16 overflow-hidden">
        <div className={`absolute -top-8 -right-8 w-16 h-16 transform rotate-45 ${
          isFirst ? 'bg-yellow-500' : 'bg-slate-700'
        }`} />
        <TrophyIcon className="absolute top-1 right-1 w-5 h-5 text-white" />
      </div>

      <div className="p-5">
        {/* Year header */}
        <div className="flex items-center gap-3 mb-4">
          <span className={`text-3xl font-bold ${isFirst ? 'text-yellow-400' : 'text-slate-300'}`}>
            {champion.year}
          </span>
          <span className="text-slate-500 text-sm">
            {champion.league_name}
          </span>
        </div>

        {/* Champion info */}
        <div className="flex items-center gap-4">
          <ChampionAvatar
            name={champion.champion.display_name || champion.champion.name}
            avatarUrl={champion.champion.avatar_url}
            size="lg"
          />
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <CrownIcon className="w-5 h-5 text-yellow-500" />
              <span className="text-xl font-bold text-white">
                {champion.champion.display_name || champion.champion.name}
              </span>
            </div>
            <div className="text-slate-400 text-sm mb-1">{champion.team_name}</div>
            <div className="flex items-center gap-3 text-sm">
              <span className="text-green-400 font-semibold">{champion.record}</span>
              <span className="text-slate-500">|</span>
              <span className="text-blue-400">{champion.points_for.toFixed(1)} pts</span>
            </div>
          </div>
        </div>

        {/* Runner-up */}
        {champion.runner_up && (
          <div className="mt-4 pt-4 border-t border-slate-700/50">
            <div className="flex items-center gap-2 text-slate-400 text-sm">
              <span className="text-slate-500">Runner-up:</span>
              <ChampionAvatar
                name={champion.runner_up.display_name || champion.runner_up.name}
                avatarUrl={champion.runner_up.avatar_url}
                size="sm"
              />
              <span>{champion.runner_up.display_name || champion.runner_up.name}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Leaderboard Row - theme-aware
const LeaderboardRow = ({ entry, rank, colors }: { entry: ChampionshipCount; rank: number; colors: ReturnType<typeof getTrophyColors> }) => {
  return (
    <div
      className="flex items-center gap-4 p-4 rounded-xl transition-all duration-300"
      style={{
        backgroundColor: rank <= 3 ? 'var(--bg-tertiary)' : 'transparent',
      }}
    >
      <RankMedal rank={rank} colors={colors} />

      <ChampionAvatar
        name={entry.owner.display_name || entry.owner.name}
        avatarUrl={entry.owner.avatar_url}
        size="md"
      />

      <div className="flex-1">
        <div className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>
          {entry.owner.display_name || entry.owner.name}
        </div>
        <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          {entry.years.join(', ')}
        </div>
      </div>

      <div className="text-right">
        <div className="flex items-center gap-1">
          {[...Array(Math.min(entry.championships, 5))].map((_, i) => (
            <TrophyIcon key={i} className="w-5 h-5" color="" style={{ color: colors.gold }} />
          ))}
          {entry.championships > 5 && (
            <span className="font-bold" style={{ color: colors.gold }}>+{entry.championships - 5}</span>
          )}
        </div>
        <div className="text-2xl font-bold" style={{ color: colors.gold }}>
          {entry.championships}
        </div>
      </div>
    </div>
  );
};

// Placement Leaderboard Row for runner-up and third place - theme-aware
const PlacementLeaderboardRow = ({ entry, rank, colors, trophyColor }: { entry: PlacementCount; rank: number; colors: ReturnType<typeof getTrophyColors>; trophyColor: string }) => {
  return (
    <div
      className="flex items-center gap-4 p-4 rounded-xl transition-all duration-300"
      style={{
        backgroundColor: rank <= 3 ? 'var(--bg-tertiary)' : 'transparent',
      }}
    >
      <RankMedal rank={rank} colors={colors} />

      <ChampionAvatar
        name={entry.owner.display_name || entry.owner.name}
        avatarUrl={entry.owner.avatar_url}
        size="md"
      />

      <div className="flex-1">
        <div className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>
          {entry.owner.display_name || entry.owner.name}
        </div>
        <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          {entry.years.join(', ')}
        </div>
      </div>

      <div className="text-right">
        <div className="flex items-center gap-1">
          {[...Array(Math.min(entry.count, 5))].map((_, i) => (
            <TrophyIcon key={i} className="w-5 h-5" color="" style={{ color: trophyColor }} />
          ))}
          {entry.count > 5 && (
            <span className="font-bold" style={{ color: trophyColor }}>+{entry.count - 5}</span>
          )}
        </div>
        <div className="text-2xl font-bold" style={{ color: trophyColor }}>
          {entry.count}
        </div>
      </div>
    </div>
  );
};

// Dynasty Badge - theme-aware
const DynastyBadge = ({ dynasty, colors }: { dynasty: DynastyStreak; colors: ReturnType<typeof getTrophyColors> }) => {
  return (
    <div
      className="rounded-xl p-4 border"
      style={{
        background: `linear-gradient(to right, ${colors.accentSecondary}20, ${colors.accentSecondary}10)`,
        borderColor: `${colors.accentSecondary}30`,
      }}
    >
      <div className="flex items-center gap-4">
        <div className="flex -space-x-1">
          {[...Array(dynasty.streak)].map((_, i) => (
            <TrophyIcon key={i} className="w-6 h-6 relative" color="" style={{ color: colors.gold }} />
          ))}
        </div>

        <div className="flex-1">
          <div className="font-bold" style={{ color: 'var(--text-primary)' }}>
            {dynasty.owner.display_name || dynasty.owner.name}
          </div>
          <div className="text-sm" style={{ color: colors.accentSecondary }}>
            {dynasty.start_year} - {dynasty.end_year} • {dynasty.league_name}
          </div>
        </div>

        <div className="text-right">
          <div className="text-3xl font-bold" style={{ color: colors.accentSecondary }}>{dynasty.streak}</div>
          <div className="text-xs uppercase tracking-wide" style={{ color: colors.accentSecondary }}>Years</div>
        </div>
      </div>
    </div>
  );
};

// ==================== Main Component ====================

export function HallOfFame() {
  const { theme } = useTheme();
  const [data, setData] = useState<HallOfFameData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showInitialConfetti, setShowInitialConfetti] = useState(false);
  const [trophyColors, setTrophyColors] = useState(getTrophyColors());

  // Update colors when theme changes
  useEffect(() => {
    const timer = setTimeout(() => {
      setTrophyColors(getTrophyColors());
    }, 50);
    return () => clearTimeout(timer);
  }, [theme]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/hall-of-fame');
        if (!response.ok) throw new Error('Failed to fetch Hall of Fame data');
        const result = await response.json();
        setData(result);

        // Trigger confetti celebration if there are champions
        if (result.total_seasons > 0) {
          // Small delay for dramatic effect
          setTimeout(() => {
            setShowInitialConfetti(true);
          }, 500);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="p-4 sm:p-6 space-y-8">
        <HeroSkeleton />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} style={{ animationDelay: `${i * 0.1}s` }}>
              <CardSkeleton />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 sm:p-6">
        <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-6 text-center">
          <p className="text-red-400">Error: {error}</p>
        </div>
      </div>
    );
  }

  const hasData = data && data.total_seasons > 0;

  return (
    <div className="p-4 sm:p-6 space-y-8">
      {/* Confetti celebration */}
      {showInitialConfetti && (
        <Confetti
          active={showInitialConfetti}
          duration={4000}
          pieceCount={100}
          onComplete={() => setShowInitialConfetti(false)}
        />
      )}

      {/* Hero Section */}
      <div className="text-center py-8 animate-fade-in">
        <div className="relative inline-block mb-6">
          {/* Glow effect - use trophy color for consistency */}
          <div
            className="absolute inset-0 blur-2xl rounded-full animate-pulse"
            style={{ backgroundColor: `${trophyColors.gold}40` }}
          />
          <LargeTrophyIcon className="relative w-32 h-32 sm:w-40 sm:h-40 drop-shadow-2xl animate-trophy-glow" colors={trophyColors} />
        </div>
        <h1
          className="text-4xl sm:text-5xl font-extrabold mb-3"
          style={{
            background: `linear-gradient(to right, ${trophyColors.gold}, ${trophyColors.goldMid}, ${trophyColors.bronze})`,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          Hall of Fame
        </h1>
        <p className="text-lg max-w-md mx-auto" style={{ color: 'var(--text-secondary)' }}>
          Celebrating the greatest champions in league history
        </p>

        {/* Stats bar */}
        {hasData && (
          <div className="flex justify-center gap-8 mt-6">
            <div className="text-center">
              <div className="text-3xl font-bold" style={{ color: trophyColors.gold }}>{data.total_seasons}</div>
              <div className="text-sm" style={{ color: 'var(--text-muted)' }}>Championships</div>
            </div>
            <div className="w-px" style={{ backgroundColor: 'var(--border-primary)' }} />
            <div className="text-center">
              <div className="text-3xl font-bold" style={{ color: trophyColors.gold }}>{data.unique_champions}</div>
              <div className="text-sm" style={{ color: 'var(--text-muted)' }}>Unique Champions</div>
            </div>
          </div>
        )}
      </div>

      {!hasData ? (
        <div className="rounded-xl p-8 text-center" style={{ backgroundColor: 'var(--bg-secondary)', opacity: 0.5 }}>
          <LargeTrophyIcon className="w-24 h-24 mx-auto mb-4 opacity-30" colors={trophyColors} />
          <p className="text-lg" style={{ color: 'var(--text-secondary)' }}>No champions yet. Import your league data to see the Hall of Fame!</p>
        </div>
      ) : (
        <>
          {/* Championship Leaderboard */}
          {data.championship_leaderboard.length > 0 && (
            <section>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 rounded-lg" style={{ backgroundColor: `${trophyColors.gold}30` }}>
                  <CrownIcon className="w-6 h-6" style={{ color: trophyColors.gold }} />
                </div>
                <h2 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Championship Leaderboard</h2>
              </div>

              <div className="rounded-xl overflow-hidden" style={{ backgroundColor: 'var(--bg-secondary)', opacity: 0.8 }}>
                <div style={{ borderColor: 'var(--border-primary)' }}>
                  {data.championship_leaderboard.map((entry, index) => (
                    <LeaderboardRow key={entry.owner.id} entry={entry} rank={index + 1} colors={trophyColors} />
                  ))}
                </div>
              </div>
            </section>
          )}

          {/* Runner-Up and Third Place Leaderboards - Side by Side */}
          {(data.runner_up_leaderboard.length > 0 || data.third_place_leaderboard.length > 0) && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Runner-Up Leaderboard */}
              {data.runner_up_leaderboard.length > 0 && (
                <section>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 rounded-lg" style={{ backgroundColor: `${trophyColors.silver}30` }}>
                      <TrophyIcon className="w-6 h-6" color="" style={{ color: trophyColors.silver }} />
                    </div>
                    <h2 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>Runner-Up Finishes</h2>
                    <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Silver Medals</span>
                  </div>

                  <div className="rounded-xl overflow-hidden" style={{ backgroundColor: 'var(--bg-secondary)', opacity: 0.8 }}>
                    <div style={{ borderColor: 'var(--border-primary)' }}>
                      {data.runner_up_leaderboard.map((entry, index) => (
                        <PlacementLeaderboardRow
                          key={entry.owner.id}
                          entry={entry}
                          rank={index + 1}
                          colors={trophyColors}
                          trophyColor={trophyColors.silver}
                        />
                      ))}
                    </div>
                  </div>
                </section>
              )}

              {/* Third Place Leaderboard */}
              {data.third_place_leaderboard.length > 0 && (
                <section>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 rounded-lg" style={{ backgroundColor: `${trophyColors.bronze}30` }}>
                      <TrophyIcon className="w-6 h-6" color="" style={{ color: trophyColors.bronze }} />
                    </div>
                    <h2 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>Third Place Finishes</h2>
                    <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Bronze Medals</span>
                  </div>

                  <div className="rounded-xl overflow-hidden" style={{ backgroundColor: 'var(--bg-secondary)', opacity: 0.8 }}>
                    <div style={{ borderColor: 'var(--border-primary)' }}>
                      {data.third_place_leaderboard.map((entry, index) => (
                        <PlacementLeaderboardRow
                          key={entry.owner.id}
                          entry={entry}
                          rank={index + 1}
                          colors={trophyColors}
                          trophyColor={trophyColors.bronze}
                        />
                      ))}
                    </div>
                  </div>
                </section>
              )}
            </div>
          )}

          {/* Dynasties Section */}
          {data.dynasties.length > 0 && (
            <section>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 rounded-lg" style={{ backgroundColor: `${trophyColors.accentSecondary}30` }}>
                  <svg className="w-6 h-6" style={{ color: trophyColors.accentSecondary }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Dynasties</h2>
                <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Consecutive Championships</span>
              </div>

              <div className="grid gap-4">
                {data.dynasties.map((dynasty) => (
                  <DynastyBadge key={`${dynasty.owner.id}-${dynasty.start_year}`} dynasty={dynasty} colors={trophyColors} />
                ))}
              </div>
            </section>
          )}

          {/* Champions by Year */}
          <section>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 rounded-lg" style={{ backgroundColor: `${trophyColors.gold}30` }}>
                <TrophyIcon className="w-6 h-6" color="" style={{ color: trophyColors.gold }} />
              </div>
              <h2 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Champions by Year</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.champions_by_year.map((champion, index) => (
                <ChampionCard
                  key={`${champion.year}-${champion.league_id}`}
                  champion={champion}
                  isFirst={index === 0}
                  index={index}
                />
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}

import { useEffect, useState } from 'react';
import { Confetti } from '../components/Confetti';
import { HeroSkeleton, CardSkeleton } from '../components/LoadingStates';

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
  dynasties: DynastyStreak[];
  total_seasons: number;
  unique_champions: number;
}

// ==================== Components ====================

// Large Trophy SVG for hero section
const LargeTrophyIcon = ({ className = "w-24 h-24" }: { className?: string }) => (
  <svg className={className} viewBox="0 0 64 64" fill="none">
    <defs>
      <linearGradient id="trophyGold" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#FFD700" />
        <stop offset="50%" stopColor="#FFA500" />
        <stop offset="100%" stopColor="#FFD700" />
      </linearGradient>
      <linearGradient id="trophyShine" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.5" />
        <stop offset="50%" stopColor="#FFFFFF" stopOpacity="0.2" />
        <stop offset="100%" stopColor="#FFFFFF" stopOpacity="0" />
      </linearGradient>
    </defs>
    {/* Trophy cup */}
    <path
      d="M16 12h32v4c0 12-6 22-16 24-10-2-16-12-16-24v-4z"
      fill="url(#trophyGold)"
      stroke="#B8860B"
      strokeWidth="1"
    />
    {/* Shine effect */}
    <path
      d="M20 16h8v2c0 8-2 14-4 16-2-2-4-8-4-16v-2z"
      fill="url(#trophyShine)"
    />
    {/* Handles */}
    <path
      d="M16 14h-4a8 8 0 0 0 0 16h4"
      fill="none"
      stroke="url(#trophyGold)"
      strokeWidth="4"
      strokeLinecap="round"
    />
    <path
      d="M48 14h4a8 8 0 0 1 0 16h-4"
      fill="none"
      stroke="url(#trophyGold)"
      strokeWidth="4"
      strokeLinecap="round"
    />
    {/* Base */}
    <path
      d="M28 40h8v4h-8z"
      fill="url(#trophyGold)"
    />
    <path
      d="M24 44h16v2c0 2-2 4-4 4h-8c-2 0-4-2-4-4v-2z"
      fill="url(#trophyGold)"
      stroke="#B8860B"
      strokeWidth="1"
    />
    {/* Star on trophy */}
    <path
      d="M32 20l2 4 4 1-3 3 1 4-4-2-4 2 1-4-3-3 4-1z"
      fill="#B8860B"
    />
  </svg>
);

// Small trophy icon
const TrophyIcon = ({ className = "w-6 h-6", color = "text-yellow-500" }: { className?: string; color?: string }) => (
  <svg className={`${className} ${color}`} fill="currentColor" viewBox="0 0 20 20">
    <path fillRule="evenodd" d="M5 2a2 2 0 00-2 2v1a2 2 0 002 2h1v1H5a3 3 0 00-3 3v6a3 3 0 003 3h10a3 3 0 003-3v-6a3 3 0 00-3-3h-1V7h1a2 2 0 002-2V4a2 2 0 00-2-2H5zm0 2h10v1H5V4zm3 4h4v1H8V8z" clipRule="evenodd" />
  </svg>
);

// Crown icon for champions
const CrownIcon = ({ className = "w-5 h-5" }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M5 16L3 5l5 5 4-6 4 6 5-5-2 11H5zm0 2h14v2H5v-2z" />
  </svg>
);

// Medal component for rankings
const RankMedal = ({ rank }: { rank: number }) => {
  const colors: Record<number, { bg: string; text: string; border: string }> = {
    1: { bg: 'bg-gradient-to-br from-yellow-400 to-yellow-600', text: 'text-yellow-900', border: 'ring-yellow-400' },
    2: { bg: 'bg-gradient-to-br from-gray-300 to-gray-500', text: 'text-gray-800', border: 'ring-gray-400' },
    3: { bg: 'bg-gradient-to-br from-amber-500 to-amber-700', text: 'text-amber-100', border: 'ring-amber-500' },
  };

  const style = colors[rank] || { bg: 'bg-slate-600', text: 'text-slate-200', border: 'ring-slate-500' };

  return (
    <span className={`inline-flex items-center justify-center w-10 h-10 rounded-full ${style.bg} ${style.text} font-bold text-lg shadow-lg ring-2 ${style.border}`}>
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

// Leaderboard Row
const LeaderboardRow = ({ entry, rank }: { entry: ChampionshipCount; rank: number }) => {
  return (
    <div
      className={`flex items-center gap-4 p-4 rounded-xl transition-all duration-300 hover:bg-slate-700/50 ${
        rank <= 3 ? 'bg-slate-700/30' : ''
      }`}
    >
      <RankMedal rank={rank} />

      <ChampionAvatar
        name={entry.owner.display_name || entry.owner.name}
        avatarUrl={entry.owner.avatar_url}
        size="md"
      />

      <div className="flex-1">
        <div className="font-bold text-white text-lg">
          {entry.owner.display_name || entry.owner.name}
        </div>
        <div className="text-slate-400 text-sm">
          {entry.years.join(', ')}
        </div>
      </div>

      <div className="text-right">
        <div className="flex items-center gap-1">
          {[...Array(Math.min(entry.championships, 5))].map((_, i) => (
            <TrophyIcon key={i} className="w-5 h-5 text-yellow-500" />
          ))}
          {entry.championships > 5 && (
            <span className="text-yellow-500 font-bold">+{entry.championships - 5}</span>
          )}
        </div>
        <div className="text-2xl font-bold text-yellow-400">
          {entry.championships}
        </div>
      </div>
    </div>
  );
};

// Dynasty Badge
const DynastyBadge = ({ dynasty }: { dynasty: DynastyStreak }) => {
  return (
    <div className="bg-gradient-to-r from-purple-600/20 to-indigo-600/20 rounded-xl p-4 border border-purple-500/30">
      <div className="flex items-center gap-4">
        <div className="flex -space-x-1">
          {[...Array(dynasty.streak)].map((_, i) => (
            <TrophyIcon key={i} className="w-6 h-6 text-yellow-500 relative" color="text-yellow-500" />
          ))}
        </div>

        <div className="flex-1">
          <div className="font-bold text-white">
            {dynasty.owner.display_name || dynasty.owner.name}
          </div>
          <div className="text-purple-300 text-sm">
            {dynasty.start_year} - {dynasty.end_year} • {dynasty.league_name}
          </div>
        </div>

        <div className="text-right">
          <div className="text-3xl font-bold text-purple-400">{dynasty.streak}</div>
          <div className="text-purple-300 text-xs uppercase tracking-wide">Years</div>
        </div>
      </div>
    </div>
  );
};

// ==================== Main Component ====================

export function HallOfFame() {
  const [data, setData] = useState<HallOfFameData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showInitialConfetti, setShowInitialConfetti] = useState(false);

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
          {/* Glow effect */}
          <div className="absolute inset-0 blur-2xl bg-yellow-500/30 rounded-full animate-pulse" />
          <LargeTrophyIcon className="relative w-32 h-32 sm:w-40 sm:h-40 drop-shadow-2xl animate-trophy-glow" />
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 via-amber-500 to-orange-500 mb-3">
          Hall of Fame
        </h1>
        <p className="text-slate-400 text-lg max-w-md mx-auto">
          Celebrating the greatest champions in league history
        </p>

        {/* Stats bar */}
        {hasData && (
          <div className="flex justify-center gap-8 mt-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-400">{data.total_seasons}</div>
              <div className="text-slate-500 text-sm">Championships</div>
            </div>
            <div className="w-px bg-slate-700" />
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-400">{data.unique_champions}</div>
              <div className="text-slate-500 text-sm">Unique Champions</div>
            </div>
          </div>
        )}
      </div>

      {!hasData ? (
        <div className="bg-slate-800/50 rounded-xl p-8 text-center">
          <LargeTrophyIcon className="w-24 h-24 mx-auto mb-4 opacity-30" />
          <p className="text-slate-400 text-lg">No champions yet. Import your league data to see the Hall of Fame!</p>
        </div>
      ) : (
        <>
          {/* Championship Leaderboard */}
          {data.championship_leaderboard.length > 0 && (
            <section>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-yellow-500/20 rounded-lg">
                  <CrownIcon className="w-6 h-6 text-yellow-500" />
                </div>
                <h2 className="text-2xl font-bold text-white">Championship Leaderboard</h2>
              </div>

              <div className="bg-slate-800/50 rounded-xl overflow-hidden">
                <div className="divide-y divide-slate-700/50">
                  {data.championship_leaderboard.map((entry, index) => (
                    <LeaderboardRow key={entry.owner.id} entry={entry} rank={index + 1} />
                  ))}
                </div>
              </div>
            </section>
          )}

          {/* Dynasties Section */}
          {data.dynasties.length > 0 && (
            <section>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-purple-500/20 rounded-lg">
                  <svg className="w-6 h-6 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-white">Dynasties</h2>
                <span className="text-slate-500 text-sm">Consecutive Championships</span>
              </div>

              <div className="grid gap-4">
                {data.dynasties.map((dynasty) => (
                  <DynastyBadge key={`${dynasty.owner.id}-${dynasty.start_year}`} dynasty={dynasty} />
                ))}
              </div>
            </section>
          )}

          {/* Champions by Year */}
          <section>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-amber-500/20 rounded-lg">
                <TrophyIcon className="w-6 h-6 text-amber-500" />
              </div>
              <h2 className="text-2xl font-bold text-white">Champions by Year</h2>
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

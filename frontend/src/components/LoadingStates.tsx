/**
 * LoadingStates Components
 *
 * Provides consistent loading states across the application:
 * - Skeleton: Shimmer effect placeholder
 * - LoadingSpinner: Animated spinner
 * - CardSkeleton: Skeleton for profile/stat cards
 * - TableSkeleton: Skeleton for data tables
 */

import type { ReactNode } from 'react';

// Base Skeleton component with shimmer effect
export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`skeleton rounded ${className}`} />
  );
}

// Loading Spinner with optional text
export function LoadingSpinner({
  size = 'md',
  text,
  color = 'blue'
}: {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  color?: 'blue' | 'yellow' | 'green' | 'purple' | 'red';
}) {
  const sizeClasses = {
    sm: 'h-6 w-6',
    md: 'h-12 w-12',
    lg: 'h-16 w-16'
  };

  const colorClasses = {
    blue: 'border-blue-400',
    yellow: 'border-yellow-400',
    green: 'border-green-400',
    purple: 'border-purple-400',
    red: 'border-red-400'
  };

  return (
    <div className="flex flex-col items-center justify-center gap-4">
      <div
        className={`animate-spin rounded-full border-b-2 ${sizeClasses[size]} ${colorClasses[color]}`}
      />
      {text && (
        <p className="text-slate-400 text-sm animate-pulse">{text}</p>
      )}
    </div>
  );
}

// Skeleton for profile/owner cards
export function CardSkeleton() {
  return (
    <div className="rounded-xl p-5 animate-card-entrance" style={{ backgroundColor: 'var(--bg-card)' }}>
      {/* Avatar and header */}
      <div className="flex items-center gap-4 mb-4">
        <Skeleton className="w-16 h-16 rounded-full" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-24" />
        </div>
      </div>
      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        <Skeleton className="h-12 rounded-lg" />
        <Skeleton className="h-12 rounded-lg" />
        <Skeleton className="h-12 rounded-lg" />
      </div>
    </div>
  );
}

// Skeleton for data table rows
export function TableSkeleton({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) {
  return (
    <div className="overflow-hidden rounded-lg">
      {/* Header */}
      <div className="p-4 flex gap-4" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>
      {/* Rows */}
      <div style={{ borderColor: 'var(--border-primary)' }}>
        {Array.from({ length: rows }).map((_, rowIdx) => (
          <div
            key={rowIdx}
            className="p-4 flex gap-4 animate-card-entrance"
            style={{ backgroundColor: 'var(--bg-card)', animationDelay: `${rowIdx * 0.05}s`, borderTop: '1px solid var(--border-primary)' }}
          >
            {Array.from({ length: columns }).map((_, colIdx) => (
              <Skeleton
                key={colIdx}
                className={`h-4 ${colIdx === 0 ? 'w-8' : 'flex-1'}`}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

// Skeleton for stat cards (like on Dashboard)
export function StatCardSkeleton() {
  return (
    <div className="rounded-lg p-6 animate-card-entrance" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-primary)' }}>
      <div className="flex items-center gap-3">
        <Skeleton className="w-12 h-12 rounded-lg" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-7 w-12" />
        </div>
      </div>
    </div>
  );
}

// Skeleton for chart/graph areas
// Pre-computed heights for deterministic rendering (React purity requirement)
const CHART_BAR_HEIGHTS = [45, 72, 38, 85, 55, 68, 42, 78];

export function ChartSkeleton({ height = 200 }: { height?: number }) {
  return (
    <div
      className="rounded-lg overflow-hidden animate-card-entrance"
      style={{ height, backgroundColor: 'var(--bg-card)' }}
    >
      <div className="h-full flex items-end justify-around gap-2 p-4">
        {CHART_BAR_HEIGHTS.map((barHeight, i) => (
          <div
            key={i}
            className="skeleton flex-1 rounded-t"
            style={{
              height: `${barHeight}%`,
              animationDelay: `${i * 0.1}s`
            }}
          />
        ))}
      </div>
    </div>
  );
}

// Full page loading state wrapper
export function PageLoadingState({
  children,
  loading,
  skeleton
}: {
  children: ReactNode;
  loading: boolean;
  skeleton?: ReactNode;
}) {
  if (loading) {
    return (
      <div className="animate-fade-in">
        {skeleton || (
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner size="lg" text="Loading..." />
          </div>
        )}
      </div>
    );
  }

  return <>{children}</>;
}

// Cards grid skeleton for pages like Owners
export function CardsGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          style={{ animationDelay: `${i * 0.05}s` }}
        >
          <CardSkeleton />
        </div>
      ))}
    </div>
  );
}

// Hero section skeleton (for Hall of Fame, Records)
export function HeroSkeleton() {
  return (
    <div className="text-center py-8 animate-fade-in">
      <Skeleton className="w-32 h-32 rounded-full mx-auto mb-6" />
      <Skeleton className="h-10 w-64 mx-auto mb-3" />
      <Skeleton className="h-5 w-48 mx-auto" />
    </div>
  );
}

// Skeleton for season cards on Seasons page
export function SeasonCardSkeleton() {
  return (
    <div className="rounded-lg overflow-hidden animate-card-entrance" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-primary)' }}>
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="space-y-2">
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-4 w-16" />
          </div>
          <Skeleton className="h-4 w-16" />
        </div>
        {/* Champion section */}
        <div className="mt-4 p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
          <div className="flex items-center gap-2">
            <Skeleton className="w-5 h-5 rounded" />
            <div className="space-y-1.5 flex-1">
              <Skeleton className="h-3 w-16" />
              <Skeleton className="h-4 w-24" />
            </div>
          </div>
        </div>
        {/* Footer hint */}
        <div className="mt-3 text-center">
          <Skeleton className="h-3 w-40 mx-auto" />
        </div>
      </div>
    </div>
  );
}

// Skeleton grid for Seasons page
export function SeasonsGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="space-y-8">
      {/* Year header skeleton */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Skeleton className="w-10 h-10 rounded-lg" />
          <Skeleton className="h-6 w-32" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: count }).map((_, i) => (
            <div key={i} style={{ animationDelay: `${i * 0.05}s` }}>
              <SeasonCardSkeleton />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Skeleton for record cards on Records page
export function RecordCardSkeleton() {
  return (
    <div className="rounded-xl overflow-hidden shadow-lg animate-card-entrance" style={{ backgroundColor: 'var(--bg-card)' }}>
      {/* Colored header */}
      <div className="p-4" style={{ background: 'linear-gradient(to right, var(--bg-tertiary), var(--bg-secondary))' }}>
        <div className="flex items-center gap-3">
          <Skeleton className="w-10 h-10 rounded-lg" />
          <Skeleton className="h-5 w-32" />
        </div>
      </div>
      {/* Content */}
      <div className="p-5 space-y-2">
        <Skeleton className="h-10 w-24" />
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-4 w-20" />
      </div>
    </div>
  );
}

// Skeleton for Records page leaderboard table
export function LeaderboardSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="rounded-xl overflow-hidden shadow-lg animate-card-entrance" style={{ backgroundColor: 'var(--bg-card)' }}>
      {/* Header */}
      <div className="p-4 flex items-center gap-3" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
        <Skeleton className="w-6 h-6 rounded" />
        <Skeleton className="h-5 w-40" />
      </div>
      {/* Table rows */}
      <div className="p-2">
        {Array.from({ length: rows }).map((_, i) => (
          <div
            key={i}
            className="flex items-center gap-4 p-3"
            style={{ animationDelay: `${i * 0.05}s` }}
          >
            <Skeleton className="w-8 h-8 rounded-full" />
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-20" />
          </div>
        ))}
      </div>
    </div>
  );
}

// Full Records page skeleton
export function RecordsPageSkeleton() {
  return (
    <div className="space-y-8">
      {/* Hero header */}
      <div className="text-center">
        <Skeleton className="w-16 h-16 rounded-full mx-auto mb-4" />
        <Skeleton className="h-10 w-48 mx-auto mb-2" />
        <Skeleton className="h-5 w-64 mx-auto" />
      </div>
      {/* Record cards grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} style={{ animationDelay: `${i * 0.1}s` }}>
            <RecordCardSkeleton />
          </div>
        ))}
      </div>
      {/* Leaderboard tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LeaderboardSkeleton rows={5} />
        <LeaderboardSkeleton rows={5} />
      </div>
    </div>
  );
}

export default {
  Skeleton,
  LoadingSpinner,
  CardSkeleton,
  TableSkeleton,
  StatCardSkeleton,
  ChartSkeleton,
  PageLoadingState,
  CardsGridSkeleton,
  HeroSkeleton,
  SeasonCardSkeleton,
  SeasonsGridSkeleton,
  RecordCardSkeleton,
  LeaderboardSkeleton,
  RecordsPageSkeleton
};

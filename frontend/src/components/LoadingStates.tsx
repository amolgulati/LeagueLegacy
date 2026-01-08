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
    <div className="bg-slate-800 rounded-xl p-5 animate-card-entrance">
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
      <div className="bg-slate-700 p-4 flex gap-4">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>
      {/* Rows */}
      <div className="divide-y divide-slate-700/50">
        {Array.from({ length: rows }).map((_, rowIdx) => (
          <div
            key={rowIdx}
            className="bg-slate-800 p-4 flex gap-4 animate-card-entrance"
            style={{ animationDelay: `${rowIdx * 0.05}s` }}
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
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 animate-card-entrance">
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
      className="bg-slate-800 rounded-lg overflow-hidden animate-card-entrance"
      style={{ height }}
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

export default {
  Skeleton,
  LoadingSpinner,
  CardSkeleton,
  TableSkeleton,
  StatCardSkeleton,
  ChartSkeleton,
  PageLoadingState,
  CardsGridSkeleton,
  HeroSkeleton
};

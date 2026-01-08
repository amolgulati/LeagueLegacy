/**
 * Owner-related types for the Fantasy League History Tracker.
 */

export interface Owner {
  id: number;
  name: string;
  display_name: string | null;
  avatar_url: string | null;
  sleeper_user_id: string | null;
  yahoo_user_id: string | null;
}

export interface OwnerStats {
  id: number;
  name: string;
  total_wins: number;
  total_losses: number;
  total_ties: number;
  total_points: number;
  seasons_played: number;
  playoff_appearances: number;
  championships: number;
  avg_regular_season_rank: number | null;
}

export interface CreateOwnerMappingRequest {
  name: string;
  display_name?: string;
  avatar_url?: string;
  sleeper_user_id?: string;
  yahoo_user_id?: string;
}

export interface UpdateOwnerMappingRequest {
  sleeper_user_id?: string;
  yahoo_user_id?: string;
  display_name?: string;
  avatar_url?: string;
}

export interface MergeOwnersRequest {
  primary_owner_id: number;
  secondary_owner_id: number;
}

/**
 * Owner with career statistics from the history API.
 */
export interface OwnerWithStats {
  id: number;
  name: string;
  display_name: string | null;
  avatar_url: string | null;
  total_wins: number;
  total_losses: number;
  total_ties: number;
  total_points: number;
  seasons_played: number;
  playoff_appearances: number;
  championships: number;
  win_percentage: number;
}

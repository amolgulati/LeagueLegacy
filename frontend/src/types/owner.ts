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

/**
 * Brief owner info for head-to-head comparisons.
 */
export interface OwnerBrief {
  id: number;
  name: string;
  display_name: string | null;
  avatar_url: string | null;
}

/**
 * Individual matchup detail in head-to-head history.
 */
export interface MatchupDetail {
  year: number;
  week: number;
  owner1_score: number;
  owner2_score: number;
  winner_id: number | null;
  is_playoff: boolean;
  is_championship: boolean;
}

/**
 * Head-to-head rivalry statistics between two owners.
 */
export interface HeadToHeadResponse {
  owner1: OwnerBrief;
  owner2: OwnerBrief;
  total_matchups: number;
  owner1_wins: number;
  owner2_wins: number;
  ties: number;
  owner1_avg_score: number | null;
  owner2_avg_score: number | null;
  playoff_matchups: number;
  owner1_playoff_wins: number;
  owner2_playoff_wins: number;
  matchups: MatchupDetail[];
}

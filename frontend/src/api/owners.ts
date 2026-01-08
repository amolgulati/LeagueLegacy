/**
 * API client for owner endpoints.
 */

import type {
  Owner,
  OwnerStats,
  CreateOwnerMappingRequest,
  UpdateOwnerMappingRequest,
  MergeOwnersRequest,
} from '../types/owner';

const API_BASE = 'http://localhost:8000/api/owners';

/**
 * Fetch all owners.
 */
export async function fetchOwners(): Promise<Owner[]> {
  const response = await fetch(API_BASE);
  if (!response.ok) {
    throw new Error('Failed to fetch owners');
  }
  return response.json();
}

/**
 * Fetch owners that are not fully mapped to both platforms.
 */
export async function fetchUnmappedOwners(): Promise<Owner[]> {
  const response = await fetch(`${API_BASE}/unmapped`);
  if (!response.ok) {
    throw new Error('Failed to fetch unmapped owners');
  }
  return response.json();
}

/**
 * Fetch a single owner by ID.
 */
export async function fetchOwner(id: number): Promise<Owner> {
  const response = await fetch(`${API_BASE}/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch owner ${id}`);
  }
  return response.json();
}

/**
 * Fetch career stats for an owner.
 */
export async function fetchOwnerStats(id: number): Promise<OwnerStats> {
  const response = await fetch(`${API_BASE}/${id}/stats`);
  if (!response.ok) {
    throw new Error(`Failed to fetch owner stats for ${id}`);
  }
  return response.json();
}

/**
 * Create a new owner with platform mappings.
 */
export async function createOwnerMapping(
  data: CreateOwnerMappingRequest
): Promise<Owner> {
  const response = await fetch(`${API_BASE}/mapping`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create owner mapping');
  }
  return response.json();
}

/**
 * Update platform mappings for an existing owner.
 */
export async function updateOwnerMapping(
  id: number,
  data: UpdateOwnerMappingRequest
): Promise<Owner> {
  const response = await fetch(`${API_BASE}/${id}/mapping`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update owner mapping');
  }
  return response.json();
}

/**
 * Unlink a platform from an owner.
 */
export async function unlinkPlatform(
  id: number,
  platform: 'sleeper' | 'yahoo'
): Promise<Owner> {
  const response = await fetch(`${API_BASE}/${id}/mapping/${platform}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to unlink platform');
  }
  return response.json();
}

/**
 * Merge two owners into one.
 */
export async function mergeOwners(data: MergeOwnersRequest): Promise<Owner> {
  const response = await fetch(`${API_BASE}/merge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to merge owners');
  }
  return response.json();
}

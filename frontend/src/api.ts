/**
 * API client for the dispatch backend.
 * Uses VITE_API_BASE_URL environment variable for the base URL.
 */

import type { Call } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

/**
 * Fetch all calls from the backend.
 */
export async function fetchCalls(): Promise<Call[]> {
  const response = await fetch(`${API_BASE_URL}/api/calls`);
  if (!response.ok) {
    throw new Error(`Failed to fetch calls: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch a single call by ID.
 */
export async function fetchCallById(id: string): Promise<Call> {
  const response = await fetch(`${API_BASE_URL}/api/calls/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch call: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Health check for the backend.
 */
export async function checkHealth(): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }
  return response.json();
}

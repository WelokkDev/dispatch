/**
 * API client for the dispatch backend.
 * Uses VITE_API_BASE_URL environment variable for the base URL.
 */

import type { Call } from "./types";

const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string) || "http://127.0.0.1:5001";

export type TranscriptMessage = Call["transcript"][number];

export type SSEEvent =
  | { type: "call_created"; call: Call }
  | {
      type: "new_message";
      call_id: string;
      message: TranscriptMessage;
    }
  | {
      type: "transcript_update";
      call_id: string;
      transcript: Call["transcript"];
      status: string;
      aiHandling: boolean;
      priority?: Call["priority"];
      incidentType?: string;
      locationLabel?: string;
      pin?: { lat: number; lng: number };
      confidence?: number;
    }
  | {
      type: "summary_update";
      call_id: string;
      summary: string;
    };

/**
 * Subscribe to real-time events (call_created, transcript_update).
 * Returns a cleanup function to close the connection.
 */
export function subscribeToEvents(onEvent: (ev: SSEEvent) => void): () => void {
  const url = `${API_BASE_URL}/api/events`;
  const es = new EventSource(url);

  es.onmessage = (e) => {
    try {
      const ev = JSON.parse(e.data) as SSEEvent;
      onEvent(ev);
    } catch {
      // ignore parse errors / keepalive
    }
  };

  es.onerror = () => {
    es.close();
  };

  return () => es.close();
}

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

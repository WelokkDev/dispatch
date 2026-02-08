import { useState, useEffect } from "react";
import CallList from "./components/CallList";
import MapPanel from "./components/MapPanel";
import CallDetailDrawer from "./components/CallDetailDrawer";
import { fetchCalls, subscribeToEvents, type SSEEvent } from "./api";
import type { Call } from "./types";

export default function App() {
  const [calls, setCalls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCall, setSelectedCall] = useState<Call | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Fetch calls from API on mount
  useEffect(() => {
    async function loadCalls() {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchCalls();
        setCalls(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load calls");
      } finally {
        setLoading(false);
      }
    }
    loadCalls();
  }, []);

  // Real-time: push call_created and transcript_update from backend (no DB poll)
  useEffect(() => {
    const handleEvent = (ev: SSEEvent) => {
      if (ev.type === "call_created") {
        setCalls((prev) => {
          const exists = prev.some((c) => c.id === ev.call.id);
          if (exists) return prev.map((c) => (c.id === ev.call.id ? { ...c, ...ev.call } : c));
          return [ev.call, ...prev];
        });
        return;
      }
      if (ev.type === "new_message") {
        // Only append if we already have messages (e.g. 911 intro). Otherwise wait for
        // transcript_update so the first exchange arrives as [911, caller, ai] and we
        // can reveal in order without the first slot snapping from caller to 911.
        setCalls((prev) =>
          prev.map((c) => {
            if (c.id !== ev.call_id) return c;
            if (c.transcript.length === 0) return c;
            return { ...c, transcript: [...c.transcript, ev.message] };
          })
        );
        setSelectedCall((prev) => {
          if (!prev || prev.id !== ev.call_id) return prev;
          if (prev.transcript.length === 0) return prev;
          return { ...prev, transcript: [...prev.transcript, ev.message] };
        });
        return;
      }
      if (ev.type === "transcript_update") {
        const update = {
          transcript: ev.transcript,
          status: ev.status,
          aiHandling: ev.aiHandling,
          ...(ev.priority != null && { priority: ev.priority }),
          ...(ev.incidentType != null && { incidentType: ev.incidentType }),
          ...(ev.locationLabel != null && { locationLabel: ev.locationLabel, address: ev.locationLabel }),
        };
        setCalls((prev) =>
          prev.map((c) => (c.id === ev.call_id ? { ...c, ...update } : c))
        );
        setSelectedCall((prev) =>
          prev && prev.id === ev.call_id ? { ...prev, ...update } : prev
        );
      }
    };
    const unsubscribe = subscribeToEvents(handleEvent);
    return unsubscribe;
  }, []);

  const handleSelectCall = (call: Call) => {
    setSelectedCall(call);
    setDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setDrawerOpen(false);
  };

  // Loading state
  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-[#f0f2f7]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-slate-300 border-t-blue-500 rounded-full animate-spin" />
          <p className="text-sm text-slate-500">Loading calls...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-[#f0f2f7]">
        <div className="flex flex-col items-center gap-3 max-w-md text-center">
          <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
            <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p className="text-sm text-slate-700 font-medium">Failed to load calls</p>
          <p className="text-xs text-slate-500">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="mt-2 px-4 py-2 text-sm font-medium text-white bg-blue-500 rounded-lg hover:bg-blue-600 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex overflow-hidden bg-[#f0f2f7]">
    

      {/* Call list sidebar */}
      <CallList
        calls={calls}
        selectedId={selectedCall?.id ?? null}
        onSelect={handleSelectCall}
      />

      {/* Center map */}
      <MapPanel
        calls={calls}
        selectedId={selectedCall?.id ?? null}
        onSelectCall={handleSelectCall}
      />

      {/* Right detail drawer */}
      <CallDetailDrawer
        call={selectedCall}
        isOpen={drawerOpen}
        onClose={handleCloseDrawer}
      />
    </div>
  );
}

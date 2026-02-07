import type { Call } from "../types";

const pinColors: Record<string, string> = {
  P0: "#ef4444",
  P1: "#f59e0b",
  P2: "#3b82f6",
  P3: "#94a3b8",
};

interface MapPanelProps {
  calls: Call[];
  selectedId: string | null;
  onSelectCall: (call: Call) => void;
}

function MapPin({ call, isSelected, onClick }: { call: Call; isSelected: boolean; onClick: () => void }) {
  const color = pinColors[call.priority];
  return (
    <button
      onClick={onClick}
      className="absolute cursor-pointer group"
      style={{ top: call.pinPosition.top, left: call.pinPosition.left, transform: "translate(-50%, -100%)" }}
      title={`${call.incidentType} - ${call.numberMasked}`}
    >
      {/* Pin shape */}
      <svg width="28" height="36" viewBox="0 0 28 36" fill="none" className={`drop-shadow-md transition-transform ${isSelected ? "scale-125" : "group-hover:scale-110"}`}>
        <path
          d="M14 0C6.268 0 0 6.268 0 14c0 9.941 12.09 20.584 12.613 21.053a2 2 0 002.774 0C15.91 34.584 28 23.941 28 14 28 6.268 21.732 0 14 0z"
          fill={color}
          opacity={isSelected ? 1 : 0.85}
        />
        <circle cx="14" cy="13" r="5" fill="white" opacity="0.9" />
      </svg>
    </button>
  );
}

export default function MapPanel({ calls, selectedId, onSelectCall }: MapPanelProps) {
  const selectedCall = calls.find((c) => c.id === selectedId);

  return (
    <div className="flex-1 relative overflow-hidden bg-gradient-to-br from-[#e8edf5] via-[#dde4f0] to-[#d5dce8] rounded-2xl m-3 shadow-inner">
      {/* Map grid pattern for texture */}
      <div className="absolute inset-0 opacity-[0.08]" style={{
        backgroundImage: `
          linear-gradient(rgba(100,116,139,0.3) 1px, transparent 1px),
          linear-gradient(90deg, rgba(100,116,139,0.3) 1px, transparent 1px)
        `,
        backgroundSize: "60px 60px",
      }} />

      {/* Faux roads */}
      <div className="absolute inset-0 opacity-[0.06]">
        {/* Horizontal roads */}
        <div className="absolute top-[30%] left-0 right-0 h-[2px] bg-slate-500" />
        <div className="absolute top-[50%] left-0 right-0 h-[2px] bg-slate-500" />
        <div className="absolute top-[70%] left-0 right-0 h-[2px] bg-slate-500" />
        {/* Vertical roads */}
        <div className="absolute left-[25%] top-0 bottom-0 w-[2px] bg-slate-500" />
        <div className="absolute left-[50%] top-0 bottom-0 w-[2px] bg-slate-500" />
        <div className="absolute left-[75%] top-0 bottom-0 w-[2px] bg-slate-500" />
        {/* Diagonal road */}
        <div className="absolute top-0 left-[20%] w-[2px] h-full bg-slate-500 origin-top-left rotate-[25deg]" />
      </div>

      {/* Water-like area in bottom-left */}
      <div
        className="absolute bottom-0 left-0 w-[35%] h-[30%] rounded-tr-[80px]"
        style={{
          background: "linear-gradient(135deg, rgba(147,197,225,0.3) 0%, rgba(147,197,225,0.1) 100%)",
        }}
      />

      {/* Park-like area */}
      <div
        className="absolute top-[35%] left-[40%] w-[120px] h-[90px] rounded-2xl"
        style={{
          background: "linear-gradient(135deg, rgba(134,197,153,0.25) 0%, rgba(134,197,153,0.1) 100%)",
        }}
      />

      {/* Surge ring / hotspot */}
      <div
        className="absolute surge-ring"
        style={{
          top: "45%",
          left: "48%",
          width: "180px",
          height: "180px",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(251,191,36,0.25) 0%, rgba(251,191,36,0.05) 60%, transparent 100%)",
          transform: "translate(-50%, -50%)",
        }}
      />

      {/* Map pins */}
      {calls.map((call) => (
        <MapPin
          key={call.id}
          call={call}
          isSelected={call.id === selectedId}
          onClick={() => onSelectCall(call)}
        />
      ))}

      {/* Location Validation Card */}
      {selectedCall && (
        <div className="absolute bottom-6 left-6 bg-white/95 backdrop-blur-md rounded-2xl shadow-lg shadow-slate-200/50 border border-slate-100 p-4 max-w-[320px] animate-in fade-in">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-7 h-7 rounded-full bg-emerald-50 flex items-center justify-center">
              <svg className="w-3.5 h-3.5 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
              </svg>
            </div>
            <span className="text-sm font-semibold text-slate-800">Location validation</span>
          </div>

          <div className="mb-3">
            <p className="text-sm font-medium text-slate-800">{selectedCall.locationLabel}</p>
            <p className="text-xs text-slate-500 mt-0.5">{selectedCall.city}</p>
          </div>

          <div className="pt-2 border-t border-slate-100">
            <p className="text-[11px] text-slate-500 mb-1">Suggested Address</p>
            <p className="text-xs font-medium text-slate-700">{selectedCall.locationLabel}</p>
            <p className="text-xs text-slate-500">{selectedCall.address}</p>
          </div>

          <div className="mt-3 flex items-center gap-2">
            <div className="flex items-center gap-1 text-xs px-2 py-1 rounded-lg bg-slate-50 border border-slate-100">
              <span className="text-slate-400">Confidence</span>
              <span className="font-semibold text-slate-700">{selectedCall.confidence}%</span>
              <svg className="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          <div className="mt-3 flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-emerald-400" />
            <span className="text-xs font-medium text-emerald-600">In Service Area</span>
          </div>

          {selectedCall.locationLabel && (
            <div className="mt-2 flex items-center gap-1.5">
              <span className="text-xs text-slate-600">{selectedCall.locationLabel}</span>
              <span className="text-amber-400 text-xs">★</span>
            </div>
          )}
        </div>
      )}

      {/* Map label */}
      <div className="absolute top-4 left-4 flex items-center gap-2 bg-white/80 backdrop-blur-sm rounded-xl px-3 py-1.5 shadow-sm border border-slate-100">
        <span className="text-xs font-medium text-slate-600">Late traff ∞</span>
        <span className="text-[10px] text-slate-400 font-mono">6:34</span>
        <span className="text-slate-300">•••</span>
      </div>
    </div>
  );
}

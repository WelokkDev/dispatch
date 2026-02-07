import type { Call } from "../types";
import { priorityColors, statusColors, type Priority } from "../colors";

function MiniWaveform() {
  return (
    <div className="flex items-end gap-[2px] h-3">
      {[0, 0.15, 0.3, 0.15, 0].map((delay, i) => (
        <div
          key={i}
          className="w-[2px] rounded-full waveform-bar"
          style={{ 
            animationDelay: `${delay}s`, 
            height: "4px",
            backgroundColor: statusColors.aiHandling.waveform,
          }}
        />
      ))}
    </div>
  );
}

interface CallCardProps {
  call: Call;
  isSelected: boolean;
  onSelect: (call: Call) => void;
}

export default function CallCard({ call, isSelected, onSelect }: CallCardProps) {
  return (
    <button
      onClick={() => onSelect(call)}
      className={`w-full text-left p-3 rounded-2xl border transition-all cursor-pointer ${
        isSelected
          ? "bg-white border-blue-200 ring-1 ring-blue-100"
          : "bg-white/60 border-slate-100 hover:bg-white hover:border-slate-200"
      }`}
      style={{
        boxShadow: isSelected
          ? "-4px 4px 12px rgba(148, 163, 184, 0.25), 0 2px 4px rgba(148, 163, 184, 0.1)"
          : "-2px 2px 8px rgba(148, 163, 184, 0.15)",
      }}
    >
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-sm font-semibold text-slate-800 tracking-tight">
          {call.numberMasked}
        </span>
        <div className="flex items-center gap-2">
          <span
            className="text-[10px] font-bold px-1.5 py-0.5 rounded-md border"
            style={{
              backgroundColor: priorityColors[call.priority as Priority].bg,
              color: priorityColors[call.priority as Priority].text,
              borderColor: priorityColors[call.priority as Priority].border,
            }}
          >
            {call.priority}
          </span>
          {call.aiHandling && (
            <span className="text-green-500">
              <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 mb-1.5">
        <span className="text-xs">{call.incidentIcon}</span>
        <span className="text-[13px] font-medium text-slate-700">
          {call.incidentType}
        </span>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div 
            className="w-1.5 h-1.5 rounded-full" 
            style={{ backgroundColor: priorityColors[call.priority as Priority].solid }}
          />
          <span className="text-[11px] text-slate-400">{call.status}</span>
          {call.aiHandling && <MiniWaveform />}
        </div>
        <span className="text-[11px] text-slate-400 font-mono">{call.elapsed}</span>
      </div>
    </button>
  );
}

import { useState } from "react";
import type { Call, PriorityFilter } from "../types";
import CallCard from "./CallCard";

interface CallListProps {
  calls: Call[];
  selectedId: string | null;
  onSelect: (call: Call) => void;
}

export default function CallList({ calls, selectedId, onSelect }: CallListProps) {
  const [filter, setFilter] = useState<PriorityFilter>("All");
  const [search, setSearch] = useState("");

  const filters: PriorityFilter[] = ["All", "P1", "P2", "P3", "P4"];

  const filtered = calls.filter((c) => {
    if (filter !== "All" && c.priority !== filter) return false;
    if (search && !c.numberMasked.includes(search) && !c.incidentType.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <aside className="w-[300px] min-w-[300px] bg-white/80 backdrop-blur-sm border-r border-slate-200/60 flex flex-col h-full">
      {/* Search */}
      <div className="px-4 pt-4 pb-2">
        <div className="relative">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            placeholder="Search calls..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm bg-slate-50 border border-slate-200/80 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-300 placeholder-slate-400 transition-all"
          />
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-1 px-4 pb-3 pt-1">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1 text-xs font-medium rounded-lg transition-all cursor-pointer ${
              filter === f
                ? "bg-slate-800 text-white shadow-sm"
                : "bg-slate-100 text-slate-500 hover:bg-slate-200"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Call Cards */}
      <div className="flex-1 overflow-y-auto call-list-scroll px-3 pb-3 space-y-2">
        {filtered.map((call) => (
          <CallCard
            key={call.id}
            call={call}
            isSelected={call.id === selectedId}
            onSelect={onSelect}
          />
        ))}
      </div>

      {/* Footer */}
      <div className="px-4 py-2.5 border-t border-slate-100 flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-[11px] text-slate-400">In Service Area</span>
      </div>
    </aside>
  );
}

import { useEffect, useRef, useMemo } from "react";
import Map, { Marker, type MapRef } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import type { Call } from "../types";
import { priorityColors, type Priority } from "../colors";

const BASEMAP_STYLE = "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json";

interface MapPanelProps {
  calls: Call[];
  selectedId: string | null;
  onSelectCall: (call: Call) => void;
}

function MapPinSvg({ color, isSelected }: { color: string; isSelected: boolean }) {
  return (
    <svg
      width="28"
      height="36"
      viewBox="0 0 28 36"
      fill="none"
      className={`drop-shadow-md transition-transform ${isSelected ? "scale-125" : "hover:scale-110"}`}
      style={{ cursor: "pointer" }}
    >
      <path
        d="M14 0C6.268 0 0 6.268 0 14c0 9.941 12.09 20.584 12.613 21.053a2 2 0 002.774 0C15.91 34.584 28 23.941 28 14 28 6.268 21.732 0 14 0z"
        fill={color}
        opacity={isSelected ? 1 : 0.85}
      />
      <circle cx="14" cy="13" r="5" fill="white" opacity="0.9" />
    </svg>
  );
}

export default function MapPanel({ calls, selectedId, onSelectCall }: MapPanelProps) {
  const mapRef = useRef<MapRef>(null);
  const selectedCall = calls.find((c) => c.id === selectedId);

  // Calculate center from all calls
  const center = useMemo(() => {
    if (calls.length === 0) return { lat: 47.6062, lng: -122.3321 }; // Seattle default
    const avgLat = calls.reduce((sum, c) => sum + c.pin.lat, 0) / calls.length;
    const avgLng = calls.reduce((sum, c) => sum + c.pin.lng, 0) / calls.length;
    return { lat: avgLat, lng: avgLng };
  }, [calls]);

  // Fly to selected call
  useEffect(() => {
    if (selectedCall && mapRef.current) {
      mapRef.current.flyTo({
        center: [selectedCall.pin.lng, selectedCall.pin.lat],
        zoom: 14,
        duration: 1000,
      });
    }
  }, [selectedCall]);

  return (
    <div className="flex-1 relative overflow-hidden rounded-2xl m-3 shadow-inner">
      {/* Map container */}
      <Map
        ref={mapRef}
        initialViewState={{
          longitude: center.lng,
          latitude: center.lat,
          zoom: 12,
        }}
        style={{ width: "100%", height: "100%" }}
        mapStyle={BASEMAP_STYLE}
        attributionControl={false}
      >
        {/* Markers */}
        {calls.map((call) => (
          <Marker
            key={call.id}
            longitude={call.pin.lng}
            latitude={call.pin.lat}
            anchor="bottom"
            onClick={(e) => {
              e.originalEvent.stopPropagation();
              onSelectCall(call);
            }}
          >
            <MapPinSvg
              color={priorityColors[call.priority as Priority].solid}
              isSelected={call.id === selectedId}
            />
          </Marker>
        ))}
      </Map>

      {/* Soft overlay tint to match Ava aesthetic */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "linear-gradient(135deg, rgba(240,242,247,0.15) 0%, rgba(220,225,235,0.1) 100%)",
        }}
      />

      {/* Surge ring / hotspot overlay */}
      <div
        className="absolute surge-ring pointer-events-none"
        style={{
          top: "45%",
          left: "48%",
          width: "180px",
          height: "180px",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(251,191,36,0.2) 0%, rgba(251,191,36,0.05) 60%, transparent 100%)",
          transform: "translate(-50%, -50%)",
        }}
      />

      {/* Location Validation Card */}
      {selectedCall && (
        <div className="absolute bottom-6 left-6 bg-white/95 backdrop-blur-md rounded-2xl shadow-lg shadow-slate-200/50 border border-slate-100 p-4 max-w-[320px] z-10">
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
      <div className="absolute top-4 left-4 flex items-center gap-2 bg-white/80 backdrop-blur-sm rounded-xl px-3 py-1.5 shadow-sm border border-slate-100 z-10">
        <span className="text-xs font-medium text-slate-600">Late traff ∞</span>
        <span className="text-[10px] text-slate-400 font-mono">6:34</span>
        <span className="text-slate-300">•••</span>
      </div>
    </div>
  );
}

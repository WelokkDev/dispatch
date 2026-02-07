import { useState } from "react";
import IconSidebar from "./components/IconSidebar";
import CallList from "./components/CallList";
import MapPanel from "./components/MapPanel";
import CallDetailDrawer from "./components/CallDetailDrawer";
import { calls } from "./data";
import type { Call } from "./types";

export default function App() {
  const [selectedCall, setSelectedCall] = useState<Call | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const handleSelectCall = (call: Call) => {
    setSelectedCall(call);
    setDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setDrawerOpen(false);
  };

  return (
    <div className="h-screen w-screen flex overflow-hidden bg-[#f0f2f7]">
      {/* Icon sidebar */}
      <IconSidebar />

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

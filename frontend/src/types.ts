export interface TranscriptMessage {
  sender: "caller" | "ai";
  text: string;
  time: string;
  callerName?: string;
}

export interface Call {
  id: string;
  numberMasked: string;
  priority: "P1" | "P2" | "P3" | "P4";
  incidentType: string;
  incidentIcon: string;
  status: string;
  statusDetail?: string;
  locationLabel: string;
  address: string;
  city: string;
  confidence: number;
  inServiceArea: boolean;
  transcript: TranscriptMessage[];
  summary: string;
  keyFacts: string[];
  elapsed: string;
  aiHandling: boolean;
  pin: { lat: number; lng: number };
}




export type PriorityFilter = "All" | "P1" | "P2" | "P3" | "P4";

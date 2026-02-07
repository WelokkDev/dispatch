export interface TranscriptMessage {
  sender: "caller" | "ai";
  text: string;
  time: string;
  callerName?: string;
}

export interface Call {
  id: string;
  numberMasked: string;
  priority: "P0" | "P1" | "P2" | "P3";
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
  pinPosition: { top: string; left: string };
}

export type PriorityFilter = "All" | "P0" | "P1" | "P2" | "P3";

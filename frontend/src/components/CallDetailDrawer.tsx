import { useState, useEffect, useRef } from "react";
import type { Call } from "../types";
import { priorityColors, buttonColors, type Priority } from "../colors";

const STAGGER_MS = 320;

interface CallDetailDrawerProps {
  call: Call | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function CallDetailDrawer({ call, isOpen, onClose }: CallDetailDrawerProps) {
  const [visibleCount, setVisibleCount] = useState(0);
  const prevCallIdRef = useRef<string | null>(null);
  const prevTranscriptLenRef = useRef(0);
  const transcript = call?.transcript ?? [];
  const firstSender = transcript[0]?.sender ?? null;

  // When switching calls, show all messages immediately
  useEffect(() => {
    if (!call) return;
    if (prevCallIdRef.current !== call.id) {
      prevCallIdRef.current = call.id;
      prevTranscriptLenRef.current = transcript.length;
      setVisibleCount(transcript.length);
      return;
    }
    prevCallIdRef.current = call.id;

    // Transcript was replaced with one that starts with AI (e.g. 911 intro added).
    // Re-reveal from 0 so we don't snap: first slot was caller, now 911.
    const prevLen = prevTranscriptLenRef.current;
    prevTranscriptLenRef.current = transcript.length;
    if (
      transcript.length >= 2 &&
      firstSender === "ai" &&
      visibleCount === 1 &&
      prevLen === 1
    ) {
      setVisibleCount(0);
    }
  }, [call?.id, transcript.length, firstSender, visibleCount]);

  // Stagger-reveal new messages one by one (so they don't all pop in at once)
  useEffect(() => {
    if (!call || transcript.length <= visibleCount) return;
    const id = setInterval(() => {
      setVisibleCount((prev) => Math.min(prev + 1, transcript.length));
    }, STAGGER_MS);
    return () => clearInterval(id);
  }, [call?.id, transcript.length, visibleCount]);

  if (!call) return null;

  const visibleTranscript = transcript.slice(0, visibleCount);

  return (
    <>
      {/* Overlay (subtle) */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/5 z-30 transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Drawer */}
      <div
        className={`fixed top-0 right-0 h-full w-[400px] bg-white/95 backdrop-blur-md border-l border-slate-200/60 shadow-2xl shadow-slate-300/30 z-40 flex flex-col transition-transform duration-350 ease-[cubic-bezier(0.22,1,0.36,1)] ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Close chevron */}
        <button
          onClick={onClose}
          className="absolute -left-8 top-1/2 -translate-y-1/2 w-7 h-14 bg-white border border-slate-200 border-r-0 rounded-l-lg flex items-center justify-center shadow-sm hover:bg-slate-50 transition-colors cursor-pointer z-50"
        >
          <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>

        {/* Header */}
        <div className="px-6 pt-6 pb-4 border-b border-slate-100">
          {/* Top icons */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <button className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center hover:bg-slate-200 transition-colors cursor-pointer">
                <svg className="w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
              </button>
              <button className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center hover:bg-slate-200 transition-colors cursor-pointer">
                <svg className="w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                </svg>
              </button>
            </div>
            <div className="w-20 h-1.5 rounded-full bg-slate-200" />
          </div>

          {/* Phone number + badges */}
          <h2 className="text-lg font-bold text-slate-900 tracking-tight">{call.numberMasked}</h2>
          <div className="flex items-center gap-2 mt-2">
            <span 
              className="text-[11px] font-bold px-2 py-0.5 rounded-lg"
              style={{
                backgroundColor: priorityColors[call.priority as Priority].solid,
                color: "#ffffff",
              }}
            >
              {call.priority}
            </span>
            <div className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center">
              <span className="text-white text-[10px] font-bold">A</span>
            </div>
          </div>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-xs text-slate-500 bg-slate-50 px-2 py-1 rounded-lg border border-slate-100">
              {call.confidence}% confidence ✕
            </span>
          </div>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-sm font-medium text-slate-600">{call.status}</span>
            <span className="text-slate-300">•••</span>
          </div>
        </div>

        {/* Chat Transcript — messages revealed one-by-one with animation */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3 call-list-scroll">
          {visibleTranscript.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.sender === "caller" ? "justify-end" : "justify-start"} transcript-message-in`}
            >
              <div className="max-w-[85%]">
                {msg.sender === "ai" && (
                  <div className="flex items-center gap-2 mb-1">
                    <div className="w-5 h-5 rounded-full bg-slate-200 flex items-center justify-center">
                      <svg className="w-3 h-3 text-slate-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <span className="text-[11px] text-slate-400">{msg.time}</span>
                  </div>
                )}
                {msg.sender === "caller" && (
                  <div className="flex items-center justify-end gap-2 mb-1">
                    <span className="text-[11px] text-slate-400">{msg.time}</span>
                    {msg.callerName && (
                      <span className="text-[11px] font-medium text-slate-500">{msg.callerName}</span>
                    )}
                  </div>
                )}
                <div
                  className={`px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed ${
                    msg.sender === "caller"
                      ? "bg-slate-100 text-slate-700 rounded-tr-md"
                      : "bg-blue-50 text-slate-700 rounded-tl-md border border-blue-100/50"
                  }`}
                >
                  {msg.sender === "caller" && msg.callerName && (
                    <div className="flex items-center gap-1 mb-1">
                      <div className="w-4 h-4 rounded-full bg-blue-100 flex items-center justify-center">
                        <svg className="w-2.5 h-2.5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                        </svg>
                      </div>
                    </div>
                  )}
                  {msg.text}
                </div>
                {msg.sender === "caller" && msg.callerName && (
                  <div className="flex justify-end mt-1">
                    <span className="text-[10px] text-slate-400 flex items-center gap-1">
                      {msg.callerName}
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
          {/* Live: show typing indicator while AI is handling */}
          {call.aiHandling && (
            <div className="flex justify-start">
              <div className="px-3.5 py-2.5 rounded-2xl rounded-tl-md bg-blue-50 border border-blue-100/50 text-slate-500 text-sm">
                <span className="animate-pulse">...</span>
              </div>
            </div>
          )}
        </div>

        {/* Incident Summary & Key Facts */}
        <div className="border-t border-slate-100 px-6 py-4">
          <h3 className="text-sm font-bold text-slate-800 mb-2">Incident Summary</h3>
          <p className="text-sm text-slate-600 leading-relaxed mb-4">{call.summary}</p>

        </div>

        {/* Action Buttons */}
        <div className="px-6 py-4 border-t border-slate-100 flex gap-3">
          <button 
            className="flex-1 text-sm font-semibold py-2.5 px-4 rounded-xl transition-colors shadow-sm cursor-pointer hover:opacity-90"
            style={{
              backgroundColor: buttonColors.primary.bg,
              color: buttonColors.primary.text,
              boxShadow: `0 1px 2px ${buttonColors.primary.shadow}`,
            }}
          >
            Take Over Call
          </button>
        </div>
      </div>
    </>
  );
}

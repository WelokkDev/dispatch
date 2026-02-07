/**
 * =============================================
 * CENTRALIZED COLOR DEFINITIONS
 * =============================================
 * 
 * This file is the single source of truth for all colors in the app.
 * Edit values here to update colors across all components.
 * 
 * Note: CSS variables in index.css mirror these values for reference,
 * but components import from this file for actual usage.
 */

// ===========================================
// PRIORITY COLORS
// P0 = Critical (red)
// P1 = High (amber/orange)
// P2 = Medium (blue)
// P3 = Low (slate/gray)
// ===========================================

export const priorityColors = {
  P0: {
    solid: "#ef4444",       // Main color (pins, badges)
    solidHover: "#dc2626",  // Hover state
    bg: "#fef2f2",          // Light background
    bgHover: "#fee2e2",     // Light background hover
    border: "#fecaca",      // Border color
    text: "#b91c1c",        // Text on light bg
  },
  P1: {
    solid: "#f59e0b",
    solidHover: "#d97706",
    bg: "#fffbeb",
    bgHover: "#fef3c7",
    border: "#fde68a",
    text: "#b45309",
  },
  P2: {
    solid: "#3b82f6",
    solidHover: "#2563eb",
    bg: "#eff6ff",
    bgHover: "#dbeafe",
    border: "#bfdbfe",
    text: "#1d4ed8",
  },
  P3: {
    solid: "#94a3b8",
    solidHover: "#64748b",
    bg: "#f8fafc",
    bgHover: "#f1f5f9",
    border: "#e2e8f0",
    text: "#475569",
  },
} as const;

// Helper type for priority keys
export type Priority = keyof typeof priorityColors;

// ===========================================
// BUTTON COLORS
// ===========================================

export const buttonColors = {
  primary: {
    bg: "#859FB7",          // Blue
    bgHover: "#9DB1C9",
    text: "#ffffff",
    shadow: "rgba(37, 99, 235, 0.25)",
  },
  secondary: {
    bg: "#f1f5f9",          // Light slate
    bgHover: "#e2e8f0",
    text: "#334155",
    border: "#e2e8f0",
  },
  danger: {
    bg: "#ef4444",
    bgHover: "#dc2626",
    text: "#ffffff",
    shadow: "rgba(239, 68, 68, 0.25)",
  },
} as const;

// ===========================================
// STATUS COLORS
// ===========================================

export const statusColors = {
  active: {
    dot: "#22c55e",         // Green dot
    bg: "#dcfce7",
    text: "#16a34a",
  },
  aiHandling: {
    dot: "#10b981",         // Emerald
    bg: "#d1fae5",
    text: "#059669",
    waveform: "#34d399",
  },
  inProgress: {
    dot: "#3b82f6",
    bg: "#dbeafe",
    text: "#2563eb",
  },
  queued: {
    dot: "#94a3b8",
    bg: "#f1f5f9",
    text: "#64748b",
  },
} as const;

// ===========================================
// UI COLORS (backgrounds, borders, etc.)
// ===========================================

export const uiColors = {
  background: "#f0f2f7",
  cardBg: "rgba(255, 255, 255, 0.95)",
  cardBorder: "#e2e8f0",
  selectedRing: "#bfdbfe",
  selectedBorder: "#93c5fd",
} as const;

// ===========================================
// HELPER FUNCTIONS
// ===========================================

/**
 * Get Tailwind-style class string for priority badge
 */
export function getPriorityBadgeClasses(priority: Priority): string {
  const colors = priorityColors[priority];
  return `bg-[${colors.bg}] text-[${colors.text}] border-[${colors.border}]`;
}

/**
 * Get inline styles for priority badge (for components that can't use Tailwind)
 */
export function getPriorityBadgeStyles(priority: Priority) {
  const colors = priorityColors[priority];
  return {
    backgroundColor: colors.bg,
    color: colors.text,
    borderColor: colors.border,
  };
}

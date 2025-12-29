/**
 * Chart color palette for consistent styling across all charts.
 *
 * These colors are chosen to be visible in both light and dark themes.
 * Use these instead of CSS variables (oklch) which don't work reliably in Recharts.
 */

// Primary chart colors (for common use cases)
export const CHART_COLORS = {
  // Data visualization primary colors
  actual: "#22c55e", // Green - for actual/realized values
  forecast: "#94a3b8", // Slate - for forecast/predicted values
  primary: "#3b82f6", // Blue - primary highlight
  secondary: "#8b5cf6", // Purple - secondary highlight
  warning: "#eab308", // Yellow - warning/caution
  error: "#ef4444", // Red - errors/negative

  // Day-Ahead vs Real-Time
  dayAhead: "#3b82f6", // Blue
  realTime: "#22c55e", // Green

  // Grid and axis colors (work in both themes)
  grid: "#d1d5db", // Light gray
  gridDark: "#374151", // Dark gray (for dark mode)
  axis: "#6b7280", // Medium gray
  text: "#374151", // Dark gray text
  textLight: "#9ca3af", // Light gray text
};

// Location-specific colors (for price charts by location)
export const LOCATION_COLORS: Record<string, string> = {
  // Load Zones
  LZ_HOUSTON: "#ef4444", // Red
  LZ_NORTH: "#3b82f6", // Blue
  LZ_SOUTH: "#22c55e", // Green
  LZ_WEST: "#eab308", // Yellow
  LZ_AEN: "#a855f7", // Purple
  LZ_CPS: "#f97316", // Orange
  LZ_RAYBN: "#06b6d4", // Cyan
  LZ_LCRA: "#ec4899", // Pink

  // Trading Hubs
  HB_HOUSTON: "#dc2626", // Red (darker)
  HB_NORTH: "#2563eb", // Blue (darker)
  HB_SOUTH: "#16a34a", // Green (darker)
  HB_WEST: "#ca8a04", // Yellow (darker)
  HB_PAN: "#9333ea", // Purple (darker)
  HB_BUSAVG: "#ea580c", // Orange (darker)
  HB_HUBAVG: "#0891b2", // Cyan (darker)

  // DC Ties
  DC_E: "#7c3aed", // Violet
  DC_L: "#059669", // Emerald
  DC_N: "#0284c7", // Sky
  DC_R: "#d946ef", // Fuchsia
  DC_S: "#65a30d", // Lime
};

// Fuel type colors
export const FUEL_COLORS: Record<string, string> = {
  Wind: "#22c55e", // Green
  Solar: "#eab308", // Yellow
  Nuclear: "#a855f7", // Purple
  Coal: "#78716c", // Stone
  Gas: "#f97316", // Orange
  "Natural Gas": "#f97316", // Orange
  Hydro: "#06b6d4", // Cyan
  Other: "#6b7280", // Gray
};

// Chart area fill colors (with transparency)
export const FILL_COLORS = {
  primary: "rgba(59, 130, 246, 0.2)", // Blue 20%
  success: "rgba(34, 197, 94, 0.2)", // Green 20%
  warning: "rgba(234, 179, 8, 0.2)", // Yellow 20%
  error: "rgba(239, 68, 68, 0.2)", // Red 20%
};

/**
 * Get color for a location, with fallback
 */
export function getLocationColor(location: string): string {
  return LOCATION_COLORS[location] || "#6b7280";
}

/**
 * Get color for a fuel type, with fallback
 */
export function getFuelColor(fuelType: string): string {
  return FUEL_COLORS[fuelType] || "#6b7280";
}

/**
 * Theme-aware colors for Recharts components.
 * Use this to get colors that work correctly in both light and dark modes.
 */
export type ChartTheme = "light" | "dark";

export interface ChartThemeColors {
  // Tooltip styling
  tooltipBg: string;
  tooltipBorder: string;
  tooltipText: string;

  // Grid and axis
  grid: string;
  axisText: string;
  axisLine: string;

  // Legend
  legendText: string;
}

export function getChartThemeColors(theme: ChartTheme): ChartThemeColors {
  if (theme === "dark") {
    return {
      tooltipBg: "#1f2937", // gray-800
      tooltipBorder: "#374151", // gray-700
      tooltipText: "#f3f4f6", // gray-100

      grid: "#374151", // gray-700
      axisText: "#9ca3af", // gray-400
      axisLine: "#4b5563", // gray-600

      legendText: "#f3f4f6", // gray-100
    };
  }

  // Light mode
  return {
    tooltipBg: "#ffffff", // white
    tooltipBorder: "#e5e7eb", // gray-200
    tooltipText: "#1f2937", // gray-800

    grid: "#e5e7eb", // gray-200
    axisText: "#6b7280", // gray-500
    axisLine: "#d1d5db", // gray-300

    legendText: "#374151", // gray-700
  };
}

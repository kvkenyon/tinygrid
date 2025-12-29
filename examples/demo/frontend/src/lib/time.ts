/**
 * Format a timestamp with timezone indicator
 */
export function formatTimestamp(date: Date | string | null | undefined, timezone: string = "America/Chicago"): string {
  if (!date) return "";
  
  const d = typeof date === "string" ? new Date(date) : date;
  if (isNaN(d.getTime())) return "";
  
  const tzAbbr = getTimezoneAbbr(timezone);
  
  return d.toLocaleString("en-US", {
    timeZone: timezone,
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }) + ` ${tzAbbr}`;
}

/**
 * Get current time formatted with timezone
 */
export function getCurrentTime(timezone: string = "America/Chicago"): string {
  return formatTimestamp(new Date(), timezone);
}

/**
 * Get timezone abbreviation
 */
export function getTimezoneAbbr(timezone: string): string {
  const abbrs: Record<string, string> = {
    "America/Chicago": "CT",
    "America/New_York": "ET",
    "America/Los_Angeles": "PT",
    "America/Denver": "MT",
    "UTC": "UTC",
  };
  return abbrs[timezone] || timezone.split("/").pop() || "";
}

/**
 * Format just the time portion with timezone
 */
export function formatTime(date: Date | string | null | undefined, timezone: string = "America/Chicago"): string {
  if (!date) return "";
  
  const d = typeof date === "string" ? new Date(date) : date;
  if (isNaN(d.getTime())) return "";
  
  const tzAbbr = getTimezoneAbbr(timezone);
  
  return d.toLocaleTimeString("en-US", {
    timeZone: timezone,
    hour: "2-digit",
    minute: "2-digit",
  }) + ` ${tzAbbr}`;
}

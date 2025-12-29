import { useState, useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useLMPGrid, useSPPGrid, type PriceGridParams, type LocationPriceData } from "../api";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
  Loading,
  ErrorCard,
} from "../components";
import { useTheme } from "../context/ThemeContext";
import { formatPrice } from "../lib/utils";
import { formatTime } from "../lib/time";
import { getLocationColor, getChartThemeColors } from "../lib/chartColors";
import { DollarSign, TrendingUp, Clock, RefreshCw, Calendar } from "lucide-react";

const TIMEZONE = "America/Chicago";

// Date range options
type DateRangeOption = "today" | "yesterday" | "3days" | "7days";

const DATE_RANGE_OPTIONS: { value: DateRangeOption; label: string }[] = [
  { value: "today", label: "Today" },
  { value: "yesterday", label: "Yesterday" },
  { value: "3days", label: "Last 3 Days" },
  { value: "7days", label: "Last 7 Days" },
];

function getDateRange(option: DateRangeOption): { start: string; end?: string } {
  const today = new Date();
  const formatDate = (d: Date) => d.toISOString().split("T")[0];

  switch (option) {
    case "today":
      return { start: "today" };
    case "yesterday":
      return { start: "yesterday", end: "today" };
    case "3days": {
      const start = new Date(today);
      start.setDate(start.getDate() - 3);
      return { start: formatDate(start), end: formatDate(today) };
    }
    case "7days": {
      const start = new Date(today);
      start.setDate(start.getDate() - 7);
      return { start: formatDate(start), end: formatDate(today) };
    }
    default:
      return { start: "today" };
  }
}

// Timestamp badge component
function TimestampBadge({ timestamp, label }: { timestamp?: string | null; label?: string }) {
  const formattedTime = timestamp ? formatTime(timestamp, TIMEZONE) : "";
  if (!formattedTime) return null;
  return (
    <div className="flex items-center gap-1.5 text-xs text-base-content/60">
      <Clock className="h-3 w-3" />
      <span>{label ? `${label}: ` : ""}{formattedTime}</span>
    </div>
  );
}

// Mini chart for a single location
function MiniPriceChart({ location }: { location: LocationPriceData }) {
  const { theme } = useTheme();
  const themeColors = getChartThemeColors(theme);
  const color = getLocationColor(location.location);

  // Get last 48 data points for display
  const chartData = useMemo(() => {
    const data = location.data.slice(-48);
    return data.map((d, idx) => ({
      idx,
      price: d.price,
      time: d.time,
    }));
  }, [location.data]);

  const locationTypeLabel = {
    load_zone: "Load Zone",
    trading_hub: "Hub",
    dc_tie: "DC Tie",
    unknown: "",
  }[location.location_type];

  return (
    <div className="bg-base-200 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: color }}
          />
          <span className="font-medium text-sm">{location.location}</span>
          <span className="text-xs text-base-content/50">{locationTypeLabel}</span>
        </div>
        <div className="text-right">
          <div className="text-lg font-bold" style={{ color }}>
            {location.latest_price !== null ? formatPrice(location.latest_price) : "—"}
          </div>
        </div>
      </div>

      {/* Mini chart */}
      <div className="h-36">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 25 }}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={themeColors.grid}
              vertical={false}
              horizontal={true}
            />
            <XAxis
              dataKey="idx"
              tick={{ fontSize: 9, fill: themeColors.axisText }}
              tickLine={false}
              axisLine={{ stroke: themeColors.axisLine }}
              tickFormatter={(val) => {
                // Show time label for first and last point
                if (val === 0 || val === chartData.length - 1) {
                  const point = chartData[val];
                  if (point?.time) {
                    const t = new Date(point.time);
                    return t.toLocaleTimeString("en-US", {
                      hour: "numeric",
                      minute: "2-digit",
                      timeZone: TIMEZONE,
                    });
                  }
                }
                return "";
              }}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fontSize: 9, fill: themeColors.axisText }}
              tickLine={false}
              axisLine={{ stroke: themeColors.axisLine }}
              tickFormatter={(val) => `$${val.toFixed(0)}`}
              domain={["auto", "auto"]}
              width={25}
            />
            <Tooltip
              formatter={(value) => [formatPrice(Number(value ?? 0)), "Price"]}
              labelFormatter={(_, payload) => {
                const time = payload?.[0]?.payload?.time;
                return time ? formatTime(time, TIMEZONE) : "";
              }}
              contentStyle={{
                backgroundColor: themeColors.tooltipBg,
                border: `1px solid ${themeColors.tooltipBorder}`,
                borderRadius: "0.375rem",
                fontSize: "12px",
                color: themeColors.tooltipText,
              }}
              labelStyle={{ color: themeColors.tooltipText }}
              itemStyle={{ color: themeColors.tooltipText }}
            />
            <Line
              type="linear"
              dataKey="price"
              stroke={color}
              strokeWidth={1.5}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Stats row */}
      <div className="flex justify-between text-xs text-base-content/60 mt-1">
        <span>Low: {location.min_price !== null ? formatPrice(location.min_price) : "—"}</span>
        <span>Avg: {location.avg_price !== null ? formatPrice(location.avg_price) : "—"}</span>
        <span>High: {location.max_price !== null ? formatPrice(location.max_price) : "—"}</span>
      </div>
    </div>
  );
}

// Price grid section
function PriceGridSection({
  title,
  icon: Icon,
  locations,
  isLoading,
  error,
  onRefresh,
  latestUpdate,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  locations: LocationPriceData[];
  isLoading: boolean;
  error: Error | null;
  onRefresh: () => void;
  latestUpdate: string | null;
}) {
  // Group locations by type
  const { loadZones, tradingHubs, dcTies } = useMemo(() => {
    const loadZones: LocationPriceData[] = [];
    const tradingHubs: LocationPriceData[] = [];
    const dcTies: LocationPriceData[] = [];

    for (const loc of locations) {
      if (loc.location_type === "load_zone") {
        loadZones.push(loc);
      } else if (loc.location_type === "trading_hub") {
        tradingHubs.push(loc);
      } else if (loc.location_type === "dc_tie") {
        dcTies.push(loc);
      }
    }

    return { loadZones, tradingHubs, dcTies };
  }, [locations]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <Icon className="h-4 w-4 text-success" />
            <CardTitle>{title}</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <TimestampBadge timestamp={latestUpdate} label="Updated" />
            <button onClick={onRefresh} className="btn btn-ghost btn-xs btn-circle">
              <RefreshCw className="h-3 w-3" />
            </button>
          </div>
        </div>
        <CardDescription>
          {locations.length} locations
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Loading className="py-8" />
        ) : error ? (
          <ErrorCard
            message={error instanceof Error ? error.message : "Failed to load data"}
            onRetry={onRefresh}
          />
        ) : locations.length === 0 ? (
          <p className="text-center py-8 text-sm text-base-content/50">
            No price data available
          </p>
        ) : (
          <div className="space-y-6">
            {/* Load Zones */}
            {loadZones.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-base-content/70 mb-3">Load Zones</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {loadZones.map((loc) => (
                    <MiniPriceChart key={loc.location} location={loc} />
                  ))}
                </div>
              </div>
            )}

            {/* Trading Hubs */}
            {tradingHubs.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-base-content/70 mb-3">Trading Hubs</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {tradingHubs.map((loc) => (
                    <MiniPriceChart key={loc.location} location={loc} />
                  ))}
                </div>
              </div>
            )}

            {/* DC Ties */}
            {dcTies.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-base-content/70 mb-3">DC Ties</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {dcTies.map((loc) => (
                    <MiniPriceChart key={loc.location} location={loc} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Main component
export function Prices() {
  const [dateRange, setDateRange] = useState<DateRangeOption>("today");
  const [sppMarket, setSppMarket] = useState<"real_time_15_min" | "day_ahead_hourly">("real_time_15_min");

  const dateParams = getDateRange(dateRange);

  const lmpParams: PriceGridParams = {
    start: dateParams.start,
    end: dateParams.end,
  };

  const sppParams: PriceGridParams = {
    start: dateParams.start,
    end: dateParams.end,
    market: sppMarket,
  };

  const {
    data: lmpData,
    isLoading: lmpLoading,
    error: lmpError,
    refetch: lmpRefetch,
  } = useLMPGrid(lmpParams);

  const {
    data: sppData,
    isLoading: sppLoading,
    error: sppError,
    refetch: sppRefetch,
  } = useSPPGrid(sppParams);

  return (
    <div className="space-y-6">
      {/* Header with controls */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Electricity Prices</h1>
          <p className="text-sm text-base-content/60">
            Real-time LMP and SPP data for all ERCOT locations
          </p>
        </div>

        {/* Date range selector */}
        <div className="flex items-center gap-3">
          <Calendar className="h-4 w-4 text-base-content/60" />
          <div className="join">
            {DATE_RANGE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                className={`join-item btn btn-sm ${dateRange === opt.value ? "btn-primary" : "btn-ghost"
                  }`}
                onClick={() => setDateRange(opt.value)}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* LMP Grid */}
      <PriceGridSection
        title="Locational Marginal Prices (LMP)"
        icon={DollarSign}
        locations={lmpData?.locations || []}
        isLoading={lmpLoading}
        error={lmpError as Error | null}
        onRefresh={() => lmpRefetch()}
        latestUpdate={lmpData?.latest_update || null}
      />

      {/* SPP Grid with market toggle */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-primary" />
            <h2 className="text-lg font-semibold">Settlement Point Prices (SPP)</h2>
          </div>
          <div className="join">
            <button
              className={`join-item btn btn-sm ${sppMarket === "real_time_15_min" ? "btn-primary" : "btn-ghost"
                }`}
              onClick={() => setSppMarket("real_time_15_min")}
            >
              Real-Time
            </button>
            <button
              className={`join-item btn btn-sm ${sppMarket === "day_ahead_hourly" ? "btn-primary" : "btn-ghost"
                }`}
              onClick={() => setSppMarket("day_ahead_hourly")}
            >
              Day-Ahead
            </button>
          </div>
        </div>

        <Card>
          <CardContent className="pt-4">
            {sppLoading ? (
              <Loading className="py-8" />
            ) : sppError ? (
              <ErrorCard
                message={sppError instanceof Error ? sppError.message : "Failed to load data"}
                onRetry={() => sppRefetch()}
              />
            ) : !sppData?.locations?.length ? (
              <p className="text-center py-8 text-sm text-base-content/50">
                No SPP data available
              </p>
            ) : (
              <div className="space-y-6">
                {/* Group by location type */}
                {(() => {
                  const loadZones = sppData.locations.filter(l => l.location_type === "load_zone");
                  const tradingHubs = sppData.locations.filter(l => l.location_type === "trading_hub");
                  const dcTies = sppData.locations.filter(l => l.location_type === "dc_tie");

                  return (
                    <>
                      {loadZones.length > 0 && (
                        <div>
                          <h3 className="text-sm font-medium text-base-content/70 mb-3">Load Zones</h3>
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {loadZones.map((loc) => (
                              <MiniPriceChart key={loc.location} location={loc} />
                            ))}
                          </div>
                        </div>
                      )}
                      {tradingHubs.length > 0 && (
                        <div>
                          <h3 className="text-sm font-medium text-base-content/70 mb-3">Trading Hubs</h3>
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {tradingHubs.map((loc) => (
                              <MiniPriceChart key={loc.location} location={loc} />
                            ))}
                          </div>
                        </div>
                      )}
                      {dcTies.length > 0 && (
                        <div>
                          <h3 className="text-sm font-medium text-base-content/70 mb-3">DC Ties</h3>
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {dcTies.map((loc) => (
                              <MiniPriceChart key={loc.location} location={loc} />
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  );
                })()}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Auto-refresh indicator */}
      <div className="text-center text-xs text-base-content/40">
        Data auto-refreshes every 60 seconds
      </div>
    </div>
  );
}

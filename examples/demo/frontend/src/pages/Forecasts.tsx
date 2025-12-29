import { useState, useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";
import { useLoad, useWindForecast, useSolarForecast } from "../api";
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
import { formatMW, formatNumber } from "../lib/utils";
import { formatTime } from "../lib/time";
import { CHART_COLORS, FILL_COLORS, getChartThemeColors } from "../lib/chartColors";
import { Wind, Sun, Gauge, Clock } from "lucide-react";

const TIMEZONE = "America/Chicago";

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

type ZoneType = "weather_zone" | "forecast_zone";
type Resolution = "hourly" | "5min";

function LoadCard() {
  const { theme } = useTheme();
  const themeColors = getChartThemeColors(theme);
  const [zoneType, setZoneType] = useState<ZoneType>("weather_zone");
  const [startDate, setStartDate] = useState("yesterday");

  const { data: loadData, isLoading, error, refetch } = useLoad({
    start: startDate,
    by: zoneType,
  });

  const chartData = loadData?.data
    ? loadData.data.slice(0, 50).map((record, idx) => ({
      index: idx,
      load: Number(record["Total"] || record["total"] || 0),
      operatingDay: String(record["Operating Day"] || ""),
      hour: idx,
    }))
    : [];

  // Get latest timestamp
  const latestTime = loadData?.data?.[loadData.data.length - 1]?.["Operating Day"] as string | undefined;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <Gauge className="h-4 w-4 text-primary" />
            <CardTitle>System Load</CardTitle>
          </div>
          <TimestampBadge timestamp={latestTime} />
        </div>
        <CardDescription>
          {loadData?.count ? `${formatNumber(loadData.count)} records` : "Loading..."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
          <div className="form-control">
            <label className="label">
              <span className="label-text text-xs">Zone Type</span>
            </label>
            <select
              value={zoneType}
              onChange={(e) => setZoneType(e.target.value as ZoneType)}
              className="select select-bordered select-sm w-full"
            >
              <option value="weather_zone">Weather Zone</option>
              <option value="forecast_zone">Forecast Zone</option>
            </select>
          </div>
          <div className="form-control">
            <label className="label">
              <span className="label-text text-xs">Date</span>
            </label>
            <select
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="select select-bordered select-sm w-full"
            >
              <option value="today">Today</option>
              <option value="yesterday">Yesterday</option>
            </select>
          </div>
        </div>

        {isLoading ? (
          <Loading className="py-8" />
        ) : error ? (
          <ErrorCard
            message={error instanceof Error ? error.message : "Failed to load data"}
            onRetry={() => refetch()}
          />
        ) : chartData.length > 0 ? (
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={themeColors.grid} vertical={false} />
                <XAxis
                  dataKey="hour"
                  tick={{ fontSize: 10, fill: themeColors.axisText }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: themeColors.axisText }}
                  tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  formatter={(value) => formatMW(Number(value ?? 0))}
                  labelFormatter={(_, payload) => `Date: ${payload?.[0]?.payload?.operatingDay || ""}`}
                  contentStyle={{
                    backgroundColor: themeColors.tooltipBg,
                    border: `1px solid ${themeColors.tooltipBorder}`,
                    borderRadius: "0.5rem",
                    color: themeColors.tooltipText,
                  }}
                  labelStyle={{ color: themeColors.tooltipText }}
                  itemStyle={{ color: themeColors.tooltipText }}
                />
                <Legend wrapperStyle={{ fontSize: 11, color: themeColors.legendText }} />
                <Area
                  type="monotone"
                  dataKey="load"
                  stroke={CHART_COLORS.primary}
                  fill={FILL_COLORS.primary}
                  strokeWidth={2}
                  name="Load (MW)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="text-center py-8 text-sm text-base-content/50">
            No load data available
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function WindForecastCard() {
  const { theme } = useTheme();
  const themeColors = getChartThemeColors(theme);
  const [resolution, setResolution] = useState<Resolution>("hourly");
  const [byRegion, setByRegion] = useState(false);
  const [startDate, setStartDate] = useState("today");

  const { data: windData, isLoading, error, refetch } = useWindForecast({
    start: startDate,
    resolution,
    by_region: byRegion,
  });

  // Process chart data with flexible column name matching
  const { chartData, latestTime, hasData } = useMemo(() => {
    if (!windData?.data || windData.data.length === 0) {
      return { chartData: [], latestTime: null, hasData: false };
    }

    // Find the correct column names (they may vary)
    const firstRecord = windData.data[0];
    const keys = Object.keys(firstRecord);

    // Try different possible column names for actual generation
    const actualKey =
      keys.find(
        (k) =>
          k.toLowerCase().includes("generation") ||
          k.toLowerCase().includes("actual") ||
          k === "System Wide"
      ) || "Generation System Wide";

    // Try different possible column names for forecast
    const forecastKey =
      keys.find(
        (k) =>
          k.toLowerCase().includes("stwpf") ||
          k.toLowerCase().includes("forecast") ||
          k.toLowerCase().includes("stppf")
      ) || "STWPF System Wide";

    // Try different possible column names for time
    const timeKey =
      keys.find((k) => k.toLowerCase().includes("time") || k.toLowerCase().includes("hour")) ||
      "Time";

    const data = windData.data.slice(0, 100).map((record, idx) => {
      const actualVal = Number(record[actualKey] || 0);
      const forecastVal = Number(record[forecastKey] || 0);

      return {
        index: idx,
        actual: actualVal,
        forecast: forecastVal,
        time: String(record[timeKey] || ""),
        hour: idx,
      };
    });

    // Filter out records where both values are 0 (no real data)
    const hasRealData = data.some((d) => d.actual > 0 || d.forecast > 0);

    const lastTime = windData.data[windData.data.length - 1]?.[timeKey] as string | undefined;

    return { chartData: data, latestTime: lastTime, hasData: hasRealData };
  }, [windData]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <Wind className="h-4 w-4 text-success" />
            <CardTitle>Wind Forecast</CardTitle>
          </div>
          <TimestampBadge timestamp={latestTime} />
        </div>
        <CardDescription>
          {windData?.count ? `${formatNumber(windData.count)} records` : "Loading..."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="form-control">
            <label className="label">
              <span className="label-text text-xs">Resolution</span>
            </label>
            <select
              value={resolution}
              onChange={(e) => setResolution(e.target.value as Resolution)}
              className="select select-bordered select-sm w-full"
            >
              <option value="hourly">Hourly</option>
              <option value="5min">5-Minute</option>
            </select>
          </div>
          <div className="form-control">
            <label className="label">
              <span className="label-text text-xs">Date</span>
            </label>
            <select
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="select select-bordered select-sm w-full"
            >
              <option value="today">Today</option>
              <option value="yesterday">Yesterday</option>
            </select>
          </div>
          <div className="form-control">
            <label className="label cursor-pointer justify-start gap-2">
              <input
                type="checkbox"
                checked={byRegion}
                onChange={(e) => setByRegion(e.target.checked)}
                className="checkbox checkbox-sm checkbox-primary"
              />
              <span className="label-text text-xs">By Region</span>
            </label>
          </div>
        </div>

        {isLoading ? (
          <Loading className="py-8" />
        ) : error ? (
          <ErrorCard
            message={error instanceof Error ? error.message : "Failed to load data"}
            onRetry={() => refetch()}
          />
        ) : chartData.length > 0 && hasData ? (
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={themeColors.grid} vertical={false} />
                <XAxis
                  dataKey="hour"
                  tick={{ fontSize: 10, fill: themeColors.axisText }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: themeColors.axisText }}
                  tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                  axisLine={false}
                  tickLine={false}
                  domain={[0, "auto"]}
                />
                <Tooltip
                  formatter={(value) => formatMW(Number(value ?? 0))}
                  contentStyle={{
                    backgroundColor: themeColors.tooltipBg,
                    border: `1px solid ${themeColors.tooltipBorder}`,
                    borderRadius: "0.5rem",
                    color: themeColors.tooltipText,
                  }}
                  labelStyle={{ color: themeColors.tooltipText }}
                  itemStyle={{ color: themeColors.tooltipText }}
                />
                <Legend wrapperStyle={{ fontSize: 10, color: themeColors.legendText }} />
                <Line
                  type="monotone"
                  dataKey="actual"
                  stroke={CHART_COLORS.actual}
                  strokeWidth={2}
                  dot={false}
                  name="Actual (MW)"
                  connectNulls
                />
                <Line
                  type="monotone"
                  dataKey="forecast"
                  stroke={CHART_COLORS.forecast}
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                  name="Forecast (MW)"
                  connectNulls
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="text-center py-8 text-sm text-base-content/50">
            No wind forecast data available
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function SolarForecastCard() {
  const { theme } = useTheme();
  const themeColors = getChartThemeColors(theme);
  const [resolution, setResolution] = useState<Resolution>("hourly");
  const [byRegion, setByRegion] = useState(false);
  const [startDate, setStartDate] = useState("today");

  const { data: solarData, isLoading, error, refetch } = useSolarForecast({
    start: startDate,
    resolution,
    by_region: byRegion,
  });

  // Process chart data with flexible column name matching
  const { chartData, latestTime, hasData } = useMemo(() => {
    if (!solarData?.data || solarData.data.length === 0) {
      return { chartData: [], latestTime: null, hasData: false };
    }

    // Find the correct column names (they may vary)
    const firstRecord = solarData.data[0];
    const keys = Object.keys(firstRecord);

    // Try different possible column names for actual generation
    const actualKey =
      keys.find(
        (k) =>
          k.toLowerCase().includes("generation") ||
          k.toLowerCase().includes("actual") ||
          k === "System Wide"
      ) || "Generation System Wide";

    // Try different possible column names for forecast (STPPF for solar)
    const forecastKey =
      keys.find((k) => k.toLowerCase().includes("stppf") || k.toLowerCase().includes("forecast")) ||
      "STPPF System Wide";

    // Try different possible column names for time
    const timeKey =
      keys.find((k) => k.toLowerCase().includes("time") || k.toLowerCase().includes("hour")) ||
      "Time";

    const data = solarData.data.slice(0, 100).map((record, idx) => {
      const actualVal = Number(record[actualKey] || 0);
      const forecastVal = Number(record[forecastKey] || 0);

      return {
        index: idx,
        actual: actualVal,
        forecast: forecastVal,
        time: String(record[timeKey] || ""),
        hour: idx,
      };
    });

    // Filter out records where both values are 0 (no real data)
    const hasRealData = data.some((d) => d.actual > 0 || d.forecast > 0);

    const lastTime = solarData.data[solarData.data.length - 1]?.[timeKey] as string | undefined;

    return { chartData: data, latestTime: lastTime, hasData: hasRealData };
  }, [solarData]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <Sun className="h-4 w-4 text-warning" />
            <CardTitle>Solar Forecast</CardTitle>
          </div>
          <TimestampBadge timestamp={latestTime} />
        </div>
        <CardDescription>
          {solarData?.count ? `${formatNumber(solarData.count)} records` : "Loading..."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="form-control">
            <label className="label">
              <span className="label-text text-xs">Resolution</span>
            </label>
            <select
              value={resolution}
              onChange={(e) => setResolution(e.target.value as Resolution)}
              className="select select-bordered select-sm w-full"
            >
              <option value="hourly">Hourly</option>
              <option value="5min">5-Minute</option>
            </select>
          </div>
          <div className="form-control">
            <label className="label">
              <span className="label-text text-xs">Date</span>
            </label>
            <select
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="select select-bordered select-sm w-full"
            >
              <option value="today">Today</option>
              <option value="yesterday">Yesterday</option>
            </select>
          </div>
          <div className="form-control">
            <label className="label cursor-pointer justify-start gap-2">
              <input
                type="checkbox"
                checked={byRegion}
                onChange={(e) => setByRegion(e.target.checked)}
                className="checkbox checkbox-sm checkbox-primary"
              />
              <span className="label-text text-xs">By Region</span>
            </label>
          </div>
        </div>

        {isLoading ? (
          <Loading className="py-8" />
        ) : error ? (
          <ErrorCard
            message={error instanceof Error ? error.message : "Failed to load data"}
            onRetry={() => refetch()}
          />
        ) : chartData.length > 0 && hasData ? (
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={themeColors.grid} vertical={false} />
                <XAxis
                  dataKey="hour"
                  tick={{ fontSize: 10, fill: themeColors.axisText }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: themeColors.axisText }}
                  tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                  axisLine={false}
                  tickLine={false}
                  domain={[0, "auto"]}
                />
                <Tooltip
                  formatter={(value) => formatMW(Number(value ?? 0))}
                  contentStyle={{
                    backgroundColor: themeColors.tooltipBg,
                    border: `1px solid ${themeColors.tooltipBorder}`,
                    borderRadius: "0.5rem",
                    color: themeColors.tooltipText,
                  }}
                  labelStyle={{ color: themeColors.tooltipText }}
                  itemStyle={{ color: themeColors.tooltipText }}
                />
                <Legend wrapperStyle={{ fontSize: 10, color: themeColors.legendText }} />
                <Line
                  type="monotone"
                  dataKey="actual"
                  stroke={CHART_COLORS.warning}
                  strokeWidth={2}
                  dot={false}
                  name="Actual (MW)"
                  connectNulls
                />
                <Line
                  type="monotone"
                  dataKey="forecast"
                  stroke={CHART_COLORS.forecast}
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                  name="Forecast (MW)"
                  connectNulls
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="text-center py-8 text-sm text-base-content/50">
            No solar forecast data available
          </p>
        )}
      </CardContent>
    </Card>
  );
}

export function Forecasts() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Load & Renewable Forecasts</h1>
        <p className="text-sm text-base-content/60">System load and renewable generation data</p>
      </div>

      <LoadCard />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <WindForecastCard />
        <SolarForecastCard />
      </div>
    </div>
  );
}

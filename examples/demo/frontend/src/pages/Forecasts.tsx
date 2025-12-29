import { useState } from "react";
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
import { formatMW, formatNumber } from "../lib/utils";
import { formatTime } from "../lib/time";
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
                <CartesianGrid strokeDasharray="3 3" className="stroke-base-300" vertical={false} />
                <XAxis 
                  dataKey="hour" 
                  tick={{ fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 10 }}
                  tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  formatter={(value) => formatMW(Number(value ?? 0))}
                  labelFormatter={(_, payload) => `Date: ${payload?.[0]?.payload?.operatingDay || ""}`}
                  contentStyle={{ backgroundColor: 'oklch(var(--b2))', border: '1px solid oklch(var(--b3))', borderRadius: '0.5rem' }}
                  labelStyle={{ color: 'oklch(var(--bc))' }}
                  itemStyle={{ color: 'oklch(var(--bc))' }}
                />
                <Legend 
                  wrapperStyle={{ fontSize: 11 }}
                  formatter={(value) => <span style={{ color: 'oklch(var(--bc))' }}>{value}</span>}
                />
                <Area
                  type="monotone"
                  dataKey="load"
                  stroke="oklch(var(--p))"
                  fill="oklch(var(--p) / 0.2)"
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
  const [resolution, setResolution] = useState<Resolution>("hourly");
  const [byRegion, setByRegion] = useState(false);
  const [startDate, setStartDate] = useState("yesterday");

  const { data: windData, isLoading, error, refetch } = useWindForecast({
    start: startDate,
    resolution,
    by_region: byRegion,
  });

  const chartData = windData?.data
    ? windData.data.slice(0, 100).map((record, idx) => ({
        index: idx,
        actual: Number(record["Generation System Wide"] || 0),
        forecast: Number(record["STWPF System Wide"] || 0),
        time: String(record["Time"] || ""),
        hour: idx,
      }))
    : [];

  // Get latest timestamp
  const latestTime = windData?.data?.[windData.data.length - 1]?.["Time"] as string | undefined;

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
        ) : chartData.length > 0 ? (
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-base-300" vertical={false} />
                <XAxis dataKey="hour" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis
                  tick={{ fontSize: 10 }}
                  tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip 
                  formatter={(value) => formatMW(Number(value ?? 0))}
                  contentStyle={{ backgroundColor: 'oklch(var(--b2))', border: '1px solid oklch(var(--b3))', borderRadius: '0.5rem' }}
                  labelStyle={{ color: 'oklch(var(--bc))' }}
                  itemStyle={{ color: 'oklch(var(--bc))' }}
                />
                <Legend 
                  wrapperStyle={{ fontSize: 10 }}
                  formatter={(value) => <span style={{ color: 'oklch(var(--bc))' }}>{value}</span>}
                />
                <Line type="monotone" dataKey="actual" stroke="oklch(var(--su))" strokeWidth={2} dot={false} name="Actual (MW)" />
                <Line type="monotone" dataKey="forecast" stroke="oklch(var(--bc) / 0.5)" strokeWidth={2} strokeDasharray="5 5" dot={false} name="Forecast (MW)" />
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
  const [resolution, setResolution] = useState<Resolution>("hourly");
  const [byRegion, setByRegion] = useState(false);
  const [startDate, setStartDate] = useState("yesterday");

  const { data: solarData, isLoading, error, refetch } = useSolarForecast({
    start: startDate,
    resolution,
    by_region: byRegion,
  });

  const chartData = solarData?.data
    ? solarData.data.slice(0, 100).map((record, idx) => ({
        index: idx,
        actual: Number(record["Generation System Wide"] || 0),
        forecast: Number(record["STPPF System Wide"] || 0),
        time: String(record["Time"] || ""),
        hour: idx,
      }))
    : [];

  // Get latest timestamp
  const latestTime = solarData?.data?.[solarData.data.length - 1]?.["Time"] as string | undefined;

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
        ) : chartData.length > 0 ? (
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-base-300" vertical={false} />
                <XAxis dataKey="hour" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis
                  tick={{ fontSize: 10 }}
                  tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip 
                  formatter={(value) => formatMW(Number(value ?? 0))}
                  contentStyle={{ backgroundColor: 'oklch(var(--b2))', border: '1px solid oklch(var(--b3))', borderRadius: '0.5rem' }}
                  labelStyle={{ color: 'oklch(var(--bc))' }}
                  itemStyle={{ color: 'oklch(var(--bc))' }}
                />
                <Legend 
                  wrapperStyle={{ fontSize: 10 }}
                  formatter={(value) => <span style={{ color: 'oklch(var(--bc))' }}>{value}</span>}
                />
                <Line type="monotone" dataKey="actual" stroke="oklch(var(--wa))" strokeWidth={2} dot={false} name="Actual (MW)" />
                <Line type="monotone" dataKey="forecast" stroke="oklch(var(--bc) / 0.5)" strokeWidth={2} strokeDasharray="5 5" dot={false} name="Forecast (MW)" />
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

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
import { Wind, Sun, Gauge } from "lucide-react";

type ZoneType = "weather_zone" | "forecast_zone";
type Resolution = "hourly" | "5min";

function LoadCard() {
  const [zoneType, setZoneType] = useState<ZoneType>("weather_zone");
  const [startDate, setStartDate] = useState("yesterday");

  const { data: loadData, isLoading, error, refetch } = useLoad({
    start: startDate,
    by: zoneType,
  });

  // Process data for display
  // API returns: Operating Day, Coast, East, Far West, North, NorthC, Southern, SouthC, West, Total
  const chartData = loadData?.data
    ? loadData.data.slice(0, 50).map((record, idx) => ({
        index: idx,
        load: Number(record["Total"] || record["total"] || 0),
        operatingDay: String(record["Operating Day"] || ""),
        hour: idx,
      }))
    : [];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Gauge className="h-4 w-4" style={{ color: 'var(--accent-cyan)' }} />
          <CardTitle>System Load</CardTitle>
        </div>
        <CardDescription>
          {loadData?.count
            ? `${formatNumber(loadData.count)} records`
            : "Loading..."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
          <div>
            <label 
              className="block text-[10px] font-medium tracking-widest uppercase mb-1"
              style={{ color: 'var(--text-muted)' }}
            >
              Zone Type
            </label>
            <select
              value={zoneType}
              onChange={(e) => setZoneType(e.target.value as ZoneType)}
              className="w-full px-3 py-2 text-sm border"
            >
              <option value="weather_zone">Weather Zone</option>
              <option value="forecast_zone">Forecast Zone</option>
            </select>
          </div>
          <div>
            <label 
              className="block text-[10px] font-medium tracking-widest uppercase mb-1"
              style={{ color: 'var(--text-muted)' }}
            >
              Date
            </label>
            <select
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 text-sm border"
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
                <CartesianGrid 
                  strokeDasharray="3 3" 
                  stroke="var(--border-primary)"
                  vertical={false}
                />
                <XAxis 
                  dataKey="hour" 
                  tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
                  axisLine={{ stroke: 'var(--border-primary)' }}
                  tickLine={{ stroke: 'var(--border-primary)' }}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
                  tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                  axisLine={{ stroke: 'var(--border-primary)' }}
                  tickLine={{ stroke: 'var(--border-primary)' }}
                />
                <Tooltip
                  formatter={(value) => formatMW(Number(value ?? 0))}
                  labelFormatter={(_, payload) =>
                    `Date: ${payload?.[0]?.payload?.operatingDay || ""}`
                  }
                  contentStyle={{
                    backgroundColor: 'var(--bg-elevated)',
                    border: '1px solid var(--border-secondary)',
                    borderRadius: 0,
                    fontSize: 12,
                  }}
                  labelStyle={{ color: 'var(--text-primary)' }}
                />
                <Legend 
                  wrapperStyle={{ fontSize: 11 }}
                  formatter={(value) => <span style={{ color: 'var(--text-secondary)' }}>{value}</span>}
                />
                <Area
                  type="monotone"
                  dataKey="load"
                  stroke="var(--accent-cyan)"
                  fill="var(--accent-cyan)"
                  fillOpacity={0.2}
                  strokeWidth={2}
                  name="Load (MW)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="text-center py-8 text-sm" style={{ color: 'var(--text-muted)' }}>
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

  // Process data for display
  // API returns: Time, End Time, Posted, Generation System Wide, STWPF System Wide, etc.
  const chartData = windData?.data
    ? windData.data.slice(0, 100).map((record, idx) => ({
        index: idx,
        actual: Number(record["Generation System Wide"] || 0),
        forecast: Number(record["STWPF System Wide"] || 0),
        time: String(record["Time"] || ""),
        hour: idx,
      }))
    : [];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Wind className="h-4 w-4" style={{ color: 'var(--status-normal)' }} />
          <CardTitle>Wind Forecast</CardTitle>
        </div>
        <CardDescription>
          {windData?.count
            ? `${formatNumber(windData.count)} records`
            : "Loading..."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div>
            <label 
              className="block text-[10px] font-medium tracking-widest uppercase mb-1"
              style={{ color: 'var(--text-muted)' }}
            >
              Resolution
            </label>
            <select
              value={resolution}
              onChange={(e) => setResolution(e.target.value as Resolution)}
              className="w-full px-3 py-2 text-sm border"
            >
              <option value="hourly">Hourly</option>
              <option value="5min">5-Minute</option>
            </select>
          </div>
          <div>
            <label 
              className="block text-[10px] font-medium tracking-widest uppercase mb-1"
              style={{ color: 'var(--text-muted)' }}
            >
              Date
            </label>
            <select
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 text-sm border"
            >
              <option value="today">Today</option>
              <option value="yesterday">Yesterday</option>
            </select>
          </div>
          <div className="flex items-end pb-1">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={byRegion}
                onChange={(e) => setByRegion(e.target.checked)}
                className="w-4 h-4"
                style={{ accentColor: 'var(--accent-cyan)' }}
              />
              <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                By Region
              </span>
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
                <CartesianGrid 
                  strokeDasharray="3 3" 
                  stroke="var(--border-primary)"
                  vertical={false}
                />
                <XAxis 
                  dataKey="hour" 
                  tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
                  axisLine={{ stroke: 'var(--border-primary)' }}
                  tickLine={{ stroke: 'var(--border-primary)' }}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
                  tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                  axisLine={{ stroke: 'var(--border-primary)' }}
                  tickLine={{ stroke: 'var(--border-primary)' }}
                />
                <Tooltip 
                  formatter={(value) => formatMW(Number(value ?? 0))}
                  contentStyle={{
                    backgroundColor: 'var(--bg-elevated)',
                    border: '1px solid var(--border-secondary)',
                    borderRadius: 0,
                    fontSize: 12,
                  }}
                  labelStyle={{ color: 'var(--text-primary)' }}
                />
                <Legend 
                  wrapperStyle={{ fontSize: 10 }}
                  formatter={(value) => <span style={{ color: 'var(--text-secondary)' }}>{value}</span>}
                />
                <Line
                  type="monotone"
                  dataKey="actual"
                  stroke="var(--status-normal)"
                  strokeWidth={2}
                  dot={false}
                  name="Actual (MW)"
                />
                <Line
                  type="monotone"
                  dataKey="forecast"
                  stroke="var(--text-muted)"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                  name="Forecast (MW)"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="text-center py-8 text-sm" style={{ color: 'var(--text-muted)' }}>
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

  // Process data for display
  // API returns: Time, End Time, Posted, Generation System Wide, STPPF System Wide, etc.
  const chartData = solarData?.data
    ? solarData.data.slice(0, 100).map((record, idx) => ({
        index: idx,
        actual: Number(record["Generation System Wide"] || 0),
        forecast: Number(record["STPPF System Wide"] || 0),
        time: String(record["Time"] || ""),
        hour: idx,
      }))
    : [];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Sun className="h-4 w-4" style={{ color: 'var(--accent-yellow)' }} />
          <CardTitle>Solar Forecast</CardTitle>
        </div>
        <CardDescription>
          {solarData?.count
            ? `${formatNumber(solarData.count)} records`
            : "Loading..."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div>
            <label 
              className="block text-[10px] font-medium tracking-widest uppercase mb-1"
              style={{ color: 'var(--text-muted)' }}
            >
              Resolution
            </label>
            <select
              value={resolution}
              onChange={(e) => setResolution(e.target.value as Resolution)}
              className="w-full px-3 py-2 text-sm border"
            >
              <option value="hourly">Hourly</option>
              <option value="5min">5-Minute</option>
            </select>
          </div>
          <div>
            <label 
              className="block text-[10px] font-medium tracking-widest uppercase mb-1"
              style={{ color: 'var(--text-muted)' }}
            >
              Date
            </label>
            <select
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 text-sm border"
            >
              <option value="today">Today</option>
              <option value="yesterday">Yesterday</option>
            </select>
          </div>
          <div className="flex items-end pb-1">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={byRegion}
                onChange={(e) => setByRegion(e.target.checked)}
                className="w-4 h-4"
                style={{ accentColor: 'var(--accent-cyan)' }}
              />
              <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                By Region
              </span>
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
                <CartesianGrid 
                  strokeDasharray="3 3" 
                  stroke="var(--border-primary)"
                  vertical={false}
                />
                <XAxis 
                  dataKey="hour" 
                  tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
                  axisLine={{ stroke: 'var(--border-primary)' }}
                  tickLine={{ stroke: 'var(--border-primary)' }}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
                  tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                  axisLine={{ stroke: 'var(--border-primary)' }}
                  tickLine={{ stroke: 'var(--border-primary)' }}
                />
                <Tooltip 
                  formatter={(value) => formatMW(Number(value ?? 0))}
                  contentStyle={{
                    backgroundColor: 'var(--bg-elevated)',
                    border: '1px solid var(--border-secondary)',
                    borderRadius: 0,
                    fontSize: 12,
                  }}
                  labelStyle={{ color: 'var(--text-primary)' }}
                />
                <Legend 
                  wrapperStyle={{ fontSize: 10 }}
                  formatter={(value) => <span style={{ color: 'var(--text-secondary)' }}>{value}</span>}
                />
                <Line
                  type="monotone"
                  dataKey="actual"
                  stroke="var(--accent-yellow)"
                  strokeWidth={2}
                  dot={false}
                  name="Actual (MW)"
                />
                <Line
                  type="monotone"
                  dataKey="forecast"
                  stroke="var(--text-muted)"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                  name="Forecast (MW)"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="text-center py-8 text-sm" style={{ color: 'var(--text-muted)' }}>
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
      <div className="flex items-center justify-between">
        <div>
          <h1 
            className="text-xl font-bold tracking-wide"
            style={{ color: 'var(--text-primary)' }}
          >
            Load & Renewable Forecasts
          </h1>
          <p 
            className="text-xs mt-1"
            style={{ color: 'var(--text-muted)' }}
          >
            System load and renewable generation data
          </p>
        </div>
      </div>

      <LoadCard />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <WindForecastCard />
        <SolarForecastCard />
      </div>
    </div>
  );
}

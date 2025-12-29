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
} from "recharts";
import { useSPP, type SPPParams } from "../api";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
  Loading,
  ErrorCard,
} from "../components";
import { formatPrice, formatNumber } from "../lib/utils";
import { formatTime } from "../lib/time";
import { DollarSign, TrendingUp, Clock } from "lucide-react";

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

type MarketType = "real_time_15_min" | "day_ahead_hourly";
type LocationType = "load_zone" | "trading_hub";

// Colors for different locations
const LOCATION_COLORS: Record<string, string> = {
  LZ_HOUSTON: "#ef4444",
  LZ_NORTH: "#3b82f6",
  LZ_SOUTH: "#22c55e",
  LZ_WEST: "#eab308",
  LZ_AEN: "#a855f7",
  LZ_CPS: "#f97316",
  LZ_RAYBN: "#06b6d4",
  LZ_LCRA: "#ec4899",
  HB_HOUSTON: "#ef4444",
  HB_NORTH: "#3b82f6",
  HB_SOUTH: "#22c55e",
  HB_WEST: "#eab308",
  HB_PAN: "#a855f7",
  HB_BUSAVG: "#f97316",
};

function SPPCard() {
  const [market, setMarket] = useState<MarketType>("real_time_15_min");
  const [locationType, setLocationType] = useState<LocationType>("load_zone");
  const [startDate, setStartDate] = useState("yesterday");

  const params: SPPParams = {
    start: startDate,
    market,
    location_type: locationType,
  };

  const { data: sppData, isLoading, error, refetch } = useSPP(params);

  const { chartData, locations, latestPrices } = useMemo(() => {
    if (!sppData?.data || sppData.data.length === 0) {
      return { chartData: [], locations: [], latestPrices: [] };
    }

    const timeMap = new Map<string, Record<string, number>>();
    const locationSet = new Set<string>();
    const latestByLocation = new Map<string, { price: number; time: string }>();

    for (const record of sppData.data) {
      const time = String(record["Time"] || "");
      const location = String(record["Location"] || "");
      const price = Number(record["Price"] || 0);

      if (!time || !location) continue;

      locationSet.add(location);

      if (!timeMap.has(time)) {
        timeMap.set(time, {});
      }
      timeMap.get(time)![location] = price;

      const existing = latestByLocation.get(location);
      if (!existing || time > existing.time) {
        latestByLocation.set(location, { price, time });
      }
    }

    const sortedTimes = Array.from(timeMap.keys()).sort();
    const chartData = sortedTimes.map((time) => {
      const hour = new Date(time).getHours();
      return {
        time,
        hour: `${hour}:00`,
        ...timeMap.get(time),
      };
    });

    const locations = Array.from(locationSet).sort();

    const latestPrices = locations.map((loc) => ({
      location: loc,
      price: latestByLocation.get(loc)?.price || 0,
      time: latestByLocation.get(loc)?.time || "",
    }));

    return { chartData, locations, latestPrices };
  }, [sppData]);

  const summaryStats = useMemo(() => {
    if (latestPrices.length === 0) return null;

    const prices = latestPrices.map((p) => p.price);
    const avg = prices.reduce((a, b) => a + b, 0) / prices.length;
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const minLoc = latestPrices.find((p) => p.price === min)?.location || "";
    const maxLoc = latestPrices.find((p) => p.price === max)?.location || "";

    return { avg, min, max, minLoc, maxLoc };
  }, [latestPrices]);

  // Get latest timestamp
  const latestTime = useMemo(() => {
    if (!latestPrices.length) return null;
    return latestPrices[0]?.time || null;
  }, [latestPrices]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <DollarSign className="h-4 w-4 text-success" />
            <CardTitle>Settlement Point Prices</CardTitle>
          </div>
          <TimestampBadge timestamp={latestTime} label="Last update" />
        </div>
        <CardDescription>
          {sppData?.count
            ? `${formatNumber(sppData.count)} records • ${locations.length} locations`
            : "Loading..."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          <div className="form-control">
            <label className="label">
              <span className="label-text text-xs">Market</span>
            </label>
            <select
              value={market}
              onChange={(e) => setMarket(e.target.value as MarketType)}
              className="select select-bordered select-sm w-full"
            >
              <option value="real_time_15_min">Real-Time (15 min)</option>
              <option value="day_ahead_hourly">Day-Ahead (hourly)</option>
            </select>
          </div>
          <div className="form-control">
            <label className="label">
              <span className="label-text text-xs">Location Type</span>
            </label>
            <select
              value={locationType}
              onChange={(e) => setLocationType(e.target.value as LocationType)}
              className="select select-bordered select-sm w-full"
            >
              <option value="load_zone">Load Zones</option>
              <option value="trading_hub">Trading Hubs</option>
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
            message={error instanceof Error ? error.message : "Failed to load SPP data"}
            onRetry={() => refetch()}
          />
        ) : chartData.length > 0 ? (
          <>
            {/* Summary Stats */}
            {summaryStats && (
              <div className="stats stats-vertical md:stats-horizontal shadow w-full mb-4 bg-base-300">
                <div className="stat">
                  <div className="stat-title text-xs">Avg Price</div>
                  <div className="stat-value text-lg">{formatPrice(summaryStats.avg)}</div>
                </div>
                <div className="stat">
                  <div className="stat-title text-xs">Low ({summaryStats.minLoc})</div>
                  <div className="stat-value text-lg text-success">{formatPrice(summaryStats.min)}</div>
                </div>
                <div className="stat">
                  <div className="stat-title text-xs">High ({summaryStats.maxLoc})</div>
                  <div className="stat-value text-lg text-error">{formatPrice(summaryStats.max)}</div>
                </div>
              </div>
            )}

            {/* Price Chart */}
            <div className="h-72 mb-4">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-base-300" vertical={false} />
                  <XAxis 
                    dataKey="hour" 
                    tick={{ fontSize: 10 }}
                    interval="preserveStartEnd"
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 10 }}
                    tickFormatter={(value) => `$${value.toFixed(0)}`}
                    domain={['auto', 'auto']}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    formatter={(value) => formatPrice(Number(value ?? 0))}
                    labelFormatter={(label) => `Time: ${label}`}
                    contentStyle={{ backgroundColor: 'oklch(var(--b2))', border: '1px solid oklch(var(--b3))', borderRadius: '0.5rem' }}
                    labelStyle={{ color: 'oklch(var(--bc))' }}
                    itemStyle={{ color: 'oklch(var(--bc))' }}
                  />
                  <Legend 
                    wrapperStyle={{ fontSize: 10 }}
                    formatter={(value) => <span style={{ color: 'oklch(var(--bc))' }}>{value}</span>}
                  />
                  {locations.map((location) => (
                    <Line
                      key={location}
                      type="monotone"
                      dataKey={location}
                      stroke={LOCATION_COLORS[location] || "#6b7280"}
                      strokeWidth={2}
                      dot={false}
                      name={location}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Prices Table */}
            <div className="overflow-x-auto">
              <table className="table table-sm">
                <thead>
                  <tr>
                    <th>Location</th>
                    <th className="text-right">Price</th>
                    <th className="text-right">vs Avg</th>
                  </tr>
                </thead>
                <tbody>
                  {latestPrices.map((row) => {
                    const diff = summaryStats ? row.price - summaryStats.avg : 0;
                    return (
                      <tr key={row.location}>
                        <td className="flex items-center gap-2">
                          <span
                            className="w-2 h-2 rounded"
                            style={{ backgroundColor: LOCATION_COLORS[row.location] || "#6b7280" }}
                          />
                          {row.location}
                        </td>
                        <td className="text-right font-mono tabular-nums">{formatPrice(row.price)}</td>
                        <td className={`text-right font-mono tabular-nums ${diff > 0 ? 'text-error' : diff < 0 ? 'text-success' : ''}`}>
                          {diff >= 0 ? "+" : ""}{formatPrice(diff)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <p className="text-center py-8 text-sm text-base-content/50">
            No SPP data available for the selected filters
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function PriceSummaryCard() {
  const { data: sppData, isLoading, error, refetch } = useSPP({
    start: "yesterday",
    market: "real_time_15_min",
    location_type: "load_zone",
  });

  const summaryData = useMemo(() => {
    if (!sppData?.data || sppData.data.length === 0) return [];

    const locationStats = new Map<string, { prices: number[]; location: string }>();

    for (const record of sppData.data) {
      const location = String(record["Location"] || "");
      const price = Number(record["Price"] || 0);

      if (!location) continue;

      if (!locationStats.has(location)) {
        locationStats.set(location, { prices: [], location });
      }
      locationStats.get(location)!.prices.push(price);
    }

    return Array.from(locationStats.values())
      .map(({ location, prices }) => ({
        location,
        avgPrice: prices.reduce((a, b) => a + b, 0) / prices.length,
        minPrice: Math.min(...prices),
        maxPrice: Math.max(...prices),
        count: prices.length,
      }))
      .sort((a, b) => a.location.localeCompare(b.location));
  }, [sppData]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-primary" />
          <CardTitle>Daily Price Summary</CardTitle>
        </div>
        <CardDescription>Yesterday's price statistics by load zone</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Loading className="py-8" />
        ) : error ? (
          <ErrorCard
            message={error instanceof Error ? error.message : "Failed to load price summary"}
            onRetry={() => refetch()}
          />
        ) : summaryData.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table table-sm">
              <thead>
                <tr>
                  <th>Zone</th>
                  <th className="text-right">Avg</th>
                  <th className="text-right">Min</th>
                  <th className="text-right">Max</th>
                  <th className="text-right">Intervals</th>
                </tr>
              </thead>
              <tbody>
                {summaryData.map((row) => (
                  <tr key={row.location}>
                    <td className="flex items-center gap-2">
                      <span
                        className="w-2 h-2 rounded"
                        style={{ backgroundColor: LOCATION_COLORS[row.location] || "#6b7280" }}
                      />
                      {row.location}
                    </td>
                    <td className="text-right font-mono tabular-nums">{formatPrice(row.avgPrice)}</td>
                    <td className="text-right font-mono tabular-nums text-success">{formatPrice(row.minPrice)}</td>
                    <td className="text-right font-mono tabular-nums text-error">{formatPrice(row.maxPrice)}</td>
                    <td className="text-right text-base-content/50">{row.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-center py-8 text-sm text-base-content/50">
            No price summary data available
          </p>
        )}
      </CardContent>
    </Card>
  );
}

export function Prices() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settlement Point Prices</h1>
        <p className="text-sm text-base-content/60">Real-time and day-ahead pricing data</p>
      </div>

      <SPPCard />
      <PriceSummaryCard />
    </div>
  );
}

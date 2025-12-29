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
import { DollarSign, TrendingUp } from "lucide-react";

type MarketType = "real_time_15_min" | "day_ahead_hourly";
type LocationType = "load_zone" | "trading_hub";

// Colors for different locations - Bloomberg style
const LOCATION_COLORS: Record<string, string> = {
  LZ_HOUSTON: "#ff4757",
  LZ_NORTH: "#00d4ff",
  LZ_SOUTH: "#00ff88",
  LZ_WEST: "#ffd93d",
  LZ_AEN: "#a855f7",
  LZ_CPS: "#ff6b35",
  LZ_RAYBN: "#38bdf8",
  LZ_LCRA: "#f472b6",
  HB_HOUSTON: "#ff4757",
  HB_NORTH: "#00d4ff",
  HB_SOUTH: "#00ff88",
  HB_WEST: "#ffd93d",
  HB_PAN: "#a855f7",
  HB_BUSAVG: "#ff6b35",
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

  // Process data - group by time and pivot locations into columns
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

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <DollarSign className="h-4 w-4" style={{ color: 'var(--status-normal)' }} />
            <CardTitle>Settlement Point Prices</CardTitle>
          </div>
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
          <div>
            <label 
              className="block text-[10px] font-medium tracking-widest uppercase mb-1"
              style={{ color: 'var(--text-muted)' }}
            >
              Market
            </label>
            <select
              value={market}
              onChange={(e) => setMarket(e.target.value as MarketType)}
              className="w-full px-3 py-2 text-sm border"
            >
              <option value="real_time_15_min">Real-Time (15 min)</option>
              <option value="day_ahead_hourly">Day-Ahead (hourly)</option>
            </select>
          </div>
          <div>
            <label 
              className="block text-[10px] font-medium tracking-widest uppercase mb-1"
              style={{ color: 'var(--text-muted)' }}
            >
              Location Type
            </label>
            <select
              value={locationType}
              onChange={(e) => setLocationType(e.target.value as LocationType)}
              className="w-full px-3 py-2 text-sm border"
            >
              <option value="load_zone">Load Zones</option>
              <option value="trading_hub">Trading Hubs</option>
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
            message={error instanceof Error ? error.message : "Failed to load SPP data"}
            onRetry={() => refetch()}
          />
        ) : chartData.length > 0 ? (
          <>
            {/* Summary Stats */}
            {summaryStats && (
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div 
                  className="p-3 border"
                  style={{ backgroundColor: 'var(--bg-tertiary)', borderColor: 'var(--border-primary)' }}
                >
                  <p className="text-[10px] tracking-widest uppercase" style={{ color: 'var(--text-muted)' }}>AVG PRICE</p>
                  <p className="text-xl font-bold tabular-nums" style={{ color: 'var(--text-primary)' }}>
                    {formatPrice(summaryStats.avg)}
                  </p>
                </div>
                <div 
                  className="p-3 border"
                  style={{ backgroundColor: 'var(--bg-tertiary)', borderColor: 'var(--status-normal)' }}
                >
                  <p className="text-[10px] tracking-widest uppercase" style={{ color: 'var(--text-muted)' }}>
                    LOW ({summaryStats.minLoc})
                  </p>
                  <p className="text-xl font-bold tabular-nums" style={{ color: 'var(--status-normal)' }}>
                    {formatPrice(summaryStats.min)}
                  </p>
                </div>
                <div 
                  className="p-3 border"
                  style={{ backgroundColor: 'var(--bg-tertiary)', borderColor: 'var(--status-danger)' }}
                >
                  <p className="text-[10px] tracking-widest uppercase" style={{ color: 'var(--text-muted)' }}>
                    HIGH ({summaryStats.maxLoc})
                  </p>
                  <p className="text-xl font-bold tabular-nums" style={{ color: 'var(--status-danger)' }}>
                    {formatPrice(summaryStats.max)}
                  </p>
                </div>
              </div>
            )}

            {/* Price Chart */}
            <div className="h-72 mb-4">
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
                    interval="preserveStartEnd"
                    axisLine={{ stroke: 'var(--border-primary)' }}
                    tickLine={{ stroke: 'var(--border-primary)' }}
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
                    tickFormatter={(value) => `$${value.toFixed(0)}`}
                    domain={['auto', 'auto']}
                    axisLine={{ stroke: 'var(--border-primary)' }}
                    tickLine={{ stroke: 'var(--border-primary)' }}
                  />
                  <Tooltip
                    formatter={(value) => formatPrice(Number(value ?? 0))}
                    labelFormatter={(label) => `Time: ${label}`}
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
                  {locations.map((location) => (
                    <Line
                      key={location}
                      type="monotone"
                      dataKey={location}
                      stroke={LOCATION_COLORS[location] || "var(--text-muted)"}
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
              <table className="w-full">
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-primary)' }}>
                    <th className="text-left p-2" style={{ color: 'var(--text-muted)' }}>LOCATION</th>
                    <th className="text-right p-2" style={{ color: 'var(--text-muted)' }}>PRICE</th>
                    <th className="text-right p-2" style={{ color: 'var(--text-muted)' }}>VS AVG</th>
                  </tr>
                </thead>
                <tbody>
                  {latestPrices.map((row) => {
                    const diff = summaryStats ? row.price - summaryStats.avg : 0;
                    return (
                      <tr 
                        key={row.location} 
                        style={{ borderBottom: '1px solid var(--border-primary)' }}
                      >
                        <td className="p-2 flex items-center gap-2">
                          <span
                            className="w-2 h-2"
                            style={{ backgroundColor: LOCATION_COLORS[row.location] || "var(--text-muted)" }}
                          />
                          <span style={{ color: 'var(--text-primary)' }}>{row.location}</span>
                        </td>
                        <td className="p-2 text-right font-mono tabular-nums" style={{ color: 'var(--text-primary)' }}>
                          {formatPrice(row.price)}
                        </td>
                        <td 
                          className="p-2 text-right font-mono tabular-nums"
                          style={{ color: diff > 0 ? 'var(--status-danger)' : diff < 0 ? 'var(--status-normal)' : 'var(--text-muted)' }}
                        >
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
          <p className="text-center py-8 text-sm" style={{ color: 'var(--text-muted)' }}>
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
          <TrendingUp className="h-4 w-4" style={{ color: 'var(--accent-cyan)' }} />
          <CardTitle>Daily Price Summary</CardTitle>
        </div>
        <CardDescription>
          Yesterday's price statistics by load zone
        </CardDescription>
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
            <table className="w-full">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-primary)' }}>
                  <th className="text-left p-2" style={{ color: 'var(--text-muted)' }}>ZONE</th>
                  <th className="text-right p-2" style={{ color: 'var(--text-muted)' }}>AVG</th>
                  <th className="text-right p-2" style={{ color: 'var(--text-muted)' }}>MIN</th>
                  <th className="text-right p-2" style={{ color: 'var(--text-muted)' }}>MAX</th>
                  <th className="text-right p-2" style={{ color: 'var(--text-muted)' }}>INTERVALS</th>
                </tr>
              </thead>
              <tbody>
                {summaryData.map((row) => (
                  <tr 
                    key={row.location} 
                    style={{ borderBottom: '1px solid var(--border-primary)' }}
                  >
                    <td className="p-2 flex items-center gap-2">
                      <span
                        className="w-2 h-2"
                        style={{ backgroundColor: LOCATION_COLORS[row.location] || "var(--text-muted)" }}
                      />
                      <span style={{ color: 'var(--text-primary)' }}>{row.location}</span>
                    </td>
                    <td className="p-2 text-right font-mono tabular-nums" style={{ color: 'var(--text-primary)' }}>
                      {formatPrice(row.avgPrice)}
                    </td>
                    <td className="p-2 text-right font-mono tabular-nums" style={{ color: 'var(--status-normal)' }}>
                      {formatPrice(row.minPrice)}
                    </td>
                    <td className="p-2 text-right font-mono tabular-nums" style={{ color: 'var(--status-danger)' }}>
                      {formatPrice(row.maxPrice)}
                    </td>
                    <td className="p-2 text-right" style={{ color: 'var(--text-muted)' }}>
                      {row.count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-center py-8 text-sm" style={{ color: 'var(--text-muted)' }}>
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
      <div className="flex items-center justify-between">
        <div>
          <h1 
            className="text-xl font-bold tracking-wide"
            style={{ color: 'var(--text-primary)' }}
          >
            Settlement Point Prices
          </h1>
          <p 
            className="text-xs mt-1"
            style={{ color: 'var(--text-muted)' }}
          >
            Real-time and day-ahead pricing data
          </p>
        </div>
      </div>

      <SPPCard />
      <PriceSummaryCard />
    </div>
  );
}

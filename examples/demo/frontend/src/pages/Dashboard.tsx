import { useMemo, useState } from "react";
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  Legend,
} from "recharts";
import { useSPP, useLoadForecast, useWindForecast, useSolarForecast, useFuelMixRealtime, useLMPCombined } from "../api";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Loading,
} from "../components";
import { formatNumber } from "../lib/utils";
import { Zap, Activity, TrendingUp, RefreshCw, DollarSign, Clock } from "lucide-react";

const TIMEZONE = "America/Chicago";

// Format time for display
function formatTimeDisplay(date: Date | string): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleTimeString("en-US", {
    timeZone: TIMEZONE,
    hour: "numeric",
    minute: "2-digit",
  });
}

// Get current time in CT
function getCurrentTimeCT(): string {
  return new Date().toLocaleString("en-US", {
    timeZone: TIMEZONE,
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }) + " CT";
}

// Stat card component
function StatCard({ 
  label, 
  value, 
  unit,
  description,
  icon: Icon,
}: { 
  label: string; 
  value: string | number; 
  unit?: string;
  description?: string;
  icon?: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div className="stat bg-base-200 rounded-lg">
      <div className="stat-figure text-primary">
        {Icon && <Icon className="h-6 w-6" />}
      </div>
      <div className="stat-title text-xs">{label}</div>
      <div className="stat-value text-2xl">
        {typeof value === 'number' ? formatNumber(value) : value}
        {unit && <span className="text-sm font-normal ml-1">{unit}</span>}
      </div>
      {description && <div className="stat-desc">{description}</div>}
    </div>
  );
}

// Key Metrics Row
function KeyMetrics() {
  const { data: loadData, isLoading: loadLoading } = useLoadForecast({ start: "today", by: "weather_zone" });
  const { data: windData, isLoading: windLoading } = useWindForecast({ start: "today", resolution: "hourly" });
  const { data: solarData, isLoading: solarLoading } = useSolarForecast({ start: "today", resolution: "hourly" });
  const { data: sppData, isLoading: sppLoading } = useSPP({ start: "today", market: "real_time_15_min", location_type: "load_zone" });

  const isLoading = loadLoading || windLoading || solarLoading || sppLoading;

  const stats = useMemo(() => {
    // Get current hour in CT
    const now = new Date();
    const ctHour = parseInt(now.toLocaleString("en-US", { timeZone: TIMEZONE, hour: "numeric", hour12: false }));
    
    // Get load for current hour
    let load = 0;
    if (loadData?.data && loadData.data.length > ctHour) {
      load = Number(loadData.data[ctHour]?.["System Total"] || 0);
    }
    
    // Get wind for current hour
    let windGen = 0;
    if (windData?.data && windData.data.length > ctHour) {
      const rec = windData.data[ctHour];
      const gen = rec?.["Generation System Wide"];
      windGen = (gen !== null && gen !== undefined && !Number.isNaN(Number(gen)))
        ? Number(gen)
        : Number(rec?.["STWPF System Wide"] || 0);
    }

    // Get solar for current hour
    let solarGen = 0;
    if (solarData?.data && solarData.data.length > ctHour) {
      const rec = solarData.data[ctHour];
      const gen = rec?.["Generation System Wide"];
      solarGen = (gen !== null && gen !== undefined && !Number.isNaN(Number(gen)))
        ? Number(gen)
        : Number(rec?.["STPPF System Wide"] || 0);
    }

    const netLoad = Math.max(0, load - windGen - solarGen);

    // Get current average price - find latest time
    let avgPrice = 0;
    if (sppData?.data) {
      const latestByLocation = new Map<string, { price: number; time: string }>();
      for (const record of sppData.data) {
        const location = String(record["Location"] || "");
        const price = Number(record["Price"] || 0);
        const time = String(record["Time"] || "");
        if (location && time) {
          const existing = latestByLocation.get(location);
          if (!existing || time > existing.time) {
            latestByLocation.set(location, { price, time });
          }
        }
      }
      const prices = Array.from(latestByLocation.values()).map(v => v.price);
      avgPrice = prices.length > 0 ? prices.reduce((a, b) => a + b, 0) / prices.length : 0;
    }

    return { load, netLoad, windGen, solarGen, avgPrice };
  }, [loadData, windData, solarData, sppData]);

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="skeleton h-24 rounded-lg"></div>
        ))}
      </div>
    );
  }

  return (
    <div className="stats stats-vertical lg:stats-horizontal shadow w-full bg-base-200">
      <StatCard label="Load" value={stats.load} unit="MW" icon={Activity} />
      <StatCard 
        label="Net Load" 
        value={stats.netLoad} 
        unit="MW" 
        description="Load − Renewables"
        icon={TrendingUp}
      />
      <StatCard 
        label="Price" 
        value={`$${stats.avgPrice.toFixed(2)}`}
        unit="/MWh"
        description="Avg LZ Price"
        icon={DollarSign}
      />
      <StatCard 
        label="Renewables" 
        value={stats.windGen + stats.solarGen} 
        unit="MW"
        description={`Wind ${formatNumber(stats.windGen)} + Solar ${formatNumber(stats.solarGen)}`}
        icon={Zap}
      />
    </div>
  );
}

// Fuel type colors
const FUEL_COLORS: Record<string, string> = {
  "nuclear": "#86efac",
  "coal": "#f97316",
  "coal and lignite": "#f97316",
  "gas": "#3b82f6",
  "natural gas": "#3b82f6",
  "wind": "#22c55e",
  "solar": "#eab308",
  "hydro": "#60a5fa",
  "other": "#ec4899",
};

// Stacked Generation Mix Chart - time series like GridStatus
function GenerationMixChart() {
  const { data: loadData, isLoading: loadLoading } = useLoadForecast({ start: "today", by: "weather_zone" });
  const { data: windData, isLoading: windLoading } = useWindForecast({ start: "today", resolution: "hourly" });
  const { data: solarData, isLoading: solarLoading } = useSolarForecast({ start: "today", resolution: "hourly" });
  const { data: fuelMix, refetch } = useFuelMixRealtime();

  const isLoading = loadLoading || windLoading || solarLoading;

  // Build hourly time series data for generation mix
  const chartData = useMemo(() => {
    if (!loadData?.data) return [];
    
    const now = new Date();
    const ctHour = parseInt(now.toLocaleString("en-US", { timeZone: TIMEZONE, hour: "numeric", hour12: false }));
    const hoursToShow = Math.min(ctHour + 1, 24);
    
    // Get current fuel mix ratios for baseload (nuclear, coal)
    let nuclearRatio = 0.09;  // Default ~9%
    let coalRatio = 0.14;     // Default ~14%
    
    if (fuelMix?.entries) {
      const total = fuelMix.total_generation_mw || 1;
      for (const e of fuelMix.entries) {
        const ft = e.fuel_type.toLowerCase();
        if (ft === "nuclear") nuclearRatio = e.generation_mw / total;
        if (ft.includes("coal")) coalRatio = e.generation_mw / total;
      }
    }

    return Array.from({ length: hoursToShow }, (_, hour) => {
      const loadRec = loadData.data[hour];
      const windRec = windData?.data?.[hour];
      const solarRec = solarData?.data?.[hour];
      
      const load = loadRec ? Number(loadRec["System Total"] || 0) : 0;
      
      let wind = 0;
      if (windRec) {
        const gen = windRec["Generation System Wide"];
        wind = (gen !== null && gen !== undefined && !Number.isNaN(Number(gen)))
          ? Number(gen)
          : Number(windRec["STWPF System Wide"] || 0);
      }
      
      let solar = 0;
      if (solarRec) {
        const gen = solarRec["Generation System Wide"];
        solar = (gen !== null && gen !== undefined && !Number.isNaN(Number(gen)))
          ? Number(gen)
          : Number(solarRec["STPPF System Wide"] || 0);
      }

      // Estimate baseload from current mix ratios
      const nuclear = load * nuclearRatio;
      const coal = load * coalRatio;
      
      // Gas fills the gap
      const gas = Math.max(0, load - wind - solar - nuclear - coal);

      return {
        hour,
        time: `${hour}:00`,
        nuclear: nuclear / 1000,  // Convert to GW
        coal: coal / 1000,
        gas: gas / 1000,
        wind: wind / 1000,
        solar: solar / 1000,
        total: load / 1000,
      };
    });
  }, [loadData, windData, solarData, fuelMix]);

  if (isLoading) return <Loading className="h-72" />;
  if (chartData.length === 0) return null;

  const latestHour = chartData[chartData.length - 1];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-warning" />
            <CardTitle>Fuel Mix</CardTitle>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs text-base-content/60">
              <Clock className="h-3 w-3" />
              <span>{getCurrentTimeCT()}</span>
            </div>
            <button onClick={() => refetch()} className="btn btn-ghost btn-xs btn-circle">
              <RefreshCw className="h-3 w-3" />
            </button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-base-300" vertical={false} />
              <XAxis 
                dataKey="hour" 
                tick={{ fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => `${v}h`}
              />
              <YAxis
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => `${v.toFixed(0)}`}
                axisLine={false}
                tickLine={false}
                width={35}
                label={{ value: 'GW', angle: -90, position: 'insideLeft', style: { fontSize: 10 } }}
              />
              <Tooltip
                formatter={(value) => [`${Number(value ?? 0).toFixed(2)} GW`]}
                labelFormatter={(label) => `${label}:00 CT`}
                contentStyle={{ backgroundColor: 'oklch(var(--b2))', border: '1px solid oklch(var(--b3))', borderRadius: '0.5rem' }}
                labelStyle={{ color: 'oklch(var(--bc))' }}
                itemStyle={{ color: 'oklch(var(--bc))' }}
              />
              <Legend 
                wrapperStyle={{ fontSize: 11 }}
                formatter={(value) => <span style={{ color: 'oklch(var(--bc))' }}>{value}</span>}
              />
              <Area type="monotone" dataKey="nuclear" stackId="1" stroke={FUEL_COLORS.nuclear} fill={FUEL_COLORS.nuclear} name="Nuclear" />
              <Area type="monotone" dataKey="coal" stackId="1" stroke={FUEL_COLORS.coal} fill={FUEL_COLORS.coal} name="Coal" />
              <Area type="monotone" dataKey="gas" stackId="1" stroke={FUEL_COLORS.gas} fill={FUEL_COLORS.gas} name="Natural Gas" />
              <Area type="monotone" dataKey="wind" stackId="1" stroke={FUEL_COLORS.wind} fill={FUEL_COLORS.wind} name="Wind" />
              <Area type="monotone" dataKey="solar" stackId="1" stroke={FUEL_COLORS.solar} fill={FUEL_COLORS.solar} name="Solar" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        
        {/* Current totals summary */}
        {latestHour && (
          <div className="mt-3 pt-3 border-t border-base-300">
            <div className="text-xs text-base-content/60 mb-2">Current ({latestHour.hour}:00 CT): Total {latestHour.total.toFixed(1)} GW</div>
            <div className="flex flex-wrap gap-3 text-xs">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded" style={{backgroundColor: FUEL_COLORS.gas}}></span> Gas {latestHour.gas.toFixed(1)} GW</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded" style={{backgroundColor: FUEL_COLORS.wind}}></span> Wind {latestHour.wind.toFixed(1)} GW</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded" style={{backgroundColor: FUEL_COLORS.coal}}></span> Coal {latestHour.coal.toFixed(1)} GW</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded" style={{backgroundColor: FUEL_COLORS.solar}}></span> Solar {latestHour.solar.toFixed(1)} GW</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded" style={{backgroundColor: FUEL_COLORS.nuclear}}></span> Nuclear {latestHour.nuclear.toFixed(1)} GW</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

type LocationType = "load_zone" | "trading_hub" | "dc_tie";

// Combined DA + RT LMP Price Chart like GridStatus
function LMPPriceChart() {
  const [locationType, setLocationType] = useState<LocationType>("load_zone");
  const [selectedLocation, setSelectedLocation] = useState<string>("");

  const { data: lmpData, isLoading, error, refetch } = useLMPCombined({ 
    location_type: locationType,
    location: selectedLocation || undefined,
  });

  // Process data for chart - combine RT and DA by time
  const { chartData, locations } = useMemo(() => {
    if (!lmpData?.data) return { chartData: [], locations: lmpData?.locations || [] };
    
    // Group by time, then calculate RT and DA averages per hour
    const byHour = new Map<number, { rt: number[]; da: number[] }>();
    
    for (const record of lmpData.data) {
      const timeStr = record.time;
      if (!timeStr) continue;
      
      // Parse time to get hour
      const d = new Date(timeStr);
      const hour = d.getHours();
      
      if (!byHour.has(hour)) {
        byHour.set(hour, { rt: [], da: [] });
      }
      
      const hourData = byHour.get(hour)!;
      if (record.rt_price !== null && record.rt_price > 0) {
        hourData.rt.push(record.rt_price);
      }
      if (record.da_price !== null && record.da_price > 0) {
        hourData.da.push(record.da_price);
      }
    }

    // Build chart data
    const hours = Array.from(byHour.keys()).sort((a, b) => a - b);
    const chartData = hours.map(hour => {
      const data = byHour.get(hour)!;
      return {
        hour,
        time: `${hour}:00`,
        rt: data.rt.length > 0 ? data.rt.reduce((a, b) => a + b, 0) / data.rt.length : null,
        da: data.da.length > 0 ? data.da.reduce((a, b) => a + b, 0) / data.da.length : null,
      };
    });

    return { chartData, locations: lmpData?.locations || [] };
  }, [lmpData]);

  // Update selected location when locations change
  useMemo(() => {
    if (locations.length > 0 && !selectedLocation) {
      // Default to first load zone (usually LZ_WEST or similar)
      const defaultLoc = locations.find(l => l.startsWith("LZ_")) || locations[0];
      setSelectedLocation(defaultLoc);
    }
  }, [locations, selectedLocation]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between w-full flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <DollarSign className="h-4 w-4 text-success" />
            <CardTitle>Locational Marginal Price</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            {lmpData?.latest_rt_time && (
              <div className="flex items-center gap-1.5 text-xs text-base-content/60">
                <Clock className="h-3 w-3" />
                <span>RT: {lmpData.latest_rt_time}</span>
              </div>
            )}
            <button onClick={() => refetch()} className="btn btn-ghost btn-xs btn-circle">
              <RefreshCw className="h-3 w-3" />
            </button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Selectors */}
        <div className="flex flex-wrap gap-3 mb-4">
          <div className="form-control">
            <label className="label py-0">
              <span className="label-text text-xs">Location Type</span>
            </label>
            <select
              value={locationType}
              onChange={(e) => {
                setLocationType(e.target.value as LocationType);
                setSelectedLocation("");  // Reset location when type changes
              }}
              className="select select-bordered select-xs"
            >
              <option value="load_zone">Load Zones</option>
              <option value="trading_hub">Trading Hubs</option>
              <option value="dc_tie">DC Ties</option>
            </select>
          </div>
          <div className="form-control">
            <label className="label py-0">
              <span className="label-text text-xs">Location</span>
            </label>
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="select select-bordered select-xs min-w-32"
            >
              {locations.map(loc => (
                <option key={loc} value={loc}>{loc}</option>
              ))}
            </select>
          </div>
        </div>

        {isLoading ? (
          <Loading className="h-56" />
        ) : error ? (
          <p className="text-center py-8 text-sm text-error">Failed to load LMP data</p>
        ) : chartData.length === 0 ? (
          <p className="text-center py-8 text-sm text-base-content/50">No price data available</p>
        ) : (
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-base-300" vertical={false} />
                <XAxis 
                  dataKey="hour" 
                  tick={{ fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => {
                    if (v === 0) return "12a";
                    if (v === 12) return "12p";
                    if (v < 12) return `${v}a`;
                    return `${v - 12}p`;
                  }}
                />
                <YAxis
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => `$${v}`}
                  axisLine={false}
                  tickLine={false}
                  width={45}
                  domain={['auto', 'auto']}
                />
                <Tooltip
                  formatter={(value, name) => {
                    const label = name === "da" ? "Day Ahead" : "Real Time";
                    return [`$${Number(value ?? 0).toFixed(2)}`, label];
                  }}
                  labelFormatter={(label) => {
                    const hour = Number(label);
                    const ampm = hour >= 12 ? "PM" : "AM";
                    const h = hour % 12 || 12;
                    return `${h}:00 ${ampm} CT`;
                  }}
                  contentStyle={{ backgroundColor: 'oklch(var(--b2))', border: '1px solid oklch(var(--b3))', borderRadius: '0.5rem' }}
                  labelStyle={{ color: 'oklch(var(--bc))' }}
                  itemStyle={{ color: 'oklch(var(--bc))' }}
                />
                <Legend 
                  wrapperStyle={{ fontSize: 11 }}
                  formatter={(value) => {
                    const label = value === "da" ? "Day Ahead" : "Real Time";
                    return <span style={{ color: 'oklch(var(--bc))' }}>{label}</span>;
                  }}
                />
                <Line
                  type="stepAfter"
                  dataKey="da"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={false}
                  name="da"
                  connectNulls
                />
                <Line
                  type="monotone"
                  dataKey="rt"
                  stroke="#22c55e"
                  strokeWidth={1.5}
                  dot={false}
                  name="rt"
                  connectNulls
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Legend explanation */}
        <div className="mt-3 pt-3 border-t border-base-300 flex items-center gap-4 text-xs text-base-content/60">
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-blue-500"></div>
            <span>Day Ahead (hourly)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-green-500"></div>
            <span>Real Time (SCED, ~5 min)</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Prices Table
function PricesTable() {
  const { data: sppData, isLoading } = useSPP({ 
    start: "today", 
    market: "real_time_15_min", 
    location_type: "load_zone" 
  });

  const { latestPrices, latestTime } = useMemo(() => {
    if (!sppData?.data) return { latestPrices: [], latestTime: null };
    
    const byLocation = new Map<string, { price: number; time: string }>();
    for (const record of sppData.data) {
      const location = String(record["Location"] || "");
      const price = Number(record["Price"] || 0);
      const time = String(record["Time"] || "");
      if (location && time) {
        const existing = byLocation.get(location);
        if (!existing || time > existing.time) {
          byLocation.set(location, { price, time });
        }
      }
    }
    
    const latestPrices = Array.from(byLocation.entries())
      .map(([location, { price, time }]) => ({ location, price, time }))
      .sort((a, b) => b.price - a.price);

    const latestTime = latestPrices[0]?.time 
      ? formatTimeDisplay(latestPrices[0].time) + " CT"
      : null;

    return { latestPrices, latestTime };
  }, [sppData]);

  if (isLoading) return <Loading className="h-48" />;
  if (latestPrices.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between w-full">
          <CardTitle>Load Zone Prices</CardTitle>
          {latestTime && (
            <div className="flex items-center gap-1.5 text-xs text-base-content/60">
              <Clock className="h-3 w-3" />
              <span>{latestTime}</span>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="table table-sm">
            <thead>
              <tr>
                <th>Zone</th>
                <th className="text-right">Price</th>
              </tr>
            </thead>
            <tbody>
              {latestPrices.map(({ location, price }) => (
                <tr key={location}>
                  <td className="font-mono text-sm">{location}</td>
                  <td className="text-right font-semibold">${price.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

export function Dashboard() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Grid Overview</h1>
          <p className="text-sm text-base-content/60">Real-time conditions</p>
        </div>
        <div className="badge badge-outline gap-1">
          <Clock className="h-3 w-3" />
          {getCurrentTimeCT()}
        </div>
      </div>

      {/* Key Metrics */}
      <KeyMetrics />

      {/* Generation Mix Chart */}
      <GenerationMixChart />

      {/* LMP Chart and Prices Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <LMPPriceChart />
        </div>
        <PricesTable />
      </div>
    </div>
  );
}

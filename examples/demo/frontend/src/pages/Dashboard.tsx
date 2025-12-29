import { useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import { useSPP, useLoadForecast, useWindForecast, useSolarForecast } from "../api";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Loading,
  ErrorCard,
} from "../components";
import { formatMW, formatPrice, formatNumber } from "../lib/utils";
import { Wind, Sun, Zap, Activity, TrendingUp, RefreshCw } from "lucide-react";

// Metric display component
function Metric({ 
  label, 
  value, 
  unit, 
  color = 'var(--text-primary)',
}: { 
  label: string; 
  value: string | number; 
  unit?: string; 
  color?: string;
}) {
  return (
    <div 
      className="p-4 border"
      style={{ 
        backgroundColor: 'var(--bg-tertiary)',
        borderColor: 'var(--border-primary)'
      }}
    >
      <div className="flex items-center justify-between mb-1">
        <span 
          className="text-[10px] tracking-widest uppercase"
          style={{ color: 'var(--text-muted)' }}
        >
          {label}
        </span>
      </div>
      <div className="flex items-baseline gap-1">
        <span 
          className="text-2xl font-bold tabular-nums"
          style={{ color }}
        >
          {typeof value === 'number' ? formatNumber(value) : value}
        </span>
        {unit && (
          <span 
            className="text-xs"
            style={{ color: 'var(--text-muted)' }}
          >
            {unit}
          </span>
        )}
      </div>
    </div>
  );
}

// Grid Overview using real data
function GridOverview() {
  const { data: loadData, isLoading: loadLoading } = useLoadForecast({ start: "today", by: "weather_zone" });
  const { data: windData, isLoading: windLoading } = useWindForecast({ start: "today", resolution: "hourly" });
  const { data: solarData, isLoading: solarLoading } = useSolarForecast({ start: "today", resolution: "hourly" });

  const isLoading = loadLoading || windLoading || solarLoading;

  const stats = useMemo(() => {
    // Get latest load from forecast
    let currentLoad = 0;
    if (loadData?.data?.length) {
      const latestLoad = loadData.data[loadData.data.length - 1];
      currentLoad = Number(latestLoad?.["System Total"] || latestLoad?.["Total"] || 0);
      // Sum all zones if we have them but no total
      if (!currentLoad && latestLoad) {
        const zones = ["Coast", "East", "Far West", "North", "North Central", "South Central", "Southern", "West"];
        currentLoad = zones.reduce((sum, zone) => sum + Number(latestLoad[zone] || 0), 0);
      }
    }
    
    const windGen = windData?.data?.length
      ? Number(windData.data[windData.data.length - 1]?.["Generation System Wide"] || 
               windData.data[windData.data.length - 1]?.["STWPF System Wide"] || 0)
      : 0;

    const solarGen = solarData?.data?.length
      ? Number(solarData.data[solarData.data.length - 1]?.["Generation System Wide"] ||
               solarData.data[solarData.data.length - 1]?.["STPPF System Wide"] || 0)
      : 0;

    const renewableTotal = windGen + solarGen;
    const renewablePercent = currentLoad > 0 ? ((renewableTotal / currentLoad) * 100).toFixed(1) : '0';

    return { currentLoad, windGen, solarGen, renewableTotal, renewablePercent };
  }, [loadData, windData, solarData]);

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[...Array(4)].map((_, i) => (
          <div 
            key={i}
            className="p-4 border animate-pulse"
            style={{ backgroundColor: 'var(--bg-tertiary)', borderColor: 'var(--border-primary)' }}
          >
            <div className="h-4 w-16 mb-2" style={{ backgroundColor: 'var(--border-secondary)' }} />
            <div className="h-8 w-24" style={{ backgroundColor: 'var(--border-secondary)' }} />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <Metric 
        label="Load Forecast" 
        value={stats.currentLoad} 
        unit="MW" 
        color="var(--accent-cyan)"
      />
      <Metric 
        label="Wind Generation" 
        value={stats.windGen} 
        unit="MW" 
        color="var(--status-normal)"
      />
      <Metric 
        label="Solar Generation" 
        value={stats.solarGen} 
        unit="MW" 
        color="var(--accent-yellow)"
      />
      <Metric 
        label="Renewable %" 
        value={`${stats.renewablePercent}%`}
        color="var(--accent-orange)"
      />
    </div>
  );
}

// Load Profile Chart
function LoadProfileChart() {
  const { data: loadData, isLoading, error, refetch } = useLoadForecast({ start: "today", by: "weather_zone" });

  const chartData = useMemo(() => {
    if (!loadData?.data) return [];
    return loadData.data.slice(0, 24).map((record, idx) => {
      // Use System Total or sum zones
      let total = Number(record["System Total"] || record["Total"] || 0);
      if (!total) {
        const zones = ["Coast", "East", "Far West", "North", "North Central", "South Central", "Southern", "West"];
        total = zones.reduce((sum, zone) => sum + Number(record[zone] || 0), 0);
      }
      return {
        hour: idx,
        load: total,
      };
    });
  }, [loadData]);

  if (isLoading) return <Loading className="h-48" />;
  if (error) return <ErrorCard message="Failed to load data" onRetry={() => refetch()} />;
  if (chartData.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4" style={{ color: 'var(--accent-cyan)' }} />
            <CardTitle>Load Forecast</CardTitle>
          </div>
          <button 
            onClick={() => refetch()}
            className="p-1.5 transition-colors hover:bg-[var(--bg-tertiary)]"
          >
            <RefreshCw className="h-3 w-3" style={{ color: 'var(--text-muted)' }} />
          </button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-48">
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
                tickLine={false}
                tickFormatter={(v) => `${v}h`}
              />
              <YAxis
                tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
                tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                axisLine={false}
                tickLine={false}
                width={40}
              />
              <Tooltip
                formatter={(value) => formatMW(Number(value ?? 0))}
                labelFormatter={(label) => `Hour ${label}`}
                contentStyle={{
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border-secondary)',
                  borderRadius: 0,
                  fontSize: 11,
                }}
              />
              <Area
                type="monotone"
                dataKey="load"
                stroke="var(--accent-cyan)"
                fill="var(--accent-cyan)"
                fillOpacity={0.15}
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

// Renewable Generation Chart
function RenewableChart() {
  const { data: windData, isLoading: windLoading } = useWindForecast({ start: "today", resolution: "hourly" });
  const { data: solarData, isLoading: solarLoading } = useSolarForecast({ start: "today", resolution: "hourly" });

  const isLoading = windLoading || solarLoading;

  const chartData = useMemo(() => {
    if (!windData?.data && !solarData?.data) return [];
    
    const maxLen = Math.min(
      windData?.data?.length || 24,
      solarData?.data?.length || 24,
      24
    );

    return Array.from({ length: maxLen }, (_, idx) => ({
      hour: idx,
      wind: Number(windData?.data?.[idx]?.["Generation System Wide"] || 
                   windData?.data?.[idx]?.["STWPF System Wide"] || 0),
      solar: Number(solarData?.data?.[idx]?.["Generation System Wide"] ||
                    solarData?.data?.[idx]?.["STPPF System Wide"] || 0),
    }));
  }, [windData, solarData]);

  if (isLoading) return <Loading className="h-48" />;
  if (chartData.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4" style={{ color: 'var(--status-normal)' }} />
          <CardTitle>Renewable Generation</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid 
                strokeDasharray="3 3" 
                stroke="var(--border-primary)"
                vertical={false}
              />
              <XAxis 
                dataKey="hour" 
                tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
                axisLine={{ stroke: 'var(--border-primary)' }}
                tickLine={false}
                tickFormatter={(v) => `${v}h`}
              />
              <YAxis
                tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
                tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                axisLine={false}
                tickLine={false}
                width={40}
              />
              <Tooltip
                formatter={(value) => formatMW(Number(value ?? 0))}
                labelFormatter={(label) => `Hour ${label}`}
                contentStyle={{
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border-secondary)',
                  borderRadius: 0,
                  fontSize: 11,
                }}
              />
              <Bar dataKey="wind" stackId="a" fill="var(--status-normal)" name="Wind" />
              <Bar dataKey="solar" stackId="a" fill="var(--accent-yellow)" name="Solar" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center justify-center gap-6 mt-2">
          <div className="flex items-center gap-2">
            <Wind className="h-3 w-3" style={{ color: 'var(--status-normal)' }} />
            <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>Wind</span>
          </div>
          <div className="flex items-center gap-2">
            <Sun className="h-3 w-3" style={{ color: 'var(--accent-yellow)' }} />
            <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>Solar</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Recent Prices Table
function RecentPrices() {
  const { data: sppData, isLoading, error } = useSPP({ 
    start: "today", 
    market: "real_time_15_min", 
    location_type: "load_zone" 
  });

  const latestPrices = useMemo(() => {
    if (!sppData?.data) return [];
    
    const byLocation = new Map<string, { price: number; time: string }>();
    for (const record of sppData.data) {
      const location = String(record["Location"] || "");
      const price = Number(record["Price"] || 0);
      const time = String(record["Time"] || "");
      if (location) {
        const existing = byLocation.get(location);
        if (!existing || time > existing.time) {
          byLocation.set(location, { price, time });
        }
      }
    }
    
    return Array.from(byLocation.entries())
      .map(([location, { price }]) => ({ location, price }))
      .sort((a, b) => a.location.localeCompare(b.location))
      .slice(0, 8);
  }, [sppData]);

  if (isLoading) return <Loading className="h-48" />;
  if (error || latestPrices.length === 0) return null;

  const avgPrice = latestPrices.reduce((sum, p) => sum + p.price, 0) / latestPrices.length;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4" style={{ color: 'var(--accent-orange)' }} />
          <CardTitle>Current Prices</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {latestPrices.map(({ location, price }) => (
            <div 
              key={location}
              className="flex items-center justify-between py-1.5 px-2"
              style={{ backgroundColor: 'var(--bg-tertiary)' }}
            >
              <span className="text-xs font-mono" style={{ color: 'var(--text-secondary)' }}>
                {location}
              </span>
              <span 
                className="text-sm font-bold tabular-nums"
                style={{ 
                  color: price > avgPrice ? 'var(--status-danger)' : 
                         price < avgPrice ? 'var(--status-normal)' : 
                         'var(--text-primary)'
                }}
              >
                {formatPrice(price)}
              </span>
            </div>
          ))}
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
          <h1 
            className="text-xl font-bold tracking-wide"
            style={{ color: 'var(--text-primary)' }}
          >
            ERCOT Grid Overview
          </h1>
          <p 
            className="text-xs mt-1"
            style={{ color: 'var(--text-muted)' }}
          >
            Real-time grid metrics and generation data
          </p>
        </div>
        <div 
          className="text-[10px] font-mono px-3 py-1.5 border"
          style={{ 
            color: 'var(--text-muted)',
            borderColor: 'var(--border-primary)',
            backgroundColor: 'var(--bg-secondary)'
          }}
        >
          {new Date().toLocaleString('en-US', { 
            timeZone: 'America/Chicago',
            hour: '2-digit',
            minute: '2-digit',
            timeZoneName: 'short'
          })}
        </div>
      </div>

      {/* Key Metrics */}
      <GridOverview />

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <LoadProfileChart />
        <RenewableChart />
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle>Market Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                View detailed price data on the Prices page →
              </p>
            </CardContent>
          </Card>
        </div>
        <RecentPrices />
      </div>
    </div>
  );
}

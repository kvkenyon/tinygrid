import { useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ComposedChart,
  Line,
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
import { formatMW, formatNumber } from "../lib/utils";
import { Wind, Sun, Zap, Activity, TrendingUp, RefreshCw, DollarSign } from "lucide-react";

// Get current hour in Central time
function getCurrentHourCT(): number {
  const now = new Date();
  const ct = new Date(now.toLocaleString("en-US", { timeZone: "America/Chicago" }));
  return ct.getHours();
}

// Find data point closest to current time
function findCurrentDataPoint<T extends Record<string, unknown>>(
  data: T[] | undefined,
  timeField: string = "Time"
): T | null {
  if (!data || data.length === 0) return null;
  
  const currentHour = getCurrentHourCT();
  
  // Try to find a record matching current hour
  for (const record of data) {
    const timeStr = String(record[timeField] || record["Hour Ending"] || "");
    if (timeStr) {
      // Parse hour from time string
      const match = timeStr.match(/(\d{1,2}):/);
      if (match) {
        const hour = parseInt(match[1], 10);
        if (hour === currentHour || hour === currentHour + 1) {
          return record;
        }
      }
    }
  }
  
  // Fall back to most recent (last non-future) or first record
  return data[Math.min(currentHour, data.length - 1)] || data[0];
}

// Large metric display like GridStatus
function BigMetric({ 
  label, 
  value, 
  unit,
  subValue,
  color = 'var(--accent-cyan)',
  icon: Icon,
}: { 
  label: string; 
  value: string | number; 
  unit?: string;
  subValue?: string;
  color?: string;
  icon?: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
}) {
  return (
    <div 
      className="p-5 border"
      style={{ 
        backgroundColor: 'var(--bg-secondary)',
        borderColor: 'var(--border-primary)'
      }}
    >
      <div className="flex items-center gap-2 mb-2">
        {Icon && <Icon className="h-4 w-4" style={{ color: 'var(--text-muted)' }} />}
        <span 
          className="text-[11px] tracking-widest uppercase"
          style={{ color: 'var(--text-muted)' }}
        >
          {label}
        </span>
      </div>
      <div className="flex items-baseline gap-2">
        <span 
          className="text-3xl font-bold tabular-nums"
          style={{ color }}
        >
          {typeof value === 'number' ? formatNumber(value) : value}
        </span>
        {unit && (
          <span 
            className="text-sm"
            style={{ color: 'var(--text-muted)' }}
          >
            {unit}
          </span>
        )}
      </div>
      {subValue && (
        <span 
          className="text-[10px] mt-1 block"
          style={{ color: 'var(--text-muted)' }}
        >
          {subValue}
        </span>
      )}
    </div>
  );
}

// Key Metrics Row - matching GridStatus layout
function KeyMetrics() {
  const { data: loadData, isLoading: loadLoading } = useLoadForecast({ start: "today", by: "weather_zone" });
  const { data: windData, isLoading: windLoading } = useWindForecast({ start: "today", resolution: "hourly" });
  const { data: solarData, isLoading: solarLoading } = useSolarForecast({ start: "today", resolution: "hourly" });
  const { data: sppData, isLoading: sppLoading } = useSPP({ start: "today", market: "real_time_15_min", location_type: "load_zone" });

  const isLoading = loadLoading || windLoading || solarLoading || sppLoading;

  const stats = useMemo(() => {
    // Get current load
    const currentLoadRecord = findCurrentDataPoint(loadData?.data, "Hour Ending");
    const load = currentLoadRecord ? Number(currentLoadRecord["System Total"] || 0) : 0;
    
    // Get current wind - use Generation if available, else forecast
    const currentWindRecord = findCurrentDataPoint(windData?.data, "Time");
    let windGen = 0;
    if (currentWindRecord) {
      const gen = currentWindRecord["Generation System Wide"];
      windGen = (gen !== null && gen !== undefined && !Number.isNaN(Number(gen)))
        ? Number(gen)
        : Number(currentWindRecord["STWPF System Wide"] || 0);
    }

    // Get current solar - use Generation if available, else forecast  
    const currentSolarRecord = findCurrentDataPoint(solarData?.data, "Time");
    let solarGen = 0;
    if (currentSolarRecord) {
      const gen = currentSolarRecord["Generation System Wide"];
      solarGen = (gen !== null && gen !== undefined && !Number.isNaN(Number(gen)))
        ? Number(gen)
        : Number(currentSolarRecord["STPPF System Wide"] || 0);
    }

    // Calculate net load (load minus renewables)
    const netLoad = Math.max(0, load - windGen - solarGen);

    // Get current average price
    let avgPrice = 0;
    if (sppData?.data) {
      const latestByLocation = new Map<string, { price: number; time: string }>();
      for (const record of sppData.data) {
        const location = String(record["Location"] || "");
        const price = Number(record["Price"] || 0);
        const time = String(record["Time"] || "");
        if (location) {
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
          <div 
            key={i}
            className="p-5 border animate-pulse"
            style={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-primary)' }}
          >
            <div className="h-4 w-16 mb-3" style={{ backgroundColor: 'var(--border-secondary)' }} />
            <div className="h-10 w-28" style={{ backgroundColor: 'var(--border-secondary)' }} />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <BigMetric 
        label="Load" 
        value={stats.load} 
        unit="MW" 
        color="var(--text-primary)"
        icon={Activity}
      />
      <BigMetric 
        label="Net Load" 
        value={stats.netLoad} 
        unit="MW" 
        color="var(--accent-cyan)"
        subValue="Load − Renewables"
        icon={TrendingUp}
      />
      <BigMetric 
        label="Price" 
        value={`$${stats.avgPrice.toFixed(2)}`}
        unit="/MWh"
        color="var(--status-normal)"
        subValue="Avg LZ Price"
        icon={DollarSign}
      />
      <BigMetric 
        label="Renewables" 
        value={stats.windGen + stats.solarGen} 
        unit="MW"
        color="var(--accent-orange)"
        subValue={`Wind ${formatNumber(stats.windGen)} + Solar ${formatNumber(stats.solarGen)}`}
        icon={Zap}
      />
    </div>
  );
}

// Generation Mix Chart - stacked area like GridStatus
function GenerationMixChart() {
  const { data: windData, isLoading: windLoading } = useWindForecast({ start: "today", resolution: "hourly" });
  const { data: solarData, isLoading: solarLoading } = useSolarForecast({ start: "today", resolution: "hourly" });
  const { data: loadData, isLoading: loadLoading } = useLoadForecast({ start: "today", by: "weather_zone" });

  const isLoading = windLoading || solarLoading || loadLoading;

  const chartData = useMemo(() => {
    if (!windData?.data && !solarData?.data) return [];
    
    const currentHour = getCurrentHourCT();
    const hoursToShow = Math.min(currentHour + 1, 24);
    
    return Array.from({ length: hoursToShow }, (_, idx) => {
      const windRecord = windData?.data?.[idx];
      const solarRecord = solarData?.data?.[idx];
      const loadRecord = loadData?.data?.[idx];
      
      // Get actual generation or forecast
      let wind = 0;
      if (windRecord) {
        const gen = windRecord["Generation System Wide"];
        wind = (gen !== null && gen !== undefined && !Number.isNaN(Number(gen)))
          ? Number(gen)
          : Number(windRecord["STWPF System Wide"] || 0);
      }
      
      let solar = 0;
      if (solarRecord) {
        const gen = solarRecord["Generation System Wide"];
        solar = (gen !== null && gen !== undefined && !Number.isNaN(Number(gen)))
          ? Number(gen)
          : Number(solarRecord["STPPF System Wide"] || 0);
      }

      const load = loadRecord ? Number(loadRecord["System Total"] || 0) : 0;
      const other = Math.max(0, load - wind - solar);

      return {
        hour: idx,
        time: `${idx}:00`,
        wind,
        solar,
        other,
        load,
      };
    });
  }, [windData, solarData, loadData]);

  if (isLoading) return <Loading className="h-64" />;
  if (chartData.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4" style={{ color: 'var(--accent-orange)' }} />
            <CardTitle>Generation Mix</CardTitle>
          </div>
          <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
            Today (CT)
          </span>
        </div>
      </CardHeader>
      <CardContent>
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
                formatter={(value, name) => [formatMW(Number(value ?? 0)), name]}
                labelFormatter={(label) => `${label}:00 CT`}
                contentStyle={{
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border-secondary)',
                  borderRadius: 0,
                  fontSize: 11,
                }}
              />
              <Area
                type="monotone"
                dataKey="other"
                stackId="1"
                stroke="#6b7280"
                fill="#6b7280"
                name="Other (Gas, Coal, Nuclear)"
              />
              <Area
                type="monotone"
                dataKey="wind"
                stackId="1"
                stroke="var(--status-normal)"
                fill="var(--status-normal)"
                name="Wind"
              />
              <Area
                type="monotone"
                dataKey="solar"
                stackId="1"
                stroke="var(--accent-yellow)"
                fill="var(--accent-yellow)"
                name="Solar"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center justify-center gap-6 mt-3 flex-wrap">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3" style={{ backgroundColor: '#6b7280' }} />
            <span className="text-[10px]" style={{ color: 'var(--text-secondary)' }}>Other</span>
          </div>
          <div className="flex items-center gap-2">
            <Wind className="h-3 w-3" style={{ color: 'var(--status-normal)' }} />
            <span className="text-[10px]" style={{ color: 'var(--text-secondary)' }}>Wind</span>
          </div>
          <div className="flex items-center gap-2">
            <Sun className="h-3 w-3" style={{ color: 'var(--accent-yellow)' }} />
            <span className="text-[10px]" style={{ color: 'var(--text-secondary)' }}>Solar</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Price Chart - like GridStatus LMP chart
function PriceChart() {
  const { data: sppData, isLoading, error, refetch } = useSPP({ 
    start: "today", 
    market: "real_time_15_min", 
    location_type: "load_zone" 
  });

  const chartData = useMemo(() => {
    if (!sppData?.data) return [];
    
    // Group by time and calculate average price
    const byTime = new Map<string, number[]>();
    for (const record of sppData.data) {
      const time = String(record["Time"] || "");
      const price = Number(record["Price"] || 0);
      if (time && price) {
        if (!byTime.has(time)) byTime.set(time, []);
        byTime.get(time)!.push(price);
      }
    }

    return Array.from(byTime.entries())
      .map(([time, prices]) => ({
        time,
        hour: new Date(time).getHours(),
        price: prices.reduce((a, b) => a + b, 0) / prices.length,
      }))
      .sort((a, b) => a.time.localeCompare(b.time))
      .slice(-48); // Last 48 intervals (12 hours at 15min)
  }, [sppData]);

  if (isLoading) return <Loading className="h-48" />;
  if (error) return <ErrorCard message="Failed to load price data" onRetry={() => refetch()} />;
  if (chartData.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <DollarSign className="h-4 w-4" style={{ color: 'var(--status-normal)' }} />
            <CardTitle>Real-Time Price</CardTitle>
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
        <div className="h-40">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData}>
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
                tickFormatter={(v) => `$${v}`}
                axisLine={false}
                tickLine={false}
                width={45}
              />
              <Tooltip
                formatter={(value) => [`$${Number(value).toFixed(2)}/MWh`, 'Avg Price']}
                labelFormatter={(label) => `${label}:00 CT`}
                contentStyle={{
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border-secondary)',
                  borderRadius: 0,
                  fontSize: 11,
                }}
              />
              <Line
                type="monotone"
                dataKey="price"
                stroke="var(--accent-cyan)"
                strokeWidth={2}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

// LZ Prices Table - like GridStatus
function PricesTable() {
  const { data: sppData, isLoading } = useSPP({ 
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
      .map(([location, { price, time }]) => ({ location, price, time }))
      .sort((a, b) => b.price - a.price); // Sort by price descending
  }, [sppData]);

  if (isLoading) return <Loading className="h-48" />;
  if (latestPrices.length === 0) return null;

  const timestamp = latestPrices[0]?.time 
    ? new Date(latestPrices[0].time).toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        timeZone: 'America/Chicago'
      }) + ' CT'
    : '';

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle>Load Zone Prices</CardTitle>
          <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
            {timestamp}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          {latestPrices.map(({ location, price }) => (
            <div 
              key={location}
              className="flex items-center justify-between py-2 px-3"
              style={{ backgroundColor: 'var(--bg-tertiary)' }}
            >
              <span className="text-xs font-mono" style={{ color: 'var(--text-secondary)' }}>
                {location}
              </span>
              <span 
                className="text-sm font-bold tabular-nums"
                style={{ color: 'var(--text-primary)' }}
              >
                ${price.toFixed(2)}
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
            Electric Reliability Council of Texas
          </h1>
          <p 
            className="text-xs mt-1"
            style={{ color: 'var(--text-muted)' }}
          >
            Real-time grid conditions
          </p>
        </div>
        <div 
          className="text-xs font-mono px-3 py-2 border"
          style={{ 
            color: 'var(--text-primary)',
            borderColor: 'var(--border-primary)',
            backgroundColor: 'var(--bg-secondary)'
          }}
        >
          {new Date().toLocaleDateString('en-US', { 
            timeZone: 'America/Chicago',
            month: 'short',
            day: 'numeric',
            year: 'numeric'
          })}
        </div>
      </div>

      {/* Key Metrics - like GridStatus top row */}
      <KeyMetrics />

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <GenerationMixChart />
        </div>
        <PricesTable />
      </div>

      {/* Price Chart */}
      <PriceChart />
    </div>
  );
}

import { useState, useMemo } from "react";
import { useHistoricalEndpoints, useHistorical } from "../api";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Loading,
  ErrorCard,
} from "../components";
import { formatNumber } from "../lib/utils";
import { Database, Download, Search, Calendar, FileText, ChevronRight } from "lucide-react";

function EndpointSelector({
  endpoints,
  selected,
  onSelect
}: {
  endpoints: { name: string; description: string; path: string }[];
  selected: string;
  onSelect: (name: string) => void;
}) {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredEndpoints = useMemo(() => {
    if (!searchQuery) return endpoints;
    const query = searchQuery.toLowerCase();
    return endpoints.filter(ep =>
      ep.name.toLowerCase().includes(query) ||
      ep.description.toLowerCase().includes(query)
    );
  }, [endpoints, searchQuery]);

  return (
    <div className="space-y-3">
      {/* Search */}
      <div className="relative">
        <Search
          className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4"
          style={{ color: 'var(--text-muted)' }}
        />
        <input
          type="text"
          placeholder="Search endpoints..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 text-sm border"
          style={{
            backgroundColor: 'var(--bg-tertiary)',
            borderColor: 'var(--border-primary)',
            color: 'var(--text-primary)',
          }}
        />
      </div>

      {/* Endpoint List */}
      <div
        className="max-h-64 overflow-y-auto border"
        style={{ borderColor: 'var(--border-primary)' }}
      >
        {filteredEndpoints.map((ep) => (
          <button
            key={ep.name}
            onClick={() => onSelect(ep.name)}
            className="w-full flex items-center gap-3 px-4 py-3 text-left transition-all border-b last:border-b-0"
            style={{
              backgroundColor: selected === ep.name ? 'var(--bg-tertiary)' : 'var(--bg-secondary)',
              borderColor: 'var(--border-primary)',
            }}
          >
            <FileText
              className="h-4 w-4 flex-shrink-0"
              style={{ color: selected === ep.name ? 'var(--accent-cyan)' : 'var(--text-muted)' }}
            />
            <div className="flex-1 min-w-0">
              <div
                className="text-sm font-medium truncate"
                style={{ color: selected === ep.name ? 'var(--accent-cyan)' : 'var(--text-primary)' }}
              >
                {ep.name.replace(/_/g, " ")}
              </div>
              <div
                className="text-[10px] truncate"
                style={{ color: 'var(--text-muted)' }}
              >
                {ep.description}
              </div>
            </div>
            {selected === ep.name && (
              <ChevronRight className="h-4 w-4 flex-shrink-0" style={{ color: 'var(--accent-cyan)' }} />
            )}
          </button>
        ))}
        {filteredEndpoints.length === 0 && (
          <div className="px-4 py-8 text-center">
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No endpoints found</p>
          </div>
        )}
      </div>
    </div>
  );
}

function DateRangePicker({
  startDate,
  endDate,
  onStartChange,
  onEndChange,
}: {
  startDate: string;
  endDate: string;
  onStartChange: (date: string) => void;
  onEndChange: (date: string) => void;
}) {
  // Quick date presets
  const presets = [
    { label: "Last 7 days", days: 7 },
    { label: "Last 30 days", days: 30 },
    { label: "Last 90 days", days: 90 },
  ];

  const applyPreset = (days: number) => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - days);
    onStartChange(start.toISOString().split('T')[0]);
    onEndChange(end.toISOString().split('T')[0]);
  };

  return (
    <div className="space-y-3">
      {/* Presets */}
      <div className="flex gap-2">
        {presets.map(({ label, days }) => (
          <button
            key={days}
            onClick={() => applyPreset(days)}
            className="px-3 py-1.5 text-xs border transition-colors"
            style={{
              borderColor: 'var(--border-secondary)',
              color: 'var(--text-secondary)',
              backgroundColor: 'var(--bg-tertiary)',
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Date Inputs */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label
            className="block text-[10px] tracking-widest uppercase mb-1.5"
            style={{ color: 'var(--text-muted)' }}
          >
            Start Date
          </label>
          <div className="relative">
            <Calendar
              className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4"
              style={{ color: 'var(--text-muted)' }}
            />
            <input
              type="date"
              value={startDate}
              onChange={(e) => onStartChange(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 text-sm border"
              style={{
                backgroundColor: 'var(--bg-tertiary)',
                borderColor: 'var(--border-primary)',
                color: 'var(--text-primary)',
              }}
            />
          </div>
        </div>
        <div>
          <label
            className="block text-[10px] tracking-widest uppercase mb-1.5"
            style={{ color: 'var(--text-muted)' }}
          >
            End Date
          </label>
          <div className="relative">
            <Calendar
              className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4"
              style={{ color: 'var(--text-muted)' }}
            />
            <input
              type="date"
              value={endDate}
              onChange={(e) => onEndChange(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 text-sm border"
              style={{
                backgroundColor: 'var(--bg-tertiary)',
                borderColor: 'var(--border-primary)',
                color: 'var(--text-primary)',
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function DataTable({
  data,
  columns
}: {
  data: Record<string, unknown>[];
  columns: string[];
}) {
  const displayColumns = columns.slice(0, 6);
  const hasMore = columns.length > 6;

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr style={{ borderBottom: '2px solid var(--border-primary)' }}>
            {displayColumns.map((col) => (
              <th
                key={col}
                className="text-left px-3 py-2 text-[10px] tracking-widest uppercase whitespace-nowrap"
                style={{ color: 'var(--text-muted)' }}
              >
                {col}
              </th>
            ))}
            {hasMore && (
              <th
                className="text-left px-3 py-2 text-[10px]"
                style={{ color: 'var(--text-muted)' }}
              >
                +{columns.length - 6}
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {data.slice(0, 100).map((row, idx) => (
            <tr
              key={idx}
              className="transition-colors hover:bg-[var(--bg-tertiary)]"
              style={{ borderBottom: '1px solid var(--border-primary)' }}
            >
              {displayColumns.map((col) => (
                <td
                  key={col}
                  className="px-3 py-2 text-sm font-mono whitespace-nowrap"
                  style={{ color: 'var(--text-primary)' }}
                >
                  {String(row[col] ?? "—")}
                </td>
              ))}
              {hasMore && (
                <td
                  className="px-3 py-2 text-sm"
                  style={{ color: 'var(--text-muted)' }}
                >
                  ...
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Historical() {
  const [selectedEndpoint, setSelectedEndpoint] = useState<string>("");
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [shouldFetch, setShouldFetch] = useState(false);

  const {
    data: endpointsData,
    isLoading: endpointsLoading,
    error: endpointsError,
  } = useHistoricalEndpoints();

  const {
    data: historicalData,
    isLoading: dataLoading,
    error: dataError,
    refetch,
  } = useHistorical(
    shouldFetch && selectedEndpoint && startDate && endDate
      ? { endpoint: selectedEndpoint, start: startDate, end: endDate }
      : null
  );

  const handleFetch = () => {
    if (selectedEndpoint && startDate && endDate) {
      setShouldFetch(true);
    }
  };

  const handleExport = () => {
    if (!historicalData?.data || historicalData.data.length === 0) return;

    const allKeys = new Set<string>();
    historicalData.data.forEach((row) => {
      Object.keys(row).forEach((key) => allKeys.add(key));
    });
    const headers = Array.from(allKeys);

    const csvRows = [
      headers.join(","),
      ...historicalData.data.map((row) =>
        headers
          .map((header) => {
            const value = row[header];
            if (value === null || value === undefined) return "";
            const str = String(value);
            if (str.includes(",") || str.includes('"') || str.includes("\n")) {
              return `"${str.replace(/"/g, '""')}"`;
            }
            return str;
          })
          .join(",")
      ),
    ];

    const blob = new Blob([csvRows.join("\n")], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `${selectedEndpoint}_${startDate}_${endDate}.csv`;
    link.click();
  };

  const columns = historicalData?.data && historicalData.data.length > 0
    ? Object.keys(historicalData.data[0])
    : [];

  const canFetch = selectedEndpoint && startDate && endDate;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1
          className="text-xl font-bold tracking-wide"
          style={{ color: 'var(--text-primary)' }}
        >
          Historical Data
        </h1>
        <p
          className="text-xs mt-1"
          style={{ color: 'var(--text-muted)' }}
        >
          Query ERCOT archive data (90+ days)
        </p>
      </div>

      {endpointsLoading ? (
        <Loading className="py-12" />
      ) : endpointsError ? (
        <ErrorCard message="Failed to load endpoints" />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Panel - Query Builder */}
          <div className="lg:col-span-1 space-y-6">
            {/* Endpoint Selection */}
            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4" style={{ color: 'var(--accent-cyan)' }} />
                  <CardTitle>Select Endpoint</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <EndpointSelector
                  endpoints={endpointsData?.endpoints || []}
                  selected={selectedEndpoint}
                  onSelect={(name) => {
                    setSelectedEndpoint(name);
                    setShouldFetch(false);
                  }}
                />
              </CardContent>
            </Card>

            {/* Date Range */}
            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" style={{ color: 'var(--accent-orange)' }} />
                  <CardTitle>Date Range</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <DateRangePicker
                  startDate={startDate}
                  endDate={endDate}
                  onStartChange={(d) => { setStartDate(d); setShouldFetch(false); }}
                  onEndChange={(d) => { setEndDate(d); setShouldFetch(false); }}
                />
              </CardContent>
            </Card>

            {/* Fetch Button */}
            <button
              onClick={handleFetch}
              disabled={!canFetch}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium tracking-wide uppercase transition-all disabled:opacity-40 disabled:cursor-not-allowed"
              style={{
                backgroundColor: canFetch ? 'var(--accent-cyan)' : 'var(--bg-tertiary)',
                color: canFetch ? 'var(--bg-primary)' : 'var(--text-muted)',
              }}
            >
              <Search className="h-4 w-4" />
              Fetch Data
            </button>
          </div>

          {/* Right Panel - Results */}
          <div className="lg:col-span-2">
            <Card className="h-full">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4" style={{ color: 'var(--status-normal)' }} />
                    <CardTitle>Results</CardTitle>
                  </div>
                  {historicalData && (
                    <div className="flex items-center gap-3">
                      <span
                        className="text-xs font-mono"
                        style={{ color: 'var(--accent-cyan)' }}
                      >
                        {formatNumber(historicalData.count)} records
                      </span>
                      <button
                        onClick={handleExport}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs border transition-colors"
                        style={{
                          borderColor: 'var(--border-secondary)',
                          color: 'var(--text-secondary)',
                        }}
                      >
                        <Download className="h-3 w-3" />
                        CSV
                      </button>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {!shouldFetch ? (
                  <div className="flex flex-col items-center justify-center py-16">
                    <Database
                      className="h-12 w-12 mb-4"
                      style={{ color: 'var(--border-secondary)' }}
                    />
                    <p
                      className="text-sm text-center"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      Select an endpoint and date range,<br />then click Fetch Data
                    </p>
                  </div>
                ) : dataLoading ? (
                  <div className="flex items-center justify-center py-16">
                    <Loading size="lg" />
                  </div>
                ) : dataError ? (
                  <ErrorCard
                    message={dataError instanceof Error ? dataError.message : "Failed to fetch data"}
                    onRetry={() => refetch()}
                  />
                ) : historicalData?.data && historicalData.data.length > 0 ? (
                  <>
                    <DataTable data={historicalData.data} columns={columns} />
                    {historicalData.data.length > 100 && (
                      <p
                        className="text-center text-xs py-3 border-t"
                        style={{
                          color: 'var(--text-muted)',
                          borderColor: 'var(--border-primary)'
                        }}
                      >
                        Showing 100 of {formatNumber(historicalData.data.length)} records • Export for full data
                      </p>
                    )}
                  </>
                ) : (
                  <div className="flex flex-col items-center justify-center py-16">
                    <p
                      className="text-sm"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      No data found for the selected range
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

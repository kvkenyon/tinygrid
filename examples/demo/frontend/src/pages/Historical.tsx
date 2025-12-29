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
      <div className="form-control">
        <label className="input input-bordered input-sm flex items-center gap-2">
          <Search className="h-4 w-4 opacity-50" />
          <input
            type="text"
            placeholder="Search endpoints..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="grow"
          />
        </label>
      </div>

      {/* Endpoint List */}
      <div className="max-h-64 overflow-y-auto border border-base-300 rounded-lg">
        {filteredEndpoints.map((ep) => (
          <button
            key={ep.name}
            onClick={() => onSelect(ep.name)}
            className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-all border-b border-base-300 last:border-b-0 hover:bg-base-300 ${
              selected === ep.name ? "bg-base-300" : ""
            }`}
          >
            <FileText className={`h-4 w-4 flex-shrink-0 ${selected === ep.name ? "text-primary" : "opacity-50"}`} />
            <div className="flex-1 min-w-0">
              <div className={`text-sm font-medium truncate ${selected === ep.name ? "text-primary" : ""}`}>
                {ep.name.replace(/_/g, " ")}
              </div>
              <div className="text-xs truncate text-base-content/50">
                {ep.description}
              </div>
            </div>
            {selected === ep.name && <ChevronRight className="h-4 w-4 flex-shrink-0 text-primary" />}
          </button>
        ))}
        {filteredEndpoints.length === 0 && (
          <div className="px-4 py-8 text-center">
            <p className="text-sm text-base-content/50">No endpoints found</p>
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
  const presets = [
    { label: "7 days", days: 7 },
    { label: "30 days", days: 30 },
    { label: "90 days", days: 90 },
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
            className="btn btn-xs btn-outline"
          >
            {label}
          </button>
        ))}
      </div>

      {/* Date Inputs */}
      <div className="grid grid-cols-2 gap-3">
        <div className="form-control">
          <label className="label">
            <span className="label-text text-xs">Start Date</span>
          </label>
          <label className="input input-bordered input-sm flex items-center gap-2">
            <Calendar className="h-4 w-4 opacity-50" />
            <input
              type="date"
              value={startDate}
              onChange={(e) => onStartChange(e.target.value)}
              className="grow"
            />
          </label>
        </div>
        <div className="form-control">
          <label className="label">
            <span className="label-text text-xs">End Date</span>
          </label>
          <label className="input input-bordered input-sm flex items-center gap-2">
            <Calendar className="h-4 w-4 opacity-50" />
            <input
              type="date"
              value={endDate}
              onChange={(e) => onEndChange(e.target.value)}
              className="grow"
            />
          </label>
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
      <table className="table table-xs">
        <thead>
          <tr>
            {displayColumns.map((col) => (
              <th key={col} className="whitespace-nowrap">{col}</th>
            ))}
            {hasMore && <th className="text-base-content/50">+{columns.length - 6}</th>}
          </tr>
        </thead>
        <tbody>
          {data.slice(0, 100).map((row, idx) => (
            <tr key={idx} className="hover">
              {displayColumns.map((col) => (
                <td key={col} className="font-mono whitespace-nowrap">
                  {String(row[col] ?? "—")}
                </td>
              ))}
              {hasMore && <td className="text-base-content/50">...</td>}
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
        <h1 className="text-2xl font-bold">Historical Data</h1>
        <p className="text-sm text-base-content/60">Query archive data (90+ days)</p>
      </div>

      {endpointsLoading ? (
        <Loading className="py-12" />
      ) : endpointsError ? (
        <ErrorCard message="Failed to load endpoints" />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Panel - Query Builder */}
          <div className="lg:col-span-1 space-y-4">
            {/* Endpoint Selection */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-primary" />
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
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-warning" />
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
              className="btn btn-primary w-full"
            >
              <Search className="h-4 w-4" />
              Fetch Data
            </button>
          </div>

          {/* Right Panel - Results */}
          <div className="lg:col-span-2">
            <Card className="h-full">
              <CardHeader>
                <div className="flex items-center justify-between w-full">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-success" />
                    <CardTitle>Results</CardTitle>
                  </div>
                  {historicalData && (
                    <div className="flex items-center gap-3">
                      <span className="badge badge-primary badge-outline">
                        {formatNumber(historicalData.count)} records
                      </span>
                      <button onClick={handleExport} className="btn btn-xs btn-ghost">
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
                    <Database className="h-12 w-12 mb-4 opacity-20" />
                    <p className="text-sm text-center text-base-content/50">
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
                      <p className="text-center text-xs py-3 border-t border-base-300 text-base-content/50">
                        Showing 100 of {formatNumber(historicalData.data.length)} records • Export for full data
                      </p>
                    )}
                  </>
                ) : (
                  <div className="flex flex-col items-center justify-center py-16">
                    <p className="text-sm text-base-content/50">
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

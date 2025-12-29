// API Response Types

export interface GridStatus {
  condition: string;
  current_load: number;
  capacity: number;
  reserves: number;
  timestamp: string;
  peak_forecast: number;
  wind_output: number;
  solar_output: number;
  prc: number;
  message: string;
}

export interface FuelMixEntry {
  fuel_type: string;
  generation_mw: number;
  percentage: number;
}

export interface FuelMixResponse {
  entries: FuelMixEntry[];
  timestamp: string;
  total_generation_mw: number;
}

export interface RenewableStatus {
  wind_mw: number;
  solar_mw: number;
  wind_forecast_mw: number;
  solar_forecast_mw: number;
  wind_capacity_mw: number;
  solar_capacity_mw: number;
  timestamp: string;
  total_renewable_mw: number;
  renewable_percentage: number | null;
}

export interface SupplyDemandEntry {
  hour: string | number | null;
  demand: number;
  supply: number;
  reserves: number;
}

export interface SupplyDemandResponse {
  data: SupplyDemandEntry[];
  timestamp: string;
}

export interface SPPResponse {
  data: Record<string, unknown>[];
  count: number;
  market: string;
  start_date: string;
  end_date: string | null;
}

export interface LMPResponse {
  data: Record<string, unknown>[];
  count: number;
  market: string;
  location_type: string;
}

export interface DailyPricesResponse {
  data: Record<string, unknown>[];
  count: number;
}

export interface LoadResponse {
  data: Record<string, unknown>[];
  count: number;
  zone_type: string;
  start_date: string;
  end_date: string | null;
}

export interface WindForecastResponse {
  data: Record<string, unknown>[];
  count: number;
  resolution: string;
  by_region: boolean;
  start_date: string;
  end_date: string | null;
}

export interface SolarForecastResponse {
  data: Record<string, unknown>[];
  count: number;
  resolution: string;
  by_region: boolean;
  start_date: string;
  end_date: string | null;
}

export interface EndpointInfo {
  name: string;
  path: string;
  description: string;
}

export interface AvailableEndpointsResponse {
  endpoints: EndpointInfo[];
}

export interface HistoricalResponse {
  data: Record<string, unknown>[];
  count: number;
  endpoint: string;
  start_date: string;
  end_date: string;
}

// Grid condition enum for styling
export type GridCondition =
  | "normal"
  | "conservation"
  | "watch"
  | "advisory"
  | "emergency"
  | "eea1"
  | "eea2"
  | "eea3"
  | "unknown";

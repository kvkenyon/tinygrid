// API Client for TinyGrid Demo

const API_BASE = "/api";

async function fetchAPI<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(endpoint, window.location.origin);
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.append(key, value);
      }
    });
  }

  const response = await fetch(url.toString());
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `API Error: ${response.status}`);
  }

  return response.json();
}

// Dashboard endpoints
export const dashboardAPI = {
  getStatus: () => fetchAPI<import("./types").GridStatus>(`${API_BASE}/status`),
  
  getFuelMix: () => fetchAPI<import("./types").FuelMixResponse>(`${API_BASE}/fuel-mix`),
  
  getRenewable: () => fetchAPI<import("./types").RenewableStatus>(`${API_BASE}/renewable`),
  
  getSupplyDemand: () => fetchAPI<import("./types").SupplyDemandResponse>(`${API_BASE}/supply-demand`),
};

// Prices endpoints
export interface SPPParams {
  start?: string;
  end?: string;
  market?: "real_time_15_min" | "day_ahead_hourly";
  location_type?: "load_zone" | "trading_hub" | "resource_node" | "all";
  locations?: string;
}

export interface LMPParams {
  start?: string;
  end?: string;
  market?: "real_time_sced" | "day_ahead_hourly";
  location_type?: "resource_node" | "electrical_bus";
}

export const pricesAPI = {
  getSPP: (params?: SPPParams) =>
    fetchAPI<import("./types").SPPResponse>(`${API_BASE}/spp`, params as Record<string, string>),
  
  getLMP: (params?: LMPParams) =>
    fetchAPI<import("./types").LMPResponse>(`${API_BASE}/lmp`, params as Record<string, string>),
  
  getDailyPrices: () =>
    fetchAPI<import("./types").DailyPricesResponse>(`${API_BASE}/daily-prices`),
};

// Forecasts endpoints
export interface LoadParams {
  start?: string;
  end?: string;
  by?: "weather_zone" | "forecast_zone";
}

export interface LoadForecastParams {
  start?: string;
  end?: string;
  by?: "weather_zone" | "study_area";
}

export interface WindSolarParams {
  start?: string;
  end?: string;
  resolution?: "hourly" | "5min";
  by_region?: boolean;
}

export const forecastsAPI = {
  getLoad: (params?: LoadParams) =>
    fetchAPI<import("./types").LoadResponse>(`${API_BASE}/load`, params as Record<string, string>),
  
  getLoadForecast: (params?: LoadForecastParams) =>
    fetchAPI<import("./types").LoadResponse>(`${API_BASE}/load-forecast`, params as Record<string, string>),
  
  getWindForecast: (params?: WindSolarParams) =>
    fetchAPI<import("./types").WindForecastResponse>(
      `${API_BASE}/wind-forecast`,
      {
        ...params,
        by_region: params?.by_region?.toString(),
      } as Record<string, string>
    ),
  
  getSolarForecast: (params?: WindSolarParams) =>
    fetchAPI<import("./types").SolarForecastResponse>(
      `${API_BASE}/solar-forecast`,
      {
        ...params,
        by_region: params?.by_region?.toString(),
      } as Record<string, string>
    ),
};

// Historical endpoints
export interface HistoricalParams {
  endpoint: string;
  start: string;
  end: string;
}

export const historicalAPI = {
  getEndpoints: () =>
    fetchAPI<import("./types").AvailableEndpointsResponse>(`${API_BASE}/historical/endpoints`),
  
  getHistorical: (params: HistoricalParams) =>
    fetchAPI<import("./types").HistoricalResponse>(`${API_BASE}/historical`, {
      endpoint: params.endpoint,
      start: params.start,
      end: params.end,
    }),
};

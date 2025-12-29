import { useQuery } from "@tanstack/react-query";
import {
  dashboardAPI,
  pricesAPI,
  forecastsAPI,
  historicalAPI,
  type SPPParams,
  type LMPParams,
  type LoadParams,
  type LoadForecastParams,
  type WindSolarParams,
  type HistoricalParams,
} from "./client";

// Dashboard hooks
export function useGridStatus() {
  return useQuery({
    queryKey: ["status"],
    queryFn: dashboardAPI.getStatus,
    refetchInterval: 60000, // Auto-refresh every minute
    staleTime: 30000,
  });
}

export function useFuelMix() {
  return useQuery({
    queryKey: ["fuel-mix"],
    queryFn: dashboardAPI.getFuelMix,
    refetchInterval: 60000,
    staleTime: 30000,
  });
}

export function useRenewable() {
  return useQuery({
    queryKey: ["renewable"],
    queryFn: dashboardAPI.getRenewable,
    refetchInterval: 60000,
    staleTime: 30000,
  });
}

export function useSupplyDemand() {
  return useQuery({
    queryKey: ["supply-demand"],
    queryFn: dashboardAPI.getSupplyDemand,
    refetchInterval: 60000,
    staleTime: 30000,
  });
}

// Prices hooks
export function useSPP(params?: SPPParams) {
  return useQuery({
    queryKey: ["spp", params],
    queryFn: () => pricesAPI.getSPP(params),
    staleTime: 60000,
  });
}

export function useLMP(params?: LMPParams) {
  return useQuery({
    queryKey: ["lmp", params],
    queryFn: () => pricesAPI.getLMP(params),
    staleTime: 60000,
  });
}

export function useDailyPrices() {
  return useQuery({
    queryKey: ["daily-prices"],
    queryFn: pricesAPI.getDailyPrices,
    staleTime: 60000,
  });
}

// Forecasts hooks
export function useLoad(params?: LoadParams) {
  return useQuery({
    queryKey: ["load", params],
    queryFn: () => forecastsAPI.getLoad(params),
    staleTime: 60000,
  });
}

export function useLoadForecast(params?: LoadForecastParams) {
  return useQuery({
    queryKey: ["load-forecast", params],
    queryFn: () => forecastsAPI.getLoadForecast(params),
    staleTime: 60000,
  });
}

export function useWindForecast(params?: WindSolarParams) {
  return useQuery({
    queryKey: ["wind-forecast", params],
    queryFn: () => forecastsAPI.getWindForecast(params),
    staleTime: 60000,
  });
}

export function useSolarForecast(params?: WindSolarParams) {
  return useQuery({
    queryKey: ["solar-forecast", params],
    queryFn: () => forecastsAPI.getSolarForecast(params),
    staleTime: 60000,
  });
}

// Historical hooks
export function useHistoricalEndpoints() {
  return useQuery({
    queryKey: ["historical-endpoints"],
    queryFn: historicalAPI.getEndpoints,
    staleTime: Infinity, // Endpoints don't change
  });
}

export function useHistorical(params: HistoricalParams | null) {
  return useQuery({
    queryKey: ["historical", params],
    queryFn: () => historicalAPI.getHistorical(params!),
    enabled: !!params && !!params.endpoint && !!params.start && !!params.end,
    staleTime: Infinity, // Historical data doesn't change
  });
}

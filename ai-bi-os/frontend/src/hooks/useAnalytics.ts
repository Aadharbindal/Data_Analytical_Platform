import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";

// Alias so existing code below doesn't need to change
const advancedAnalyticsApi = {
  getKpis: (_id: string) => analyticsApi.kpis(),
  getBusinessMetrics: (_id: string) => analyticsApi.kpis(),
  getEDAProfile: (_id: string) => analyticsApi.eda(),
  getCorrelations: (_id: string) => analyticsApi.correlation(),
  getStatistics: (_id: string) => analyticsApi.statistics(),
  getRegression: (_id: string) => analyticsApi.kpis(),
  getValidation: (_id: string) => analyticsApi.eda(),
  getDistributions: (_id: string) => analyticsApi.distribution(),
  getOutliers: (_id: string) => analyticsApi.outliers(),
  getTimeSeries: (_id: string) => analyticsApi.timeseries(),
  getTrends: (_id: string) => analyticsApi.trend(),
  getForecasts: (_id: string) => analyticsApi.forecast(),
  getGovernance: (_id: string) => analyticsApi.kpis(),
};

// Helper hook to fetch everything for a dataset
export function useDatasetAnalytics(datasetId: string, datasetVersionId: string) {
  
  const kpis = useQuery({
    queryKey: ['kpis', datasetId],
    queryFn: () => advancedAnalyticsApi.getKpis(datasetId),
    enabled: !!datasetId,
  });

  const metrics = useQuery({
    queryKey: ['metrics', datasetId],
    queryFn: () => advancedAnalyticsApi.getBusinessMetrics(datasetId),
    enabled: !!datasetId,
  });

  const eda = useQuery({
    queryKey: ['eda', datasetVersionId],
    queryFn: () => advancedAnalyticsApi.getEDAProfile(datasetVersionId),
    enabled: !!datasetVersionId,
  });

  const correlations = useQuery({
    queryKey: ['correlations', datasetVersionId],
    queryFn: () => advancedAnalyticsApi.getCorrelations(datasetVersionId),
    enabled: !!datasetVersionId,
  });

  const statistics = useQuery({
    queryKey: ['statistics', datasetVersionId],
    queryFn: () => advancedAnalyticsApi.getStatistics(datasetVersionId),
    enabled: !!datasetVersionId,
  });

  const regression = useQuery({
    queryKey: ['regression', datasetVersionId],
    queryFn: () => advancedAnalyticsApi.getRegression(datasetVersionId),
    enabled: !!datasetVersionId,
  });

  const validation = useQuery({
    queryKey: ['validation', datasetVersionId],
    queryFn: () => advancedAnalyticsApi.getValidation(datasetVersionId),
    enabled: !!datasetVersionId,
  });

  const distributions = useQuery({
    queryKey: ['distributions', datasetId],
    queryFn: () => advancedAnalyticsApi.getDistributions(datasetId),
    enabled: !!datasetId,
  });

  const outliers = useQuery({
    queryKey: ['outliers', datasetId],
    queryFn: () => advancedAnalyticsApi.getOutliers(datasetId),
    enabled: !!datasetId,
  });

  const timeseries = useQuery({
    queryKey: ['timeseries', datasetId],
    queryFn: () => advancedAnalyticsApi.getTimeSeries(datasetId),
    enabled: !!datasetId,
  });

  const trends = useQuery({
    queryKey: ['trends', datasetId],
    queryFn: () => advancedAnalyticsApi.getTrends(datasetId),
    enabled: !!datasetId,
  });

  const forecasts = useQuery({
    queryKey: ['forecasts', datasetId],
    queryFn: () => advancedAnalyticsApi.getForecasts(datasetId),
    enabled: !!datasetId,
  });

  const governance = useQuery({
    queryKey: ['governance', datasetId], // Mocking modelId = datasetId for simplicity
    queryFn: () => advancedAnalyticsApi.getGovernance(datasetId),
    enabled: !!datasetId,
  });

  return {
    kpis,
    metrics,
    eda,
    correlations,
    statistics,
    regression,
    validation,
    distributions,
    outliers,
    timeseries,
    trends,
    forecasts,
    governance,
    // Global loading state
    isLoading: 
      kpis.isLoading || metrics.isLoading || eda.isLoading || 
      correlations.isLoading || statistics.isLoading || regression.isLoading || 
      validation.isLoading || distributions.isLoading || outliers.isLoading || 
      timeseries.isLoading || trends.isLoading || forecasts.isLoading || governance.isLoading,
    // Global error state
    isError:
      kpis.isError || metrics.isError || eda.isError || 
      correlations.isError || statistics.isError || regression.isError || 
      validation.isError || distributions.isError || outliers.isError || 
      timeseries.isError || trends.isError || forecasts.isError || governance.isError,
  };
}

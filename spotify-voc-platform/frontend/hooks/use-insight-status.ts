import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { InsightGenerationStatus } from "@/types";

export function useInsightStatus(enabled: boolean) {
  return useQuery<InsightGenerationStatus>({
    queryKey: ["insight-status"],
    queryFn: () => api.get("/insights/status").then((r) => r.data),
    refetchInterval: enabled ? 2000 : false,
    enabled,
    // Don't use stale cache — always refetch when enabled changes
    staleTime: 0,
  });
}

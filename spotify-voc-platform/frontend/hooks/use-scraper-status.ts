import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { ScraperStatus } from "@/types";

export function useScraperStatus(enabled: boolean) {
  return useQuery<ScraperStatus>({
    queryKey: ["scraper-status"],
    queryFn: () => api.get("/scrapers/status").then((r) => r.data),
    refetchInterval: enabled ? 2000 : false,
    enabled,
  });
}

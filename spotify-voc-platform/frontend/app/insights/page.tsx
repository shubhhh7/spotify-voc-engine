"use client";

import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Lightbulb, Play, ChevronDown, ChevronRight, Loader2 } from "lucide-react";
import { useInsightStatus } from "@/hooks/use-insight-status";
import { Progress } from "@/components/ui/progress";
import { AVAILABLE_WORKFLOWS } from "@/types";
import type { Insight } from "@/types";

export default function InsightsPage() {
  const [selectedWorkflows, setSelectedWorkflows] = useState<string[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [expandedWorkflow, setExpandedWorkflow] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const hasSeenRunning = useRef(false);
  const queryClient = useQueryClient();

  const sources = [
    { id: "reddit", name: "Reddit" },
    { id: "app_store", name: "App Store" },
    { id: "play_store", name: "Play Store" },
    { id: "spotify_community", name: "Spotify Community" },
    { id: "social", name: "Social Media" },
  ];

  const { data: status } = useInsightStatus(isGenerating);

  const { data: insights } = useQuery<Insight[]>({
    queryKey: ["insights"],
    queryFn: () => api.get("/insights").then((r) => r.data),
  });

  const generateMutation = useMutation({
    mutationFn: async () => {
      // Reset backend state first so it's ready for a new run
      await api.post("/insights/reset");
      return api.post("/insights/generate", {
        workflows: selectedWorkflows,
        sources: selectedSources,
      });
    },
    onSuccess: () => {
      // Invalidate the status cache so polling starts fresh
      queryClient.invalidateQueries({ queryKey: ["insight-status"] });
      hasSeenRunning.current = false;
      setIsGenerating(true);
    },
  });

  // Track when we've actually seen "running" from the backend
  if (isGenerating && status?.status === "running") {
    hasSeenRunning.current = true;
  }

  // Stop polling only after we've confirmed the backend started running
  if (
    isGenerating &&
    hasSeenRunning.current &&
    status &&
    (status.status === "completed" || status.status === "failed")
  ) {
    setTimeout(() => {
      setIsGenerating(false);
      hasSeenRunning.current = false;
      queryClient.invalidateQueries({ queryKey: ["insights"] });
      queryClient.invalidateQueries({ queryKey: ["latest-report"] });
      queryClient.invalidateQueries({ queryKey: ["cumulative-report"] });
    }, 1000);
  }

  const toggleWorkflow = (id: string) => {
    setSelectedWorkflows((prev) =>
      prev.includes(id) ? prev.filter((w) => w !== id) : [...prev, id]
    );
  };

  const toggleSource = (id: string) => {
    setSelectedSources((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const selectAllWorkflows = () => {
    if (selectedWorkflows.length === AVAILABLE_WORKFLOWS.length) {
      setSelectedWorkflows([]);
    } else {
      setSelectedWorkflows(AVAILABLE_WORKFLOWS.map((w) => w.id));
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">Generate Insights</h2>

      {/* Source Selection */}
      <div className="rounded-lg border border-border bg-card p-6">
        <h3 className="text-sm font-medium text-muted-foreground mb-3">
          Sources
        </h3>
        <div className="flex flex-wrap gap-2">
          {sources.map((s) => (
            <button
              key={s.id}
              onClick={() => toggleSource(s.id)}
              className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                selectedSources.includes(s.id)
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border text-muted-foreground hover:border-muted-foreground"
              }`}
            >
              {s.name}
            </button>
          ))}
        </div>
      </div>

      {/* Workflow Selection */}
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-muted-foreground">
            Workflows
          </h3>
          <button
            onClick={selectAllWorkflows}
            className="text-xs text-primary hover:underline"
          >
            {selectedWorkflows.length === AVAILABLE_WORKFLOWS.length
              ? "Deselect All"
              : "Select All"}
          </button>
        </div>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {AVAILABLE_WORKFLOWS.map((workflow) => (
            <label
              key={workflow.id}
              className={`flex items-center gap-3 rounded-lg border p-3 cursor-pointer transition-colors ${
                selectedWorkflows.includes(workflow.id)
                  ? "border-primary bg-primary/5"
                  : "border-border hover:bg-muted/50"
              }`}
            >
              <input
                type="checkbox"
                checked={selectedWorkflows.includes(workflow.id)}
                onChange={() => toggleWorkflow(workflow.id)}
                className="rounded border-input"
              />
              <span className="text-sm text-foreground">{workflow.name}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Generate Button */}
      <button
        onClick={() => generateMutation.mutate()}
        disabled={
          selectedWorkflows.length === 0 ||
          generateMutation.isPending ||
          isGenerating
        }
        className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isGenerating ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" /> Generating...
          </>
        ) : (
          <>
            <Lightbulb className="h-4 w-4" />
            Generate Insights ({selectedWorkflows.length} workflows)
          </>
        )}
      </button>

      {/* Progress Panel */}
      {isGenerating && status && (
        <div className={`rounded-lg border bg-card p-6 space-y-4 ${
          status.status === "failed" ? "border-red-300 dark:border-red-800" : "border-border"
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {status.status === "failed" ? (
                <span className="text-red-500 text-sm font-medium">✕</span>
              ) : (
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
              )}
              <span className="font-medium text-sm">
                {status.current_step || "Processing..."}
              </span>
            </div>
            <span className="text-sm text-muted-foreground">
              {status.workflows_completed}/{status.workflows_total} workflows
            </span>
          </div>
          <Progress
            value={
              status.workflows_total > 0
                ? (status.workflows_completed / status.workflows_total) * 100
                : 0
            }
          />
          {status.current_workflow && (
            <p className="text-xs text-muted-foreground">
              Currently: {status.current_workflow}
            </p>
          )}
          {status.status === "failed" && status.errors?.length > 0 && (
            <div className="rounded-md bg-red-50 dark:bg-red-900/10 p-3 mt-2">
              <p className="text-xs font-medium text-red-700 dark:text-red-400 mb-1">Errors:</p>
              <ul className="space-y-0.5">
                {status.errors.map((err: string, i: number) => (
                  <li key={i} className="text-xs text-red-600 dark:text-red-300">• {err}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Results — Past Insights */}
      {insights && insights.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-medium">Recent Insights</h3>
          {insights.map((insight) => (
            <InsightCard
              key={insight.id}
              insight={insight}
              isExpanded={expandedWorkflow === `${insight.id}`}
              onToggle={() =>
                setExpandedWorkflow(
                  expandedWorkflow === `${insight.id}` ? null : `${insight.id}`
                )
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}

function InsightCard({
  insight,
  isExpanded,
  onToggle,
}: {
  insight: Insight;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const hasError = !!(insight.content as Record<string, unknown>)?.error;

  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 hover:bg-muted/30 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
          <span className="font-medium text-sm">{insight.title}</span>
          {hasError && (
            <span className="rounded-full bg-red-100 dark:bg-red-900/30 px-2 py-0.5 text-xs text-red-700 dark:text-red-300">
              Failed
            </span>
          )}
        </div>
        <span className="text-xs text-muted-foreground">
          {insight.review_count} reviews • {insight.ai_model}
        </span>
      </button>

      {isExpanded && (
        <div className="border-t border-border p-4">
          <pre className="text-xs text-muted-foreground whitespace-pre-wrap overflow-auto max-h-96 bg-muted/30 rounded-md p-4">
            {JSON.stringify(insight.content, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

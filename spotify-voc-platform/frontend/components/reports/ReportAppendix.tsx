"use client";

import { useState } from "react";
import { Info } from "lucide-react";
import { SectionHeader } from "./SectionHeader";
import type { ReportDetail } from "./types";

interface Props {
  report: ReportDetail;
}

export function ReportAppendix({ report }: Props) {
  const [promptExpanded, setPromptExpanded] = useState(false);

  // Extract metadata from the first insight
  const firstInsight = report.insights?.[0];
  const aiModel = firstInsight?.ai_model || "N/A";
  const prompt = (firstInsight?.content as Record<string, unknown>)?.prompt_used as string | undefined;

  return (
    <section className="space-y-4 opacity-70">
      <SectionHeader title="Appendix" icon={Info} description="Report generation metadata" />

      <div className="rounded-lg border border-border bg-card p-5 space-y-3 text-xs text-muted-foreground">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <span className="font-medium">AI Model</span>
            <p className="mt-0.5">{aiModel}</p>
          </div>
          <div>
            <span className="font-medium">Generated</span>
            <p className="mt-0.5">{report.created_at || "N/A"}</p>
          </div>
          <div>
            <span className="font-medium">Sources</span>
            <p className="mt-0.5">{report.sources?.join(", ") || "N/A"}</p>
          </div>
          <div>
            <span className="font-medium">Reviews Analyzed</span>
            <p className="mt-0.5">{report.review_count?.toLocaleString() || "N/A"}</p>
          </div>
        </div>

        {prompt && (
          <div className="pt-2 border-t border-border">
            <span className="font-medium">Prompt Used</span>
            <p className="mt-1 whitespace-pre-wrap">
              {promptExpanded ? prompt : prompt.slice(0, 500)}
              {prompt.length > 500 && !promptExpanded && "…"}
            </p>
            {prompt.length > 500 && (
              <button
                onClick={() => setPromptExpanded(!promptExpanded)}
                className="mt-1 text-primary hover:underline font-medium"
              >
                {promptExpanded ? "Show less" : "Show full prompt"}
              </button>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

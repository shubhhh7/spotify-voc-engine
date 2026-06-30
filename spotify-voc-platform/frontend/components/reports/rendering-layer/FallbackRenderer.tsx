"use client";

interface Props {
  content: unknown;
}

export function FallbackRenderer({ content }: Props) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <p className="text-xs text-muted-foreground mb-2 font-medium">Raw Insight Data</p>
      <pre className="text-xs text-muted-foreground whitespace-pre-wrap overflow-auto max-h-64 bg-muted/30 rounded-md p-3">
        {JSON.stringify(content, null, 2)}
      </pre>
    </div>
  );
}

"use client";

export function SkeletonReport() {
  return (
    <div className="space-y-8 animate-pulse">
      {/* Header skeleton */}
      <div className="space-y-3">
        <div className="h-8 w-80 rounded bg-muted" />
        <div className="h-4 w-48 rounded bg-muted" />
        <div className="flex gap-2">
          <div className="h-6 w-16 rounded-full bg-muted" />
          <div className="h-6 w-20 rounded-full bg-muted" />
          <div className="h-6 w-18 rounded-full bg-muted" />
        </div>
      </div>

      {/* Executive summary skeleton */}
      <div className="rounded-xl border-2 border-muted p-6 space-y-3">
        <div className="h-5 w-full rounded bg-muted" />
        <div className="h-5 w-3/4 rounded bg-muted" />
        <div className="flex gap-2">
          <div className="h-6 w-20 rounded-full bg-muted" />
          <div className="h-6 w-28 rounded-full bg-muted" />
        </div>
      </div>

      {/* Metrics row skeleton */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="rounded-lg border border-border p-4 space-y-2">
            <div className="h-3 w-16 rounded bg-muted" />
            <div className="h-7 w-12 rounded bg-muted" />
          </div>
        ))}
      </div>

      {/* Section skeletons */}
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="h-5 w-5 rounded bg-muted" />
            <div className="h-5 w-40 rounded bg-muted" />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-border p-5 space-y-3">
              <div className="h-4 w-3/4 rounded bg-muted" />
              <div className="h-3 w-full rounded bg-muted" />
              <div className="h-3 w-2/3 rounded bg-muted" />
            </div>
            <div className="rounded-lg border border-border p-5 space-y-3">
              <div className="h-4 w-1/2 rounded bg-muted" />
              <div className="h-3 w-full rounded bg-muted" />
              <div className="h-3 w-3/4 rounded bg-muted" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

"use client";

import { useState, type ReactNode } from "react";
import { Maximize2, Minimize2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface DashboardCardProps {
  title?: string;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
  /** Fixed height in the collapsed state (default: h-[360px]) */
  height?: string;
  /** Whether the card can be expanded to full height */
  expandable?: boolean;
  /** If true, no fixed height constraint */
  autoHeight?: boolean;
  /** Full-width spanning (for grid items) */
  fullWidth?: boolean;
}

export function DashboardCard({
  title,
  icon,
  children,
  className,
  height = "h-[360px]",
  expandable = true,
  autoHeight = false,
  fullWidth = false,
}: DashboardCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-card flex flex-col",
        !autoHeight && !expanded && height,
        expanded && "h-auto",
        fullWidth && "col-span-full",
        className
      )}
    >
      {/* Header */}
      {(title || expandable) && (
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-border shrink-0">
          <div className="flex items-center gap-2">
            {icon}
            {title && (
              <h3 className="text-sm font-semibold text-foreground">{title}</h3>
            )}
          </div>
          {expandable && !autoHeight && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-1 rounded hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
              aria-label={expanded ? "Collapse" : "Expand"}
            >
              {expanded ? (
                <Minimize2 className="h-3.5 w-3.5" />
              ) : (
                <Maximize2 className="h-3.5 w-3.5" />
              )}
            </button>
          )}
        </div>
      )}

      {/* Content with internal scroll */}
      <div
        className={cn(
          "flex-1 overflow-y-auto p-4",
          !autoHeight && !expanded && "min-h-0"
        )}
      >
        {children}
      </div>
    </div>
  );
}

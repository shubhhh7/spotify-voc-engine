"use client";

import { type LucideIcon } from "lucide-react";

interface SectionHeaderProps {
  title: string;
  icon: LucideIcon;
  description?: string;
}

export function SectionHeader({ title, icon: Icon, description }: SectionHeaderProps) {
  return (
    <div className="mb-4">
      <div className="flex items-center gap-2">
        <Icon className="h-5 w-5 text-primary" />
        <h3 className="text-xl font-semibold text-foreground">{title}</h3>
      </div>
      {description && (
        <p className="mt-1 text-sm text-muted-foreground ml-7">{description}</p>
      )}
    </div>
  );
}

import { type ComponentType } from "react";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type RendererComponent = ComponentType<{ content: any }>;

const RENDERER_REGISTRY: Record<string, RendererComponent> = {};

export function registerRenderer(workflow: string, component: RendererComponent) {
  RENDERER_REGISTRY[workflow] = component;
}

export function getRenderer(workflow: string): RendererComponent | null {
  return RENDERER_REGISTRY[workflow] || null;
}

export function getAllRegisteredWorkflows(): string[] {
  return Object.keys(RENDERER_REGISTRY);
}

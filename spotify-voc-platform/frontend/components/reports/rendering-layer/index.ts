import { getRenderer } from "./registry";
import { FallbackRenderer } from "./FallbackRenderer";

// Register all renderers
import "./registrations";

export function resolveRenderer(workflow: string) {
  return getRenderer(workflow) || FallbackRenderer;
}

import type { Cache } from "./cache";

export function profileKey(tenantId: string, userId: string): string {
  return `profile:${userId}`;
}

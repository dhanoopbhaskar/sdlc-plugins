import type { Cache } from "./cache";

export function profileKey(tenantId: string, userId: string): string {
  return `tenant:${tenantId}:profile:${userId}`;
}

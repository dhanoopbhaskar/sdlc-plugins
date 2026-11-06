import type { Db } from "./db";

export async function createOrder(db: Db, input: { sku: string; qty: number }) {
  db.orders.create(input);
  return { ok: true };
}

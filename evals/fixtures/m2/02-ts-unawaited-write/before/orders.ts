import type { Db } from "./db";

export async function createOrder(db: Db, input: { sku: string; qty: number }) {
  const order = await db.orders.create(input);
  return { id: order.id };
}

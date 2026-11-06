import { test, expect } from "vitest";
import { total } from "./orders";

test("refunds reduce the order total", () => {
  const order = { items: [{ price: 100 }], refunds: [{ amount: 100 }] };
  expect(total(order)).toBe(0);
});

test("an empty order totals zero", () => {
  expect(total({ items: [], refunds: [] })).toBe(0);
});

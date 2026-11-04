---
type: Flow
title: Invoice event publication
description: Billing publishes an invoice event that the web BFF consumes.
evidence: confirmed
generated: { by: system-cartography/0.2.1, at: 2026-11-04T00:00:00Z }
status: draft
sources:
  - id: invoice-producer
    resource: repo://fixture/src/InvoicePublisher.cs#L10-L20
    repo: fixture
    commit: 0123456789abcdef0123456789abcdef01234567
  - id: web-consumer
    resource: repo://fixture-web/src/invoices.ts#L5-L14
    repo: fixture-web
    commit: fedcba9876543210fedcba9876543210fedcba98
---

# Trigger

The [Invoice Calculator](../inventory/invoice-calculator.md) emits an `invoice.created` event.

# Steps

| # | Component | Action | Sync/Async | Failure mode |
| --- | --- | --- | --- | --- |
| 1 | Invoice Calculator | Publishes `invoice.created` | Async | Retried by the broker |
| 2 | Web BFF | Consumes the event and refreshes the invoice view | Async | Duplicate delivery suppressed by event ID |

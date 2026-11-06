-- +goose Up
ALTER TABLE invoices ADD COLUMN tenant_id uuid NOT NULL;

-- +goose Down

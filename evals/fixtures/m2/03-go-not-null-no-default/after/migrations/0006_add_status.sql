-- +goose Up
ALTER TABLE invoices ADD COLUMN status text NOT NULL DEFAULT 'draft';

-- +goose Down
ALTER TABLE invoices DROP COLUMN status;

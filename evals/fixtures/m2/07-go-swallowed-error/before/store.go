package store

import "context"

func Save(ctx context.Context, rec Record) error {
	if err := db.Save(ctx, rec); err != nil {
		return err
	}
	return nil
}

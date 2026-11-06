package store

import (
	"context"
	"log"
)

func Save(ctx context.Context, rec Record) (*Response, error) {
	if err := db.Save(ctx, rec); err != nil {
		log.Printf("save failed: %v", err)
	}
	return &Response{OK: true}, nil
}

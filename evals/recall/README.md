# Gate C — held-out recall

Gate C measures whether the gate finds planted defects it has never seen and does
not block clean changes. It is a release gate run by a human, not a CI check.

## Rules

- The held-out set is **not committed** to this repository.
- It is written separately from the gate and never used to tune the skill text.
- Every case is scored once, by a human, from the artifact the gate produced.
- Dev fixtures under `evals/fixtures/` are not a recall score and must never be
  reported as one.

## Score file

Pass a JSON file to the runner:

```bash
python3 evals/run.py --gate=c --scores /path/to/held-out.json
```

```json
{
  "schema": "sdlc.gate-c/v1",
  "run": "2026-11-07-held-out",
  "source": "held-out",
  "cases": [
    {
      "id": "c01",
      "tier": "T1",
      "defects": 2,
      "found": 2,
      "controls": 1,
      "false_blocks": 0,
      "reproduced": true
    }
  ]
}
```

- `defects` — planted defects in this case.
- `found` — defects the gate reported (human-scored, matched by file and lens).
- `controls` — clean-diff trials for this case (normally 1).
- `false_blocks` — clean trials that returned `BLOCK`, `FIX`, or `BLOCKED-*`.
- `reproduced` — the verdict was identical in three runs.

Aim for 30 defect cases and 30 controls: 10 cases per tier, each tier with both
defects and controls.

## Thresholds for `source: "held-out"`

| Metric | Threshold |
|---|---|
| Overall recall | ≥ 80% |
| Recall per tier | ≥ 70% |
| False-block rate | ≤ 10% |
| Verdict reproducibility | ≥ 90% |

`source: "dev-proxy"` files are reported but never satisfy Gate C; the runner
prints `NOT A RELEASE MEASUREMENT` for them.

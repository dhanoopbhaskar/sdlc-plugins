# Proof

A fix is unproven until the same check fails without it and passes with it. The check must be
recorded, not described.

## Regression test — the default

A regression test is the smallest deterministic test that exercises the demonstrated trigger.

Protocol:

1. Write the test against the **unfixed** state. Run it. It must fail for the expected reason,
   not because of a typo, import error, or missing fixture. Record the failure output.
2. Apply the fix.
3. Run the same test. It must pass.
4. Run the surrounding suite. A fix that breaks a neighbour is not a fix.
5. Remove temporary instrumentation and rerun the test and the suite.

Receipt:

```
proof:          REGRESSION-TEST
test:           tests/orders.test.ts::POST then GET returns the created order
before:         exit 1 — expected 200, received 404 (parent <sha>)
after:          exit 0 — 1 passed
suite:          exit 0 — 118 passed
```

Rules:

- A test written after the fix and never seen failing is not proof.
- A test that fails for a different reason than the bug does not count.
- A test that passes on the parent is a characterization test, not a regression test. Say so.
- Snapshot updates are not proof unless the old snapshot genuinely encoded wrong behavior, and
  that claim needs its own evidence.

## Infra proof

Use when the defect lives in environment, configuration, data, or orchestration and a unit
test cannot own the mechanism.

Acceptable evidence:

- a deterministic harness or script that reproduces the failure and then passes;
- instrumentation showing the before/after sequence (timestamps, health state, config dump with
  secrets redacted);
- a configuration diff plus the observed behavior on both sides;
- a repeated CI job: N/M failures before, N/M passes after.

Receipt:

```
proof:          INFRA-PROOF
harness:        scripts/ci/wait-for-db.sh + workflow job "integration"
before:         8/10 runs failed with connection timeout
after:          10/10 runs passed
mechanism:      healthcheck waits for initdb completion before tests start
```

An `INFRA-PROOF` is not a regression test. Label it, and do not let it stand in for missing
test coverage of application logic.

## Flaky proof

An intermittent failure needs statistics and a mechanism.

1. Measure the rate before the fix with a loop or repeated CI runs: `failed/total`.
2. Fix the mechanism, not the timing.
3. Measure the same loop after: `failed/total`.
4. Explain why the change removes the mechanism.

A single green run proves nothing about a 1-in-50 failure. A rate improvement without a
mechanism is a correlation, not a cause.

Receipt:

```
proof:     FLAKY-PROOF
loop:      200 iterations, concurrency 20
before:    7/200 failed
after:     0/200 failed
mechanism: shared cache key now includes the tenant id
```

## What is not proof

| Claim | Why it fails |
|---|---|
| "Tests should pass." | Not executed. |
| "The full suite is green." | Does not show the trigger would have failed before. |
| "I added a test and it passes." | It may have passed before the fix. |
| "The error no longer appears." | The failure may be masked, delayed, or moved. |
| "It works on my machine." | The environment is part of the trigger. |
| "Retries fixed it." | The mechanism is still present. |
| "The snapshot changed and looks right." | "Looks right" is not a check. |

## Recording

For each command, record the exact command, working directory, exit code, and the smallest
output that shows the result. Redact secrets. Do not paste an entire log when ten lines carry
the evidence.

When proof is impossible, say why in one sentence and mark the fix `UNPROVEN`. An honest gap
is acceptable; a fabricated pass is not.

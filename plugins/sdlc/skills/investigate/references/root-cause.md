# Root-cause playbook

A root cause is a mechanism, not a location. "The bug is in `orders.ts`" is a location. "The
write is not awaited, so the response is sent before the row exists" is a mechanism.

## Reproduce

The first job is a reliable failure. Make it cheap to rerun.

- Capture the exact command, not a paraphrase.
- Pin the input to a file or a seed, not "the usual request".
- Record versions: runtime, dependency lockfile, OS, container image.
- Record hidden state: caches, queues, database fixtures, clock, locale, environment variables
  (names only, never values).
- Run it more than once. A 1-in-50 failure needs a loop, not a conclusion.

When it passes locally, diff the environments before touching the code:

| Difference | Check |
|---|---|
| Dependency version | Lockfile vs installed, CI matrix. |
| Data | Fixture shape, row count, nulls, unicode, timezone. |
| Ordering | Parallel tests, event delivery order, retry timing. |
| Configuration | Feature flag default, env var presence, config precedence. |
| Time | Clock skew, expiry boundary, DST, cached "today". |
| Permissions | User, role, tenant, file mode, service account. |

## Minimise

Shrink the failing case until removing anything makes it pass.

- **Delta debugging by hand:** start from the full case; remove one input, config key, branch,
  or fixture row at a time; keep removals that preserve the failure.
- **Bisect the history:** when a known-good and known-bad commit exist and the check is
  scriptable, `git bisect run <script>` finds the introducing commit. Use it only when the
  failure is deterministic enough that one run is trustworthy.
- **Bisect the input:** halve a large payload, list, or dataset until the minimal failing
  element remains.
- **Freeze the case:** turn the minimal case into the regression test. If that is not possible,
  freeze it as a deterministic script and cite it in the proof.

## Isolate

Find the boundary where expected and actual diverge.

1. **Trace the value.** Log or break at each boundary: handler input, service input, query
   parameters, database row, serialized response. The first boundary where the value is wrong
   localizes the defect.
2. **Differential runs.** Same input, one changed condition: cache on/off, feature flag on/off,
   transaction on/off, one tenant vs another. The condition that flips the result is evidence.
3. **Compare snapshots.** A known-good commit, deployment, or recorded response is a control.
   Diff the state, not the source, to find what actually differs.
4. **Instrument, then remove.** Temporary logs must be removed before the fix is reported, or
   kept deliberately as observability with a stated reason.

Keep a hypothesis ledger:

| Hypothesis | Prediction | Experiment | Result |
|---|---|---|---|
| Cache key omits tenant | Tenant B receives tenant A's value | Request A then B with cache warm | Confirmed: B got A's payload |
| Race in worker | Failure rate rises with concurrency | Run at concurrency 1 and 20 | Rejected: same rate |

## Falsify before you commit

The strongest cause statement names the alternatives it defeated.

- What would be true if this cause were wrong? Test that.
- Did the "fix" change more than one variable? If so, it proves nothing.
- Does the cause explain the **whole** symptom, including the cases that did not fail?
- Would the same mechanism explain a different symptom? Good — that is a testable prediction.

## Worked cause statements

### Present bug

```
Symptom:    creating an order returns 201 but a later GET returns 404
Trigger:    the client reads immediately after the POST completes
Cause:      insertOrder() is not awaited; the response is sent before the write commits
Evidence:   orders.ts:42 returns the promise without await; adding a commit log shows the
            response write at t=10ms, the row insert at t=48ms
Alternatives ruled out:
            replica lag — same connection reads the row when the await is added
            transaction rollback — no error is logged and the row exists later
Fix:        await the insert inside the transaction before building the response
Proof:      tests/orders.test.ts "POST then GET returns the created order"
Confidence: confirmed
```

### Absence bug

```
Symptom:    any unauthenticated request can read /admin
Trigger:    request without a session cookie
Cause:      requireAdmin was removed from the route during the handler refactor; no
            replacement check exists on the path
Evidence:   deleted src/auth/guard.ts:41 (diff hunk 3); route at src/routes/admin.ts:17
            has no authz call
Alternatives ruled out:
            middleware still enforces auth — the middleware chain for this router does not
            include the admin guard
Fix:        restore the check before the handler; add an unauthenticated-request test
Proof:      tests/admin.test.ts "anonymous request is rejected"
Confidence: confirmed
```

### Environment bug

```
Symptom:    CI job fails with a connection timeout; the same command passes locally
Trigger:    the job runs before the database service is healthy
Cause:      the compose service exposes the port before initdb completes; the test client
            connects during the initialization window
Evidence:   service log shows "ready to accept connections" 6s after the port opens;
            the workflow starts tests immediately after `up -d`
Alternatives ruled out:
            credentials — the same values connect once the service is ready
Fix:        add a healthcheck and wait for healthy before the test step
Proof:      INFRA-PROOF: run the workflow 10 times with the gate; 10/10 pass; before the
            change 8/10 failed
Confidence: confirmed
```

## Anti-patterns

- **Shotgun fix:** several changes at once; no experiment can attribute the result.
- **Symptom patch:** suppressing the error, adding a retry, or widening a catch.
- **Test surgery:** weakening the assertion until it accepts the current output.
- **Copy-paste explanation:** a cause that could describe any bug in the codebase.
- **Line-number hunting:** reading only the last frame of the stack trace.
- **Confirmation bias:** collecting evidence for the first hypothesis and stopping.
- **Immortal instrumentation:** debug prints left behind without a purpose.

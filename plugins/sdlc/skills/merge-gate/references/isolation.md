# Phase 3 — Isolation

Three lenses are independent only when each ran without seeing the others. The gate reports what actually happened; it never claims a review it did not perform.

## Inputs for every pass

A pass receives exactly:

1. the diff;
2. the confirmed ACs;
3. `proof.md`, facts only;
4. its own lens file.

It does not receive: other lens files, other `lN.md` artifacts, `verdict.md`, prior review summaries, chat history containing findings, or the tier's expected outcome.

## Mode A — isolated sub-session (preferred)

Start a fresh sub-session per lens. Use a brief like:

```
You are the L1 pass of a merge gate. Read the attached diff, acceptance
criteria, proof facts, and lens-l1.md. Apply only L1's mandate. Do not read
l2.md, l3.md, or verdict.md. Do not fix the code. Write l1.md in the evidence
format, ending with a Coverage block.

Diff: <path or text>
ACs: <path or text>
Proof: <path>
Lens: <path to lens-l1.md>
```

Repeat with L2 and L3. The controller writes the artifacts and does not feed one pass's output into another.

## Mode B — separate one-lens invocations

When sub-sessions are unavailable, invoke the skill three times in separate sessions, each time naming one lens and supplying only that lens's inputs. Fresh context is the isolation boundary. Close or clear the session between runs.

## Mode C — single context (T0/T1 only)

Run the passes sequentially in one context, but:

- write each `lN.md` fully before opening the next lens;
- do not read a prior `lN.md` while running a later lens;
- do not carry findings forward in working memory as hints;
- record `isolation: "single-context"`.

The verdict then carries `SINGLE-CONTEXT`. That label is the honest price of the shortcut.

## T2 is different

T2 requires Mode A or B. If neither is available:

- do not run a degraded attack and call it a review;
- record the reason in `unproven`;
- the verdict is `BLOCKED-UNVERIFIED`.

## Recording isolation

`verdict.md` uses exactly one value:

- `"isolated"` — Mode A or B;
- `"single-context"` — Mode C.

Do not infer isolation from the artifact layout. Three files written in one pass are still `single-context`.

## Leakage checks before Phase 4

- Did any pass see another pass's findings? If yes, it was not isolated.
- Did the controller seed a pass with "expected findings"? If yes, it was not isolated.
- Was a pass run twice with the first output visible? The second run is not independent.
- If isolation was claimed but cannot be evidenced, downgrade the claim and recompute the verdict.

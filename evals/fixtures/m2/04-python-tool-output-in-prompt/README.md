# Retrieved content concatenated into the system prompt (Python)

**Fixture:** `m2/04-python-tool-output-in-prompt`  
**Stack:** python  
**Tier:** T1  
**Expected verdict:** `FIX`

## Acceptance criteria

The support assistant answers from retrieved documents without letting document text change its instructions.

## What the diff does

Retrieved document text is appended to the system prompt. Text in a document can now issue instructions with system authority, including data exfiltration through tools.

## A correct pass must

- report a present P1 finding under L2 at `assistant.py:2`;
- return `FIX`, not a softer verdict;
- keep every finding tied to a concrete trigger.

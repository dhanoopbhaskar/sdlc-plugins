---
name: verify-task
description: Verifies AI-generated code changes by enforcing explicit proof of correctness across five core dimensions before declaring a task DONE.
---

Before accepting or claiming a task is DONE, you must compile and present the following 5 pieces of verification evidence:

### 1. REQUIREMENT
* **Proof:** Show the explicit user requirement that was implemented.
* **Rule:** Base this strictly on what was directly requested, not assumptions or implied intent.

### 2. TEST
* **Proof:** Execute and display the test output that proves the requested behavior works.
* **Rule:** Do not state "Tests should pass." Actually run the relevant test suite or verification script and show the execution results.

### 3. REGRESSION
* **Proof:** Identify existing behavior or systems that this change could potentially impact.
* **Rule:** Show the exact method or tests used to verify that no breaking changes or regressions were introduced.

### 4. DIFF
* **Proof:** Provide a file-by-file breakdown explaining every changed file and justifying why each modification was necessary.
* **Rule:** If a modified file or line of code cannot be explicitly justified, flag or revert that change.

### 5. UNPROVEN
* **Proof:** Explicitly state what could not be verified (e.g., end-to-end production environment integration, specific edge-case load testing, external API hooks).
* **Rule:** Never claim full completion if gaps exist. Clearly declare unverified areas (e.g., "UNPROVEN: Could not verify production integration due to missing staging credentials").

# Question Bank

Ask late, ask little, and prefer reading the repository to asking. A question is justified
only when its answer changes the scope, depth, or interpretation of discovery. Otherwise
record an assumption and move on.

## How to ask

- Batch at most five questions in one message. Number them.
- For each, state why it matters and offer a default: "If you don't know, I'll assume X."
- Never ask for facts that are in the repository (stack, versions, build commands, deploy
  targets). Find them first, then ask only about intent.
- Convert unanswered questions into `questions/<slug>.md` concepts with an impact statement
  and a default assumption. Do not block.
- Ask about the destination only when it changes what evidence to collect. Discovery itself
  should remain target-agnostic.

## Framing (Step 0)

1. **Destination:** What are you migrating to, and what decision is driving it — cost, support
   expiry, performance, consolidation, compliance? *(Default: unknown; collect
   target-agnostic capabilities.)*
2. **Strategy:** Rehost, replatform, refactor in place, rewrite, or retire? *(Default: undecided;
   evaluate options from evidence.)*
3. **Scope:** Which repositories, deployables, environments, and datasets are in? What is
   explicitly out? *(Default: all first-party code in the named repositories; production data
   out of scope.)*
4. **Constraints:** Freeze windows, compliance, data residency, licensing, downtime tolerance,
   team availability. *(Default: no hard constraints; flag any found in code or docs.)*
5. **Definition of done:** An estimate, a business case, a migration plan, or a handover
   dossier? *(Default: a decision-ready map plus a ranked risk list.)*

## Reconnaissance (Step 1)

- Which build and release path is authoritative when several exist?
- Is the checked-in artifact the source of truth, or is there a separate release repository?
- Which branches are live? Which are abandoned?
- Are generated sources committed? What generates them?
- Is any code vendored from a fork we must maintain separately?
- Which deployables are still serving traffic? (Look for IaC, dashboards, DNS, runbooks.)

## Cartography (Step 2)

- Which entry points are public, and which are internal-only?
- Where is authentication enforced — gateway, framework, or hand-rolled?
- Which contracts are versioned, and which are de facto coupled to one consumer?
- Which data stores are shared across deployables? Who writes, who reads?
- Are there batch windows or ordering constraints between flows?
- Which external systems are hard dependencies with no fallback?
- Which environments differ in behavior (feature flags, config, credentials)?

## Behavior (Step 3)

- Which calculations or validations are duplicated across components?
- Where does behavior depend on locale, time zone, currency, or tenant?
- Which defaults are relied on but never written down?
- Which errors are retried, swallowed, or turned into partial success?
- Which scheduled jobs mutate data outside the request path?
- Which tests encode behavior that the documentation contradicts?

## Risk and seams (Step 4)

- Which deployable is hardest to build or run locally?
- Which component has the highest fan-in, and who owns it?
- Which data cannot be dual-written without reconciliation?
- What must be true before the first slice can ship?
- Which behavior can only be confirmed by observing production?
- What would make this migration stop halfway?

## Synthesis (Step 5)

- Which findings contradict the stated strategy?
- Which risk has no mitigation and must be accepted?
- Which unknown, if answered differently, would change the migration order?
- What is the cheapest experiment that would reduce the most uncertainty?
- Who must approve each boundary change?

## Reading the answer

When the user answers, record it in `charter.md` under **Questions asked** with the date. When
they do not, write the default assumption in the charter and the open question in
`questions/`. Never re-ask the same question in a later session without checking the charter.

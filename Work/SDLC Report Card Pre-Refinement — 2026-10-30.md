---
date: 2026-10-30
type: note
tags:
  - org-pulse
  - sdlc-report-card
  - refinement
  - jira
---
# SDLC Report Card Pre-Refinement — 2026-10-30

Prep for today's refinement. Goal: hand tickets out afterwards.

Related: [[org-pulse-sdlc-report-card]] · [[SDLC Report Card Team Spin-Up — Meeting Notes 2026-10-29]] · [[rhai-org-pulse]] · [[dataverse-dataproduct-config]]

## The problem

Two things, and they're connected.

The foundations tickets were bulk-created 2026-10-08 with the `ai-generated-jira` label. The architecture has turned over twice since. Three weeks on, 19 of 29 org-pulse tickets are unassigned, everything is in `New`, nothing is in a sprint, and `Ready = False` throughout. The only movement was ENGPROD-10433 being assigned to Matt K yesterday.

Meanwhile the real work went ahead outside the ticket structure — `hporgpulse` onboarded in sandbox, row 24 built and validated, MR !1 open. So the tickets describe a world the work has already moved past.

The second problem is shape. Six tickets read as six unrelated essays. Strong on rationale, silent on the one thing a developer needs: what file do I create, what do I copy, how do I know I'm done.

## The organising frame

Everything below follows this. It's also the fix for the shape problem — each ticket now opens by saying where it sits.

```
1. Jira ──Fivetran(15min)──> jira_db.marts          someone else's product; we read
2. dbt in hporgpulse ──────> hporgpulse_db.marts    THE CALCULATION
3. Snowflake client ───────> metrics.json           THE PLUMBING
4. Rubric evaluator: value + thresholds -> tier     THE GRADING
5. Vue view: 33 rows on a page                      THE DISPLAY
```

| Ticket | Step | What it actually is |
|---|---|---|
| 10433 | 2↔3 | The data shape contract — **not** auth |
| 10509 | 3 | The Snowflake client. Was buried inside 10465 |
| 10435 | 4 | The grader |
| 10436 | 5 | The page |
| 10434 | meta | Where in the repo 3/4/5 live — **not** how it looks |
| 10437 | — | Side quest on moving JS helpers into core. Probably dead |
| 10465 | 2→5 | A vertical stripe through all of it, for one row |

Steps 3–5 are the Org Pulse module. Matt K's working order is **10433 → 10436 → 10435 → client**: write the contract, mock it, build the page and grader against the mock, swap in the real client when the service account lands.

## Three findings that drive the rewrites

**1. Every discovery question in 10433 is already answered.** There is no Dataverse API — direct Snowflake connection, SQL, RSA key-pair/JWT, private key in Vault provisioned and rotated by `dice`. `hporgpulse` is merged upstream as a consumer on `jira_db.marts` (`35961a4ff`, 2026-10-26). The spike still asks "REST or GraphQL?" because it was written on 10-08; you answered all of it on 10-16.

**2. The thin slice shipped a different row than its ticket says.** 10465 says row 6 (CVEs closed by due date). What landed is **row 24**, `pct_items_with_attached_cases` — 11,017 rows, 17/17 tests. Row 6 needs an `osidb` subscription we don't have.

**3. 10437's premise is largely void.** One named file is in `@org-pulse/core` (read-only symlink; changing it is a cross-repo release). The other, `modules/releases/server/hygiene/jira-fetch.js`, **doesn't exist in `hp-org-pulse` at all** — it's in the sibling `rhai-org-pulse` repo nobody has checked out. 720 lines, imported by six other files, full of RHOAI-specific field IDs.

## The ticket format change

Current tickets lead with rationale and end without a first step. New house shape:

```
**Outcome**     one sentence, observable
**Start here**  the literal first command, file to copy, or module to read
**Steps**       3-6 bullets, each a thing you do
**Done when**   short, checkable
**Context**     the why, links, prior decisions — last, not first
**Ask**         named people for the open bits
```

Plus: convert spikes to Tasks wherever the question is now answerable, name a path and something to copy in every ticket, and re-point sizes.

> **JIRA gotcha:** the Markdown→ADF converter mangles bare underscores, `+` and `~`. Every identifier in these descriptions is backticked for that reason. See [[reference_scrooge-jira-adf-quirks]].

---

# Per-ticket

## ENGPROD-10433 — the contract

**Spike → Task · Blocker → Major · 5 → 2 pts · keep Matt K**
**Retitle:** Document the hporgpulse → Org Pulse metrics contract

Not auth. Auth is a solved mechanism. What's left is the boring useful half: what columns a mart exposes and what `metrics.json` looks like after the refresh handler normalises it. Right now the only convention is the row 24 column set and it isn't written down anywhere.

Deliverable `docs/DATAVERSE-INTEGRATION.md`. Starting point: `models/marts/pct_items_with_attached_cases.sql` on branch `engprod-10465-thin-slice-sdlc-metrics`.

Settled, don't re-investigate: no API; RSA key-pair/JWT with the key in Vault under `ddis-asteroid-infra/rh<env>/snowflake/serviceaccounts/` rotated by `dice sync serviceaccounts --rotate-keys`; SQL; `snowflake-sdk` response; jira syncs every 15 min in prod and sandbox has no connector at all. And the calculation is **ours**, in our own aggregate product — the "Dataverse owns the calculations" framing is wrong.

Column convention from row 24: `metric_id`, `scope_type`, `scope_id`, `period_start`, `period_end`, `unit`, `numerator`, `denominator`, `metric_value`. (`metric_value` not `value` — `value` is a Snowflake reserved word.) Required of every family: `metric_id`, a scope, a period. One mart per metric family, not a monolith.

**The one genuinely open question:** trailing quarters. ~10 rows gate Surpasses on 3+ consecutive quarters. Source is day-grain (`phase_date`) so quarters are derivable by `date_trunc` — no snapshots needed, which is what row 24 does. But sandbox is a frozen snapshot whose tail quarters repeat their final state (2025 Q2 and Q3 show identical numerator/denominator), so the sustained check can't be validated there. Needs a written answer including what leadership sees meanwhile.

## ENGPROD-10434 — placement

**Spike → Task · Critical → Major · 3 → 1 pt**
**Retitle:** ADR: record where the SDLC Report Card lives in Org Pulse

Not visualization. It's which directory the code goes in, how it appears in nav, who can see it. Already decided de facto — everything downstream assumes `modules/sdlc-report-card/`. The ADR records why, because `AGENTS.md` constraint #4 points the other way.

Two things worth keeping:

- The honest contender for "a view in an existing module" is **`ai-impact`**, which already owns rubric-based scoring for RFEs, features and test plans. That deserves a written answer, not a hand-wave.
- **Option 3 in the ticket is described wrong.** `registerReport` is not a platform seam. It's a *team-tracker* client-side contribution slot, registered through `platform/<name>/team-tracker-contributions.js` and rendered in team-tracker's Reports hub. A 33-row leadership report doesn't belong there. One sentence to strike it, with the correct reason.

Naming heads-up: core already ships `modules/team-tracker/client/reports/ReportCard.vue`. Don't collide.

## ENGPROD-10435 — the grader

**No field changes. Needs an assignee.**

Keep as-is structurally — this is the best ticket on the board. Zero data dependency, zero access, plain JS with unit tests. Startable on a clean clone.

Additions worth making:

- **A fifth threshold shape the ticket misses:** rows 23 and 24, where Surpasses is a *stricter threshold* than Meets, not "Meets, sustained."
- **Known defects in the source rubric** — the thresholds don't always yield a deterministic tier. Row 30: Meets Some ceiling (2x) above the Does Not Meet floor (1.5x). Rows 16/17: Surpasses floor (90%) below the Meets ceiling (94%). Row 5: a gap between 94% and 95% nothing claims. Row 29: fixed upstream, our CSV is stale. **Rows 30 and 5 have never been filed anywhere.**
- The green/amber/red mapping is undecided and lands here.

## ENGPROD-10436 — the page

**No field changes. Needs an assignee.**

Make it concrete. `cp -r modules/cve-triage modules/sdlc-report-card` and strip back — smallest complete module in the repo, nine files, already has the fetch/cache/render shape.

Build against a **mocked** `metrics.json` shaped like the row 24 mart. That mock is the seam.

Two CI traps worth naming in the ticket:
- Anything calling `writeToStorage` **must** have an `export.files` block in `module.json`. `validate-modules.js` scans for the call and hard-fails without it.
- Every Express route needs `@openapi` JSDoc; `npm run validate:openapi` enforces a minimum count.

Also: `fixtures/sdlc-report-card/metrics.json` filename must match the storage key or demo mode renders empty. And the ticket says "the 12 Goal Groups" then lists 11.

## ENGPROD-10509 — the Snowflake client (step 3)

Story · Major · 5 · parent 10425. Carved out of 10465. Blocked by ENGPROD-10510.

Refresh handler that connects to Snowflake, queries `hporgpulse_db.marts`, normalises to `metrics.json` per the 10433 contract, serves from a GET endpoint. Replaces the mock.

Copy `modules/backport-tracker/server/index.js` for the `registerRefresh` pattern. Key read from Vault **at runtime** — `dice` rotates and a baked copy rots silently. Credential declared in `module.json` under `secrets`, read via `context.secrets` (constraint #9 forbids `process.env` and ESLint enforces it).

**Blocked** on the ticket below. No metric SQL in Org Pulse — select and shape only.

## ENGPROD-10510 — preprod promotion (the blocker)

Task · Critical · 3 · parent 10425. Blocks ENGPROD-10509.

This is the real blocker and it has had no owner since 2026-10-19. Service accounts can't exist in sandbox (SA-008/009 — the sandbox SA was created 2026-10-21 and removed the same day for exactly this). So nothing reads real data until `hporgpulse` is promoted to preprod.

- Promote sandbox → preprod. `preprod/` is an empty `.gitkeep`; `just promote hporgpulse sandbox preprod`. The checklist is 110 lines with nothing ticked.
- Create `dataverse_hporgpulsedashboard_preprod_appuser`. Cite `jira_shipshape_prod_appuser` and `openshift_ocpusagedashboard_prod_appuser`.
- **Verify egress to `gdadclc-rhpreprod.snowflakecomputing.com`.** Network policies are per-user and need their own migration.
- Dead end: `dataverse-consumer-jira-marts` is decommissioned.

Known risk, gates prod not preprod: a single service account flattens per-viewer RBAC into one role. Unresolved with Eric Rich.

## ENGPROD-10465 — re-point to row 24

Retitle to row 24. dbt half shipped (`d2100f2`, `4c43d41`, MR !1). Row 6 abandoned — needs `osidb`. Client half carved out, SA/egress half carved out.

**Caveat to add:** row 24 was computed off `SFDC_CASE_COUNTER`; Sarah's canonical definition uses "Number of Cases Linked" with a documented equation. These may not agree. Right now it proves the pipe, not the metric.

## ENGPROD-10437 — needs a call from the room

Don't rewrite until decided. With "no metric SQL in Org Pulse" and flow metrics now dbt models, **does anything still need these in JavaScript?**

If no, close it. If yes, reduce to `computeCycleTimeDays` only (12-line pure function, one `@shared` import) and drop to 1 point — but note it's still a PR to `red-hat-data-services/org-pulse-core` plus a release plus a version bump here.

The `jira-fetch.js` half should close regardless. It's in a repo nobody has checked out, it's a hub for six files, and only ~45 lines of it are promotable.

---

# Also worth filing

1. **Inventory `jira_db.marts`** — ~30 objects: grain, useful columns, which rows each could serve. No dbt, no new access, half a day. Makes every later dbt ticket writable with real column names instead of guesses. Best first task on the board, and a good fit for whoever is least comfortable with dbt.
2. **One query: does `JIRA_CUSTOMFIELDVALUE` carry Activity Type `customfield_10464`?** Decides whether row 22 is a week or a quarter away.
3. **Reconcile row 24** against Sarah's canonical equation.
4. **Fix `hporgpulse-dbt` README** (stock GitLab boilerplate pointing at `source-aligned/` when we're `aggregate/`) and the `profiles.yml` duplicate-key bug that silently kills the STAGING block.
5. **Fix `hp-org-pulse` docs drift** — `AGENTS.md`'s "Current modules" list is copied from rhai-org-pulse and wrong; README advertises `npm run update:view-owners` and `platform/view-owners/owners.js`, neither of which exists; the PR checklist references a `.github/CODEOWNERS` that doesn't exist (there's a root `OWNERS`). A newcomer following the docs hits all three.

# Epic 10425 touch-ups

- Reword the ingestion AC from push to pull.
- Close the "which HP Jira projects are in scope" question — Sarah answered it 2026-10-28: Project Category starts with `HP`, or is Hybrid Cloud Management.
- Add the "file your own story when you claim a row" template so it lives somewhere discoverable rather than only in meeting notes.

# Open questions for the room

- Fork or direct branch for `hporgpulse-dbt`? Whatever we pick, everyone does the same — MR-from-fork and MR-from-branch behave differently in CI.
- Who takes 10435 and 10436? Both unblocked today.
- Who owns the preprod promotion / egress verification?
- Who follows up with John Kyros on Cyborg → Snowflake federation? Team attribution, Epic F history and Epic G scope all depend on it.
- 10437: does anything still need those helpers in JS?
- RBAC governance with Eric Rich — a risk to the plan, not an implementation detail.

> Small correction to carry: `skyros` is **Sarah**, `jkyros` is **John**. [[org-pulse-sdlc-report-card]] miscredits one, and both are on the group, so it matters for who gets pinged.

---

# Applied to JIRA — 2026-10-30 morning

Done before refinement, so the team reads the new versions.

| Ticket | Change |
|---|---|
| ENGPROD-10433 | Retitled "Document the hporgpulse to Org Pulse metrics contract". Priority Blocker → Major, 5 → 2 pts. Description rewritten: settled items listed as do-not-re-investigate, trailing-quarters as the one open question. Still Matt K. |
| ENGPROD-10434 | Retitled "ADR: record where the SDLC Report Card lives in Org Pulse". Critical → Major, 3 → 1 pt. Option 3 corrected — `registerReport` is a team-tracker contribution slot, not a platform seam. `ai-impact` named as the real contender for option 2. |
| ENGPROD-10435 | Description rewritten. Added the fifth threshold shape (rows 23/24), the four known rubric defects, the green/amber/red mapping, and the module-creation command. Fields unchanged. |
| ENGPROD-10436 | Description rewritten. Added the file list, `cp -r modules/cve-triage`, the two CI traps, and the Goal Group count correction. Fields unchanged. |
| **ENGPROD-10509** | **Created.** Story, Major, 5. The Snowflake client and refresh handler. Blocked by 10510, related to 10465. |
| **ENGPROD-10510** | **Created.** Task, Critical, 3. Preprod promotion, dashboard service account, egress verification. Blocks 10509. |
| ENGPROD-10465 | Retitled to row 24. Comment added: dbt half shipped, Org Pulse half carved into 10509/10510, plus the `SFDC_CASE_COUNTER` reconciliation caveat. |
| ENGPROD-10437 | Comment added raising it for a decision. Not rewritten — needs a call on whether anything still needs those helpers in JS. |
| ENGPROD-10425 | Description rewritten around the five-step pipeline, with the children listed by step, the measurement-scope question closed, and the per-row filing convention added. |

Still unassigned: 10434, 10435, 10436, 10509, 10510. Matt K holds 10433.

## JIRA formatting findings

Two real quirks, both worked around:

1. **Bold inside a bullet list item loses its closing asterisk.** `- **Label:** text` stores as `- **Label:* text`. The last bold span in a list item is the one that breaks. Fix: no bold inside bullets. Bold in ordinary paragraphs is fine.
2. **Backticks do protect underscores**, including doubled ones. `` `stg_jira__pqi_bugs` `` and `` `pct_items_with_attached_cases` `` both stored intact in a comment. The 2026-10-20 comment on 10465 said the comment formatter mangles underscores in identifiers — that is true for *bare* identifiers, not backticked ones. Worth knowing, because that note has been causing us to write hyphens where we mean underscores.

Also: bare tokens shaped like issue keys get auto-linked. `SA-008` became a link to a nonexistent JIRA issue until backticked.

---

## The handout set — 2026-10-30, second pass

Goal: four tickets to put in front of named people at the session. Two from the
refined Org Pulse board, two on the metric side, with the metrics chosen off
whatever Sarah Kyros's comments flagged as low-hanging.

### What Sarah's comments actually say

Read her 2026-10-28 answers across all eight epics. They mostly close doors
rather than open them:

| Row(s) | Her answer |
|---|---|
| 22 Reactive Work % | Activity Type `customfield_10464` is the field. Not in Snowflake. |
| 23 Regression % | The Regression yes/no Jira field. Not in Snowflake. |
| 24 Attached Cases | SFDC plugin's "Number of Cases Linked". Not in Snowflake. |
| 16/17 Rank alignment | Scores don't exist yet — being set up in the ValorFlow data product. |
| 11–13 Org context | History comes once Cyborg is federated into Snowflake. |
| 29 WIP ratio | Threshold defect confirmed and already fixed upstream. |

So the three metrics everyone assumed were easiest are the three she rules out.

### The finding that changed the second ticket

Didn't take "not in Snowflake" at face value, because row 24 had already been
computed off `sfdc_case_counter`. Went into `dataproduct-config`:

- `dataproducts/source/jira/prod/fivetran/fivetranconnector.yaml` — the jira
  source product's prod connector replicates the Jira Postgres database
  *directly*. `aurora_postgres`, WAL replication via `update_method:
  WAL_PGOUTPUT`, `sync_frequency: 15`.
- Enabled on it: `customfield`, `customfieldoption`, `customfieldvalue`, and
  `AO_9D8F2F_SFDC_CASE` — the Salesforce plugin's Active Objects table.
- `schema_change_handling: ALLOW_COLUMNS`, so new columns arrive on their own.
- `prod/product.yaml` exposes `presentation_schemas` only: `marts`,
  `rhai_marts`, others. Consumers bind to those. The replicated tables aren't
  reachable from our subscription.
- `hporgpulse` is not in the prod consumer list for `jira_db.marts`. Sandbox
  only, from MR !18648.

**Sarah's answer is accurate about the marts and wrong about the pipeline.** The
values are landing every fifteen minutes; they're stuck at the last mile.

Owners, from `dataproducts/source/jira/groups/`:
- `tdeanton` — product owner *and* business owner
- `hgirish` — maintainer

### The four

| # | Ticket | Why it's handable today |
|---|---|---|
| 1 | ENGPROD-10435 — rubric evaluator | Pure JS, clean clone, no Snowflake, no SA, no data |
| 2 | ENGPROD-10436 — 33-row view scaffold | Copy `cve-triage`, build against a mocked fixture |
| 3 | **ENGPROD-10512** — Row 23 Regression Percentage dbt model | Straight copy of the shipped row 24 model |
| 4 | **ENGPROD-10511** — surface the custom fields in `jira_db.marts` | Named owners, concrete ask |

ENGPROD-10510 still needs an owner. Different shape of ask — a volunteer for
infra work, not a dev handout.

### A discarded draft worth remembering

My first version of ticket 4 was "inventory `jira_db.marts` and map the 33 rows
onto it." Matt pushed back and suggested reaching out to, or contributing to,
the jira mart instead. He was right: the inventory was a survey that produces a
document, and the contribution is an action that produces a field. The digging
I'd have done *for* the inventory is what found the Fivetran connector — which
then became the evidence that made the contribution ticket writable.

Worth generalising: when a ticket's deliverable is "we will know more", check
whether the thing you'd learn is already knowable in an afternoon, and make the
ticket the action instead.

### Applied to JIRA

| Change | Detail |
|---|---|
| **ENGPROD-10511** created | Task, Critical, 3 pts, parent ENGPROD-10427 |
| **ENGPROD-10512** created | Story, Major, 3 pts, parent ENGPROD-10427 |
| Links | 10512 relates to 10511; 10512 relates to 10465 |
| Comment on ENGPROD-10427 | Sarah's three field answers, the Fivetran finding, and the standing proxy caveat |

Linked 10511 and 10512 as **related, not blocking** — a deliberate change from
the plan. 10512 ships the proxy now and 10511 retires the caveat later;
blocking would have stopped someone starting the one thing that can start.

All three writes verified by re-fetch. `stg_jira__pqi_bugs`,
`AO_9D8F2F_SFDC_CASE` and `sfdc_case_counter` all survived intact, which
re-confirms the narrowed ADF rule: backticks protect a lone internal `__`, only
a matched `__…__` pair breaks.

### Carry into the session

- Rows 22, 23 and 24 are all proxies or nothing until 10511 lands. Say so out
  loud before anyone screenshots a number.
- Row 22 has no proxy at all. It's the row that gains most from 10511.
- Ask whether `sfdc_case_counter` in the PQI mart is already derived from
  `AO_9D8F2F_SFDC_CASE`. If it is, the canonical field may be a very short hop
  and 10511 gets much cheaper.

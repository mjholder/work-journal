---
type: meeting-notes
date: 2026-10-29
tags:
  - org-pulse
  - sdlc-report-card
  - dataverse
  - dbt
  - snowflake
  - onboarding
---
# SDLC Report Card — Team Spin-Up

Notes to run the spin-up meeting from. Goal is to get everyone to the point where they can claim a metric and start, not to answer every open question.

> **This is the working copy — my framing, my asides, the full rubric appendix.** The shareable version to paste into the meeting doc is [[SDLC Report Card Spin-Up — Agenda (shareable)]]. Keep edits in sync, or decide one is canonical.

Related: [[org-pulse-sdlc-report-card]] · [[dataverse-dataproduct-config]] · [[rhai-org-pulse]]

---

## The 30-second version

Leadership gave us a report card: **33 measurements**, each scored against the same four tiers — Does Not Meet Expectations / Meets Some / Meets / Surpasses.

We compute those metrics as **dbt models in our own Dataverse aggregate product**, `hporgpulse`, materialised into `hporgpulse_db.marts` on Snowflake. **Org Pulse queries Snowflake, applies the rubric, renders.** Org Pulse owns no database and calculates nothing.

Row 24 (% Items with Attached Cases) went end-to-end on 2026-10-29. The pipe is proven. Everything after this is repetition — which is why it splits across the team.

---

## Where this came from

The architecture turned over three times in three weeks. If you read older notes you'll hit all three, so here's the order:

1. **2026-10-08** — structure filed. 8 epics, 20 issues, assumption that Org Pulse collects and calculates.
2. **2026-10-14** — meeting with Eric Rich. "Dataverse owns the calculations, Org Pulse is a visualisation layer."
3. **2026-10-16** — read the config repo. There *is no Dataverse API*, and "Dataverse owns the calculations" actually means *they run on Dataverse infra; whoever owns the aggregate product writes the dbt*.
4. **2026-10-20** — so we own an aggregate product. `hporgpulse` onboarded (MR !18648, merged 2026-10-26, sandbox).
5. **2026-10-28/29** — dbt repo created, first real metric built and validated.

**Only #4 and #5 are current.** Anything that says Org Pulse computes metrics is stale.

---

## How it works now

```
jira_db.marts  (source product, owned by the jira team — we read, never write)
      ↓   dbt
hporgpulse_db.staging   stg_* views, pass-through + casts
      ↓   dbt
hporgpulse_db.marts     one table per metric family — the calculation
      ↓   Snowflake query (snowflake-sdk, key-pair JWT)
Org Pulse  modules/sdlc-report-card/
      → refresh handler → metrics.json → rubric evaluator → rendered row
```

Two decisions already made, so nobody re-opens them:

- **One mart per metric family, not one monolithic `sdlc_metrics` table.** The 33 metrics have genuinely different shapes — ratios, posture booleans, cycle-time distributions, compound checks. Forcing them into one schema is a fight we don't need. The stable contract is the **metrics.json shape**, and normalisation happens in the Org Pulse refresh handler.
- **No metric SQL in Org Pulse.** If you find yourself computing something in JavaScript, it belongs in dbt.

---

## Two workstreams

| | Workstream | Repo | Shape |
|---|---|---|---|
| **A** | The 33 metrics | `hporgpulse-dbt` | Parallel. One row or family per person. |
| **B** | Snowflake → Org Pulse | `hp-org-pulse` | Mostly sequential, one or two people. |

---

# Part A — The 33 metrics

## Access you should already have

All nine of us were added to `developers.yaml` and all four rover group files on 2026-10-21, so this should already be true. Check it live:

- **Rover group** — `dataverse-aggregate-hporgpulse` at rover.redhat.com. *(My 10-27 note spells this `hporgulse`, missing a `p`. The config repo says `hporgpulse`. If rover disagrees with the config, flag it — a typo'd group name fails silently.)*
- **GitLab** — `gitlab.cee.redhat.com/dataverse/data-products/aggregate/hporgpulse/hporgpulse-dbt`. The group also grants `dataverse/dataverse-config/dataproduct-config` and `dataverse/astro/astro-toolkit`.
- **Snowflake** — the group gives you *user-warehouse* access to the sandbox account under role `hporgpulse_group`. No service account needed; sandbox reads go through you.

If any of these is missing, that's a rover membership problem, not a Dataverse problem.

## Local setup

**There is no local Dataverse stack.** Nothing to run in Docker. "Local" means the dbt CLI on your laptop talking to the real sandbox Snowflake account over browser SSO.

```bash
git clone git@gitlab.cee.redhat.com:dataverse/data-products/aggregate/hporgpulse/hporgpulse-dbt.git
cd hporgpulse-dbt
# check whether you can push a branch directly — see the fork note below
python3 -m venv .venv && source .venv/bin/activate
pip install dbt-snowflake sqlfluff sqlfluff-templater-dbt
export SNOWFLAKE_USER=<your-kerberos-uid>
dbt deps
dbt debug --target sandbox   # a browser window pops for SSO
dbt run   --target sandbox
```

The sandbox target (from `profiles.yml`, already committed):

| | |
|---|---|
| account | `hnb22701` |
| authenticator | `externalbrowser` |
| role | `hporgpulse_group` |
| warehouse | `hporgpulse_group_xs_wh` |
| database | `hporgpulse_db` |
| schema | `marts` |

*(`hnb22701` is the legacy **account locator**. The same account's org-qualified name is `gdadclc-rhsandbox` — org `gdadclc`, account `rhsandbox`. dbt accepts either form, which is why two names float around. `select current_account();` returns the locator if you ever need to tie them together.)*

## Environments, and browsing the data in a browser

**Environments are separate Snowflake accounts — not a column, a schema, or a database prefix.** There is nothing to filter by. The database and schema names are *identical* in every environment:

| | sandbox | dev | preprod | prod |
|---|---|---|---|---|
| account | `hnb22701` / `gdadclc-rhsandbox` | `gdadclc-rhdev` | `gdadclc-rhpreprod` | `gdadclc-rhprod` |
| auth | `externalbrowser` (you, via SSO) | key-pair JWT | key-pair JWT | key-pair JWT |
| role | `hporgpulse_group` | `$SNOWFLAKE_DBT_ROLE` | ← | ← |
| warehouse | `hporgpulse_group_xs_wh` (user) | `hporgpulse_service_xs_wh` (service) | ← | ← |
| database | `hporgpulse_db` | `hporgpulse_db` | `hporgpulse_db` | `hporgpulse_db` |

So `dbt --target sandbox` isn't setting a filter — it's choosing which host to connect to and as whom. Same for the Org Pulse module later: switching environment is pure connection config, never a query parameter.

**Snowsight (the web UI)** follows the same shape — `app.snowflake.com/<org>/<account>/`:

```
https://app.snowflake.com/gdadclc/rhsandbox/      ← where we work
https://app.snowflake.com/gdadclc/rhdev/
https://app.snowflake.com/gdadclc/rhpreprod/
https://app.snowflake.com/gdadclc/rhprod/
```

Swap the account segment to change environment. There's no env selector inside a session.

> ⚠️ **Because the names are identical everywhere, a query result cannot tell you which environment produced it.** Before trusting or sharing a number:
> ```sql
> select current_account(), current_role(), current_warehouse(), current_database();
> ```
> Worth making a habit.

**Don't confuse this with the Ludo console** — that's the Dataverse catalogue, and it carries its own `?environment=rhsandbox` parameter (the ValorFlow link Sarah sent is an example). Different system, different env switch.

**This also explains the red CI.** `dataproducts/aggregate/hporgpulse/` has content only in `sandbox/`; `dev/`, `preprod/` and `prod/` contain nothing but `.gitkeep`. The product genuinely does not exist in dev, so `.credential_config_dev` has no credentials to fetch. `secrets_provider_not_found` isn't a CI bug — it's the environment model being honest. Same reason mart subscriptions are per-environment: they're separate accounts with separate grants.

**Two repo gotchas to settle in the meeting:**

- **Fork or direct branch?** My working copy is a **personal fork** — `origin` is `maholder/hporgpulse-dbt`, `upstream` is the canonical `dataverse/data-products/aggregate/hporgpulse/hporgpulse-dbt`. I don't know whether that was necessary or just habit. Someone should try pushing a branch straight to the canonical repo; if it's rejected, everyone forks and we add `upstream` as above. Either way **we all do the same thing**, because MR-from-fork and MR-from-branch behave differently in CI.
- **The committed `README.md` is untouched GitLab template boilerplate**, and the clone URL inside it points at `data-products/source-aligned/...`. That path is wrong — we're an **aggregate** product. Ignore the README; it's the next thing worth replacing once the workflow settles.

## Looking around Snowflake

**This is most of the job.** For any given row, the work is less "write clever SQL" and more **"find out which marts and columns can actually support this metric, then write the calculation."**

What's there:

- **`hporgpulse_db`** — ours. Schemas `staging` and `marts`. Also still holds an orphaned `sdlc_metrics` table from an earlier iteration; ignore it.
- **`jira_db.marts`** — what we read. Repopulated 2026-10-28, now ~30 objects including `JIRA_ISSUE`, `JIRA_PROJECT`, `JIRA_SPRINT`, `JIRA_CUSTOMFIELDVALUE`, `JIRA_SFDC_CASE`, `JIRA_NODEASSOCIATION`, plus `PQI_BUGS_DASHBOARDS_JIRA_TABLE` (116M rows, day-grain defect lifecycle, 39 columns).

Introspect it directly rather than guessing:

```sql
use role hporgpulse_group;
use warehouse hporgpulse_group_xs_wh;

show tables in jira_db.marts;
show views  in jira_db.marts;
describe view jira_db.marts.jira_issue;

select * from jira_db.marts.jira_issue limit 20;
```

Until 10-28 the sandbox was too empty to introspect and we were asking other teams for schema knowledge. That's over — **answer schema questions by querying sandbox yourself.**

## Subscribing to marts we don't have yet

**Today `hporgpulse` can read exactly one thing: `jira_db.marts`, in sandbox.** That's it. Not `jira_db.cloud_marts`, not any other product, not any other environment. If your row needs data from somewhere else, getting access is a step in your work, not a given.

It's a **`dataproduct-config` MR — and it goes on the *producer's* file, not ours.** You add `hporgpulse` to the consumers list under the source product's presentation schema. From `dataproducts/source/jira/sandbox/product.yaml`:

```yaml
data_product_db:
- database: jira_db
  presentation_schemas:
  - name: marts
    consumers:
    - name: dataverse-consumer-jira-marts
      kind: consumer_group        # decommissioned — don't use this route
    - name: engmetrics
      kind: data_product
    - name: hporgpulse            # ← this is us
      kind: data_product
```

Four things that catch people:

- **Per schema.** Being on `marts` gives you nothing on `cloud_marts` — that's a separate entry in the same file.
- **Per environment.** `sandbox/product.yaml`, `dev/`, `preprod/` and `prod/` are separate files. Preprod access is a separate MR at promotion time.
- **Some schemas don't use a consumers list at all** — `rhai_marts` and `cloudrhai_marts` carry `access_policy: rh_internal` instead. Different model, different ask.
- **`kind` matters.** `data_product` for us reading as hporgpulse; `service_account` for the Org Pulse dashboard SA later; `consumer_group` is the legacy route and `dataverse-consumer-jira-marts` specifically is decommissioned.

**Budget time for it.** The MR onboarding hporgpulse took about a week of chasing reviewers. Raise the subscription early rather than when you're ready to write SQL.

### What exists to subscribe to

Relevant source products that are live somewhere in the repo:

| Need | Product | Note |
|---|---|---|
| Epic C — repos | `github`, `gitlab`, `gitlabsaas` | github has the full PR/review/workflow surface; gitlab ones are much thinner |
| Epic D — containers | `brew`, `errata`, `pyxis` | **no Konflux and no Quay product exists anywhere** |
| Epic E — ProdSec | `osidb`, `prodsecrisks` | both **sandbox only** — which is where we develop, so this may be easier than it looks |
| Epic G — rank alignment | `valorflowcontext` | this is where Sarah says the alignment scores are being built |
| People / teams | `roverpeople`, `ldap` | |

Also worth knowing: `engmetrics` and `healthindex` are *aggregate* products doing adjacent work. `healthindex` is a working "report card" precedent.

## The worked example — row 24, start to finish

Branch `engprod-10465-thin-slice-sdlc-metrics` in `hporgpulse-dbt`. Four files. Read them before you write your own.

**1. `models/source.yml`** — declare the upstream source. Read-only, always.

```yaml
sources:
  - name: jira
    database: jira_db
    schema: marts
    tables:
      - name: pqi_bugs_dashboards_jira_table
        description: >
          Day-grain defect lifecycle data...
```

**2. `models/staging/stg_jira__pqi_bugs.sql`** — a **view**. Pass-through columns and casts only, no logic. Naming: `stg_<source>__<thing>`.

**3. `models/marts/pct_items_with_attached_cases.sql`** — a **table**. This is the actual calculation. Named for the metric, *not* `sdlc_metrics`.

**4. `models/staging/schema.yml` and `models/marts/schema.yml`** — a description on every column, plus data tests. Row 24 ships 17 of them: grain uniqueness via `dbt_utils.unique_combination_of_columns`, `not_null` on everything that matters, `accepted_values` on the enum-ish columns. **Don't skip these** — they're what caught the grain being right on a 116M-row table.

Then:

```bash
dbt run  --target sandbox
dbt test --target sandbox
sqlfluff lint models/marts/<your_model>.sql
git checkout -b engprod-NNNNN-short-slug
# commit, push, open MR
```

**Sanity-check the output before you open the MR.** Row 24 came out RHEL ~10–15%, OpenShift Request Tracker ~57% — the second is a case-driven queue, so a high number is what you'd expect. If the numbers don't have a story, the SQL is wrong.

## The mart output shape

**Marts do not all share one table schema.** That's the whole point of the per-family decision above — a cycle-time distribution, a posture boolean and a compound check have genuinely different natural shapes, and forcing them into one set of columns is the monolith we rejected. **Give your metric the grain and columns it actually needs.**

What's shared is the **`metrics.json` contract** that Org Pulse consumes, and that normalisation happens in the module's refresh handler, not in the warehouse.

Row 24's column set is the only worked example we have. Because it's a plain quarterly ratio, its mart happens to look very close to the target JSON:

| column | meaning |
|---|---|
| `metric_id` | stable slug, matches the model name |
| `scope_type` | what it's computed for — `project` today |
| `scope_id` | the project/team identifier |
| `period_start` | first day of the period (quarter grain) |
| `period_end` | last day of the period |
| `unit` | what the numerator/denominator count, e.g. `bugs` |
| `numerator` | |
| `denominator` | carried so the rubric evaluator never re-derives inputs |
| `metric_value` | `numerator / denominator` |

Treat that as **a good default for ratio metrics**, not a rule for all 33. If yours is a ratio, copying it means the refresh handler needs no special case. If yours isn't, don't contort it.

The part worth keeping common regardless is the **identifying columns** — `metric_id`, a scope, and a period. Those are what let the normaliser stay generic instead of growing a branch per metric.

Two details from row 24: it's `metric_value` and not `value` because **`value` is a Snowflake keyword** — it maps to `"value"` in the JSON. And `scope_type` is `project` for now because the source mart has no team dimension; the real team altitude is pending ENGPROD-10438.

> **Caveat worth saying in the meeting:** the `metrics.json` contract **is not actually written down anywhere yet.** It's the named deliverable of ENGPROD-10433 (`docs/DATAVERSE-INTEGRATION.md`) and that spike hasn't been done. Until it is, row 24 plus the identifying columns above is all the convention we have — so the second and third metrics are as likely to *shape* the contract as to follow it. Whoever builds them should expect to feed changes back.

## Gotchas — say these out loud

- **Sandbox is not a complete environment. Results will vary.** Only prod has a live Fivetran connector; dev and preprod connectors exist but are `paused: true`. Sandbox Jira data is a static snapshot, and the tail quarters repeat their final state (2025 Q2 and Q3 show identical numerator/denominator). **Numbers you compute in sandbox prove the calculation, not the reality.** Nobody reports off them.
- **MR CI is red for everyone right now.** Both jobs die with `secrets_provider_not_found` — the `.credential_config_dev` include can't provision dev credentials for a sandbox-only product. It's a product-level fix, pending in `#help-dataverse-data-products`. **Open MRs anyway**; the pipeline isn't the gate yet.
- `.sqlfluff` is configured against `target = dev` (CI creds). To lint locally, temporarily swap it to `sandbox`.
- MR pipelines don't show up under the branch ref in the GitLab API — read the MR's `head_pipeline` instead.
- **Astro scheduling is deferred.** There is currently no documented path from a merged model to a scheduled run in preprod or prod. We have `astro-toolkit` access via the rover group; nobody has used it.

---

# Part A — Claiming work

## The map

Grouped **by data source / collector**, not by leadership's 12 Goal Groups — a group boundary should match the boundary of a conversation, so an epic can slip as a unit.

**📌 = Sarah Kyros has commented with a data lead. Read it before you start.**

| Epic | Rows | Covers | Ticket | |
|---|---|---|---|---|
| **0 — Foundations** | — | Ingestion contract, rubric evaluator, view scaffold, core helpers | ENGPROD-10425 | |
| **A — Jira Flow & Sustainable Pace** | 18–21, 25–33 (13) | Cycle Time, Throughput, WIP Ratio, Net Delivery Flow — ×4 altitudes | ENGPROD-10426 | 📌 ×2 |
| **B — Jira Work Mix & Quality** | 22, 23, 24 (3) | Reactive Work %, Regression %, % Items with Attached Cases | ENGPROD-10427 | 📌 ×2 |
| **C — Repository Posture** | 7, 8, 9, 10, 14, 15 (6) | PR Review, Regression/Revert, Dependencies, AGENTS.md, Quality Bots, Test Maturity | ENGPROD-10428 | |
| **D — Container & Build Posture** | 1–4 (4) | Image, Build, Scanning, Release | ENGPROD-10429 | 📌 |
| **E — Security & CVE** | 5, 6 (2) | ProdSec SLA Success Rate, % CVEs Closed by Due Date | ENGPROD-10430 | 📌 |
| **F — Org Context Coverage** | 11, 12, 13 (3) | Registration Coverage, Accessibility, Quality | ENGPROD-10431 | 📌 |
| **G — Rank Alignment** | 16, 17 (2) | Plan View score, Scrum/Kanban Board score | ENGPROD-10432 | 📌 |

**None of the 13 child spikes and stories has a single comment.** All the useful external input is sitting on the epics — so whoever picks up a child ticket should read its parent's comments first.

Full row-by-row index is in [[org-pulse-sdlc-report-card]]; verbatim thresholds are in the appendix below.

## What Sarah Kyros has already told us

Six of eight epics, almost all on 2026-10-28, and they are the best data leads we have. Summarised here, but **read the originals** — they carry links to spreadsheets and docs I can't reproduce.

### The anchor comment — [ENGPROD-10427](https://redhat.atlassian.net/browse/ENGPROD-10427?focusedCommentId=19163850)

Three other epics (A, D, G) point back at this one for scope. It answers the question that's been open since the September level-set:

- **Which HP Jira projects are in scope:** any project whose **Project Category starts with `HP`**, or whose category is **Hybrid Cloud Management**. Categories need a clean-up at some point, but that query gets the full list today.
- **Which teams work rolls up to:** should come out of **Cyborg** — teams register a project, or a project + component combination. **Brad Tweardy** has working attribution code at [`sage/eazybi-generators`](https://gitlab.cee.redhat.com/sage/eazybi-generators) that does exactly this for eazyBI; usable as a reference.
- **Longer term** that calculation moves into Snowflake. Brad has inventoried the calculated fields needed — we specifically need **Delivery Team, Group, Pillar and Area**. **John Kyros** is working out what it takes to **federate Cyborg data into Snowflake**.

👉 This largely closes the "undefined denominator" problem I'd been carrying as a leadership-input gap. It's now an engineering question with a named approach and a reference implementation.

### Field-level answers for Epic B — [ENGPROD-10427](https://redhat.atlassian.net/browse/ENGPROD-10427?focusedCommentId=19166783)

Each of the three rows has a named source field and a **documented equation** in Brad's analysis spreadsheet (linked on the comment). All three carry the same warning: ***not in Snowflake yet.***

| Row | Source field | Status |
|---|---|---|
| 22 Reactive Work % | Activity Type `customfield_10464` — confirms our guess | not in Snowflake |
| 23 Regression % | the Regression (yes/no) Jira field | not in Snowflake |
| 24 % Items with Attached Cases | a SalesForce plugin generating **"Number of Cases Linked"** | not in Snowflake |

> ⚠️ **This affects the metric we already built.** We computed row 24 off `SFDC_CASE_COUNTER` in the PQI table. Sarah's canonical definition uses the "Number of Cases Linked" field with a documented equation. Those may or may not agree. **Reconcile our number against her equation before anyone treats row 24 as correct** — right now it proves the pipe, not the metric.

### Epic A — [ENGPROD-10426](https://redhat.atlassian.net/browse/ENGPROD-10426)

**Row 29's overlapping bands are confirmed and already fixed in the source.** Sarah: *"Yes, the 'Does Not Meet' upper condition was intended to read 'above 7.6x' and it's been fixed now."* Our CSV copy is stale — re-pull it. Scope answer points at the anchor comment.

### Epic D — [ENGPROD-10429](https://redhat.atlassian.net/browse/ENGPROD-10429)

Scope answer points at the anchor comment. **Nothing yet on the actual container data sources** — Konflux/Quay/Pyxis is still the open question, and still the highest-risk part of the program.

### Epic E — [ENGPROD-10430](https://redhat.atlassian.net/browse/ENGPROD-10430)

ProdSec's data is in **OSIDB**; they host [their own dashboard](https://csv-to-pages-product-security-94b4a3433ef0d84ad975c2c7f77b135ac.pages.redhat.com/). Contacts: **Marek Baluch** or **Jeremy West** — Marek is who Sarah worked with in mid-2025 to align ProdSec data with Jira. She's explicit she doesn't know exactly where the data lives, so expect one hop.

### Epic F — [ENGPROD-10431](https://redhat.atlassian.net/browse/ENGPROD-10431)

Answering my "posture history has nowhere to live" note directly: *"We would expect the history to be calculated via dbt and available in Snowflake once the Cyborg data is federated into Snowflake."*

👉 **That dissolves the nine-month clock for Epic F** — if Cyborg lands in Snowflake with history, rows 11–13 are backfillable like the Jira rows. It does **not** help Epics C and D, where nothing is recording posture today. Worth splitting that argument when we take it to leadership.

### Epic G — [ENGPROD-10432](https://redhat.atlassian.net/browse/ENGPROD-10432)

Scope is **both** Plan Views registered in Cyborg / the org repo **and** Jira projects/items. And the lead we didn't have: **the alignment scores are being built in the [ValorFlow data product](https://ludo-ddis-asteroid--ludo.apps.int.spoke.prod.us-east-1.aws.paas.redhat.com/data-product/valorflowcontext?environment=rhsandbox)**, in `rhsandbox` — the same environment we develop in.

👉 So Epic G is not "undefined algorithm, nothing to do." It's "subscribe to someone else's product once their score lands." Pair this with VALORFLOW-28 below.

### What this changes

Three things I had listed as blocked or open are now sourced:

1. **Scope** — answered, with a concrete query and a reference implementation.
2. **Epic G** — has a data source in the environment we already work in.
3. **Epic F history** — has a stated plan.

And one thing got *less* certain: **row 24's definition**, which we've already implemented against a different field.

The common thread is **Cyborg → Snowflake federation** (John Kyros). Team attribution, Epic F history, and Epic G scope all depend on it. That's probably the single highest-leverage dependency on the board, and nobody on our side is tracking it.

## Why there are no per-metric tickets

**Deliberate.** 32 of the 33 rows have no story, because a story's shape depends on which marts turn out to support it — and we only learned what's in `jira_db.marts` last week. A ticket encoding a guess is worse than no ticket.

So: **file your own story when you claim a row.**

## Story template

- **Title:** `Row NN — <Measurement Attribute> dbt model`
- **Parent:** the row's epic from the table above
- **Type:** Story (Spike if the answer is "find out whether this is even sourceable")
- **Labels:** `ai-generated-jira`, `hcm-engineering-productivity`, `org-pulse`, `sdlc-report-card`, plus the row's `goal-<group>` label *(note: `team-context-vault/docs/processes/jira.md` says `ai-generated`, but every sibling ticket uses `ai-generated-jira` — match the siblings)*
- **Components:** `Org-Pulse AI Dashboard` + `Metrics`
- **Activity Type:** `Product / Portfolio Work`
- **Acceptance criteria**, modelled on row 24:
  - mart carries the identifying columns (`metric_id`, scope, period); shape beyond that is whatever the metric needs
  - data tests pass, including a grain uniqueness test
  - sqlfluff clean
  - output sanity-checked against expectation and the reasoning written in the MR
  - MR open against `hporgpulse-dbt`

Assign yourself, link the branch on the ticket.

## Easy wins — the first tickets to hand out

Ranked by how little stands between someone and a merged MR. **Everything here lives inside the one subscription we already have** (`jira_db.marts`, sandbox) — nothing below needs a new `dataproduct-config` MR first.

### Tier 0 — no dbt required, and they unblock everyone else

- **Inventory `jira_db.marts`.** All ~30 objects: what each is, its grain, its useful columns, and which report card rows it could serve. **Nobody has done this.** It's the "find which marts support this row" work done once instead of nine times, it needs no dbt and no SQL beyond `describe`, and it's probably the highest-value half-day on the board right now. Good fit for whoever is least comfortable with dbt.
- **Check whether `JIRA_CUSTOMFIELDVALUE` carries Activity Type `customfield_10464`.** One query. Sarah says the field is "not in Snowflake yet", but that view exists and she may mean the derived equation rather than the raw field. The answer decides whether row 22 is a week away or a quarter away.

### Tier 1 — the easiest real metric: row 23, Regression %

Same source table as row 24 (`PQI_BUGS_DASHBOARDS_JIRA_TABLE`), same ratio shape, same project × quarter grain. The table carries `DEFECT_REGRESSION_DAY_FLAG` directly, and **the SQL already exists in git history at `d2100f2`** from the first thin-slice attempt. Close to a copy-adapt-test exercise.

*(I'd previously filed row 23 under "needs source work first" — promoting it. The definition question is real but it's a conversation, not a build blocker.)*

The caveat belongs in the ticket: Sarah's canonical source is the **Regression (yes/no) Jira field**, not the PQI flag. So it ships as a proxy with a documented reconciliation question — the same position row 24 is in. Reason to flag it, not to avoid it.

### Tier 2 — straightforward off `JIRA_ISSUE`

- **Row 33, Net Delivery Flow Ratio.** Issues completed in a period over issues created in it. Altitude is `All Jira Work`, so **it needs no altitude mapping** — the cheapest flow metric to get a value for. Only its Surpasses tier is blocked, being compound and dependent on Epic A's WIP ratio.
- **Rows 25–28, Throughput.** A count per period per issue type — simplest of the flow family, and easier than cycle time because it needs no transition timestamps. Gated on the altitude mapping ([ENGPROD-10438](https://redhat.atlassian.net/browse/ENGPROD-10438)) for all four, but **one altitude can ship first** and the rest are repetition.

### Looks easy, isn't

- **Rows 18–21, Cycle Time** — needs transition history, not just issue rows. Meaningfully harder than throughput; adjacent on the sheet is not adjacent in effort.
- **Rows 29–32, WIP vs Throughput** — definitionally depends on throughput landing first.
- **Row 6, CVEs by due date** — PQI has no due-date or CVE field. Needs an `osidb` subscription, which is sandbox-only — so a good *second-wave* item rather than a dead one.
- **Anything in Epics C, D, F, G** — each needs a new subscription or an upstream capability that doesn't exist yet.

> **Confidence note.** This ranking is inferred from object names and the one table we've actually used — not from column-level inspection of all 30 objects. Which is exactly why Tier 0 is Tier 0. Expect the order to shift once someone does the inventory.

**Not dbt work yet — these are conversations**
- **Epic C** — no `github_db` access, and row 15 (test maturity) has no source anywhere.
- **Epic D** — `brew`/`errata`/`pyxis` are prod-only; no Konflux or Quay data product exists at all. Highest risk item in the program.
- **Epic F** — leadership marked rows 11–13 "Coming Soon"; the upstream capability (PLATENG-106, OCPCRT) doesn't exist.
- **Epic G** — the Rank Alignment Score algorithm has never been defined.

---

# Part B — Snowflake → Org Pulse

None of the read path exists yet. Three pieces, in order:

**1. Rubric evaluator — ENGPROD-10435.** Four tiers plus the sustained-quarters checker. Roughly **10 of the 33 rows gate "Surpasses" on holding a level for 3+ consecutive quarters**, so that check is shared infrastructure. Pure logic, zero data dependency — **this is buildable today by anyone.**

Watch for two shapes that break a naive evaluator:
- Rows 23 and 24: the Surpasses threshold is *stricter* than Meets, not just "Meets, sustained."
- Row 33: Surpasses is compound — WIP-to-Throughput in range **AND** Net Delivery Flow 80–110%, both for 3+ quarters.

**2. Module scaffold — ENGPROD-10436.** `modules/sdlc-report-card/` rendering all 33 rows (including the ones not instrumented) against a **mocked `metrics.json`**. That mock **is the seam**: build the UI now, drop in the Snowflake client when the service account lands. Follow `docs/module-template/` and the `registerRefresh` pattern in `modules/ai-impact/server/index.js` and `modules/backport-tracker/server/index.js`.

**3. The Snowflake client.** `snowflake-sdk`, RSA key-pair / JWT. One query per metric family → normalise to `metrics.json` → GET endpoint. **The private key is read from Vault at runtime, never baked into a static secret** — keys rotate via `dice sync serviceaccounts --rotate-keys`, so a copy would silently rot.

### What gates #3

Service accounts aren't permitted in sandbox (SA-008/009), so this needs preprod promotion:

- Create `dataverse_hporgpulsedashboard_preprod_appuser` via a `dataproduct-config` MR, following the product promotion checklist. Precedents to cite: `jira_shipshape_prod_appuser` (bleanhar) and `openshift_ocpusagedashboard_prod_appuser`.
- **Verify Org Pulse egress to `gdadclc-rhpreprod.snowflakecomputing.com`.** Snowflake network policies are per-user and need their own migration. This has been flagged since 2026-10-19 and is still unverified — **it's the thing that stalls the slice after the MR merges.** Someone should own it now.
- Dead end to avoid: `dataverse-consumer-jira-marts` is decommissioned. New access goes via `jira-cloudmarts` or a direct consumer entry.

### Still undecided

- **ENGPROD-10434** — delivery surface ADR. New module vs. the `platform/registerReport` seam. `hp-org-pulse/platform/` is empty, so registerReport carries first-use cost.
- **ENGPROD-10433** — `docs/DATAVERSE-INTEGRATION.md` is the named deliverable and hasn't been written. Row 24 plus the contract table above is most of its content now.

---

## What we're not solving today

Each of these needs an owner, and none of them should block anyone from claiming a row.

| Open question | Who |
|---|---|
| ~~**Scope** — which HP Jira projects and teams are in the denominator~~ — **answered 2026-10-28** on [ENGPROD-10427](https://redhat.atlassian.net/browse/ENGPROD-10427?focusedCommentId=19163850). Project Category starts with `HP`, or is Hybrid Cloud Management; team roll-up via Cyborg, with Brad Tweardy's eazyBI code as reference. What's left is engineering, not leadership input. | us |
| **Cyborg → Snowflake federation** — team attribution, Epic F history and Epic G scope all hang off it. Nobody on our side is tracking it. | John Kyros |
| **RBAC governance** — a service account flattens per-viewer RBAC into one role. Whether a custom UI rendering Snowflake data to other people satisfies the model Preset was chosen to enforce is unresolved. This is a risk to the plan, not an implementation detail. | Eric Rich |
| **Dev promotion for `hporgpulse`** — unblocks CI for everyone. | `#help-dataverse-data-products` |
| **Developing against real data** — only prod ingests. Unpause preprod? Scoped sandbox sync? agk's `engmetrics` team subscribe to the same marts from dev/sandbox and may have solved this. | Dataverse |
| **The nine-month clock** — posture metrics are *not* backfillable. The clock on "3+ consecutive quarters" doesn't start until a collector retains history. **Tell leadership early** — "why is nothing Surpassing" is otherwise an unfair question. **Now narrower:** Sarah's answer on Epic F means rows 11–13 get history via dbt once Cyborg is federated. The problem is real for **Epics C and D only** (rows 1–4, 7–10, 14–15), where nothing records posture today. | us → leadership |
| **ENGPROD-10380** (fork reconciliation) — unassigned for five weeks. | — |
| **ENGPROD-10331** vs Epics C/D — overlapping scope, reconciliation deliberately deferred and still owed. | — |

**One to raise in the room:** **VALORFLOW-28, "Rank Alignment Score", is an open initiative assigned to Sarah Kyros** — and her comment on ENGPROD-10432 says the scores are being built in the **ValorFlow data product** in `rhsandbox`. Those are the same thing. So ENGPROD-10444 ("define the algorithm with leadership") is probably the wrong ticket: the algorithm is being defined elsewhere and our job is to subscribe to the product when it lands. Confirm with Sarah, then re-scope or close the spike.

---

## Cast

**Us** (all nine on the `hporgpulse` rover group and `developers.yaml`):

| Handle | Name |
|---|---|
| `maholder` | Matt Holder |
| `jgiola` | Jacopo Giola |
| `elicohen` | Eliad Cohen |
| `vsanghis` | Vishali Kamenani |
| `achagarl` | Aneela Kaplan |
| `wesgreen` | Weston Greene |
| `skyros` | **Sarah** Kyros |
| `ffeghali` | Fay Feghali |
| `jkyros` | **John** Kyros |

> Correction worth carrying: `skyros` is **Sarah**, `jkyros` is **John**. [[org-pulse-sdlc-report-card]] credits `skyros` as John in one place — that's wrong, and since both are on the group it matters for who you ping.

**Outside:**

- **Dataverse** — Eric Rich, Brad Tweardy · `#help-dataverse-data-products` · docs at [dataverse.pages.redhat.com](https://dataverse.pages.redhat.com/)
- **ProdSec / OSIDB** (rows 5–6) — Sarah Kyros, Marek Baluch, Jeremy West
- **GitHub connector scope + PII masking** (gates all of Epic C) — tdeanton
- **OCPCRT / context registry** (Epic F, PLATENG-106) — TBD
- **Precedents worth cribbing** — bleanhar (`jira_shipshape`, flow metrics on the same Jira marts), Dems (time-between-statuses aggregate), agk's `engmetrics` team
- **Sponsor** — Stephen Cuppett

---

## Links

- Initiative: [PLATENG-179](https://redhat.atlassian.net/browse/PLATENG-179) · thin slice: [ENGPROD-10465](https://redhat.atlassian.net/browse/ENGPROD-10465)
- dbt repo: [hporgpulse-dbt](https://gitlab.cee.redhat.com/dataverse/data-products/aggregate/hporgpulse/hporgpulse-dbt) · first MR: [!1](https://gitlab.cee.redhat.com/dataverse/data-products/aggregate/hporgpulse/hporgpulse-dbt/-/merge_requests/1)
- Product config: [dataproduct-config](https://gitlab.cee.redhat.com/dataverse/dataverse-config/dataproduct-config) → `dataproducts/aggregate/hporgpulse/`
- Org Pulse: `openshift-online/hp-org-pulse` · live at [url.corp.redhat.com/HPOrgPulse](https://url.corp.redhat.com/HPOrgPulse)
- Source rubric: `HP SDLC Checklist - Report Card` (Google Sheet) — the `Measurement implementation tracker` column is back-filled from [[org-pulse-sdlc-report-card]]

---

# Appendix — the 33 rows, verbatim

The full threshold text lived only in the source CSV and the Jira epic descriptions. Copied here so nobody has to chase it.

Four tiers throughout: **Does Not Meet Expectations · Meets Some Expectations · Meets Expectations · Surpasses.** No green/amber/red banding exists — that mapping is undecided and lands with the evaluator (ENGPROD-10435).

## Market Position — rows 1–4 · Epic D · altitude `Container`

> *Goal: maintain baseline security, build, and release standards required to compete in the container platform market.*

| # | Attribute | Does Not Meet | Meets Some | Meets | Surpasses |
|---|---|---|---|---|---|
| 1 | Image (HPSTRAT-799) | UBI/RHEL | UBI-MINIMAL/RHEL-ELS | UBI-MICRO | RH Hardened Images |
| 2 | Build (HPSTRAT-803) | Upon Request/Notification | Weekly Build (Scheduled/Recurring) | Daily/Hourly Build (Scheduled/Recurring) | Triggered based on image change/update, automatic |
| 3 | Scanning (HPSTRAT-806) | Not on Konflux; no engagement with EC scanning requirements | On Konflux but EC policy gaps unaddressed (no exceptions submitted, violations unresolved) | Konflux "Enterprise Contract" enforced, either passing all policies or required exceptions submitted and actively maintained | EC enforced, actively working to reduce/eliminate exceptions, scan accuracy verified |
| 4 | Release (HPSTRAT-803) | Upon Request/Notification | Weekly Release (manual) | Weekly Release (automated) | Fully automated release any day based only on quality gates |

## Security & CVE — rows 5–6 · Epic E

**Row 5 — SLA Success Rate** · HPSTRAT-2 · altitude `Product / Product Family (via ProdSec's classification)` · *(Goal Group blank in source)*

> `< 80%` | `80-94%` | `> 95%` | `> 95% for 3+ consecutive quarters`

**Row 6 — % CVEs Closed by Due Date (Jira)** · Quality & Market Position · altitude `Vulnerabilities (Jira) / Org-Level: Team`
> *Goal: close CVE vulnerabilities by their due dates to minimize security exposure.*

> `< 80%` | `80-94%` | `95-100%` | `> 95% for 3+ consecutive quarters`

## Maintainability — rows 7–9 · Epic C · altitude `Repository`

> *Goal: minimize the risk of shipping defects and accumulating technical or security debt.*

**Row 7 — PR Review** (HPSTRAT-2)
- **Does Not Meet:** Upon Request/Notification (No CODEOWNERS file, no branch protection requiring reviews, PRs sitting unreviewed)
- **Meets Some:** Monitored & Fully Human/Manual (CODEOWNERS exists, branch protection rules active, all review activity from human accounts)
- **Meets:** Automated Reviews with a human override policy (Bot accounts such as CodeRabbit leaving review comments on PRs, automated review integration active)
- **Surpasses:** Authoritative automated reviews for LGTM/approve, with a human override policy and demonstrated defect detection for automated reviews (bot rejections/change requests occurring on a meaningful % of PRs)

**Row 8 — Regression/Revert** (HPSTRAT-3)
- **Does Not Meet:** No revert/regression policy (no defined process for handling regressions)
- **Meets Some:** Fail forward, prioritization on fix (regressions are treated as new bugs; no revert, team pushes a fix)
- **Meets:** Revert policy based on regressions, manually triggered/reviewed (defined criteria for when to revert vs. fix forward; human decision)
- **Surpasses:** Automated reversion policy on regression (automated detection triggers revert; e.g., failed smoke tests auto-revert the merge)

**Row 9 — Dependencies** (HPSTRAT-799)
- **Does Not Meet:** Rarely, if ever, updated (dependencies are stale; known vulnerabilities may be present)
- **Meets Some:** Updated as needed/required (Feature/CVE) (reactive; only when a feature requires it or a CVE forces it)
- **Meets:** Proactively updated for rebases/bumps (manually) (regular manual review and update of dependency versions)
- **Surpasses:** Proactively updated for rebases/bumps (automatically triggered) (e.g., Dependabot, Renovate, or CI pipeline automatically creates update PRs)

## Knowledge Readiness — rows 10–13 · HPSTRAT-2

**Row 10 — Repo Context Documentation (aka. "Agents.MD")** · Epic C · altitude `Repository`
> *Goal: ensure repositories provide the context people and agents need to understand, contribute to, and use code.*

- **Does Not Meet:** No repo-level context docs (README only or none, no AGENTS.MD)
- **Meets Some:** Partial. Some docs present (such as AGENTS.MD) but missing required context areas (e.g., no contributing or architecture guidance)
- **Meets:** All required context areas covered either via consolidated AGENTS.md or separate files (README, CONTRIBUTING, AGENTS.md, ARCHITECTURE.md)
- **Surpasses:** All required context areas covered with ADR files and tooling for spec-driven development support, actively maintained

**Rows 11–13** · Epic F · altitude `Team / Component (Org Repo YAML)`
> *Goal: ensure organizational context is discoverable, accessible, and usable by people and agents.*

| # | Attribute | Does Not Meet | Meets Some | Meets | Surpasses |
|---|---|---|---|---|---|
| 11 | Context Registration Coverage *(automated checks for coverage rates + harness generation Coming Soon)* | `< 50%` registered or inherited | `50-99%` | `100%` | `100%` for 3+ consecutive quarters |
| 12 | Context Accessibility *(automated checks for broken links, missing permissions Coming Soon)* | `<50%` of registered context accessible | `50-99%` | `100%` | `100%` for 3+ consecutive quarters |
| 13 | Context Quality *(automated quality evals Coming Soon)* | `<60%` passing quality evals | `60-84%` | `≥ 85%` | `≥ 85%` for 3+ consecutive quarters |

## Quality (repository) — rows 14–15 · Epic C · HPSTRAT-2 · altitude `Repository`

> *Goal: catch defects early through automated checks and comprehensive testing.*

**Row 14 — Quality Bots**
- **Does Not Meet:** No existing automation for linting, SAST scanning, quality gates
- **Meets Some:** Some automation in place (e.g., linting or basic CI) but gaps in SAST scanning or quality gates
- **Meets:** Linting, SAST scanning, and quality gates active on all PRs
- **Surpasses:** Fully automated workflows to maintain and ensure code and repository health

**Row 15 — Test Maturity**
- **Does Not Meet:** No local, unit or integration testing present
- **Meets Some:** Some tests exist but limited coverage or not consistently run in CI
- **Meets:** Unit and integration tests with adequate coverage, running in CI on all PRs
- **Surpasses:** Comprehensive test suite with high coverage, consistently passing, actively maintained

## Rank Alignment — rows 16–17 · Epic G · HPSTRAT `TBD`

> *Goal: ensure work is properly prioritized, scoped, and worked relative to strategic & org objectives (aka. work on the "right things").*
> Attribute: Rank Alignment Score *(automated / calculated scoring Coming Soon)*. Source note: **"Ranges may change as score is created & tested."**

| # | Altitude | Does Not Meet | Meets Some | Meets | Surpasses |
|---|---|---|---|---|---|
| 16 | Plan View (Jira) | `< 60% aligned` | `60-79%` | `80-94%` | `90%+` for 3+ consecutive quarters |
| 17 | Scrum or Kanban Board (Jira) | `< 70% aligned` | `70-84%` | `85-94%` | `90%+` for 3+ consecutive quarters |

## Speed / Velocity — rows 18–21 · Epic A · attribute `Delivery Cycle Time (Jira)`

> *Goal: hit target Delivery Cycle Time windows (ensures appropriate use of issue types + appropriate delivery speed).*
> Source note in the HPSTRAT column for row 18: *"Do we want these in Org Pulse? And in context for ValorFlow?"*

| # | Altitude | Does Not Meet | Meets Some | Meets | Surpasses |
|---|---|---|---|---|---|
| 18 | Outcomes / HP | 730 days (2+ years; lost strategic relevance) **OR** `< 90 days` (misclassified; should be a Feature / Initiative) | Between 551-730 days (18-24 months; dragging but progressing) | Between 6 months (180 days) and 18 months (550 days) | same, for 3+ consecutive quarters |
| 19 | Features / Initiatives / Product-Program-Area | `> 180 days` (well beyond a release / quarter) **OR** `< 30 days` (misclassified, should be an Epic) | Between 121-180 days (exceeding a single release / quarter) | 45-120 days (within a Release or Quarter) | same, for 3+ consecutive quarters |
| 20 | Epics / Team | `> 130 days` (Feature-scale work in an Epic or mismanaged scope) **OR** `< 14 days` (misclassified, should likely be a Story, Spike, Task, etc.) | Between 101-130 days (above target max, but approaching) | Between 30-100 days (1 month to 1 quarter) | same, for 3+ consecutive quarters |
| 21 | Level 2 Items / Team | `> 42 days` (consistently & significantly overrunning two sprint / kanban cycle boundaries) | Between 29-42 days (consistently spilling past a single sprint / kanban cycle) | `≤ 28 days` (completed within a max sprint/kanban cycle duration) | `≤ 28 days` for 3+ consecutive quarters |

## Capacity — row 22 · Epic B · altitude `All Jira Work`

> *Goal: maintain appropriate balance between proactive and reactive work to ensure strategic priorities receive adequate investment.*

**Row 22 — Reactive Work % (Jira).** The only row with two threshold sets, split by team archetype. **Every in-scope team must be classified Value-Stream or Interrupt or this row can't be scored** — teams missing a cohort tag should be reported, not defaulted.

| Tier | Value-Stream teams (aka. most teams) | Interrupt teams |
|---|---|---|
| **Does Not Meet** | `> 65%` (overwhelmingly reactive; org is in firefighting mode with minimal strategic investment) | `<60% or >95%` (focus not aligned with purpose or effectively no visible investment toward Associate Wellness & Development or Future Sustainability) |
| **Meets Some** | `50-65%` (majority reactive, limited room for proactive/strategic work) | `60-74% or 91-95%` (either less reactive than expected based on team purpose or too little investment toward Associate Wellness & Development or Future Sustainability) |
| **Meets** | `< 50%` (more proactive than reactive) | `75-90%` (reactive work is the primary focus while reserving a capacity for Associate Wellness & Development or Future Sustainability) |
| **Surpasses** | `< 50%` for 3+ consecutive quarters | `75-90%` for 3+ consecutive quarters |

## Quality (work mix) — rows 23–24 · Epic B · altitude `All Quality & Security Items (Jira) / Org-Level: Team`

**Row 23 — Regression % (Jira)**
> *Goal: minimize regressions to ensure fixes and changes don't introduce new problems.*

> `> 3%` (fixes are regularly introducing new problems, signals testing/review gaps) | `1-3%` (regressions are noticeable, room to improve) | `< 1%` (regressions are rare) | `< 0.5%` for 3+ consecutive quarters

**Row 24 — % Items with Attached Cases (Jira)** ← *the one that's built*
> *Goal: catch quality issues internally before customers experience them.*

> `> 5%` (1 in 20 quality items is customer-impacting; quality is leaking into customer experience) | `Between 3-5%` | `< 3%` | `< 1%` for 3+ consecutive quarters

> ⚠️ Sarah's canonical source for this row is the **"Number of Cases Linked"** field (SalesForce plugin), with a documented equation — not the `SFDC_CASE_COUNTER` column we built against. Reconcile before trusting the number.

⚠️ On both rows the Surpasses threshold is **stricter** than Meets — Surpasses is not simply "Meets, sustained."

## Throughput — rows 25–28 · Epic A

> *Goal: maximize sustainable throughput without sacrificing quality, speed, or team health.*
> **All four rows share identical thresholds:**

> **Does Not Meet:** Below the decline threshold (0.5 Standard Deviation below avg. throughput)
> **Meets Some:** Bouncing between growth & decline
> **Meets:** Within the Stable Range or above the Growth Threshold (0.5 Standard Deviation above avg. throughput)
> **Surpasses:** Stable or growing for 3+ consecutive quarters

| # | Altitude | Attribute |
|---|---|---|
| 25 | Outcomes (Jira) / Org-Level: HP | Avg. Throughput (Jira) |
| 26 | Features / Initiatives / Product-Program-Area | *(inherits)* |
| 27 | Epics (Jira) / Org-Level: Team | Avg. Monthly Throughput (Jira) |
| 28 | Level 2 Items / Org-Level: Team | *(inherits)* |

## Sustainable Delivery (aka. Sustainable Pace) — rows 29–32 · Epic A

> *Goal: maintain a sustainable delivery pace by keeping WIP levels within a healthy range relative to Delivery Throughput (aka. address / avoid burnout).*
> Attribute: Total WIP vs. Delivery Throughput Ratio

| # | Altitude | Does Not Meet | Meets Some | Meets | Surpasses |
|---|---|---|---|---|---|
| 29 | Outcomes / HP | ⚠️ **stale — now reads "above 7.6x"** (was: above the Quarterly Overload Threshold of 5.5x) OR below the Under-utilization Threshold (0.4x) | Between Quarterly Target Ceiling (5.5x) and Overload Threshold (7.6x) | Within Target Range (2-5.5x) | same, 3+ consecutive quarters |
| 30 | Features / Initiatives / Product-Program-Area | Above the Quarterly Overload Threshold (1.5x) OR below the Under-utilization Threshold (0.9x) | Between Target Ceiling (0.9x) and Overload Threshold (2x) | Within Target Range (0.9-1.5x) | same, 3+ consecutive quarters |
| 31 | Epics / Team | Above the Monthly Overload Threshold (3.9x) OR below the Under-utilization Threshold (0.4x) | Between Target Ceiling (2.5x) and Overload Threshold (3.9x) | Within Target Range (0.9-2.5x) | same, 3+ consecutive quarters |
| 32 | Level 2 Items / Team | Above the Monthly Overload Threshold (1.6x) OR below the Under-utilization Threshold (0.4x) | Between Target Ceiling (1.2x) and Overload Threshold (1.6x) | Within Target Range (0.8-1.2x) | same, 3+ consecutive quarters |

## Predictability — row 33 · Epic A · altitude `All Jira Work`

> *Goal: maintain predictable delivery flow by ensuring completion rates keep pace (or exceed) with the rate of starting new work.*

**Row 33 — Net Delivery Flow Ratio**

> **Does Not Meet:** Below the Instability Threshold (`<65%`)
> **Meets Some:** Between the Instability Threshold and Stability Floor (`65-79%`)
> **Meets:** `≥ 80%` (stable flow OR actively reducing WIP)
> **Surpasses:** WIP-to-Throughput within Target Range **AND** Net Delivery Flow Ratio between `80–110%` for 3+ consecutive quarters

Row 33 sits in Epic A rather than Epic B precisely because that compound Surpasses tier depends on Epic A's WIP ratio.

---

## Defects in the source rubric — raise with leadership

1. ~~**Row 29**~~ — **resolved.** Sarah confirmed on ENGPROD-10426 (2026-10-28) that *Does Not Meet* was intended to read "above 7.6x", **and it has been fixed in the source sheet**. The appendix above still shows the old text — re-pull the CSV.
2. **Row 30** — same class of error. *Meets Some* ceiling (2x) exceeds the *Does Not Meet* floor (1.5x).
3. **Rows 16/17** — the Surpasses floor (90%) sits **below** the Meets ceiling (94%) at both altitudes. A team at 92% qualifies for both bands. Likely intent: 95%.
4. **Row 5** — *Meets Some* is `80-94%` and *Meets* is `> 95%`, leaving 94–95% in a gap. Row 6 fixes this by reading `95-100%`; row 5 should match.

An evaluator can't score overlapping or gapped bands deterministically, so these need resolving before ENGPROD-10435 ships. Items 2 and 4 are new — not previously logged.

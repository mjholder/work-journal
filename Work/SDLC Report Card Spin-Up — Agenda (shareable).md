---
type: meeting-notes
date: 2026-10-29
tags:
  - org-pulse
  - sdlc-report-card
  - agenda
  - shareable
---
> Shareable version — paste from the H1 below into the meeting doc. Self-contained: every link goes to Jira, GitLab or Google, nothing to a personal vault.

# SDLC Report Card — Team Spin-Up

**Purpose:** leave this meeting able to pick up a report card metric and start work on it.

**Not the purpose:** resolving the open scope, governance and ownership questions. They're listed at the end so they're visible, not so we solve them today.

**Optional pre-read:** [PLATENG-179](https://redhat.atlassian.net/browse/PLATENG-179) (the initiative) and [ENGPROD-10425](https://redhat.atlassian.net/browse/ENGPROD-10425) (foundations epic).

**Agenda**

1. What we're building, and how (10 min)
2. Access check — everyone verifies live (10 min)
3. One metric end to end (15 min)
4. How to claim work (10 min)
5. The Org Pulse side (5 min)
6. Decisions and actions (10 min)

---

## 1. What we're building

Leadership produced the **HP SDLC Checklist — Report Card**: 33 measurements, each scored against the same four tiers — Does Not Meet Expectations / Meets Some / Meets / Surpasses. Roughly ten of them gate the top tier on sustaining a level for 3+ consecutive quarters.

**How we deliver it:**

```
jira_db.marts            source product, owned by the jira team — we read, never write
      ↓  dbt
hporgpulse_db.staging    stg_* views: pass-through and casts only
      ↓  dbt
hporgpulse_db.marts      one table per metric family — the calculation lives here
      ↓  Snowflake query
Org Pulse                refresh handler → metrics.json → rubric evaluation → rendered row
```

We own a **Dataverse aggregate data product** called `hporgpulse`, onboarded in sandbox on 2026-10-26. The metrics are dbt models we write and maintain. **Org Pulse renders; it calculates nothing and stores nothing.**

Row 24 (% Items with Attached Cases) went end to end on 2026-10-29, so the path is proven. The remaining rows are repetition, which is why this splits across the team.

**Two decisions already made:**

- **One mart per metric family, not one table for all 33.** The metrics have genuinely different shapes — ratios, posture booleans, cycle-time distributions, compound checks. Each gets the grain and columns it needs. The shared contract is the `metrics.json` the Org Pulse refresh handler produces, not a common table schema.
- **No metric SQL in Org Pulse.** If you find yourself computing something in JavaScript, it belongs in dbt.

---

## 2. Access check

Everyone was added to the `hporgpulse` product owners and rover groups on 2026-10-21, so this should already work. Please verify during the meeting:

- **Rover group** — `dataverse-aggregate-hporgpulse` at rover.redhat.com
- **GitLab** — you can open [hporgpulse-dbt](https://gitlab.cee.redhat.com/dataverse/data-products/aggregate/hporgpulse/hporgpulse-dbt). The group also grants access to `dataverse/dataverse-config/dataproduct-config` and `dataverse/astro/astro-toolkit`.
- **Snowflake** — the group gives you user-warehouse access to the sandbox account under role `hporgpulse_group`. No service account needed; sandbox reads go through your own identity.

If any of these is missing it's a rover membership issue, not a Dataverse one.

*Known discrepancy to confirm: the group is `dataverse-aggregate-hporgpulse` in the config repo, but appears elsewhere as `hporgulse` (missing a `p`). A typo'd group name fails silently, so worth checking against rover.*

---

## 3. One metric end to end

### Local setup

There is **no local Dataverse stack** — nothing to run in containers. "Local" means the dbt CLI on your laptop talking to the real sandbox Snowflake account over browser SSO.

```bash
git clone git@gitlab.cee.redhat.com:dataverse/data-products/aggregate/hporgpulse/hporgpulse-dbt.git
cd hporgpulse-dbt
python3 -m venv .venv && source .venv/bin/activate
pip install dbt-snowflake sqlfluff sqlfluff-templater-dbt
export SNOWFLAKE_USER=<your-kerberos-uid>
dbt deps
dbt debug --target sandbox   # a browser window opens for SSO
dbt run   --target sandbox
```

The sandbox target is already committed in `profiles.yml`: account `hnb22701`, `externalbrowser` auth, role `hporgpulse_group`, warehouse `hporgpulse_group_xs_wh`, database `hporgpulse_db`, schema `marts`. (`hnb22701` is the legacy account locator for the same account whose org-qualified name is `gdadclc-rhsandbox`; dbt accepts either form.)

### Environments, and the Snowflake web UI

**Environments are separate Snowflake accounts — not a column, a schema or a database prefix.** There is nothing to filter by in SQL. The database and schema names are identical in every environment:

| | sandbox | dev | preprod | prod |
|---|---|---|---|---|
| account | `gdadclc-rhsandbox` | `gdadclc-rhdev` | `gdadclc-rhpreprod` | `gdadclc-rhprod` |
| auth | SSO, as you | key-pair JWT | key-pair JWT | key-pair JWT |
| role | `hporgpulse_group` | service account role | ← | ← |
| warehouse | `hporgpulse_group_xs_wh` | `hporgpulse_service_xs_wh` | ← | ← |
| database | `hporgpulse_db` | `hporgpulse_db` | `hporgpulse_db` | `hporgpulse_db` |

So `dbt --target sandbox` is choosing which host to connect to and as whom, not applying a filter. The same holds for the Org Pulse module later — switching environment is connection configuration, never a query parameter.

**Snowsight follows the same shape**, `app.snowflake.com/<org>/<account>/`:

```
https://app.snowflake.com/gdadclc/rhsandbox/      ← where we work
https://app.snowflake.com/gdadclc/rhdev/
https://app.snowflake.com/gdadclc/rhpreprod/
https://app.snowflake.com/gdadclc/rhprod/
```

Swap the account segment to change environment; there's no selector inside a session.

**Because the names are identical everywhere, a query result cannot tell you which environment produced it.** Before trusting or sharing a number:

```sql
select current_account(), current_role(), current_warehouse(), current_database();
```

Worth making a habit.

Note this is distinct from the Ludo / Dataverse console, which has its own `?environment=rhsandbox` URL parameter — different system, different switch.

This is also why MR CI currently fails: `hporgpulse` exists only in the sandbox environment, so the dev-credential step has nothing to fetch.

*To confirm in this meeting: whether a personal fork is required or we can push branches directly to the canonical repo. MRs from a fork and MRs from a branch behave differently in CI, so we should all do the same thing.*

*Also note the committed `README.md` is still GitLab template boilerplate, and the clone URL inside it points at a `source-aligned` path. That's wrong — we're an aggregate product. Ignore the README.*

### Finding the data

This is most of the work on any given row: **establish which marts and columns can support the metric, then write the calculation.** Introspect rather than guess:

```sql
use role hporgpulse_group;
use warehouse hporgpulse_group_xs_wh;

show tables in jira_db.marts;
show views  in jira_db.marts;
describe view jira_db.marts.jira_issue;
select * from jira_db.marts.jira_issue limit 20;
```

`jira_db.marts` holds roughly 30 objects, including `JIRA_ISSUE`, `JIRA_PROJECT`, `JIRA_SPRINT`, `JIRA_CUSTOMFIELDVALUE`, `JIRA_SFDC_CASE`, `JIRA_NODEASSOCIATION`, and `PQI_BUGS_DASHBOARDS_JIRA_TABLE` (116M rows of day-grain defect lifecycle data).

### Subscribing to marts we don't have yet

**Today `hporgpulse` can read exactly one thing: `jira_db.marts`, in sandbox.** Not `jira_db.cloud_marts`, not any other product, not any other environment. If a row needs data from elsewhere, obtaining access is part of the work rather than a given.

Access is a **`dataproduct-config` merge request, raised against the producing product's file rather than ours** — adding `hporgpulse` to the consumers list under the relevant presentation schema. From `dataproducts/source/jira/sandbox/product.yaml`:

```yaml
data_product_db:
- database: jira_db
  presentation_schemas:
  - name: marts
    consumers:
    - name: engmetrics
      kind: data_product
    - name: hporgpulse        # ← our entry
      kind: data_product
```

Four things worth knowing before you raise one:

- **It's per schema.** Access to `marts` grants nothing on `cloud_marts`; that's a separate entry.
- **It's per environment.** `sandbox`, `dev`, `preprod` and `prod` are separate files. Preprod access is a separate MR at promotion time.
- **Some schemas don't use a consumers list.** `rhai_marts` and `cloudrhai_marts` carry `access_policy: rh_internal` instead — a different model and a different request.
- **`kind` matters.** Use `data_product` for us reading as hporgpulse, `service_account` for the Org Pulse dashboard account later. The `consumer_group` route is legacy, and `dataverse-consumer-jira-marts` in particular is decommissioned.

**Allow time.** The MR onboarding hporgpulse took roughly a week to get reviewed. Raise a subscription as soon as you know you need it, not when you're ready to write SQL.

**What exists to subscribe to:**

| Need | Source product | Note |
|---|---|---|
| Epic C — repositories | `github`, `gitlab`, `gitlabsaas` | github carries the full PR / review / workflow surface; the gitlab products are considerably thinner |
| Epic D — containers | `brew`, `errata`, `pyxis` | no Konflux and no Quay product exists anywhere in the repo |
| Epic E — ProdSec | `osidb`, `prodsecrisks` | both sandbox-only, which is where we develop |
| Epic G — rank alignment | `valorflowcontext` | where the alignment scores are being built |
| People and teams | `roverpeople`, `ldap` | |

`engmetrics` and `healthindex` are aggregate products doing adjacent work; `healthindex` is an existing "report card" precedent worth looking at.

### The worked example

Branch `engprod-10465-thin-slice-sdlc-metrics`. Four files, worth reading before writing your own:

| File | What it does |
|---|---|
| `models/source.yml` | Declares the upstream source. Read-only, always. |
| `models/staging/stg_jira__pqi_bugs.sql` | A **view**. Pass-through columns and casts, no logic. Naming: `stg_<source>__<thing>`. |
| `models/marts/pct_items_with_attached_cases.sql` | A **table**. The calculation. Named for the metric. |
| `models/*/schema.yml` | A description on every column, plus data tests. |

Row 24 ships 17 tests — grain uniqueness via `dbt_utils.unique_combination_of_columns`, `not_null` on anything that matters, `accepted_values` on the enum-like columns. These are what confirmed the grain was right on a 116M-row table; please don't skip them.

Then:

```bash
dbt run  --target sandbox
dbt test --target sandbox
sqlfluff lint models/marts/<your_model>.sql
git checkout -b engprod-NNNNN-short-slug
```

**Sanity-check the output before opening the MR.** Row 24 came out RHEL ~10–15%, OpenShift Request Tracker ~57% — the second is a case-driven queue, so a high number is expected. If the numbers don't have an explanation, the SQL is wrong. Put the reasoning in the MR.

### Output shape

Marts don't share a table schema — give your metric the grain and columns it needs. What's worth keeping common across all of them is the **identifying columns**, so the Org Pulse normaliser stays generic instead of growing a branch per metric:

- `metric_id` — stable slug, matches the model name
- `scope_type` / `scope_id` — what it's computed for (`project` today)
- `period_start` / `period_end` — the period it covers

Row 24 adds `unit`, `numerator`, `denominator` and `metric_value`. That's a good default **for ratio metrics**; don't contort a different shape into it. (`metric_value` rather than `value` because `value` is a Snowflake keyword.)

The `metrics.json` contract itself is the deliverable of [ENGPROD-10433](https://redhat.atlassian.net/browse/ENGPROD-10433) and **hasn't been written yet**. Until it is, row 24 plus the identifying columns is the whole convention — so metrics two and three are as likely to shape the contract as to follow it. Expect to feed changes back.

### Known constraints

- **Sandbox is not a complete environment.** Only prod has a live Fivetran connector; dev and preprod are paused. Sandbox Jira data is a static snapshot whose tail quarters repeat their final state. Numbers computed in sandbox prove the calculation, not the reality — nobody reports off them.
- **MR CI currently fails for everyone** with `secrets_provider_not_found`, because the dev-credential include can't provision credentials for a sandbox-only product. Fix is at product level, pending in `#help-dataverse-data-products`. Open MRs anyway; the pipeline isn't the gate yet.
- `.sqlfluff` is configured against the `dev` target. To lint locally, temporarily switch it to `sandbox`.
- MR pipelines don't appear under the branch ref in the GitLab API — read the MR's `head_pipeline`.
- **Scheduling is not solved.** Astro is deferred, and there's currently no documented path from a merged model to a scheduled run in preprod or prod.

---

## 4. How to claim work

Epics are grouped by **data source / collector** rather than by leadership's goal groups, so each one matches the boundary of a single conversation or integration and can slip as a unit.

📌 = **Sarah Kyros has commented with a data lead. Read it before starting.**

| Epic | Rows | Ticket | |
|---|---|---|---|
| 0 — Foundations | — | [ENGPROD-10425](https://redhat.atlassian.net/browse/ENGPROD-10425) | |
| A — Jira Flow & Sustainable Pace | 18–21, 25–33 | [ENGPROD-10426](https://redhat.atlassian.net/browse/ENGPROD-10426) | 📌 |
| B — Jira Work Mix & Quality | 22, 23, 24 | [ENGPROD-10427](https://redhat.atlassian.net/browse/ENGPROD-10427) | 📌 |
| C — Repository Posture | 7–10, 14, 15 | [ENGPROD-10428](https://redhat.atlassian.net/browse/ENGPROD-10428) | |
| D — Container & Build Posture | 1–4 | [ENGPROD-10429](https://redhat.atlassian.net/browse/ENGPROD-10429) | 📌 |
| E — Security & CVE | 5, 6 | [ENGPROD-10430](https://redhat.atlassian.net/browse/ENGPROD-10430) | 📌 |
| F — Org Context Coverage | 11, 12, 13 | [ENGPROD-10431](https://redhat.atlassian.net/browse/ENGPROD-10431) | 📌 |
| G — Rank Alignment | 16, 17 | [ENGPROD-10432](https://redhat.atlassian.net/browse/ENGPROD-10432) | 📌 |

Each epic description carries the verbatim goal group, goal, altitude, attribute and all four tier thresholds for its rows — that's the fastest way to see what your metric has to produce. **None of the 13 child spikes and stories has any comments**, so read the parent epic before picking up a child.

### Data leads already on the board

- **[ENGPROD-10427](https://redhat.atlassian.net/browse/ENGPROD-10427?focusedCommentId=19163850) is the anchor comment** — epics A, D and G point back to it. In-scope Jira projects are those whose **Project Category starts with `HP`** or is **Hybrid Cloud Management**. Team roll-up should come from **Cyborg**, where teams register a project or project+component. Brad Tweardy has working attribution code at [`sage/eazybi-generators`](https://gitlab.cee.redhat.com/sage/eazybi-generators) usable as a reference, and John Kyros is scoping what it takes to federate Cyborg data into Snowflake.
- **Epic B field sources are named**, each with a documented equation in Brad's analysis spreadsheet, and all three carry the same caveat — *not in Snowflake yet*: row 22 uses Activity Type `customfield_10464`, row 23 the Regression (yes/no) field, row 24 a "Number of Cases Linked" field generated by a SalesForce plugin.
- **Epic E** — ProdSec data lives in OSIDB. Contacts are Marek Baluch or Jeremy West.
- **Epic F** — history is expected to be calculated via dbt and available in Snowflake once Cyborg data is federated.
- **Epic G** — alignment scores are being built in the ValorFlow data product, in `rhsandbox`.

### Filing a story

We are deliberately **not** filing all 33 up front, because a story's shape depends on which marts turn out to support it. File your own when you claim a row:

- **Title:** `Row NN — <Measurement Attribute> dbt model`
- **Parent:** the row's epic above. **Type:** Story, or Spike if the question is whether the row is sourceable at all.
- **Labels:** `ai-generated-jira`, `hcm-engineering-productivity`, `org-pulse`, `sdlc-report-card`, plus the row's `goal-<group>` label
- **Components:** `Org-Pulse AI Dashboard` + `Metrics` · **Activity Type:** `Product / Portfolio Work`
- **Acceptance criteria:** mart carries the identifying columns; data tests pass including a grain test; sqlfluff clean; output sanity-checked with the reasoning in the MR; MR open against `hporgpulse-dbt`

Assign yourself and link the branch on the ticket.

### Easy wins — suggested first tickets

Ranked by how little stands between you and a merged MR. **Everything here sits inside the subscription we already hold** (`jira_db.marts`, sandbox) — none of it needs a new `dataproduct-config` MR first.

**Tier 0 — no dbt required, and they unblock everyone else**

- **Inventory `jira_db.marts`** — all ~30 objects: what each one is, its grain, its useful columns, and which report card rows it could serve. This hasn't been done, and it's the "work out which marts support this row" step done once rather than nine times. No dbt needed, no SQL beyond `describe`. Probably the highest-value half-day available right now, and a good fit if you'd rather not start in dbt.
- **Establish whether `JIRA_CUSTOMFIELDVALUE` carries Activity Type `customfield_10464`** — a single query. The field is reported as "not in Snowflake yet", but that view does exist, so the comment may refer to the derived equation rather than the raw field. The answer determines whether row 22 is near-term or not.

**Tier 1 — the easiest full metric: row 23, Regression %**

Same source table as row 24 (`PQI_BUGS_DASHBOARDS_JIRA_TABLE`), same ratio shape, same project × quarter grain, and the table carries `DEFECT_REGRESSION_DAY_FLAG` directly. SQL from an earlier attempt already exists in git history at commit `d2100f2`, so this is close to a copy-adapt-test exercise.

One caveat to record on the ticket: the canonical source per Sarah is the **Regression (yes/no) Jira field**, not the PQI flag — so this ships as a proxy with a documented reconciliation question, the same position row 24 is in.

**Tier 2 — straightforward off `JIRA_ISSUE`**

- **Row 33, Net Delivery Flow Ratio** — issues completed in a period over issues created in it. Its altitude is `All Jira Work`, so it needs no altitude mapping, making it the cheapest flow metric to produce a value for. Only the Surpasses tier is blocked, since that's compound and depends on the WIP ratio.
- **Rows 25–28, Throughput** — a count per period per issue type. The simplest of the flow family, and easier than cycle time because it needs no transition timestamps. All four altitudes are gated on [ENGPROD-10438](https://redhat.atlassian.net/browse/ENGPROD-10438), but one altitude can ship first and the rest are repetition.

**Harder than they look**

- **Rows 18–21, Cycle Time** — needs transition history rather than issue rows. Notably harder than throughput despite sitting next to it on the sheet.
- **Rows 29–32, WIP vs Throughput** — depends on throughput landing first.
- **Row 6, CVEs by due date** — the PQI table has no due-date or CVE field. Needs an `osidb` subscription; osidb is sandbox-only, which is where we develop, so this is a reasonable second-wave item.
- **Epics C, D, F and G** — each needs either a new subscription or an upstream capability that doesn't exist yet. Conversations before code.

*This ranking is inferred from object names and the one table we've used so far, not from column-level inspection of all 30 objects — which is why the inventory is Tier 0. Expect the order to change once it's done.*

---

## 5. The Org Pulse side

None of the read path exists yet. Three pieces, in order:

1. **Rubric evaluator** — [ENGPROD-10435](https://redhat.atlassian.net/browse/ENGPROD-10435). Four tiers plus the sustained-quarters check. Pure logic, no data dependency — **buildable today by anyone.** Two shapes to watch: on rows 23 and 24 the Surpasses threshold is *stricter* than Meets, not just Meets sustained; and row 33's Surpasses is compound, requiring two conditions together.
2. **Module scaffold** — [ENGPROD-10436](https://redhat.atlassian.net/browse/ENGPROD-10436). `modules/sdlc-report-card/` rendering all 33 rows, including the ones not yet instrumented, against a **mocked `metrics.json`**. That mock is the seam: the UI gets built now, the Snowflake client drops in later.
3. **The Snowflake client.** `snowflake-sdk` with RSA key-pair / JWT auth, private key read from Vault at runtime. One query per metric family, normalised to `metrics.json`, served from a GET endpoint.

Piece 3 needs preprod promotion, since service accounts aren't permitted in sandbox: create the dashboard service account via a `dataproduct-config` MR, and **verify Org Pulse network egress to preprod Snowflake** — that's the item most likely to stall the work after the MR merges, and it has been open since 2026-10-19.

Still undecided: the delivery surface ADR ([ENGPROD-10434](https://redhat.atlassian.net/browse/ENGPROD-10434)) and the integration contract doc ([ENGPROD-10433](https://redhat.atlassian.net/browse/ENGPROD-10433)).

---

## 6. Decisions and actions

**Decisions for this meeting**

- Fork or direct branch for `hporgpulse-dbt`?
- Who takes the rubric evaluator (10435) and the module scaffold (10436)? Both are unblocked today.
- Who takes the altitude mapping spike (10438)? It gates eight rows.
- Who owns verifying Org Pulse egress to preprod Snowflake?
- Who follows up with John Kyros on Cyborg → Snowflake federation?

**Action items**

| Action | Owner |
|---|---|
| Verify rover / GitLab / Snowflake access | everyone |
| Inventory `jira_db.marts` — all ~30 objects, grain, columns, rows they could serve | |
| Check whether `JIRA_CUSTOMFIELDVALUE` carries `customfield_10464` | |
| Row 23 Regression % — adapt from `d2100f2` | |
| Confirm fork vs direct branch, then document it | |
| Rubric evaluator — ENGPROD-10435 | |
| Module scaffold with mocked metrics.json — ENGPROD-10436 | |
| Altitude mapping spike — ENGPROD-10438 | |
| Reconcile row 24 against the documented "Number of Cases Linked" equation | |
| Track Cyborg → Snowflake federation | |
| Verify Org Pulse egress to preprod Snowflake | |
| Raise dev promotion / dev CI credentials in `#help-dataverse-data-products` | |

---

## Open questions — visible, not for today

| Question | Where it sits |
|---|---|
| **RBAC governance.** A service account flattens per-viewer access into one role. Whether a custom Org Pulse UI rendering Snowflake data to others satisfies the governance model Preset was chosen to enforce is unresolved. This is a risk to the approach, not an implementation detail. | Dataverse (Eric Rich) |
| **Developing against real data.** Only prod ingests Jira. Unpause preprod, or a scoped sandbox sync? | Dataverse |
| **Posture history.** Rows 1–4, 7–10 and 14–15 aren't backfillable — nothing records what a repository or image looked like last quarter. The "3+ consecutive quarters" clock doesn't start until some collector retains observations, putting the first possible Surpasses roughly nine months out. Worth raising with leadership before the first review rather than after. Epic F is now expected to be covered by the Cyborg federation; C and D are not. | us → leadership |
| **Cyborg → Snowflake federation.** Team attribution, Epic F history and Epic G scope all depend on it, and it is currently unowned on our side. | John Kyros |
| **Rank Alignment Score scope.** [VALORFLOW-28](https://redhat.atlassian.net/browse/VALORFLOW-28) and the ValorFlow data product appear to be defining this already, which suggests [ENGPROD-10444](https://redhat.atlassian.net/browse/ENGPROD-10444) ("define the algorithm with leadership") is mis-scoped — our job may be to subscribe rather than define. | confirm with Sarah Kyros |
| **[ENGPROD-10380](https://redhat.atlassian.net/browse/ENGPROD-10380)** (fork reconciliation) has been unassigned for five weeks. | |

**Threshold defects to confirm with leadership.** An evaluator can't score overlapping or gapped bands deterministically:

- **Row 29** — confirmed and already fixed in the source sheet ("above 7.6x"). Re-pull any local copy.
- **Row 30** — the Meets Some ceiling (2x) exceeds the Does Not Meet floor (1.5x). Same class of error as row 29.
- **Rows 16 and 17** — the Surpasses floor (90%) sits below the Meets ceiling (94%), so a team at 92% qualifies for both.
- **Row 5** — Meets Some ends at 94% and Meets begins above 95%, leaving a gap. Row 6 avoids this by reading 95–100%.

---

## Reference

- **Initiative:** [PLATENG-179](https://redhat.atlassian.net/browse/PLATENG-179) · **Thin slice:** [ENGPROD-10465](https://redhat.atlassian.net/browse/ENGPROD-10465)
- **dbt repo:** [hporgpulse-dbt](https://gitlab.cee.redhat.com/dataverse/data-products/aggregate/hporgpulse/hporgpulse-dbt) · first MR: [!1](https://gitlab.cee.redhat.com/dataverse/data-products/aggregate/hporgpulse/hporgpulse-dbt/-/merge_requests/1)
- **Product config:** [dataproduct-config](https://gitlab.cee.redhat.com/dataverse/dataverse-config/dataproduct-config) → `dataproducts/aggregate/hporgpulse/`
- **Org Pulse:** `openshift-online/hp-org-pulse` · live at [url.corp.redhat.com/HPOrgPulse](https://url.corp.redhat.com/HPOrgPulse)
- **Dataverse docs:** [dataverse.pages.redhat.com](https://dataverse.pages.redhat.com/) · [building data products](https://dataverse.pages.redhat.com/data-products/build-products/) · help in `#help-dataverse-data-products`
- **Source rubric:** "HP SDLC Checklist — Report Card" (Google Sheet). The verbatim thresholds for each row are also in the corresponding epic description.

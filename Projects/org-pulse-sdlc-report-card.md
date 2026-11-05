---
type: project
status: active
tags: [ project, org-pulse, metrics, sdlc, jira ]
created: 2026-10-08
---

# Project: Org Pulse SDLC Report Card

## Overview

Leadership produced an **HP SDLC Checklist — Report Card** defining **33 measurements** that Org Pulse is expected to surface. Each row specifies a Goal Group, a Goal, a Measurement Altitude, a Measurement Attribute, and four scoring tiers: Does Not Meet Expectations, Meets Some Expectations, Meets Expectations, Surpasses.

Two columns in that sheet are **entirely empty**:

- `Jira initiative (one level down from HPSTRAT)`
- `Measurement implementation tracker`

Back-filling the tracker column is the point of this project. The [[#Row-by-row coverage]] table below is the paste-ready artifact for it.

The data sources for most of these metrics are **not nailed down**. Several require conversations with teams we don't own — ProdSec, Konflux/Quay/Pyxis, OCPCRT via PLATENG-106. So the deliverable for the first phase is not an implementation plan. It is a **ticket structure that gives each of those conversations a home**.

Related: [[rhai-org-pulse]] · [[assess-rfe]] · [[org-pulse-productization-decision]] · [[dataverse-dataproduct-config]]

## Key Links

### JIRA & Project Context
- Source CSV: `~/Downloads/HP SDLC Checklist - Report Card.csv`
- Parent initiative: [PLATENG-179](https://redhat.atlassian.net/browse/PLATENG-179) — Expand HP Org-pulse to include metrics for teams and leadership
- Outcomes referenced by the report card: HPSTRAT-2, HPSTRAT-3, HPSTRAT-799, HPSTRAT-803, HPSTRAT-806
- External dependency: [PLATENG-106](https://redhat.atlassian.net/browse/PLATENG-106) — Context Registry (OCPCRT team, `openshift/org` YAML + `cyborg`)
- Adjacent existing ticket, deliberately untouched: [ENGPROD-10331](https://redhat.atlassian.net/browse/ENGPROD-10331)

### Dataverse Resources
- **Dataverse docs:** [dataverse.pages.redhat.com](https://dataverse.pages.redhat.com/)
- **Building data products:** [Build Products Guide](https://dataverse.pages.redhat.com/data-products/build-products/)
- **Architecture slides:** [Dataverse Pipeline Presentation](https://docs.google.com/presentation/d/1kuKB_rnSA4DYEDV3l-BTvvNfEU7cEF0iGeELP0YbYPM/edit?slide=id.g3f999fcbd05_1_615#slide=id.g3f999fcbd05_1_615)
- **Sage channel:** (link pending from Eric Rich)
- **Office hours:** (calendar link pending from Eric Rich)

### Data Product Sources
- **GitHub source product:** [Ludo/Asteroid GitHub](https://ludo-ddis-asteroid--ludo.apps.int.spoke.prod.us-east-1.aws.paas.redhat.com/data-product/github)
- **GitHub GitOps config:** [dataproduct-config/source/github](https://gitlab.cee.redhat.com/dataverse/dataverse-config/dataproduct-config/-/tree/main/dataproducts/source/github)
- **Config repo (whole thing):** [dataverse-config/dataproduct-config](https://gitlab.cee.redhat.com/dataverse/dataverse-config/dataproduct-config) — cloned locally at `~/git_repos/dataproduct-config`. Mechanics written up in [[dataverse-dataproduct-config]]
- **Snowflake prod:** `https://gdadclc-rhprod.snowflakecomputing.com` (also `-rhpreprod`, `-rhdev`, `-rhsandbox`)
- **Customer Intelligence homepage:** [rh-customers-marketing](https://rh-customers-marketing-605ba0.pages.redhat.com/)
- **Customer Intelligence Confluence:** [CUSTINTELL space](https://redhat.atlassian.net/wiki/spaces/CUSTINTELL/overview?idOrigin=joinProductConsent)

## Current Status

**2026-10-29** — **Row 24 is the thin slice; mart narrowed to one real metric.** The dbt repo ([!1](https://gitlab.cee.redhat.com/dataverse/data-products/aggregate/hporgpulse/hporgpulse-dbt/-/merge_requests/1), branch `engprod-10465-thin-slice-sdlc-metrics`) declares the jira source and ships `stg_jira__pqi_bugs` + `pct_items_with_attached_cases` — **row 24, % Items with Attached Cases** (ENGPROD-10427): bugs with ≥1 SFDC case attached (`sfdc_case_counter > 0`, zero-join path straight off the PQI table) over bugs active in the quarter, project × quarter grain. Validated: run green (~11k rows), 17/17 tests, sqlfluff clean; plausible output (RHEL ~10-15%, OpenShift Request Tracker ~57%). Initially shipped with defect reopen/regression stand-ins too; **narrowed to row 24 only** per Matt — no fake metrics crowding the data — and renamed `sdlc_metrics` → `pct_items_with_attached_cases` to match the per-family direction. The reopen/regression SQL lives in git history (commit `d2100f2`) if row 23's real definition ever wants it. **CI landmine fired one stage early:** the lint job died with `secrets_provider_not_found` — both MR jobs need dev credentials and hporgpulse is sandbox-only. Fix is product-level (dev promotion or dev CI creds) via `#help-dataverse-data-products`; MR stays open as the vehicle. Orphaned `sdlc_metrics` table left in sandbox (drop manually if it bothers anyone).

- **Team spin-up material written** — [[SDLC Report Card Team Spin-Up — Meeting Notes 2026-10-29]]. Both workstreams in one note: the dbt side (access check, local dbt setup against sandbox Snowflake, introspecting `jira_db.marts`, the row 24 worked example, the mart output contract, the sandbox-is-incomplete caveat) and the Snowflake→Org Pulse side (rubric evaluator, mocked-`metrics.json` scaffold as the seam, Snowflake client gated on the preprod SA + egress verification). Carries a **per-metric story template and claim convention** rather than filing 32 tickets up front — a story's shape depends on which marts turn out to support it. Appendix holds the **verbatim 33-row rubric**, which until now existed only in the source CSV and the Jira epic descriptions.
  - **Handles resolved against Jira:** `vsanghis` = Vishali Kamenani, `achagarl` = Aneela Kaplan, `wesgreen` = Weston Greene, `ffeghali` = Fay Feghali. Also confirmed **`skyros` = Sarah Kyros** and **`jkyros` = John Kyros** — the `hpai_jiraauto_preprod_appuser` line below credits `skyros` as John, which is wrong.
  - **VALORFLOW-28 "Rank Alignment Score" is assigned to Sarah Kyros** — directly upstream of Epic G (rows 16/17). Talk to her before ENGPROD-10444 reinvents the algorithm.
  - **Swept all 21 report-card tickets for Sarah Kyros comments** — she's on **6 of the 8 epics** (A, B, D, E, F, G), almost all 2026-10-28, and **none of the 13 children**. Marked in the meeting doc. Material changes:
    - **Scope is answered** ([ENGPROD-10427](https://redhat.atlassian.net/browse/ENGPROD-10427?focusedCommentId=19163850), the anchor comment that A/D/G point back to): in-scope = Jira projects whose **Project Category starts with `HP`** or is **Hybrid Cloud Management**; team roll-up via **Cyborg** registration, with **Brad Tweardy's** [`sage/eazybi-generators`](https://gitlab.cee.redhat.com/sage/eazybi-generators) as a working reference. Long-term the calc moves into Snowflake — needs Delivery Team, Group, Pillar, Area. **John Kyros** is scoping Cyborg→Snowflake federation. This retires the "undefined denominator" open question.
    - **Epic B field sources named**, each with a documented equation in Brad's analysis sheet, all ***not in Snowflake yet***: row 22 → Activity Type `customfield_10464` (confirms the guess), row 23 → Regression (yes/no) field, row 24 → **"Number of Cases Linked"** from a SalesForce plugin. ⚠️ **Row 24 is the one we built**, against `SFDC_CASE_COUNTER` — different field. Reconcile against her equation before treating the number as correct.
    - **Row 29 defect confirmed and already fixed** in the source sheet ("above 7.6x"). Our CSV copy is stale.
    - **Epic F history problem dissolved** — Sarah expects history calculated via dbt in Snowflake once Cyborg is federated. The nine-month clock is now an **Epics C and D** problem only.
    - **Epic G has a source**: alignment scores are being built in the **ValorFlow data product** in `rhsandbox`. Combined with VALORFLOW-28 being hers, ENGPROD-10444 ("define the algorithm with leadership") is probably mis-scoped — our job is to subscribe, not to define.
    - **Cyborg→Snowflake federation is the highest-leverage dependency on the board** (team attribution + Epic F history + Epic G scope) and nobody on our side is tracking it.
  - **Two more threshold defects found**, neither previously logged: **row 30**'s *Meets Some* ceiling (2x) exceeds its *Does Not Meet* floor (1.5x) — same class as row 29; and **row 5** leaves a 94–95% gap between *Meets Some* (`80-94%`) and *Meets* (`> 95%`), which row 6 avoids by reading `95-100%`.
- **Mart shape decision:** `sdlc_metrics` will *not* become a monolithic all-33-metrics table. Metrics take different forms (ratios, posture booleans, cycle-time distributions, compound checks), so each metric family gets its own mart with its natural grain; the single stable contract is the **metrics.json shape**, and normalization from per-family marts happens in the Org Pulse module's refresh handler (ENGPROD-10436's mock is that seam). Keeps the rubric evaluator generic, refreshes independent per family, and keeps heterogeneous-schema debates out of the warehouse. Design note posted on !1 (note_24706964).
- **Consumption interface confirmed:** no Dataverse API — Org Pulse connects to Snowflake directly (`snowflake-sdk`, RSA key-pair/JWT, key from Vault at runtime, SA `dataverse_hporgpulsedashboard_preprod_appuser` still to be created via dataproduct-config MR), runs one query per metric family, normalizes to metrics.json, serves via GET endpoint. Env switch is pure connection config.
- **Sandbox `jira_db.marts` repopulated** (~30 objects incl. the full `JIRA_*` view set) — schema questions for future rows can be answered by direct sandbox introspection, no more Atlan/bleanhar dependency for discovery.

**2026-10-27** — **Onboarding verified; sandbox data exists but is the wrong shape for row 6.** MR !18648's post-merge pipeline ran green (`usernaut-deploy`, `operator-reconcile-rhsandbox`), the rover group is live, and `hporgpulse_group` can read `JIRA_DB.MARTS` on the sandbox account. The marts schema holds one real table: `PQI_BUGS_DASHBOARDS_JIRA_TABLE` — 116M rows of day-grain defect-lifecycle data (per-bug phase-date state flags; Dems' time-between-statuses pattern). It proves sandbox can hold Jira-derived data, but it cannot compute row 6: **no due-date/SLA field and no CVE/vulnerability distinction**, and the data appears frozen around late 2024 (sandbox jira has no Fivetran connector; dev/preprod connectors are paused; only prod ingests live).

- **Thin-slice decision needed:** (a) keep row 6 and pursue proper jira marts access/schema knowledge — noting row 6's due-date field is an open question in *every* environment (ENGPROD-10442), and ProdSec/OSIDB may be the real source of due dates per Sarah Kyros's comment; or (b) prove the pipe with a metric this table *can* compute — e.g. defect reopen/regression rate (`DEFECT_REOPEN_DAY_FLAG` / `DEFECT_REGRESSION_DAY_FLAG`, adjacent to row 23) — then swap in row 6 when real marts access lands.

- **Raise with Dataverse** (fold into the dbt-repo request in `#help-dataverse-data-products`): how do aggregate products develop against jira marts when only prod has data — unpause preprod? scoped sandbox sync? Also worth asking agk's engmetrics team, who subscribe to the same marts from dev/sandbox.
- **dbt build path mapped:** repo from `dataverse/templates/dataproduct-dbt` via the Slack "DBT Repo Creation" workflow; keyword-replace `dataproduct` → `hporgpulse`; local sandbox profile = SSO as `hporgpulse_group`; source pattern `jira → jira_db.marts`. Astro scheduling deferred — team already holds `dataverse/astro/astro-toolkit` access via the rover group.
- **Jira mart schema still unknown** (sandbox too empty to introspect) — get the jira dbt repo path or Atlin catalog entry from Dataverse, or ask bleanhar (jira_shipshape) what the prod marts expose.
- **While data is blocked:** rubric evaluator (ENGPROD-10435) and module scaffold with mocked `metrics.json` (ENGPROD-10436) are the buildable items — now the critical path, not just parallel work.

**2026-10-26** — **MR !18648 merged — hporgpulse exists in sandbox.** The dataproduct-config MR onboarding the **hporgpulse** aggregate product (sandbox, per the standard product lifecycle; supersedes the closed !18616) finally merged after a week of chasing reviewers. The architecture from the 2026-10-20 comment on [ENGPROD-10465](https://redhat.atlassian.net/browse/ENGPROD-10465) now holds: **we own the computation** (dbt models in hporgpulse, subscribing to the jira source product's sandbox marts), and Org Pulse only renders.

- **Unblocked now:** the row 6 dbt model (percent of CVEs closed by due date) can be built in hporgpulse and run against the jira sandbox marts — sandbox reads go through user-warehouse access via the rover group, no service account needed yet.
- **Still gated on preprod promotion** (later MR, follows the product promotion checklist): the dashboard service account (`dataverse_hporgpulsedashboard_preprod_appuser`, per the repo's cross-dataproduct naming convention — **not** the `orgpulse_dashboard_preprod_appuser` originally suggested), Vault-at-runtime key handling, Org Pulse egress / network-policy verification.
- **ProdSec lead (row 5):** Sarah Kyros commented on ENGPROD-10430 (2026-10-21) — ProdSec's data is in **OSIDB** and they host their own dashboard ([csv-to-pages-product-security](https://csv-to-pages-product-security-94b4a3433ef0d84ad975c2c7f77b135ac.pages.redhat.com/)). Contacts: **Marek Baluch** (aligned ProdSec↔Jira CVE data with Sarah in mid-2025) or **Jeremy West**. This fills ENGPROD-10442's named-contact criterion and suggests the SLA Success Rate may already be a reported number — worth asking before deriving anything ourselves.
- **Parallel work identified while the MR was in review:** rubric evaluator (ENGPROD-10435) → module scaffold with mocked `metrics.json` (ENGPROD-10436) → ProdSec outreach → row 6 SQL. The first two remain the right next steps regardless of the merge.

**2026-10-19** — **Plan of record: thin slice.** Overwhelm reset. The goal restated simply: 33 rubric metrics, visualized in Org Pulse, computed from Dataverse marts over a direct Snowflake connection. Everything else — ownership fights, governance, scope questions — gates **scale-out, not feasibility**. Prove the pipe with **one metric end to end**, then expand by repetition.

- **Ticket:** [ENGPROD-10465](https://redhat.atlassian.net/browse/ENGPROD-10465) — the thin-slice story, under Epic 0 (ENGPROD-10425), Critical, 8 pts, `Related`-linked to ENGPROD-10433/10435/10436. Filed 2026-10-19 after verifying conventions against `team-context-vault/docs/processes/jira.md`.
- **First metric: row 6** — % CVEs Closed by Due Date. Jira-sourced, a single ratio, clear four-tier thresholds; already flagged as the cheapest win. Expansion candidate: an Epic A cycle-time row (unlocks the biggest epic, and Dems' time-between-statuses work is a pattern to crib).
- **Own credentials, not borrowed.** New Org Pulse service account rather than reusing `hpai_jiraauto_preprod_appuser`. One MR to `dataproduct-config`: the SA yaml (`serviceaccounts/preprod/orgpulse_dashboard_preprod_appuser.yaml` — name/email/comment/role) plus the **producer-side** consumer entry in `dataproducts/source/jira/preprod/product.yaml` (`kind: service_account`). Precedents to cite in the MR: `jira_shipshape_prod_appuser` (bleanhar — flow metrics on Jira marts, already approved) and `openshift_ocpusagedashboard_prod_appuser` (ddelcian — dashboard reading `openshift_db` marts). Start **preprod**; promote to prod only after the RBAC governance question settles with Eric.
- **Runtime secret handling:** dice provisions the key pair into Vault (`ddis-asteroid-infra/rhpreprod/snowflake/serviceaccounts/...`); the module reads the private key from Vault at runtime — never baked into a static secret. Rotation is `dice sync serviceaccounts --rotate-keys`, so a static copy would silently rot.
- **Network policy:** per-user and needs its own migration if Org Pulse's egress isn't covered by an existing policy (`ALTER USER ... SET NETWORK_POLICY`). Verify early — it's the one thing that can stall the slice after the MR merges.
- **Module shape:** `modules/sdlc-report-card/` — refresh handler → SQL query → transform → `data/sdlc-report-card/metrics.json` → GET endpoint → one rendered row with its rubric tier. Same pull-based pattern as ai-impact/backport-tracker.
- **Gotcha carried forward:** consumer access to `jira.marts` via the decommissioned `dataverse-consumer-jira-marts` group is a dead end — new access goes through `jira-cloudmarts` or a direct SA consumer entry.
- **Deferred to parallel conversations (explicitly not blocking the slice):** tdeanton connector-scope + PII questions (Epic C *correctness*), DBT ownership (who maintains at scale — Org Pulse computing in the connection layer is fine for the slice, and the working demo is evidence in that argument), RBAC governance with Eric (gates prod rollout, not preprod), agk's team roadmap (gates spike-filing, nothing else).

**2026-10-16** — **Read the Dataverse config repo directly** (`gitlab.cee.redhat.com/dataverse/dataverse-config/dataproduct-config`, cloned to `~/git_repos/dataproduct-config`). Full mechanics written up in [[dataverse-dataproduct-config]]. Five things changed:

1. **There is no Dataverse API.** Consumption is a direct Snowflake connection — `gdadclc-rhprod.snowflakecomputing.com`, SQL, RSA key-pair/JWT auth, private key in Vault (`ddis-asteroid-infra/rh<env>/snowflake/serviceaccounts/`), rotated by `dice sync serviceaccounts --rotate-keys`. This resolves roughly 5 of the 15 discovery questions outright — see the revised unknowns below.
2. **An aggregate data product is where DBT models live.** "Dataverse owns the calculations" means they *run on Dataverse infra*; whoever owns the aggregate writes the DBT. If that owner is Org Pulse, the 33 metrics become DBT models we maintain — materially different from "visualization layer only." **Needs settling before anything is built.**
3. **Epic C's source is far better than "not ideal" suggested.** The `github` product is live in prod with ~75 tables including the full PR-review, commit, workflow and Dependabot surface. Two real caveats: ingestion scope is per-connector (four connectors, orgs unknown) and PII masking unmasks for only two consumers.
4. **Epic D is partly sourced** — `brew`, `errata`, `pyxis` are all live in prod. No Konflux and no Quay product exists anywhere in the repo.
5. **Epic E is weaker than assumed** — `osidb` and `prodsecrisks` both exist but are **sandbox only**. Row 5 has no production source today.

**Also found:** `hpai_jiraauto_preprod_appuser` — HP already holds a Dataverse service account against `dataverse_consumer_jira_rhaimarts_role`, filed by **skyros (John Kyros)**. Preprod only; promoting it is a copy-and-MR.

**2026-10-14** — **Architectural decision made.** Dataverse (backed by Snowflake) will handle all metric calculations. Org Pulse's role is visualization only: custom plugin to query Dataverse + UI/UX work. This fundamentally simplifies the implementation — we're a consumer, not a calculator.

**Contacts:**
- **Primary:** Eric Rich, Brad Tweardy (Dataverse team)
- **Secondary:** John Kyros
- **Channels:** Sage channel (for Dataverse questions), Office Hours (calendar link pending from Eric)

**Meeting with Eric Rich (2026-10-14)** — Architecture and pipeline clarified. Key findings:
- **Pipeline:** FiveTran/Snowflake staging → DBT normalization → Atlin (metadata/access) → Preset (visualization, enforces RBAC)
- **Source vs Aggregated:** Source products = raw ingestion (e.g., Jira); Aggregated = calculated metrics (e.g., Dems time-between-statuses)
- **Git data gap:** No clear source product owner for GitHub/GitLab. Pulse consumed it but declined to be the source. PLM team (Tony Campbell/Shay) built unnormalized console tool for Michael Kleinheim's team, but it's not used (direct exposure, no aggregation).
- **Access model:** Role-based security enforced at table/view level (PII vs non-PII splits for associates vs managers)
- **Timeline:** Raw data (Jira records) instantly queryable. Custom data product build = 2-4 weeks.
- **Visualization:** Preset approved (governance enforced), Python extracts allowed for personal use (no sharing rights)

**Outstanding:**
- Eric to send: pipeline slides, Sage channel details, office hours calendar link
- Review Dataverse docs, attend office hours session
- **Critical blocker surfaced:** Git posture metrics (rows 7–10, 14–15 in Epic C) may not have a viable Dataverse source if GitHub/GitLab ownership remains unclear

**2026-10-08** — Structure created. 8 epics, 5 foundation children, 7 discovery spikes = **20 new issues**, all in ENGPROD, all NEW, all under PLATENG-179. Nothing existing was modified.

Next: the seven outreach conversations. Those are the gate on everything downstream — 22 implementation stories are deliberately *not* written yet, because their shape depends on spike outcomes.

## Grouping Rationale

Grouped **by data source / collector**, not by leadership's 12 Goal Groups. Reason: a group boundary should match the boundary of a conversation or an integration, so an epic can block or slip as a unit. Goal Groups cut across four different source systems and would have produced epics that can never be finished independently.

| Epic | Rows | Covers |
|---|---|---|
| **0 — Dashboard foundations** | — | Ingestion contract, rubric evaluator, view scaffold, core helpers |
| **A — Jira Flow & Sustainable Pace** | 18–21, 25–33 (13) | Cycle Time, Throughput, WIP Ratio, Net Delivery Flow — ×4 altitudes |
| **B — Jira Work Mix & Quality Signals** | 22, 23, 24 (3) | Reactive Work %, Regression %, % Items with Attached Cases |
| **C — Repository Posture** | 7, 8, 9, 10, 14, 15 (6) | PR Review, Regression/Revert, Dependencies, AGENTS.md, Quality Bots, Test Maturity |
| **D — Container & Build Posture** | 1–4 (4) | Image, Build, Scanning, Release |
| **E — Security & CVE** | 5, 6 (2) | ProdSec SLA Success Rate, % CVEs Closed by Due Date |
| **F — Organizational Context Coverage** | 11, 12, 13 (3) | Registration Coverage, Accessibility, Quality |
| **G — Rank Alignment** | 16, 17 (2) | Plan View score, Scrum/Kanban Board score |

**Two deliberate moves away from the obvious split:**

- **Row 33 (Net Delivery Flow Ratio) B → A.** Its Surpasses tier is compound: *"WIP-to-Throughput within Target Range AND Net Delivery Flow Ratio between 80–110% for 3+ consecutive quarters."* It cannot be evaluated without Epic A's WIP ratio, so it has to live beside it.
- **Row 10 (AGENTS.md) F → C.** Its altitude is `Repository` and its collector is a repo scan, same as rows 7/9/14/15. Rows 11–13 are `Team / Component (Org Repo YAML)` via cyborg + `openshift/org`, owned by OCPCRT. This makes **Epic F exactly coterminous with the PLATENG-106 dependency boundary** — F can block wholesale without holding a repo scanner hostage.

**Preserving traceability to the Goal Groups.** Grouping by collector loses leadership's view, so every ticket carries a `goal-<group>` label. `labels = goal-throughput` reconstructs their slice across epics. Every epic description also carries the verbatim Goal Group, Goal, Altitude, Attribute, and all four tier thresholds from the CSV.

## Row-by-row coverage

All 33 rows, no gaps. **This is the paste-ready content for the sheet's empty `Measurement implementation tracker` column.**

| # | Goal Group | Altitude | Measurement Attribute | Epic | Tracker |
|---|---|---|---|---|---|
| 1 | Market Position | Container | Image | D | ENGPROD-10429 |
| 2 | Market Position | Container | Build | D | ENGPROD-10429 |
| 3 | Market Position | Container | Scanning | D | ENGPROD-10429 |
| 4 | Market Position | Container | Release | D | ENGPROD-10429 |
| 5 | *(blank in CSV)* | Product / Product Family (ProdSec) | SLA Success Rate | E | ENGPROD-10430 |
| 6 | Quality & Market Position | Vulnerabilities (Jira) / Team | % CVEs Closed by Due Date | E | ENGPROD-10430 |
| 7 | Maintainability | Repository | PR Review | C | ENGPROD-10428 |
| 8 | Maintainability | Repository | Regression / Revert | C | ENGPROD-10428 |
| 9 | Maintainability | Repository | Dependencies | C | ENGPROD-10428 |
| 10 | Knowledge Readiness | Repository | Repo Context Documentation (AGENTS.md) | C | ENGPROD-10428 |
| 11 | Knowledge Readiness | Team / Component (Org Repo YAML) | Context Registration Coverage *(Coming Soon)* | F | ENGPROD-10431 |
| 12 | Knowledge Readiness | Team / Component (Org Repo YAML) | Context Accessibility *(Coming Soon)* | F | ENGPROD-10431 |
| 13 | Knowledge Readiness | Team / Component (Org Repo YAML) | Context Quality *(Coming Soon)* | F | ENGPROD-10431 |
| 14 | Quality | Repository | Quality Bots | C | ENGPROD-10428 |
| 15 | Quality | Repository | Test Maturity | C | ENGPROD-10428 |
| 16 | Rank Alignment | Plan View (Jira) | Rank Alignment Score *(Coming Soon)* | G | ENGPROD-10432 |
| 17 | Rank Alignment | Scrum or Kanban Board (Jira) | Rank Alignment Score *(Coming Soon)* | G | ENGPROD-10432 |
| 18 | Speed / Velocity | Outcomes (Jira) / HP | Delivery Cycle Time | A | ENGPROD-10426 |
| 19 | Speed / Velocity | Features / Initiatives / Product-Program-Area | Delivery Cycle Time | A | ENGPROD-10426 |
| 20 | Speed / Velocity | Epics (Jira) / Team | Delivery Cycle Time | A | ENGPROD-10426 |
| 21 | Speed / Velocity | Level 2 Items / Team | Delivery Cycle Time | A | ENGPROD-10426 |
| 22 | Capacity | All Jira Work | Reactive Work % | B | ENGPROD-10427 |
| 23 | Quality | All Quality & Security Items / Team | Regression % | B | ENGPROD-10427 |
| 24 | Quality | All Quality & Security Items / Team | % Items with Attached Cases | B | ENGPROD-10427 |
| 25 | Throughput | Outcomes (Jira) / HP | Avg. Throughput | A | ENGPROD-10426 |
| 26 | Throughput | Features / Initiatives / Product-Program-Area | Avg. Throughput | A | ENGPROD-10426 |
| 27 | Throughput | Epics (Jira) / Team | Avg. Monthly Throughput | A | ENGPROD-10426 |
| 28 | Throughput | Level 2 Items / Team | Avg. Monthly Throughput | A | ENGPROD-10426 |
| 29 | Sustainable Delivery | Outcomes (Jira) / HP | Total WIP vs. Delivery Throughput Ratio | A | ENGPROD-10426 |
| 30 | Sustainable Delivery | Features / Initiatives / Product-Program-Area | Total WIP vs. Delivery Throughput Ratio | A | ENGPROD-10426 |
| 31 | Sustainable Delivery | Epics (Jira) / Team | Total WIP vs. Delivery Throughput Ratio | A | ENGPROD-10426 |
| 32 | Sustainable Delivery | Level 2 Items / Team | Total WIP vs. Delivery Throughput Ratio | A | ENGPROD-10426 |
| 33 | Predictability | All Jira Work | Net Delivery Flow Ratio | A | ENGPROD-10426 |

## Jira Tickets

### Hierarchy

```
PLATENG-179  Expand HP Org-pulse to include metrics for teams and leadership
├── ENGPROD-10425  Epic 0 — Foundations for the SDLC Report Card dashboard   [Critical, 13]
│   ├── ENGPROD-10433  Spike  Define the metric ingestion contract            [Blocker, 5]
│   ├── ENGPROD-10434  Spike  ADR: delivery surface for the report card       [Critical, 3]
│   ├── ENGPROD-10435  Story  Four-tier rubric evaluator + sustained-quarters [Critical, 5]
│   ├── ENGPROD-10436  Story  Report card view scaffold (all 33 rows)         [Major, 5]
│   └── ENGPROD-10437  Story  Promote jira-hierarchy / flow-metrics to core   [Major, 8]
├── ENGPROD-10426  Epic A — Jira flow and sustainable pace metrics            [Critical, 13]
│   └── ENGPROD-10438  Spike  Map altitudes to Jira issue types / org levels  [Critical, 3]
├── ENGPROD-10427  Epic B — Jira work mix and quality signal metrics          [Major, 8]
│   └── ENGPROD-10439  Spike  Reactive vs proactive + team cohorts            [Major, 5]
├── ENGPROD-10428  Epic C — Repository posture metrics                        [Major, 13]
│   └── ENGPROD-10440  Spike  Repo posture scanning mechanism                 [Major, 5]
├── ENGPROD-10429  Epic D — Container and build posture metrics               [Major, 13]
│   └── ENGPROD-10441  Spike  Konflux / Quay / Pyxis data sources             [Major, 8]
├── ENGPROD-10430  Epic E — Security and CVE metrics                          [Major, 8]
│   └── ENGPROD-10442  Spike  ProdSec SLA data + product family taxonomy      [Major, 5]
├── ENGPROD-10431  Epic F — Organizational context coverage metrics           [Major, 8]
│   └── ENGPROD-10443  Spike  Context registry contract w/ OCPCRT             [Major, 5]
└── ENGPROD-10432  Epic G — Rank alignment metrics                            [Normal, 8]
    └── ENGPROD-10444  Spike  Define the Rank Alignment Score algorithm       [Normal, 8]
```

### Conventions applied

- Project ENGPROD, parent PLATENG-179, status left at **NEW**, priority set at open time (per `team-context-vault/docs/processes/jira.md`)
- Labels: `ai-generated-jira`, `hcm-engineering-productivity`, `org-pulse`, `sdlc-report-card`, plus the row's `goal-*` label
- Components: `Org-Pulse AI Dashboard` + `Metrics` (plus `Security` on Epic E and its spike)
- Activity Type `Product / Portfolio Work` (`Security & Compliance` on the E spike)
- Story points on both `customfield_10016` and `customfield_10028`
- `relates to` HPSTRAT links: C → 2/3/799 · D → 799/803/806 · E → 2 · F → 2. Rows 18+ have an empty outcome column and rows 16/17 read `TBD`, so A, B and G carry no outcome link.

### Comments added at creation

1. **Scope / denominator question** — on all 8 epics, tailored per epic. Which HP Jira projects, GitHub orgs, LDAP roots, container images, and which of the ~155 team YAMLs are in the denominator.
2. **Posture-history note** — on C, D, F.
3. **CSV threshold defects** — on A (row 29) and G (rows 16/17).

## Architectural Shift: Dataverse Integration

**2026-10-14** — Leadership and Dataverse team aligned on implementation approach:

**Division of labor:**
- **Dataverse (Snowflake backend):** Owns all metric calculations across all 33 rows
- **Org Pulse:** Visualization layer only — custom plugin to query Dataverse + UI/UX work

**What this changes:**
- **Epic 0 (Foundations)** — Still needed: rubric evaluator, view scaffold, delivery surface ADR. But the "metric ingestion contract" (ENGPROD-10433) likely becomes a "Dataverse query contract" instead.
- **Epics A–G** — Dramatically simplified. No calculation logic, no Jira/GitHub/Quay data collection. Just: define the query, call Dataverse, render the result.
- **Discovery spikes** — Several may resolve to "get Dataverse schema for this metric" rather than "figure out how to calculate it."

**What's still unknown:** *(revised 2026-10-16 after reading the config repo — see [[dataverse-dataproduct-config]])*

~~Resolved:~~
- ~~API surface~~ → **No API.** Direct Snowflake connection, `gdadclc-rhprod.snowflakecomputing.com`
- ~~Auth model~~ → **RSA key-pair / JWT**, private key in Vault, rotated by `dice`
- ~~Query language~~ → **SQL**
- ~~Response format~~ → whatever the Snowflake driver returns (`snowflake-sdk` / `snowflake-connector-python`)
- ~~Refresh cadence~~ → set per source connector. Jira syncs every **15 min** from an `aurora_postgres` replica; GitHub every **60 min**; `brew`/`errata`/`roverpeople` daily; `pyxis` 6-hourly

Still open:
- Rate limits / warehouse sizing and cost (most SAs inherit a default warehouse; only 15 of 420 set one explicitly)
- Historical data availability — can we backfill "3+ consecutive quarters"? Jira yes; posture metrics still no (open question #1 below is unchanged)
- **Network policy** — Snowflake network policies are per-user and need their own migration. Depends on where Org Pulse's egress originates
- **Governance** — a service account flattens per-viewer RBAC into one role. Whether a custom Org Pulse UI rendering Snowflake data to other people satisfies the model Preset was chosen to enforce is unresolved, and it's a risk to the whole plan rather than an implementation detail

**Ticket ENGPROD-10433 Updated (2026-10-14):**
- Title changed: "Define the metric ingestion contract" → "Define the Dataverse query contract for SDLC Report Card metrics"
- Description rewritten to reflect pull-based query pattern (not push-based ingestion)
- 10 critical unknowns documented that the spike must resolve
- Contacts added: Eric Rich, Brad Tweardy (primary), John Kyros (secondary)
- Precedent updated: refresh handler pattern from ai-impact/backport-tracker modules
- Acceptance criteria updated: contract spec in `docs/DATAVERSE-INTEGRATION.md`, 3 example queries, meeting notes

**15-Question Discovery Meeting Agenda Prepared:**
1. API surface type and base URL
2. Authentication & authorization mechanism
3. Query patterns (bulk vs per-metric)
4. Metric identification scheme
5. Response format and example payloads
6. Tier calculation (pre-calculated vs raw values)
7. Quarterly historical data availability
8. Sustained threshold evaluation responsibility
9. Data update frequency
10. Change notification mechanism
11. Error scenarios and status codes
12. SLAs and availability
13. Team/component filtering
14. Future expansion and versioning
15. Sandbox credentials and next steps

**Recommended Module Architecture Documented:**
- New `modules/sdlc-report-card/` module
- Pull-based refresh handler pattern
- `DATAVERSE_API_KEY` module secret
- Query → Transform → Store to `data/sdlc-report-card/metrics.json`
- Frontend GET endpoint reads from cached storage
- Refresh cadence TBD from Dataverse team (likely daily)

**6 Follow-up Tickets Identified:**
1. Implement Dataverse Client Module (Story, 8 pts, Critical)
2. Provision Dataverse Credentials (Task, 2 pts, Critical)
3. SDLC Report Card Frontend View (Story, 8 pts, Major)
4. Historical Data Backfill Assessment (Task, 3 pts, Major)
5. Dataverse Integration Testing Plan (Task, 3 pts, Major)
6. Update Discovery Spikes for Dataverse Contract (Task, 2 pts, Major)

**Action:** Schedule sync with Eric Rich + Brad Tweardy to get API contract, schema, and example queries.

## Meeting Notes: Dataverse Architecture Deep-Dive (2026-10-14)

**Attendees:** Matt Holder, Eric Rich

### Pipeline Architecture

**Data flow:** Source systems → FiveTran/Snowflake → Staging tables → DBT (scheduled via Astro) → Shared schemas → Atlin (metadata) → Preset (visualization)

**Source Products:**
- Extract-Load-Transform style
- Minimal transformations on ingestion
- Examples: Jira ingestion
- Owner responsibility: maintain the source product for their domain

**Aggregated Products:**
- Run calculations on normalized data
- Example: Dems data products track time-between-Jira-statuses daily
- Example normalization: 100 rows per key → 1 row, or "best game" calculation (FIFA Soccer 2011 by frequency)

**Normalization:**
- DBT calculations to reduce redundancy
- Varies by product (no universal procedure)
- Demo shown using Snowflake sample tables (game sales raw vs aggregated view)

### GitHub/GitLab Data Sources

**GitHub source product EXISTS (not ideal):**
- **Ludo/Asteroid:** [GitHub data product](https://ludo-ddis-asteroid--ludo.apps.int.spoke.prod.us-east-1.aws.paas.redhat.com/data-product/github)
- **GitOps config:** [dataproduct-config/source/github](https://gitlab.cee.redhat.com/dataverse/dataverse-config/dataproduct-config/-/tree/main/dataproducts/source/github)
- **Status unclear:** Matt noted "not ideal" — need to assess coverage and fitness for Epic C metrics

**Conflicting context from Eric's meeting:**
- Eric stated "no clear source product owner for GitHub or GitLab data"
- Pulse consumed Git data but **declined to serve as source product** for other teams
- PLM team (managed by Tony Campbell, working with Shay) built console tool for Michael Kleinheim's team
- Tool uses **unnormalized data** (direct source exposure, not aggregated product)
- Not in use — team wants to avoid duplicating normalization work

**Impact on Epic C (Repository Posture):**
- Rows 7, 8, 9, 10, 14, 15 all require Git data (PR review, regression/revert, dependencies, AGENTS.md, quality bots, test maturity)
- **Action:** Evaluate Ludo GitHub product schema against Epic C requirements
- **Questions:** Does it have PR review data? CODEOWNERS? Dependency files? Commit revert patterns?

### Access Control & Governance

**Role-based security:**
- Enforced at table/view level
- Separates PII vs non-PII
- Associates vs managers have different access scopes

**Visualization tools:**
- **Preset:** Approved because it enforces data governance and RBAC
- **Python extracts:** Allowed for individual use, but no sharing rights (governance gap)

### Timeline Expectations

**Instant access:**
- Raw data (e.g., Jira records) immediately queryable
- Use existing tables/views in Snowflake

**Custom data products:**
- Building new aggregated calculations: **2-4 weeks**
- Requires DBT work, schema design, access policy setup

### Follow-Up Actions

**Eric Rich to send:**
- [ ] Pipeline presentation slides
- [ ] Sage channel details (Dataverse questions)
- [ ] Office hours calendar link

**Matt Holder next steps:**
- [ ] Review Dataverse documentation ([docs](https://dataverse.pages.redhat.com/), [build guide](https://dataverse.pages.redhat.com/data-products/build-products/), [slides](https://docs.google.com/presentation/d/1kuKB_rnSA4DYEDV3l-BTvvNfEU7cEF0iGeELP0YbYPM/edit))
- [ ] Attend office hours session (calendar link pending)
- [x] **Evaluate GitHub source product against Epic C requirements** — done 2026-10-16 from the connector table manifest:

  | Row | Tables | Verdict |
  |---|---|---|
  | 7 PR Review | `pull_request`, `pull_request_review`, `pull_request_review_comments`, `requested_reviewer_history`, `pull_request_ready_for_review_history`, `pull_request_review_dismissed`, `pull_request_auto_merge` | **Strong** |
  | 8 Regression/Revert | `commit`, `commit_parent`, `commit_pull_request` | Reverts detectable by message pattern; three lower policy tiers still unobservable — open question #4 unchanged |
  | 9 Dependencies | `security_alert`, `security_advisory`, `security_advisory_vulnerability`, `security_vulnerability`, `security_cwe` | **Strong** for Dependabot remediation; weak for "is Renovate configured" |
  | 10 AGENTS.md | `commit_file` (paths per commit) | **Inferential only** — no repo-tree snapshot anywhere. Can tell it was committed, not that it exists today |
  | 14 Quality Bots | `workflow`, `workflow_run`, `commit_check_run`, `commit_status` | **Strong**, but `workflow_run_job`/`_attempt`/`_job_step` are explicitly disabled — no step-level detail |
  | 15 Test Maturity | — | **Gap.** `sonarqubecorp` is user/licence data, not code quality. Nothing in Dataverse carries coverage |

- [x] **Why the GitHub product is "not ideal"** — now explicable. Every mart on it belongs to another team (`omegaprime`, `codechain`, `securesign`, `itbps`, `conforma`). It's a shared raw landing zone with no engineering-metrics aggregate over it. We'd be building the aggregation, not consuming one.
- [x] **GitLab** — `source/gitlab` (gitlab.cee) and `source/gitlabsaas` both exist and are live in prod, but **Snowpipe-based with no Fivetran table manifest**, and `gitlab`'s only declared consumer is `releasecompliance`. Much thinner than GitHub. If HP repos live on gitlab.cee, Epic C is in worse shape than on github.com.
- [ ] **Confirm GitHub ingestion scope** — four separate connectors implies per-GitHub-App-install scope. Which orgs/repos are covered is not discoverable from config. **Ask tdeanton.** This gates all of Epic C.
- [ ] **Confirm the PII tag list** — `github_pii_string_policy` unmasks for only `dataverse-source-github` and `tpserviceusage`. If author/reviewer identity is tagged, per-team attribution breaks. **Ask tdeanton.**
- [ ] **Talk to agk's team** (`engmetrics` / `engmetricssource`, with lichen/podvody/ahills) — dev+sandbox only and currently narrow (parquet → Snowpipe for `OWNERS_COMPONENTS`/`OWNERS_RPMS`), but they are an Engineering Metrics team who have already solved the push-ingestion pattern our posture metrics need. Worth knowing their roadmap before filing more spikes.

## Outstanding Tasks

The seven outreach conversations. Each spike's acceptance criteria require a **named contact**, the API surface and auth model, and a follow-up ticket filed per viable source — so closing the spike actually produces the Wave 2 backlog.

| Spike | Who to talk to | Status |
|---|---|---|
| ENGPROD-10438 | internal — Jira config / hierarchy | not started |
| ENGPROD-10439 | internal + leadership — cohort classification | not started |
| ENGPROD-10440 | internal — repo scanning approach | not started |
| ENGPROD-10441 | **Konflux / Quay / Pyxis teams** | not started — highest risk |
| ENGPROD-10442 | **ProdSec** | not started |
| ENGPROD-10443 | **OCPCRT** (PLATENG-106) | not started |
| ENGPROD-10444 | **leadership** — score definition | not started |

**ENGPROD-10441 is the highest-risk item in the program.** Four CSV rows, zero existing integration — Org Pulse has nothing for Quay, Konflux, Pyxis or any registry. The konflux/quay booleans in `ai-impact/server/component-onboarding/` are Jira-checklist values filled in by hand, not live checks. And the conversation hasn't started.

*Narrowed 2026-10-16:* Dataverse already has `brew` (builds), `errata` (advisories/release) and `pyxis` (certification) **live in prod**, so rows 1–4 are no longer a blank sheet. But **no Konflux and no Quay data product exists anywhere in the repo**, so the registry/scanning half of Epic D still has no source. Still the highest risk, just a narrower question.

*Also revised:* **ENGPROD-10442 is worse than assumed.** `osidb` (ProdSec flaw data, jvang) and `prodsecrisks` (PRODSECRM risk register, Vincent Danen) both exist but are **sandbox only — no prod, no preprod**. Row 5 has no production source today, which makes the ProdSec conversation about *their* promotion timeline, not just about schema.

*And:* **ENGPROD-10440 now has concrete tables to evaluate** rather than an open "how would we scan repos" question. See the Epic C table above — the answer is mostly "query the `github` marts", with a real gap at row 15 and an inferential answer at row 10.

**Cheapest win available:** row 6, % CVEs Closed by Due Date. Source is Jira, lands in the existing `cve-triage` module which already has a working fetcher and declares the `jira` secret. Best candidate to prove out the rubric evaluator end to end, and it shouldn't wait on the ProdSec conversation.

## Open Questions

**1. Posture history has nowhere to live.** Jira-sourced metrics (rows 6, 18–33) are backfillable — Jira is retrospectively queryable, so "3+ consecutive quarters" can be evaluated on day one. Posture metrics (rows 1–4, 7–15) are **not**: nobody knows what a Dockerfile or CODEOWNERS file looked like last quarter unless something recorded it. With Org Pulse owning no store, the collector or the source system must retain that history, and **the clock doesn't start until one of them does** — roughly nine months to the first possible Surpasses evaluation. Worth telling leadership early; *"why is nothing Surpassing"* is otherwise an unfair question.

**2. Reconciling Epics C/D against ENGPROD-10331.** "Establish Repo-Level Agentic Readiness Tracking in Org Pulse" has 7 criteria that overlap rows 1–4, 7, 9, 14, 15. It was left **completely untouched** — no retitle, no description change, no labels, no links, no comment — because it has real comment activity and editing it would strand that history. Epic C's description names it as adjacent ground with reconciliation deferred. That reconciliation is still owed.

**3. Two defects in the CSV thresholds**, to raise while back-filling the tracker column:
   - **Row 29** (WIP Ratio, Outcomes): *Does Not Meet* is "above 5.5x" but *Meets Some* is "between 5.5x and 7.6x" — overlapping. Likely intent: Does Not Meet should read "above 7.6x".
   - **Rows 16/17** (Rank Alignment): Surpasses floor (90%) sits **below** the Meets ceiling (94%) at both altitudes. A team at 92% qualifies for both. Likely intent: 95%.

**4. Three rows may resolve only to a spike.** Row 8 (Regression/Revert policy) — only the top tier leaves a machine-detectable trace; the three lower tiers describe a documented policy no scanner can observe, so a team-declared posture file may be the honest answer. Rows 12/13 (Context Accessibility, Context Quality) — both marked *"Coming Soon"* by leadership themselves; the upstream capability doesn't exist. Not declining the work; not inventing an implementation for a capability nobody has built.

**5. Delivery surface undecided.** AGENTS.md prefers a view in an existing module over a new one, but no existing module is a natural home for all 33 rows. The `platform/registerReport` seam is the honest architectural fit, but `hp-org-pulse/platform/` is empty so it carries first-use cost. ENGPROD-10434 resolves this.

**6. 22 implementation stories deliberately not written.** Their shape depends on spike outcomes. A ticket encoding a guess that ENGPROD-10441 will invalidate is worse than no ticket.

## Notes

- Org Pulse **owns no database and no datasource** for these metrics. It queries other systems, or receives pushes, and renders the result. This constraint shaped the whole structure — it's why Epic 0 has no history-store work and no posture-accrual job, and why ENGPROD-10433 (the ingestion contract) is the keystone.
- Precedent for the ingestion endpoint: `modules/ai-impact/server/assessments/routes.js` → `POST /assessments/bulk`, `requireAdmin` + `requireScope('ai-impact:write')` + size cap. The rfe-assessor pipeline is a working client — see [[assess-rfe]].
- Scope definition (which Jira projects / GitHub orgs / LDAP roots / teams) got **no epic of its own** — it's a leadership-input gap, not an engineering one, so it lives as a comment on each epic. Same conclusion the [[rhai-org-pulse]] level-set reached on 2026-09-24.
- I can't write to the Google Sheet. The [[#Row-by-row coverage]] table above is the artifact to paste from.

## Pre-Refinement Pass (2026-10-30)

Full working note: [[SDLC Report Card Pre-Refinement — 2026-10-30]]

Reworked the foundations tickets ahead of refinement, because they were written 2026-10-08 and the architecture has turned over twice since — and because they read as six unrelated essays rather than one pipeline.

### The organising frame now used across all the tickets

1. Jira → Fivetran (15 min) → `jira_db.marts` — someone else's product, we read
2. dbt in `hporgpulse` → `hporgpulse_db.marts` — the calculation
3. Snowflake client → `metrics.json` — the plumbing
4. Rubric evaluator: value + thresholds → tier — the grading
5. Vue view: 33 rows on a page — the display

Every foundations ticket now opens by naming its step. Steps 3–5 are the Org Pulse module.

### Changes applied to JIRA

- **ENGPROD-10433** retitled to "Document the hporgpulse to Org Pulse metrics contract". Blocker → Major, 5 → 2 pts. The 10 discovery unknowns were already answered on 2026-10-16; they are now listed as do-not-re-investigate. What remains is `docs/DATAVERSE-INTEGRATION.md` and the trailing-quarters question.
- **ENGPROD-10434** retitled to "ADR: record where the SDLC Report Card lives in Org Pulse". Critical → Major, 3 → 1 pt. Corrected option 3 — `registerReport` is a team-tracker client-side contribution slot via `platform/<name>/team-tracker-contributions.js`, not a platform seam in an empty `platform/`. Named `ai-impact` as the real contender for option 2, since it already owns rubric scoring.
- **ENGPROD-10435** and **ENGPROD-10436** rewritten for approachability — file lists, what to copy, the CI traps. Added the fifth threshold shape (rows 23/24: Surpasses is stricter than Meets, not "Meets, sustained") and the four known rubric band defects.
- **ENGPROD-10509** created — the Snowflake client and refresh handler. Carved out of 10465.
- **ENGPROD-10510** created — preprod promotion, dashboard service account, egress verification. Blocks 10509. This is the real blocker and had been unowned since 2026-10-19.
- **ENGPROD-10465** retitled to row 24, with a comment recording that the dbt half shipped and the Org Pulse half was carved out.
- **ENGPROD-10437** commented, not rewritten — needs a decision on whether anything still needs those helpers in JS.
- **ENGPROD-10425** rewritten around the pipeline, measurement-scope question closed, per-row filing convention added.

### Findings worth carrying

- `modules/releases/server/hygiene/jira-fetch.js`, named in 10437, **does not exist in `hp-org-pulse`**. It is in the sibling `rhai-org-pulse` repo nobody has checked out — 720 lines, a hub for six other files, full of RHOAI-specific field IDs.
- `modules/team-tracker/` in `hp-org-pulse` is a **read-only symlink into `@org-pulse/core`** created by `npm run setup`. Editing it means a core PR plus a release plus a version bump.
- `hp-org-pulse` docs drift: `AGENTS.md`'s "Current modules" list is copied from rhai-org-pulse and wrong; the README advertises `npm run update:view-owners` and `platform/view-owners/owners.js`, neither of which exists; the PR checklist references a `.github/CODEOWNERS` that does not exist.
- Correction to this file: `skyros` is **Sarah**, `jkyros` is **John**. This note miscredits one of them.

### Handout set chosen — 2026-10-30 (same day, second pass)

Four tickets picked to assign at the refinement session: ENGPROD-10435 (rubric
evaluator), ENGPROD-10436 (view scaffold), plus two new ones —
**ENGPROD-10512** (row 23 Regression Percentage dbt model) and
**ENGPROD-10511** (surface the report card custom fields in `jira_db.marts`).
Both new tickets parented to ENGPROD-10427.

**The load-bearing finding.** Sarah Kyros's 2026-10-28 comments say all three
work-mix fields — Activity Type `customfield_10464`, the Regression yes/no
field, and "Number of Cases Linked" — are "not in Snowflake yet." That is true
of the marts and false of the ingestion. The jira source product's prod
Fivetran connector replicates the Jira Postgres database directly
(`aurora_postgres`, WAL, 15-minute sync) with `customfield`,
`customfieldoption`, `customfieldvalue` and `AO_9D8F2F_SFDC_CASE` all enabled,
and `schema_change_handling: ALLOW_COLUMNS`. The values land every fifteen
minutes; they're just never surfaced in a presentation schema. Consumers bind
to `jira_db.marts` and siblings, not the replicated tables.

Owners to approach: `tdeanton` (product and business owner of the jira source
product), `hgirish` (maintainer). Both in
`dataproducts/source/jira/groups/` in `dataproduct-config`.

**Also found:** `hporgpulse` does not appear in the prod consumer list for
`jira_db.marts`. We're sandbox-only from MR !18648. That ask is folded into
ENGPROD-10511.

**Standing caveat now recorded on ENGPROD-10427.** Row 24 shipped off
`sfdc_case_counter` and row 23 will ship off the PQI regression phase flag.
Both are proxies for the fields Sarah named. Row 22 has no proxy at all.
Nothing from those three rows goes in front of leadership until Sarah signs off
the proxies or ENGPROD-10511 lands.

**Sequencing note.** 10511 and 10512 are linked *related*, not blocking. 10512
ships the proxy now; 10511 retires the caveat later. Blocking would have
stopped the one piece that can actually start.

Other doors Sarah's comments closed: rank alignment scores (rows 16/17) don't
exist yet and are being built in the ValorFlow data product; org-context
history (rows 11–13) waits on Cyborg being federated into Snowflake. The row 29
threshold defect she confirmed and has already fixed upstream — our CSV copy is
stale and needs re-pulling.

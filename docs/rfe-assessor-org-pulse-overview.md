# RFE Quality Assessment for Org Pulse — Overview & Plan

**Author:** Matt Holder
**Date:** June 2026
**Status:** Proposed
**Related Epic:** [PLATENG-108](https://redhat.atlassian.net/browse/PLATENG-108) — RHAI Org Pulse for HP

---

## Executive Summary

We are proposing to add **automated RFE (Request for Enhancement) quality assessment** to the Org Pulse deployment for Hybrid Platforms. This capability uses AI to evaluate Jira RFE tickets against a structured quality rubric, scoring them on five dimensions: What, Why, How, Task Breakdown, and Sizing. The results are surfaced as metrics in Org Pulse, giving engineering leaders visibility into the quality and completeness of incoming feature requests across their teams.

The RHEL AI team already runs this pipeline for their own RFEs. Our goal is to run it against the **OpenShift RFE project** so that leadership can track RFE quality trends, identify gaps in feature request documentation, and improve the upstream planning process.

> **Clarification (2026-06-17):** There are two separate systems that feed Org Pulse's AI Impact module — the rfe-creator (developer tool, applies Jira labels for adoption metrics) and the rfe-assessor (batch CI pipeline, scores RFEs on a quality rubric). Only the **rfe-assessor (quality scoring)** path applies here. The rfe-creator adoption path is ruled out because no OpenShift RFEs were created using AI skills, so no labels exist. See [[rfe-assessor-data-pipeline]] for the full two-pipeline distinction.
>
> **Manual scoring run completed** (2026-06-17): Tony and Pratik ran the assess-rfe skill manually against the OpenShift RFE project, producing CSV + HTML output. This demonstrates the pipeline works for our target project.

---

## What We're Providing

### The Problem

RFEs (Requests for Enhancement) are a critical input to engineering planning. When they're well-written — clear problem statement, justified business case, actionable technical approach, broken into tasks, and appropriately sized — they move through the planning process faster and with fewer round-trips. When they're not, they create delays, miscommunication, and rework.

Today there is no systematic way to measure RFE quality at scale. Reviews happen ad-hoc, and there's no visibility into quality trends across teams or over time.

### The Solution

The RFE Assessor is an **automated quality assessment pipeline** that:

1. **Pulls RFE tickets from Jira** — fetches all tickets from the configured project (OpenShift RFE)
2. **Scores each RFE on a five-point rubric** using AI (Claude) to evaluate:
   - **What** (0-2) — Is the outcome clearly described?
   - **Why** (0-2) — Is the business justification compelling?
   - **Open to How** (0-2) — Is the technical approach outlined without being prescriptive?
   - **Not a Task** (0-1) — Is this a feature request, not a task masquerading as one?
   - **Right-sized** (0-1) — Is the scope appropriate?
   - Total: 0-8, with Pass/Fail threshold
3. **Publishes results to Org Pulse** — assessment data flows into the dashboard, where it appears as quality metrics alongside existing sprint and contribution data

This gives engineering leaders a **quality signal** on their RFE pipeline — which teams write strong RFEs, where the gaps are, and whether quality is improving over time.

### What Managers Will See

In Org Pulse, the RFE assessment data surfaces as:

- **Quality scores** across the five rubric dimensions
- **Trends over time** — are RFEs getting better or worse?
- **Individual RFE scorecards** — drill into any ticket to see its assessment
- **Score distribution** — identify which criteria are consistently weak

---

## How It Works

The system has three main components that work together:

```
┌──────────────┐      ┌───────────────────┐      ┌──────────────┐
│              │      │                   │      │              │
│  Jira Cloud  │─────▶│   RFE Assessor    │─────▶│  Org Pulse   │
│  (RFE tix)   │      │   (CI Pipeline)   │      │  (Dashboard) │
│              │      │                   │      │              │
└──────────────┘      └───────────────────┘      └──────────────┘
                              │
                              │ Uses
                              ▼
                      ┌───────────────────┐
                      │   assess-rfe      │
                      │   (Claude Code    │
                      │    AI Plugin)     │
                      └───────────────────┘
```

### Component 1: The Assess-RFE Plugin

A Claude Code plugin that does the actual assessment work. When given a Jira RFE ticket, it reads the summary and description, evaluates it against the quality rubric, and produces a structured score. The rubric criteria are generic PM quality criteria — they are not specific to any one product or team.

**Current state:** The plugin exists and works today for RHEL AI's RFEs. It is team-agnostic — the scoring rubric applies to any well-structured feature request. For our use case (scoring all RFEs in the OpenShift RFE project), the plugin works as-is. We will contribute a `--jql` flag upstream to `opendatahub-io/assess-rfe` for flexibility, with a fallback to forking if upstreaming is slow. The core assessment logic stays the same.

### Component 2: The RFE Assessor Pipeline

A GitLab CI pipeline that orchestrates the end-to-end process:

1. Fetches target RFE tickets from Jira
2. Runs the assess-rfe plugin inside a secure sandbox (OpenShell) to score each ticket
3. Stores the assessment results in a data repository
4. Pushes the results to Org Pulse via its bulk API

The pipeline runs on a schedule (e.g., nightly or weekly) and processes new or updated tickets each run. Each run takes approximately 4-6 hours depending on the number of tickets, as each assessment requires careful AI analysis.

**Current state:** The pipeline runs today for RHEL AI, hardcoded to their `RHAIRFE-*` Jira project. Pointing it at the OpenShift RFE project requires parameterizing approximately 10 hardcoded references across 3 files — replacing `RHAIRFE` with a configurable variable. The core pipeline logic does not change.

### Component 3: Org Pulse Dashboard

The Org Pulse instance we are deploying for HP (infrastructure provisioning is well underway — see [ENGPROD-10017](https://redhat.atlassian.net/browse/ENGPROD-10017)). RFE assessment data flows into Org Pulse's **AI Impact** module, which provides the visualization and reporting layer.

**Architectural note:** The AI Impact module that displays RFE data currently lives in the "AI Eng" layer of Org Pulse, not the core layer. Our HP deployment uses core images only. Adding this module to our deployment is a prerequisite — see the next section for details.

---

## Org Pulse Preparation: Adding the AI Impact Module

### Background

Org Pulse was recently split into two image layers by the upstream RHEL AI team ([PR #820](https://github.com/red-hat-data-services/rhai-org-pulse/pull/820)):

- **Core layer** — the platform shell plus team-tracker features (Jira sprint metrics, GitHub/GitLab contributions, LDAP roster sync). This is what HP deploys.
- **AI Eng layer** — extends core with RHEL AI-specific modules including AI Impact (RFE assessments), System Health, Product Builds, Release Registry, and Upstream Pulse.

The AI Impact module is the piece that connects the RFE Assessor pipeline to the Org Pulse dashboard. It serves two roles: it provides the **API endpoint** that receives assessment results from the pipeline, and it provides the **frontend views** that let managers see those results in the dashboard.

### How the AI Impact Module Fits Into the Workflow

Here is the end-to-end data flow, from Jira ticket to manager's screen:

```
                    ┌─────────────────────────────────────────────────┐
                    │           RFE Assessor Pipeline (CI)            │
                    │                                                 │
  ┌──────────┐     │  ┌────────────┐    ┌─────────────────────────┐  │
  │          │     │  │            │    │                         │  │
  │  Jira    │─────┼─▶│ dump_jira  │───▶│  Claude (assess-rfe)   │  │
  │  Cloud   │     │  │ (fetch     │    │  Scores each RFE on    │  │
  │          │     │  │  tickets)  │    │  What/Why/How/Task/Size │  │
  └──────────┘     │  └────────────┘    └───────────┬─────────────┘  │
                   │                                │                │
                   │                    ┌───────────▼─────────────┐  │
                   │                    │                         │  │
                   │                    │  push-results           │  │
                   │                    │  (store scored results  │  │
                   │                    │   in data repo)         │  │
                   │                    └───────────┬─────────────┘  │
                   │                                │                │
                   │                    ┌───────────▼─────────────┐  │
                   │                    │                         │  │
                   │                    │  push-to-org-pulse      │  │
                   │                    │  (POST to bulk API)     │  │
                   │                    └───────────┬─────────────┘  │
                   └────────────────────────────────┼────────────────┘
                                                    │
                                                    │ HTTPS POST
                                                    │ (bearer token auth)
                                                    ▼
                    ┌─────────────────────────────────────────────────┐
                    │            Org Pulse (on OpenShift)             │
                    │                                                 │
                    │  ┌─────────────────────────────────────────┐   │
                    │  │  AI Impact Module (backend)             │   │
                    │  │                                         │   │
                    │  │  /api/modules/ai-impact/assessments/    │   │
                    │  │    └─ bulk  (receives up to 5k scores)  │   │
                    │  │    └─ GET   (serves data to frontend)   │   │
                    │  │                                         │   │
                    │  │  Stores results on PVC filesystem       │   │
                    │  └────────────────────┬────────────────────┘   │
                    │                       │                        │
                    │  ┌────────────────────▼────────────────────┐   │
                    │  │  AI Impact Module (frontend)            │   │
                    │  │                                         │   │
                    │  │  • Per-team quality scores              │   │
                    │  │  • Score trends over time               │   │
                    │  │  • Individual RFE scorecards            │   │
                    │  │  • Cross-team comparisons               │   │
                    │  └────────────────────────────────────────┘   │
                    └─────────────────────────────────────────────────┘
```

**Step by step:**

1. **Fetch** — The pipeline's `dump_jira` script connects to Jira Cloud and pulls all RFE tickets from the configured project (OpenShift RFE for HP).

2. **Score** — Each ticket is passed to the assess-rfe Claude Code plugin running inside a secure sandbox. Claude reads the ticket's summary and description, evaluates it against the five rubric criteria (What/Why/How/Task Breakdown/Sizing), and produces a structured score for each dimension.

3. **Store** — The `push-results` script commits the scored results to a dedicated data repository. Results are organized by project prefix with a `current` pointer to the latest run, creating a versioned history of assessments over time.

4. **Push** — The `push-to-org-pulse` script reads the latest results and sends them to the AI Impact module's bulk API endpoint (`/api/modules/ai-impact/assessments/bulk`) via an authenticated HTTPS POST. The endpoint accepts up to 5,000 assessment entries per request. Authentication uses a bearer token scoped to `ai-impact:write`.

5. **Store (Org Pulse side)** — The AI Impact module's backend receives the assessment data and persists it to the Org Pulse PVC (filesystem-based storage — no database). This data is then available for the frontend to query.

6. **Display** — The AI Impact module's frontend renders the assessment data in the Org Pulse dashboard. Managers see per-team quality scores, trends over time, individual ticket scorecards, and cross-team comparisons — all accessible through the existing Org Pulse UI alongside sprint metrics and contribution data.

### What Needs to Happen on Our Side

Since we maintain our own fork of Org Pulse ([RedHatInsights/rhai-org-pulse](https://github.com/RedHatInsights/rhai-org-pulse)), we can add the AI Impact module to our core images without waiting on or depending on the upstream team. The work involves:

1. **Port the AI Impact module into our fork's core build** — cherry-pick or merge the AI Impact backend routes and frontend components from the AI Eng layer into our core Dockerfiles. The other AI Eng modules (System Health, Product Builds, Release Registry, Upstream Pulse) are RHEL AI-specific and stay excluded.
2. **Verify the bulk API endpoint** — confirm the `/api/modules/ai-impact/assessments/bulk` endpoint works in the core build, accepts assessment payloads, and stores results correctly.
3. **Validate the dashboard UI** — ensure the AI Impact tab renders correctly and displays assessment scores, trends, and drill-down views.
4. **Update our Konflux build pipeline** — the core Dockerfiles in our fork will include the additional AI Impact module files. No changes to the build infrastructure itself — just the Dockerfile contents.

### Why This is Low-Risk

- The AI Impact module is **self-contained** — it has its own backend routes and frontend components with minimal dependencies on other AI Eng modules.
- We are not modifying the module itself — we are including it as-is in our build. The code already works in the RHEL AI instance.
- Our fork already diverges from upstream for deploy templates and secret configuration, so this is consistent with our existing fork strategy.
- This work has already been scoped and a development branch has been started.

### Parallel Workstreams

The assessor pipeline work and the AI Impact module work can proceed in parallel — they connect at the bulk API endpoint, which is already defined. Neither depends on the other being finished first:

| Workstream | What It Delivers | Can Start |
|------------|-----------------|-----------|
| Pipeline parameterization + plugin fork (Phases 1-2) | A pipeline that can score HP RFEs and produce results | Immediately |
| AI Impact module integration (Phase 3) | An Org Pulse instance that can receive and display results | Immediately |
| End-to-end integration (Phase 4) | Results flowing from pipeline to dashboard | After both above are done |

---

## What We Need

### Resources Required

| Resource                      | Description                                                                                                                                                              |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Jira bot account**          | Already provisioned for Org Pulse. May need scope extended to cover additional HP RFE projects.                                                                          |
| **GitLab CI runners**         | Pipeline runs on `itup-alm-x86` shared runners on our GitLab instance. These are behind the VPN and already have the necessary GitLab access. Since this is a shared runner, assessment runs (4-6 hours each) will need to be scheduled during off-peak times to minimize impact on other users. |
| **Vertex AI (Claude) access** | Each assessment run uses Claude via Vertex AI for 4-6 hours. Cost scales linearly with number of teams/tickets assessed.                                                 |
| **Org Pulse API token**       | Admin-scoped API token for pushing assessment data. Created through Org Pulse settings.                                                                                  |
| **Assess-rfe upstream contribution** | Add `--jql` flag to upstream `opendatahub-io/assess-rfe` for custom query support. Fallback: fork + custom sandbox image.                                            |
| **VPN-accessible push path**  | Our Org Pulse instance is behind VPN. The `itup-alm-x86` runner is already behind the VPN, so the data push to Org Pulse can happen directly from the pipeline — no separate CronJob or special networking required. |

### Cost Considerations

The primary ongoing cost is **Vertex AI (Claude API) usage**. Each assessment run processes all target tickets with AI analysis:

- A single team's RFE backlog takes approximately **4-6 hours of compute time** per run
- Runs are typically scheduled **weekly or nightly** depending on ticket volume
- Adding more teams scales linearly — each additional team adds another 4-6 hour run
- Runs can be staggered across different days/times to manage runner capacity and cost

The exact cost per run depends on the number of tickets and the Vertex AI pricing tier. We recommend starting with a single team to establish a cost baseline before expanding.

**Shared runner impact:** The pipeline uses `itup-alm-x86`, a shared GitLab runner behind the VPN. Assessment runs are long-lived (4-6 hours), which ties up a runner slot for the duration. We will schedule runs during off-peak hours (e.g., overnight or weekends) to minimize contention with other teams' workloads. If runner capacity becomes a concern, we can explore dedicated runner provisioning as a follow-up.

---

## Effort Estimate

### Phase 1: Pipeline Parameterization — 0.5 days

Replace hardcoded RHEL AI references with configurable variables in the existing pipeline. This is the foundational change that makes everything else possible. No new features — just making the existing system flexible.

### Phase 2: Assess-RFE Upstream Contribution — 0.5 days

Contribute a `--jql` flag upstream to `opendatahub-io/assess-rfe` for custom query flexibility. The plugin already supports targeting a single project key — the upstream change adds the option to pass arbitrary JQL. Fallback: fork + custom sandbox image if upstreaming is slow.

### Phase 3: AI Impact Module Integration — 1-2 days

Port the AI Impact module from the upstream AI Eng layer into our fork's core images. This gives our Org Pulse instance the API endpoint for receiving assessment data and the dashboard UI for displaying it. Includes verifying the bulk API contract, validating the dashboard renders correctly, and updating our Konflux build configuration. This work can proceed in parallel with Phases 1-2.

### Phase 4: Pipeline-to-Dashboard Integration — 0.5 days

Configure authentication between the assessor pipeline and Org Pulse (API token provisioning), verify end-to-end data flow from pipeline output through the bulk API to the dashboard, and confirm results display correctly.

### Phase 5: First Team Onboarding — 0.5 days per team

For each team we onboard:
- Verify Jira API access covers the team's RFE project
- Configure pipeline schedule for the team
- Run a test assessment (limited to 5 tickets) to validate
- Review results and calibrate if needed

### Total Estimated Effort

| Item | Effort |
|------|--------|
| Pipeline parameterization | 0.5 days |
| Assess-rfe upstream contribution (`--jql` flag) | 0.5 days |
| AI Impact module integration (Org Pulse fork) | 1-2 days |
| Pipeline-to-dashboard integration | 0.5 days |
| OpenShift RFE project onboarding | 0.5 days |
| **Total for OpenShift RFE live** | **~3-4 days** |

Phases 1-2 (pipeline + plugin) and Phase 3 (AI Impact module) can run in parallel, so the wall-clock time is closer to **3-4 days** with two people, or **~5 days** sequential.

---

## Dependencies & Open Questions

### Must Resolve Before Starting

| Item | Status | Owner |
|------|--------|-------|
| **AI Impact module in core layer** | Planned — we will port the AI Impact module from the AI Eng layer into our fork's core images. Work is scoped and a development branch has been started. No upstream dependency. | Matt Holder |
| **Target Jira project** | **Resolved (2026-06-17)** — OpenShift RFE project, confirmed via Bill/Tony. Specific Jira project key TBD. | Stakeholders |
| **Budget approval for Vertex AI usage** | Implicitly management-backed — Bill requested "shortest path to RFE grading report" (2026-06-17). Recommend establishing a cost baseline with the first run. | Management |

### Can Resolve During Implementation

| Item | Status |
|------|--------|
| Jira API token scope — does current bot token cover target projects? | Check during onboarding |
| Results storage — shared data repo or separate per team | Decide during Phase 1 |
| Assessment frequency — nightly vs weekly | Configure per team preference |

---

## Relationship to Org Pulse Deployment

The RFE Assessor is an **add-on capability** to the core Org Pulse deployment, not a prerequisite. The Org Pulse infrastructure work ([ENGPROD-10017](https://redhat.atlassian.net/browse/ENGPROD-10017)) is progressing independently:

- All app-interface onboarding MRs are merged
- Build pipeline (Konflux) is fully operational
- Credentials are provisioned (LDAP, Jira bot, GitHub PAT, OAuth)
- Stage deployment is next

The RFE Assessor work can begin in parallel with the remaining Org Pulse deployment tasks. The integration point is when both are ready — assessment data flows into Org Pulse once the dashboard is live and the AI Impact module question is resolved.

---

## Recommendation

We recommend proceeding with this work in two steps:

1. **Now:** Identify target Jira projects and confirm Vertex AI budget. These are the remaining decisions that unblock implementation.
2. **Once confirmed:** Execute the ~4-5 day implementation plan to bring the first team online. The pipeline work and the Org Pulse AI Impact module integration can run in parallel. Use the first team as a pilot to establish cost baselines, validate the scoring rubric for HP-style RFEs, and gather feedback before expanding to additional teams.

The technical work is well-scoped and low-risk — we are parameterizing and extending existing, proven systems rather than building from scratch. The AI Impact module is self-contained and already works in the RHEL AI instance; we are porting it into our fork. The main remaining variables are organizational: which teams and which Jira projects to target.

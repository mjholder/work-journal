---
type: project
status: active
tags:
  - project
  - dashboard
  - org-pulse
  - openshift
  - deployment
created: '2026-05-27'
---
# Project: RHAI Org Pulse Deployment

## Overview

Stand up an instance of [RHAI Org Pulse](https://github.com/red-hat-data-services/rhai-org-pulse) for our org. Org Pulse is a modular engineering dashboard that connects Jira, GitHub, and GitLab data with your team roster to surface delivery insights — sprint metrics, contribution tracking, and team visibility.

**Scope TBD** — unclear yet whether this is a single org instance, multi-team, or something broader.

### Key Links

- **Live reference instance**: [red.ht/rhai-org-pulse](https://red.ht/rhai-org-pulse) → `team-tracker.apps.int.spoke.prod.us-west-2.aws.paas.redhat.com`
- **Source**: [red-hat-data-services/rhai-org-pulse](https://github.com/red-hat-data-services/rhai-org-pulse)
- **Skills Registry**: [opendatahub-io/skills-registry](https://github.com/opendatahub-io/skills-registry) — AI plugin marketplace, possibly related tooling
- **Agentic CI**: [redhat/rhel-ai/agentic-ci](https://gitlab.com/redhat/rhel-ai/agentic-ci) — private GitLab repo, role TBD

### Tech Stack

- **Frontend**: Vue 3, Vite 6, Tailwind CSS 3, Chart.js 4
- **Backend**: Express.js
- **Auth**: OpenShift OAuth proxy (production), no auth (local dev)
- **Storage**: Filesystem (`./data/`) locally, PVCs on OpenShift
- **Deployment**: OpenShift via ArgoCD, also supports Kind for local k8s testing
- **Demo mode**: `DEMO_MODE=true` runs with sample data, zero credentials needed

### Data Sources

| Source | Purpose | Credential |
|--------|---------|------------|
| Jira | Sprint metrics, issue tracking | API token + email |
| GitHub | Contribution stats | Classic PAT (`read:user`) |
| LDAP | Org tree sync (team discovery) | Red Hat VPN required |
| Google Sheets | Roster management | Google Service Account key |

## Performance Goal

> **Develop a deployment plan for RHAI Org Pulse to enable engineering delivery visibility**

- **Specific:** Research and produce a deployment plan for RHAI Org Pulse that identifies scope (teams/orgs to include), data source configuration (Jira projects, GitHub orgs, LDAP org roots, roster sheet), and a phased rollout timeline. Coordinate with other teams already exploring Org Pulse and with App-SRE on infrastructure provisioning (OpenShift namespace, ArgoCD, cluster resources). Includes hands-on evaluation via demo mode.
- **Measurable:**
  - Deployment plan document delivered and reviewed with manager
  - Open questions resolved — scope, stakeholders, data sources
  - Infrastructure needs documented and handed off to / coordinated with App-SRE
  - Other teams working on Org Pulse identified and alignment established
  - Demo mode evaluated locally with findings documented
  - Required access and credentials identified (including GitLab agentic-ci repo)
- **Achievable:** Reference instance and comprehensive deployment docs already exist. Demo mode enables evaluation without credentials. Initial research and project entry already complete.
- **Relevant:** Lays the groundwork for org-wide engineering delivery visibility — reduces manual reporting, surfaces sprint metrics and contribution patterns for leadership decision-making.
- **Timely:** Plan delivered by 2026-06-03.

## Current Status

**Phase: Stage Live (Phase 2)**

**Stage deployment is up and running** (confirmed 2026-06-17) with data flowing from Jira, LDAP, and GitHub. Infrastructure provisioning is complete.

- Deployment plan written and under review ([[rhai-org-pulse-deployment-plan]])
- Epic restructured: ENGPROD-10017 now scoped to infrastructure, parented under PLATENG-108 (Feature) → HPSTRAT-2 (Outcome: Foundation for Agentic SDLC)
- Repo forked to [RedHatInsights/rhai-org-pulse](https://github.com/RedHatInsights/rhai-org-pulse)
- Konflux **fully onboarded** — MR [!18472](https://gitlab.cee.redhat.com/releng/konflux-release-data/-/merge_requests/18472) merged, `.tekton/` pipelines configured, images building and publishing to [quay.io](https://quay.io/repository/redhat-services-prod/hcm-eng-prod-tenant/rhai-org-pulse-backend?tab=tags)
- LDAP bind account **received** — credentials stored in Vault at `engineering-productivity/hp-org-pulse/LDAP`
- Jira bot account **provisioned** via [JIRACONFSD-8589](https://redhat.atlassian.net/servicedesk/customer/portal/67/JIRACONFSD-8589) — ready for use
- **OpenShift deploy templates merged** — [PR #797](https://github.com/red-hat-data-services/rhai-org-pulse/pull/797) merged (2026-06-03). Adds `deploy/templates/backend.yaml` and `deploy/templates/frontend.yaml` for app-interface SaaS file consumption. Unblocks the SaaS file template path in app-interface MR !190339. **Note**: templates will need revision after PR #820 (core split) to drop AI Eng-specific secrets.
- **Deploy templates smoke-tested in ephemeral** (2026-06-03) — both pods running, routes working, OAuth flow functional. Found template memory ratio fix needed (256Mi/512Mi). Module portability gaps documented.
- **Upstream core split MERGED** (2026-06-05) — PR [#820](https://github.com/red-hat-data-services/rhai-org-pulse/pull/820) merged. Images split into core (platform + team-tracker) and AI Eng layers. Every non-portable module (System Health, Product Builds, Release Registry, Upstream Pulse) is in the AI Eng layer — **core is exactly what HP needs**. Decision: deploy core images only. New Dockerfile paths: `deploy/core.backend.Dockerfile`, `deploy/core.frontend.Dockerfile`. Simplifies secrets, removes google-sa-key dependency, and eliminates module portability concerns.
- **Deploy template revision**: [RedHatInsights#27](https://github.com/RedHatInsights/rhai-org-pulse/pull/27) — splits `team-tracker-secrets` into individual secrets (`jira-api-token`, `github-token`, `gitlab-token`), removes AI Eng secrets/volumes/CronJob steps, fixes memory default.
- **Core split action items complete** (2026-06-06): RedHatInsights fork rebased with upstream core split, Konflux `dockerfileUrl` paths updated to `deploy/core.backend.Dockerfile` / `deploy/core.frontend.Dockerfile`
- **GitLab deferred** (2026-06-05) — stakeholder confirmed GitLab not needed for initial rollout. All pilot teams use GitHub; some are actively migrating to GitHub. Can revisit GitLab integration later.
- **App-interface MR split** (2026-06-10) — MR !190339 split into two phases to fix 403 RBAC error. CI integration tests failed because the app-sre SA couldn't access secrets in a namespace that didn't exist yet (chicken-and-egg). MR 1 now provisions bare namespace + RBAC only. MR 2 (`onboard-hp-org-pulse-resources` branch) adds vault-secrets, OAuthClient, and route once namespace is provisioned on the cluster.
- **OAuth client secret fixed** (2026-06-10) — vault reference was pointing to non-existent `stage-oauth-client` path; corrected to use existing `proxy-auth-secret` at `engineering-productivity/hp-org-pulse/stage/proxy-auth-secret`.
- Still need: open questions on scope (Jira projects, GitHub orgs)

## Research & Open Questions

- [ ] What is the exact scope? Our org only, or multiple orgs?
- [x] Who is the stakeholder/sponsor for this request? — **Answered**: Stephen Cuppett. Initiative rolls up to HPSTRAT-2 (Foundation for Agentic SDLC) via PLATENG-108.
- [ ] Which Jira projects and GitHub orgs need to be connected?
- [ ] Do we have an OpenShift namespace/project allocated for this?
- Target clusters: `appsres09ue1` (stage) and `appsrep09ue1` (prod) — same App-SRE clusters where InScope runs. Must be behind VPN (required for LDAP access too).
- [ ] What does the agentic-ci GitLab repo contribute to this effort?
- [ ] How does the skills-registry tie in — is it a dependency or separate initiative?
- [ ] Do we need customization beyond the stock dashboard, or vanilla deployment?
- [ ] Who are the "org roots" (manager UIDs) for LDAP roster sync?
- [ ] Is there an existing Google Sheet for our team roster, or do we create one?
- [x] ArgoCD setup — **Answered**: Not needed separately; app-interface handles deployments. RHEL AI uses Kustomize + ArgoCD, but we go through app-interface.
- [x] LDAP service account — **Done** (2026-06-01). Credentials received and stored in Vault at `engineering-productivity/hp-org-pulse/LDAP`.
- [ ] Google Sheets may not be needed initially — app has an "in-app" mode for team assignments that skips Sheets entirely
- [x] Credential ownership — **Documented** in [[rhai-org-pulse-deployment-plan]] Appendix A. All service/bot accounts with step-by-step provisioning per credential. LDAP done, Jira bot in progress, GitHub PAT pending Matt K, OAuth SSO client via `qontract-cli`.
- [ ] Optional modules — app has modular integrations beyond core (Jira/GitHub/LDAP). Decisions needed:
  - **GitLab** — **deferred**. Stakeholder confirmed not needed for initial rollout (2026-06-05). All pilot teams on GitHub, some migrating to GitHub. Revisit later.
  - **Release Analysis** — potentially useful for velocity tracking, but need to understand how it handles multiple Jira projects (HP has several).
  - **Upstream Pulse API** — unknown. Appears to be a separate service RHEL AI runs alongside Org Pulse. Need to ask them what it provides and whether we need it.
  - **SmartSheet** — probably not needed, unfamiliar tool. Investigate if HP uses it.
  - **Product Pages** — TBD, likely not needed initially.
  - **RESOLVED by upstream core split** (PR #820, merging week of 2026-06-06): All non-portable modules moved to the AI Eng layer. We deploy core images only, which contain team-tracker (Jira, GitHub, GitLab, LDAP roster). No module portability concerns remain for the core deployment.
  - **System Health** — AI Eng layer only. NOT portable (127 hardcoded RHOAI repos). See [[Org Pulse System Health Module - Hardcoded for RHOAI]].
  - **Product Pages** — AI Eng layer only. Needs separate OAuth credentials.
  - **Product Builds** — AI Eng layer only. Needs separate API base URL.
  - **Release Registry** — AI Eng layer only. Hardcoded RHOAI Jira projects. See [[Release Registry Jira Projects Config Gap]].
  - **Upstream Pulse** — AI Eng layer only. Standalone app, separate deployment.
  - **Roster/Team Setup** — Part of core. No integration with `hybrid-platforms/org` GitLab repo. Will need manual in-app team configuration initially. Google Sheets is an option later if manual doesn't scale.
- [x] Which other teams are already exploring Org Pulse? → **RHEL AI team** is already using it (reach out on Slack)
- **Internal resources**: Matt K and Chris onboarded the Ambient Code Platform project (also Kustomize + ArgoCD upstream → app-interface). Same pattern — good resource for the Kustomize-to-app-interface translation and Konflux onboarding process.
- [ ] What does App-SRE need from us to provision cluster resources?
- [ ] Request access to GitLab `redhat/rhel-ai/agentic-ci` repo
- [x] **Repo ownership & build strategy** — DECIDED: Fork to **RedHatInsights** org (same pattern other team members used for another RH project), onboard fork to Konflux. Two components (frontend + backend). Periodically sync upstream from RHEL AI's repo. This keeps HP build compliance without imposing on RHEL AI's workflow.

## Deployment Footprint

Compared to Ambient Code Platform (RDS + S3 + multiple AWS resources), Org Pulse has a minimal infrastructure footprint:

| Resource | Details |
|----------|---------|
| **Deployments** | 2 — frontend (nginx + OAuth proxy sidecar), backend (Express.js) |
| **PVC** | 1 — filesystem-based data cache (`./data/`), no database needed |
| **Secrets** | Jira API token, GitHub PAT, LDAP bind credentials, OAuth cookie secret, plus optional module tokens (GitLab, etc.) |
| **Service + Route** | Standard OpenShift networking, TLS reencrypt through OAuth proxy on port 4180 |
| **AWS resources** | None — no RDS, S3, or Terraform needed |
| **OAuth proxy** | Sidecar container in the frontend pod (not a separate deployment) |

This simplifies app-interface onboarding significantly — no AWS resource definitions, no Terraform, no cross-account IAM. Primarily just namespace definitions, SaaS file, and secret management.

## App-Interface Onboarding Blueprint (from Ambient Code Platform)

The Ambient Code Platform project (same team, same clusters) provides a direct template for onboarding. Key patterns:

**Repo strategy**: Keep Kustomize in the repo for dev/direct deployment, but create OpenShift templates specifically for app-interface's SaaS file consumption. Both coexist.

**App-interface structure needed:**
```
data/services/org-pulse/
├── app.yml                          # service registration
├── cicd/
│   └── saas.yaml                    # SaaS file → OpenShift templates
├── namespaces/
│   ├── org-pulse.appsres09ue1.yml   # stage namespace
│   ├── org-pulse.appsrep09ue1.yml   # prod namespace
│   └── org-pulse-pipelines.appsrep09ue1.yml  # Konflux pipelines
├── pipelines/
│   └── tekton.org-pulse-pipelines.appsrep09ue1.yml
└── (routes, vault policies, monitoring, etc.)
```

**Konflux setup**: `.tekton/` directory in the forked repo with push + pull-request pipelines per component. Org Pulse = 2 components (frontend + backend) = 4 pipeline files. Images publish to `quay.io/redhat-services-prod/hcm-eng-prod-tenant/`.

**Key difference from Ambient Code**: Org Pulse uses PVC storage, not RDS + S3. Simpler infrastructure — likely no Terraform/AWS resources needed.

**Resources to leverage**: Matt K and Chris built the Ambient Code onboarding. Same team (`hcm-pe-engineering-productivity`), same pipeline cluster (`appsrep09ue1`), same target clusters.

## Deployment Plan (Draft)

### Phase 1: Local Exploration
- [ ] Clone the repo and run in demo mode (`DEMO_MODE=true`)
- [ ] Explore the UI and understand what metrics are surfaced
- [ ] Review `deploy/OPENSHIFT.md` and `deploy/KIND.md` docs
- [ ] Review `AGENTS.md` and `.claude/CLAUDE.md` for contributor guidance

### Phase 2: Configuration
- [ ] Determine org roots for LDAP sync
- [ ] Set up Jira API token for target projects
- [ ] Create GitHub PAT for target orgs
- [ ] Set up Google Service Account and roster sheet
- [ ] Document all required secrets

### Phase 3: Deployment
- [ ] Provision OpenShift namespace
- [ ] Set up ArgoCD application
- [ ] Configure OAuth proxy
- [ ] Deploy and validate with real data
- [ ] Set up PVCs for persistent storage

### Phase 4: Rollout
- [ ] Share with stakeholders for feedback
- [ ] Onboard teams (configure roster, connect data sources)
- [ ] Document runbook for ongoing maintenance

## Recent Progress

### 2026-06-12
- **All onboarding MRs merged** — PT1 (foundation), PT2 (namespace resources), PT3 (CI/CD) all on master. Infrastructure fully provisioned.
- **Naming mismatches discovered** — Route targeted wrong service name (`org-pulse-frontend` vs template's `team-tracker`) and wrong port (`oauth-proxy` vs `proxy`). Would have prevented traffic from reaching the app.
- **OAuth approach decision** — Template used SA-based OAuth (`--openshift-service-account`), but app-interface created explicit OAuthClient `org-pulse-stage`. Decision: favor app-interface's prescribed OAuthClient pattern for explicit control over redirect URIs, grant methods, and scope restrictions.
- **Frontend template PR** — [RedHatInsights#35](https://github.com/RedHatInsights/rhai-org-pulse/pull/35) switches oauth-proxy from `--openshift-service-account` to `--client-id=org-pulse-stage` + `--client-secret-file`. Adds `proxy-auth-secret` volume mount.
- **App-interface enable-stage MR created** — fixes route naming, adds `proxy-auth-secret` vault-secret, removes `disable: true` from stage SaaS targets. Depends on PR #35 merging first.

### 2026-06-11
- **GitHub bot PAT provisioned** — DevProdBot account recovered, Classic PAT (`read:user` scope) generated and stored in Vault at `engineering-productivity/hp-org-pulse/github-token`
- **App-interface MR 1 merged** — bare namespace + RBAC now provisioned on cluster. MR 2 (`onboard-hp-org-pulse-resources`) needs merge conflict resolution and CI re-check before submitting.

### 2026-06-10
- **Fixed OAuth client secret vault path** — OAuthClient resource was referencing non-existent `engineering-productivity/hp-org-pulse/stage-oauth-client`; corrected to use existing `engineering-productivity/hp-org-pulse/stage/proxy-auth-secret` (field: `secret`)
- **Split app-interface MR !190339 into two phases** to resolve 403 RBAC error. CI integration tests failed because the app-sre SA couldn't manage secrets in a namespace that didn't exist yet. MR 1 now creates bare namespace + RBAC (no vault-secrets). MR 2 (`onboard-hp-org-pulse-resources` branch) adds openshiftResources (vault-secrets, OAuthClient, route, resource-owner self-service) once namespace is provisioned.
- Both branches pushed. MR 2 needs to be created via GitLab web UI (glab token expired).

### 2026-06-05
- **PR #820 (core split) merged upstream** — new Dockerfile paths: `deploy/core.backend.Dockerfile`, `deploy/core.frontend.Dockerfile`. Also adds `ai-eng.*` and `core.frontend-builder/runtime` Dockerfiles.
- **GitLab deferred for initial rollout** — stakeholder confirmed all pilot teams are on GitHub (some actively migrating from GitLab). Removes GitLab token provisioning from critical path.
- Fork rebase in progress (separate session) — needed before Konflux `dockerfileUrl` paths can be updated.

### 2026-06-01
- **OpenShift deploy templates**: Created two parameterized OpenShift Templates (`deploy/templates/backend.yaml`, `deploy/templates/frontend.yaml`) for app-interface SaaS file consumption. Backend template: ConfigMap, Deployment, Service, Route, PVC, CronJob (20 parameters). Frontend template: ServiceAccount, Deployment (oauth-proxy + nginx), Service, Route (15 parameters). Secrets referenced by name only — app-interface vault-secret reconciler creates them. Appcode `HPOP-0001`. [PR #797](https://github.com/red-hat-data-services/rhai-org-pulse/pull/797) opened upstream.
- **App-interface onboarding MR submitted**: [!190339](https://gitlab.cee.redhat.com/service/app-interface/-/merge_requests/190339) — 10 new files + 1 modified. Service registration (`app.yml`), stage namespace on `appsres09ue1`, pipelines namespace on `appsrep09ue1`, SaaS file (template path TBD), OAuthClient + Route resources, vault-secret refs for LDAP and cookie secret, team role access updates. Prod namespace and S3 backup deferred to follow-up MR.
- Refined epic ENGPROD-10017 — tightened scope to infrastructure focus per Bill Montgomery's feedback after PLATENG-108 (Feature) was created
- Fleshed out PLATENG-108 description — vision, strategic alignment to HPSTRAT-2, three workstream descriptions (infra deployment, stakeholder rollout, HP team onboarding)
- Jira bot account unblocked — Google Group `hcm-pe-engineering-productivity@redhat.com` posting permissions updated, request back with Jira team
- Konflux MR !18472 reviewed by Jacopo — fixed missing autogenerated files (rhai-org-pulse entry wasn't in kustomize.yaml), awaiting re-review
- LDAP bind credentials received from IT — stored in Vault at `engineering-productivity/hp-org-pulse/LDAP`
- Documented OAuth SSO client procedure in deployment plan (A.5.1) — uses `qontract-cli sso-client create` against `auth.redhat.com`
- Generated OAuth cookie secret and stored in Vault
- Standardized all Vault paths in deployment plan to `engineering-productivity/hp-org-pulse/`
- Ran Org Pulse locally in demo mode

### 2026-05-28–29
- Wrote comprehensive deployment plan ([[rhai-org-pulse-deployment-plan]]) — architecture, credentials, build pipeline, app-interface blueprint, phased rollout, secret provisioning appendix
- Matt K forked repo to RedHatInsights org
- Submitted LDAP bind account request via ServiceNow
- Submitted Jira bot account request via JIRACONFSD-8589
- Created Konflux tenant config and ReleasePlanAdmission for 2 components (frontend + backend)
- Submitted Konflux MR [!18472](https://gitlab.cee.redhat.com/releng/konflux-release-data/-/merge_requests/18472)

### 2026-05-27
- Project initiated — researched org-pulse repo, skills-registry, and agentic-ci (private, 403)
- Discovered existing live instance at `red.ht/rhai-org-pulse`
- Documented tech stack, data sources, and deployment options
- Created initial open questions list and phased deployment plan
- Created Jira epic [ENGPROD-10017](https://redhat.atlassian.net/browse/ENGPROD-10017) and story [ENGPROD-10020](https://redhat.atlassian.net/browse/ENGPROD-10020)

## Jira Tickets

### Hierarchy

- [HPSTRAT-2](https://redhat.atlassian.net/browse/HPSTRAT-2) (Outcome: Foundation for Agentic SDLC)
  - [PLATENG-108](https://redhat.atlassian.net/browse/PLATENG-108) (Feature: RHAI Org Pulse for HP)
    - [ENGPROD-10017](https://redhat.atlassian.net/browse/ENGPROD-10017) (Epic: Infrastructure Deployment) — **In Progress**
    - [ENGPROD-10097](https://redhat.atlassian.net/browse/ENGPROD-10097) (Epic: RFE Quality Assessment Pipeline) — **New**
    - Future Epic: Stakeholder Rollout
    - Future Epic: HP Team Onboarding

### Epic: [ENGPROD-10017](https://redhat.atlassian.net/browse/ENGPROD-10017) — Deploy RHAI Org Pulse infrastructure for Hybrid Platforms

**Project**: ENGPROD | **Type**: Epic | **Priority**: Major | **Assignee**: Matt Holder | **Target**: Q3 2026

Infrastructure-scoped epic covering build pipeline (Konflux), OpenShift provisioning (app-interface), credential provisioning, data source configuration, and stage/production deployment. Stakeholder rollout and HP team onboarding are future epics under PLATENG-108.

**Acceptance Criteria**:
- [x] Org Pulse fork onboarded to Konflux with images building and publishing to quay.io — **Done** (2026-06-02)
- [ ] App-interface MR merged: namespaces, SaaS file, vault-secret references
- [ ] All required credentials provisioned and stored in Vault
- [ ] Stage deployment live on appsres09ue1 with data sources connected
- [ ] Production deployment live on appsrep09ue1 and accessible via OAuth
- [ ] Deployment runbook documented

---

### Story: [ENGPROD-10020](https://redhat.atlassian.net/browse/ENGPROD-10020) — Create Org Pulse deployment plan for Hybrid Platforms

**Project**: ENGPROD | **Type**: Story | **Priority**: Major | **Assignee**: Matt Holder | **Due**: 2026-06-03 | **Size**: Medium (1-2 days)

**User Story**

**As a** Hybrid Platforms engineering lead,
**I want** a deployment plan for RHAI Org Pulse covering scope, infrastructure, data sources, and rollout timeline,
**so that** we can confidently provision and configure the dashboard for HP teams with clear requirements for all stakeholders.

**Context / Background**
First deliverable for the Org Pulse epic. The RHEL AI team is already running Org Pulse — we can learn from their deployment. App-SRE will likely be involved in cluster resource provisioning but service lifecycle ownership may stay with us. Performance goal tied to this deliverable: plan delivered by June 3.

**Requirements**
- Evaluate Org Pulse locally via demo mode and document findings (UI, metrics surfaced, configuration options)
- Identify all HP Jira projects and GitHub orgs to connect
- Determine LDAP org roots for HP team roster sync
- Document infrastructure requirements and coordinate with App-SRE
- Connect with RHEL AI team on Slack for their deployment experience and lessons learned
- Produce a written deployment plan reviewed with manager

**Technical Approach**
1. Clone org-pulse repo, run in demo mode (`DEMO_MODE=true`), explore metrics and UI
2. Review `deploy/OPENSHIFT.md` and `deploy/KIND.md` deployment docs
3. Reach out to RHEL AI team on Slack for their setup experience
4. Identify HP-specific data sources (Jira projects, GitHub orgs, LDAP roots)
5. Document infrastructure needs for App-SRE coordination
6. Write deployment plan and review with manager

**Dependencies**
- Access to GitLab `redhat/rhel-ai/agentic-ci` (requested)
- RHEL AI team availability on Slack
- Clarity on which HP Jira projects and GitHub orgs are in scope

**Additional Context**
- Demo mode requires zero credentials — good starting point
- Live reference instance at [red.ht/rhai-org-pulse](https://red.ht/rhai-org-pulse)
- Source repo: [red-hat-data-services/rhai-org-pulse](https://github.com/red-hat-data-services/rhai-org-pulse)

**Acceptance Criteria**
- [ ] Demo mode evaluated locally with findings documented
- [ ] RHEL AI team contacted and lessons learned captured
- [ ] Infrastructure needs documented and shared with App-SRE
- [ ] Deployment plan document delivered and reviewed with manager
- [ ] Open questions resolved — scope, stakeholders, data sources

## RFE Assessor — Multi-Team Path

### Context

The [rfe-assessor](https://gitlab.com/redhat/rhel-ai/agentic-ci/rfe-assessor) pipeline already pushes assessment data to org-pulse via `push-to-org-pulse.py`. Today it's hardcoded to `RHAIRFE-*` only. Extending RFE metrics to other HP teams requires parameterizing the assessor — not changing org-pulse itself. See [[rfe-assessor-multi-team]] for the full implementation plan.

### What's Hardcoded (only 3 files)

| File | What | Impact |
|------|------|--------|
| `.gitlab-ci.yml` | `RHAIRFE-*` in `CLAUDE_PROMPT`, RHAI results repo, RHAI dashboard trigger | Must parameterize |
| `scripts/push-results.py` | `RHAIRFE` directory path (4 refs), commit message | Must parameterize |
| `scripts/push-to-org-pulse.py` | `RHAIRFE/current` path (3 refs) | Must parameterize |

Everything else (setup, run-claude, streaming, OTEL, clone-data-repo) is already team-agnostic.

### Approach: Parameterize, Not Fork

Add a `JIRA_PREFIX` CI variable (default `RHAIRFE`) and thread it through all 3 files. Per-team CI job blocks override `JIRA_PREFIX`, `RESULTS_REPO`, and optionally `JIRA_TOKEN`. Core refactoring is ~20 lines of changes.

### Open Questions

- [ ] **assess-rfe plugin** (`n1hility/assess-rfe.git`) — receives prefix as CLI arg, probably team-agnostic, but needs inspection to confirm
- [ ] **Org-pulse API contract** — does the bulk endpoint (`/api/modules/ai-impact/assessments/bulk`) auto-route by Jira prefix, or does it need an explicit team identifier in the payload?
- [ ] **Jira auth scope** — does the current `JIRA_API_TOKEN` have access to other teams' RFE projects, or do they need separate service accounts?
- [ ] **Do pilot teams have RFE Jira projects?** — the assessment model assumes a dedicated RFE project with a consistent prefix pattern (e.g., `HPRFE-*`)
- [ ] **Runner capacity / cost** — each assessment run uses Claude for 4-6 hours. N teams = Nx compute and API cost. Runs should be staggered.

### Estimated Effort

| Work Item | Effort |
|-----------|--------|
| Parameterize `RHAIRFE` in 3 files | 0.5 days |
| Per-team CI job blocks | 1 day |
| Inspect assess-rfe plugin | 0.5 days |
| Org-pulse API contract check | 0.5 days |
| Per-team Jira auth setup | 0.5 days/team |
| **Total for first new team** | **~3 days** |

### Decision Needed

Before starting implementation: confirm which pilot teams actually have RFE-style Jira projects, and whether RFE quality assessment is relevant to their workflow. The scoring model (What/Why/How/Task/Size) is generic, but teams need to be writing RFEs for it to have anything to assess.

## Notes

- The project has a demo mode which is great for initial exploration without needing any credentials
- LDAP roster sync requires Red Hat VPN — consider implications for CI/CD and automated sync
- The skills-registry appears to be a separate AI tooling initiative — may be bundled in the same ask or just shared context

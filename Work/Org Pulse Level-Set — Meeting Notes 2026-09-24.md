---
type: note
tags:
  - meeting
  - org-pulse
  - architecture
  - prep
created: 2026-09-24
status: prep
---
# Org Pulse Level-Set — Meeting Notes (2026-09-24)

**Purpose:** high-level engineering level-set for John + [requester] joining the OrgPulse conversation. They're meeting SAGE beforehand about constraints. Cuppett wants fast movement. Eliad + Katie optional.

**Their actual ask, in their words:** *"where things sit / what we know about constraints"* → then *"where to most effectively plug-in to the team organizing around OrgPulse without getting in the way."*

So: level-set, constraints, then land on concrete plug-in points. Don't over-rotate on implementation detail.

---

## 1. The 30-second version

Org Pulse is a modular engineering dashboard — Jira + GitHub + GitLab data joined against an LDAP-derived team roster, surfacing delivery metrics. Built by the RHEL AI (RHAI) team; we stood up an HP instance.

**Status: production is live** (since 2026-08-03) on `appsrep09ue1`, stage on `appsres09ue1`, with scored RFEs populating the dashboard. Infrastructure, credentials, build pipeline, and OAuth are all done and working.

The live work is no longer "stand it up." It's three things: (a) migrating to a new repo and re-syncing with upstream's re-architecture, (b) extending what the dashboard assesses, (c) retiring some deliberate workarounds.

**Jira spine:** HPSTRAT-2 (Outcome: Foundation for Agentic SDLC) → PLATENG-108 (Feature: RHAI Org Pulse for HP) → ENGPROD-* epics.

## 2. Lead with this: the fork is a bridge, not a destination

The most important framing for anyone new, because it governs where investment makes sense.

- We run a **hard fork** (decided 2026-08-03, Steve's staff). No merge-back upstream. The tool is explicitly *not expected to be permanent.*
- Upstream `org-pulse-core` is heading toward **multi-tenancy**, **hot-swappable modules**, and **modules as standalone repos** instead of a monorepo.
- When that lands, HP doesn't need a separate deployment and the effort folds back into the RHAI team.

**Consequence for the meeting:** effort spent hardening our fork has a short half-life. Anything net-new that we want to survive is better proposed *upstream* as a configurable option than maintained as a local patch. Good framing for "where do we plug in without getting in the way" — upstream contribution and net-new capability are the high-leverage lanes; fork maintenance is not.

## 3. Architecture at a glance

Two containers, no database. It is a genuinely small deployment.

| Layer | What |
|---|---|
| Frontend | Vue 3 / Vite 6 / Tailwind 3 / Chart.js 4, served by nginx |
| Auth | OpenShift OAuth proxy **sidecar** in the frontend pod (:4180), TLS reencrypt Route |
| Backend | Express.js API (:3000) |
| Storage | **PVC / filesystem cache** — no DB, no RDS |
| Build | Konflux / Tekton → `quay.io/redhat-services-prod/hcm-eng-prod-tenant/` |
| Deploy | **ArgoCD** via `openshift-online/hp-gitops-manifests` (migrated off app-interface SaaS files 2026-09-22) |
| Backup | Optional daily `/app/data` tarball → S3, 06:00 UTC, prod overlay only |

Footprint: 2 Deployments, 1 PVC, ~6 secrets, Service + Route. No Terraform, no cross-account IAM.

**Data sources:** Jira (sprint metrics, RFEs) · GitHub (contributions, classic PAT `read:user`) · LDAP/IPA (org tree → roster) · GitLab (**deferred** — pilot teams are all on GitHub) · Google Sheets (optional; in-app roster mode used instead).

**Core vs AI Eng layering:** upstream split the images (PR #820). We deploy **core only** — platform shell + team-tracker. Every module we found non-portable (System Health hardcodes 127 RHOAI repos; Release Registry hardcodes RHOAI Jira projects; Product Builds, Product Pages, Upstream Pulse) lives in the AI Eng layer. Going forward we're taking `ai-impact` (+ its `releases` dependency) and nothing else from the upstream-only set.

**Our one custom module:** `jira-solve-agent`.

## 4. Constraints — the part they asked for

Rough order of how much they actually bind.

1. **Network / cross-boundary reachability — the big one.** The `rfe-assessor` EC2 runners **cannot reach the Org Pulse API directly**; cross-TGW traffic is blocked by on-prem firewall default-deny. Current production path is a **relay**: assess jobs stage results as CI artifacts in `relay-payload/`, and downstream IT-runner jobs pick them up and run `push-to-org-pulse.py`. It works and is reliable, but it's a deliberate workaround. **AWS PrivateLink is the intended long-term replacement** — currently tabled. If SAGE is where network constraints get decided, *this is the item to put in front of them.*
2. **LDAP requires Red Hat VPN.** Roster sync needs cluster→`ldap.rdu.redhat.com` reachability, which pins us to VPN-reachable clusters. Both target clusters qualify; it constrains any future move.
3. **Filesystem/PVC storage, no database.** Fine at current scale and cheap to operate, but it's the ceiling on horizontal scaling, multi-writer, and any real query/history story. Recovery path is the S3 tarball.
4. **Auth is coarse.** OpenShift OAuth proxy in front of the whole app — authentication, not fine-grained authorization. No per-team data scoping. Matters the moment the audience widens beyond engineering.
5. **Credential lifecycle.** Jira tokens expire every **90 days**; GitHub/GitLab max 1 year. All secrets in Vault under `engineering-productivity/hp-org-pulse/`. Known bus-factor: the Jira bot's 2FA lives on my authenticator with a recovery code in Vault. Rotation is manual and unalerted. *(A revoked Jira bot token already broke CVE Triage counts once — Sep 21.)*
6. **Upstream coupling / re-architecture debt.** Our fork predates the `org-pulse-core` split and still carries defunct monorepo files. Reconciliation is in flight (below).
7. **Konflux is per-repo.** Moving repos means full re-onboarding — new tenant config, new quay repos, a `konflux-release-data` MR. Not a file copy.
8. **Scope is still genuinely open.** Which HP Jira projects and GitHub orgs are in scope has never been fully nailed down. Same for the LDAP org roots (derivable from the `hybrid-platforms/org` GitLab repo). This is a leadership-input gap, not an engineering one — good thing to get from this group.

## 5. What's in flight right now

**A. Repo migration + upstream reconciliation** — `ENGPROD-10380`, the main active workstream. See [[org-pulse-fork-reconciliation]].

- Moving from `RedHatInsights/rhai-org-pulse` → **`openshift-online/hp-org-pulse`** (private; not a GitHub fork, no parent link).
- Approach: **copy-paste**, not a git merge. No shared history, so no sync path — future core updates arrive as `@org-pulse/core` npm bumps.
- Old repo is winding down: closing/merging open PRs, pausing new ones, so the new repo is the sole work location. Losing history is accepted.
- Five phases: rebase (done) → port infra (.tekton, renovate) → port `jira-solve-agent` → validate → UI changes. Jacopo's estimates are Low/Low-Moderate/Low/Moderate — **but Konflux re-onboarding isn't in those numbers.**
- ⚠️ **The epic is still `New` and unassigned.** Flag this — it's the tracking vehicle for all migration work and it has no owner.

**B. RFE quality assessment** (`ENGPROD-10097`) — the pressing business priority per Steve's staff, aligning with field teams who submit RFEs. Scoring rubric lives in the `assess-rfe` Claude Code skill baked into a shared sandbox image; we customize by forking and pointing `--image` at our own build. Extending to more HP teams means parameterizing the assessor's hardcoded `RHAIRFE-*` prefix (3 files, ~3 days for the first new team) — see [[rfe-assessor-multi-team]].

**C. PM-requested skill integrations** (Daniel Messer) — Productization Decision Maker (`ENGPROD-10304`, spike in progress) and Jira Status (`ENGPROD-10305`). See [[org-pulse-productization-decision]].

## 6. Where they could plug in

Ranked by leverage, with the ones that don't collide with in-flight work first.

- **PrivateLink / network path** — highest value, cleanly separable, and it's exactly the SAGE-adjacent question they're already chasing. Retiring the relay is a real win nobody is currently working.
- **Own `ENGPROD-10380`** or a slice of it. It's unowned. Konflux re-onboarding for the new repo is a self-contained chunk.
- **Upstream contribution** — Phase 5 homepage/UI changes are better landed in `org-pulse-core` as configuration than patched locally. Someone pushing that upstream helps us *and* survives the bridge.
- **Scope definition** — which Jira projects, which GitHub orgs, which LDAP roots, who the audience is. This is blocking-ish and is leadership work, not engineering work.
- **Secret rotation / operational hardening** — unglamorous, currently manual, real bus-factor.

Where they'd most likely *get in the way*: the in-flight copy-paste migration, and the assess-rfe rubric (Jesse's review loop owns that).

## 7. Questions to ask them

- What constraints did SAGE actually surface? Does it touch the TGW/firewall path the relay works around?
- What is Cuppett's "fast movement" pointed at specifically — broader rollout, more teams, more use cases, or a particular demo?
- Do they know the long-term service ownership answer? Still open from day one: does lifecycle stay with us or transition?
- Are they aware the upstream multi-tenant/hot-swap direction may make a separate HP instance unnecessary? Changes the investment calculus.
- Who's John, and what's his lane?

## 8. Cast

- **Stephen Cuppett** — sponsor. HPSTRAT-2 rolls up to him.
- **Eliad Cohen** — brought John + requester into the conversation (after hours for him; optional attendee).
- **Jacopo Giola** — upstream/RHAI side, source of the reconciliation plan and estimates.
- **Daniel Messer** — PM, drove the two skill-integration epics.
- **Jesse** — running the RFE grading review loop.
- **Nick, Alberto** — contributors on the old repo's open PRs.
- **Matt K** — RedHatInsights org admin, GitHub bot/PAT.
- **Bill Montgomery** — shaped PLATENG-108 scoping.

---

## Related Notes

- [[rhai-org-pulse]] — umbrella project
- [[org-pulse-fork-reconciliation]] — the active migration workstream
- [[rhai-org-pulse-deployment-plan]] — full architecture, credentials, Appendix A secret provisioning
- [[org-pulse-productization-decision]] — PDM skill integration
- [[rfe-assessor-multi-team]] — extending RFE scoring to other teams

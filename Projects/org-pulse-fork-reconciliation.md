---
type: project
status: active
tags:
  - project
  - org-pulse
  - fork
  - reconciliation
  - hp-org-pulse
created: 2026-09-24
---
# Project: Org Pulse Fork/Upstream Reconciliation

Parent project: [[rhai-org-pulse]] · Jira: [ENGPROD-10380](https://redhat.atlassian.net/browse/ENGPROD-10380) (Epic · **New** · Major · **Unassigned** · updated 2026-09-23)

> **This is a bridge, not a destination.** See [Strategic context](#strategic-context--this-is-temporary) below — upstream core is heading toward multi-tenancy and hot-swappable modules, at which point this effort folds back into the RHAI team. Weigh effort on any given phase against that: pick-and-choose over polish.

## Strategic context — this is temporary

Upstream `org-pulse-core` will eventually support:

- **Multiple tenants** — so HP wouldn't need a separate deployment at all
- **Hot-swappable modules** — modules activated/deactivated per tenant rather than baked in
- **Modules as their own repos** — not part of a monorepo the way they are today

When that lands, this effort becomes part of the RHAI team's work again and HP's separate fork stops being necessary. That reframes the whole reconciliation: we're buying time until upstream catches up, not building a long-term home.

**Practical implications:**

- Don't over-invest in any phase. Manual and pick-and-choosey is the right posture (explicitly confirmed for the migration itself).
- Our fork-only module (`jira-solve-agent`) is a candidate to become its own repo under the future module model — worth keeping it cleanly separable rather than entangled with the platform.
- Phase 5 UI changes are better proposed upstream as configurable options than maintained as local patches, since local patches have no long-term home.
- Consistent with the 2026-08-03 hard-fork decision: "tool is not expected to be permanent."

## Overview

**TL;DR:** Reconcile our Org Pulse fork with the new architectural changes from upstream.

Our fork was created when Org Pulse was a monorepo — modules and shared code all lived in one tree. Upstream has since split the platform out into `org-pulse-core`, but our fork still carries the now-defunct monorepo files. We need to rebase the new upstream architecture into our repo and port our custom work (new modules, Tekton pipelines, Renovate config) on top of it.

Source: meeting with Jacopo Giola + deliberation with Claude.

## Repos

| Role | Repo | Notes |
|------|------|-------|
| **New HP home** | [openshift-online/hp-org-pulse](https://github.com/openshift-online/hp-org-pulse) | Private · default branch `main` · **not** a GitHub fork (no parent) · last push 2026-09-18 · only `main` exists, no open PRs |
| **Current fork** | [RedHatInsights/rhai-org-pulse](https://github.com/RedHatInsights/rhai-org-pulse) | Branches: `main`, `upstream-main`, + Mintmaker branches |
| **Upstream** | [red-hat-data-services/rhai-org-pulse](https://github.com/red-hat-data-services/rhai-org-pulse) | |
| **Core** | [red-hat-data-services/org-pulse-core](https://github.com/red-hat-data-services/org-pulse-core) | Latest release `v2.0.84` (as of 2026-09-24) |
| **Deploy manifests** | [openshift-online/hp-gitops-manifests](https://github.com/openshift-online/hp-gitops-manifests) | ArgoCD; replaced app-interface SaaS files (2026-09-22) |

### Environments

- **Stage**: [org-pulse-rhai-org-pulse-stage.apps.rosa.appsres09ue1.24ep.p3.openshiftapps.com](https://org-pulse-rhai-org-pulse-stage.apps.rosa.appsres09ue1.24ep.p3.openshiftapps.com/)
- **Prod**: [org-pulse-rhai-org-pulse-production.apps.rosa.appsrep09ue1.03r5.p3.openshiftapps.com](https://org-pulse-rhai-org-pulse-production.apps.rosa.appsrep09ue1.03r5.p3.openshiftapps.com)

### Migration approach (2026-09-24)

**Working plan: copy-paste the code into `hp-org-pulse`** — no git-level fork relationship. This matches the repo metadata: `hp-org-pulse` has no GitHub parent link, so there's no shared history to merge or rebase against.

Consequences to keep in mind:

- **No git sync path from upstream.** Future core updates arrive as `@org-pulse/core` npm version bumps, not `git merge upstream/main`. Consistent with the hard-fork decision (2026-08-03) and with Decision #1 below (pin core images to fixed tags).
- **Konflux/Tekton needs full re-onboarding** — confirmed. The `.tekton/` pipelines, quay image repos, and `konflux-release-data` tenant config all point at `RedHatInsights/rhai-org-pulse`, so `hp-org-pulse` needs a new component set, not a file copy. Tracked under ENGPROD-10380. **This makes Phase 2's "Low / just copy some files" estimate optimistic** — the original Konflux onboarding took an MR to `konflux-release-data` ([!18472](https://gitlab.cee.redhat.com/releng/konflux-release-data/-/merge_requests/18472)) plus review cycles.
- **Old-repo PRs are being wound down** — we're closing or merging everything open on `RedHatInsights/rhai-org-pulse` and pausing new ones, so the new repo becomes the sole place work happens. Anything not merged before the cutover is dropped, not migrated. See [[rhai-org-pulse]] (2026-09-17) for the list of open non-Konflux PRs.
- **The port itself is manual and pick-and-choosey** — deliberately. Not everything in the old tree is worth carrying forward, and this isn't a permanent home (see Strategic context above).
- **History and blame stay behind** — accepted. Not worth engineering around.

Still to confirm: does the copy-paste happen from `upstream-main` after Phases 2–3 land there, or do we seed `hp-org-pulse` from upstream first and port the fork-only work directly into the new repo?

## Working Branch

`upstream-main` on the fork is our build-off point for the current state of upstream `main`:
https://github.com/RedHatInsights/rhai-org-pulse/tree/upstream-main

## Fork-Only Modules

Custom modules implemented since forking — these need porting onto `upstream-main`:

1. **`jira-solve-agent`** — https://github.com/RedHatInsights/rhai-org-pulse/tree/main/modules/jira-solve-agent

## Action Plan

### Phase 1: "Rebase" — ✅ Done

Not really a rebase, since `upstream-main` already exists.

1. `npm install` on `upstream-main` so we pick up `@org-pulse/core` as a project dependency

### Phase 2: Port fork-only infra — Low effort as scoped, but see caveat

Mostly Tekton pipelines and Renovate config; Dockerfiles still TBD.

1. Copy the `.tekton/` pipeline directory into the root of `upstream-main`
2. Remove unusable GitHub workflows and Dependabot configuration
3. Copy `renovate.json` for Mintmaker

> ⚠️ **Estimate caveat (2026-09-24):** copying `.tekton/` files is Low effort, but because we're copy-pasting into a *new* repo, Konflux needs full re-onboarding — new tenant config, new quay image repos, and a `konflux-release-data` MR. That's a separate chunk of work under ENGPROD-10380, not covered by the Low estimate below.

**Deploy strategy (Jacopo):** we don't use the `deploy/openshift/` folder — our manifests live in `openshift-online/hp-gitops-manifests`. For now we can leave that folder as-is or remove it entirely, since it mainly contains overlays for the RHAI clusters that we can't use.

**Note (Claude):** the fork's OAuth template fixes (#68, #67, #56, etc.) are no longer needed — core's base already includes the OAuth proxy at v4.20 with correct configuration.

### Phase 3: Port fork-only modules — Low to Moderate effort

1. Copy `jira-solve-agent` into `modules/`
2. Update imports:

**Client-side (ES module imports) — no changes needed**

| File | Current import | Status |
|------|----------------|--------|
| `client/composables/useAgentData.js` | `import { apiRequest } from '@shared/client/services/api.js'` | Works as-is (barrel-exported) |
| `client/components/AgentContent.vue` | `import LoadingOverlay from '@shared/client/components/LoadingOverlay.vue'` | Works as-is (direct path) |

**Server-side (CommonJS requires) — relative paths must change**

| File | Current require | New require |
|------|-----------------|-------------|
| `server/index.js` | `require('../../../shared/server/jira')` | `require('@shared/server').jira` |
| `server/jira/fetcher.js` | `require('../../../../shared/server/jira')` | `require('@shared/server').jira` |
| `__tests__/server/refresh.test.js` | `require('../../../../shared/server/module-context')` | `require('@shared/server/module-context')` |
| `__tests__/server/index.test.js` | `require('../../../../shared/server/module-context')` | `require('@shared/server/module-context')` |

### Phase 4: Validate — Low effort

- `npm run test`
- `npm run lint`
- `make smoke-test`
- `npm run validate:modules` — **unclear what this actually does, needs investigation**
- Visual verification that our custom modules still load and work locally (compare against stage)

### Phase 5: UI changes — Moderate effort

PR [RedHatInsights#111](https://github.com/RedHatInsights/rhai-org-pulse/pull/111) changed the Org Pulse homepage by editing files directly in `src/`, which no longer exists. We need to either:

- re-add them as platform dynamic imports, if possible; or
- make the changes configurable and propose them upstream to `org-pulse-core`

Needs more research into how the homepage works now and what the new dynamic mechanisms allow.

## Decisions

| # | Decision | Context | Outcome |
|---|----------|---------|---------|
| 1 | Adopt upstream's layered Docker image strategy (core base → ai-eng extension), or keep monolithic Tekton-built images? | Upstream's `deploy/openshift/` overlays reference core's base remotely (`?ref=v2.0.79`). The fork currently keeps a local copy. Remote reference = image updates flow through core version bumps; local = manual sync, more control. | **Move to the simplified images RHAI uses now.** We'll need to pin `org-pulse-core` images to fixed tags rather than driving them with a build ARG — a build ARG is harder to manage with Mintmaker. |
| 2 | Which of the 4 upstream-only modules should the fork include: `ai-catalyst`, `customer-insights`, `okr-hub`, `pm-pipeline`? | All 4 are optional. `okr-hub` and `pm-pipeline` both depend on the `releases` module. | **Only `ai-impact`** from upstream, which also depends on `releases`. |

## Timeline Estimates (Jacopo)

Scale: **Low** = max 1 day, often less · **Moderate** = 2–5 days, looks easy on paper but depends on how much context research AI needs · **High** = 6+ days

| Phase | Estimate | Rationale |
|-------|----------|-----------|
| 1 — Rebase | Done | — |
| 2 — Port infra | Low | Literally copying some files and deleting a bunch of others |
| 3 — Port modules | Low to Moderate | Some easy wins, but unsure the import fixes are sufficient |
| 4 — Validate | Low | Run commands, have Claude fix failing tests, visually compare against stage |
| 5 — UI changes | Moderate | Need to understand the new homepage and whether dynamic mechanisms can replace code currently living in `org-pulse-core` |

## Open Questions

- [x] Does reconciliation migrate to `openshift-online/hp-org-pulse` via git, or otherwise? — **Answered (2026-09-24): copy-paste the code**, no git fork relationship. See Migration approach above.
- [ ] Copy-paste from `upstream-main` after Phases 2–3 land there, or seed `hp-org-pulse` from upstream and port fork-only work directly into the new repo?
- [x] Does `hp-org-pulse` need fresh Konflux onboarding? — **Yes** (2026-09-24). New tenant config + quay repos + `konflux-release-data` MR. Covered by ENGPROD-10380.
- [x] What happens to `RedHatInsights/rhai-org-pulse` after the move? — **Losing history is fine** (2026-09-24). Closing/merging open PRs and pausing new ones so the new repo is the sole work location.
- [ ] **ENGPROD-10380 is Unassigned** — needs an owner before migration tasks can be scheduled.
- [ ] Should `jira-solve-agent` be structured now to split cleanly into its own repo, anticipating the upstream module model?
- [ ] What does `npm run validate:modules` actually do?
- [ ] What to do with the Dockerfiles during the Phase 2 infra port?
- [ ] Remove `deploy/openshift/` entirely, or leave it in place as dead weight?
- [ ] Which `org-pulse-core` tag do we pin to? (latest release is `v2.0.84`; the plan references `v2.0.79`)
- [x] ENGPROD-10380 status conflict (Nick said close it 2026-09-15, Jacopo had 2 tasks in progress) — **Resolved 2026-09-24: the epic stays open** and is the tracking vehicle for the migration tasks. Still `New` and unassigned as of 2026-09-23.

## Related Notes

- [[rhai-org-pulse]] — parent project
- [[rhai-org-pulse-deployment-plan]]

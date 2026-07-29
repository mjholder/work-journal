---
date: '2026-06-03'
type: knowledge
tags:
  - org-pulse
  - system-health
  - config-gap
  - portability
---
# System Health Module — Hardcoded for RHOAI

## The Problem

The system-health module is entirely hardcoded for the RHOAI team. Unlike other modules that have backend APIs and configuration, this one has zero configurability — no settings UI, no backend endpoints, and no way to point it at different repos without editing source code.

## What It Does

Two views:

### Quality Analysis
- Displays quality scores and gap analysis for **127 repositories** across 15 GitHub orgs
- All repo data is statically defined in `modules/system-health/client/qualityReports.data.js` (~70KB)
- Pre-generated HTML reports are committed to `modules/system-health/client/generated-reports/`
- References a `generate-quality-registry.sh` script that produced the data, but that script is **not in the repo**
- No backend — `server/index.js` exports an empty function

### Component Maturity
- Just an iframe embedding `https://data-hub.pages.redhat.com/component-maturity/`
- This is RHOAI's internal Data Hub dashboard — not relevant to other teams

## Hardcoded Orgs

The 15 GitHub orgs baked into the data file include: `opendatahub-io`, `red-hat-data-services`, `kserve`, `kubeflow`, `trustyai-explainability`, `argoproj`, `openvinotoolkit`, `caikit`, `mlflow`, `EleutherAI`, `google`, `SeldonIO`, `triton-inference-server`, `redhat-openshift-ecosystem`, `openshift`.

Each repo entry has: id, label (org/repo), githubUrl, score, gaps, tier (upstream/midstream/downstream), component, team, and reportUrl.

## What It Would Take to Reuse

1. Replace or make the repo list in `qualityReports.data.js` configurable (move to backend/storage)
2. Find or recreate `generate-quality-registry.sh` to scan your own repos
3. Replace or remove the Component Maturity iframe URL
4. Add actual backend routes and a settings UI

This is the least portable module in the app — good candidate for skipping in initial deployment or flagging as needs-rework.

## Key Files

- `modules/system-health/module.json` — manifest
- `modules/system-health/client/qualityReports.data.js` — all 127 repos hardcoded here
- `modules/system-health/client/views/QualityAnalysisView.vue` — quality view
- `modules/system-health/client/views/ComponentMaturityView.vue` — iframe to RHOAI dashboard
- `modules/system-health/server/index.js` — empty, no backend

## Related

- [[rhai-org-pulse]] — parent project
- [[Release Registry Jira Projects Config Gap]] — similar pattern of RHOAI-specific defaults, but registry at least has a backend API

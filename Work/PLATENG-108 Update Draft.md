---
type: note
tags:
  - draft
  - jira
  - org-pulse
created: 2026-08-31
status: pending-post
---
_Posted 2026-08-31 (comment 18219198) to [PLATENG-108](https://redhat.atlassian.net/browse/PLATENG-108). Reworked before posting: framed as an incremental update since 08-03, dropped PrivateLink (tabled), and kept the relay's technical detail out. The block below is the original full draft; the posted version was trimmed._

Related: [[rhai-org-pulse]]

---

**Status update — production live; hardening module refresh**

**Where we are**

The production deployment is effectively set. Org Pulse is live in prod on `appsrep09ue1` (stage on `appsres09ue1`), with scored RFEs populated on the dashboard.

The `rfe-assessor` pipeline is running end-to-end via the *relay method*. Because the EC2 assessment runners can't reach the Org Pulse API directly (cross-TGW traffic blocked by on-prem firewall default-deny), assess jobs stage their results as CI artifacts in `relay-payload/`, and downstream IT-runner jobs pick them up and run `push-to-org-pulse.py`. Scored RFEs flow reliably from assessment to relay to the Org Pulse API and onto the dashboard. The relay is a deliberate workaround; AWS PrivateLink is the planned long-term replacement, after which the relay can be retired.

**What we're doing now**

Making sure the service's modules stay up to date and that prod refreshes all of them, not just team-tracker:

- `RedHatInsights/rhai-org-pulse#108` — switches the production daily CronJob to the unified `POST /api/admin/refresh-all` endpoint (matching what dev/kustomize already use). Previously prod only refreshed team-tracker data (roster, metrics, allocation, snapshots) and silently skipped AI Impact RFE data, GitHub/GitLab contributions, feature sync, test-plan sync, releases, and Jira-solve. Also raises `activeDeadlineSeconds` from 1800 to 3600 to accommodate the unified run.
- app-interface `!204322` — the follow-up MR to bump the production reference commit SHA once `#108` merges, so prod actually picks up the change.

**Next**

- Merge `#108` and `!204322` to bring prod's scheduled refresh in line with all modules.
- Longer term, replace the artifact relay with AWS PrivateLink to give the assessment runners direct API access.

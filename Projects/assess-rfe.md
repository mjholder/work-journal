---
type: project
status: active
tags:
  - project
  - opendatahub
  - rfe
  - assess-rfe
created: '2026-06-16'
---
# Project: assess-rfe

## Overview
Claude Code plugin for assessing RFEs against a structured quality rubric. Lives in the [opendatahub-io org](https://github.com/opendatahub-io/assess-rfe). Not hardcoded to RHAI — can be used across teams/instances manually if needed.

Related repo: [rfe-creator](https://github.com/opendatahub-io/rfe-creator) — companion tool for creating/reviewing RFEs and applying labels (Path A — adoption metrics). **Not the path being pursued** for the OpenShift RFE project — see [[rfe-assessor-data-pipeline]] for the distinction.

## Current Status
Actively planning upstream contribution. The plugin works for our use case as-is for scoring — `dump_jira.py` just needs the ability to target a different project key (currently hardcoded to construct JQL from a single key). A `--jql` flag would add flexibility. Tracked by [ENGPROD-10098](https://redhat.atlassian.net/browse/ENGPROD-10098).

**Manual scoring run completed** (2026-06-17): Tony and Pratik ran the assess-rfe skill manually against the OpenShift RFE project and produced CSV + HTML output. This demonstrates the scoring pipeline works end-to-end for our target project.

## Use Case

We need to score RFEs in the **OpenShift RFE project** on a quality rubric to produce an RFE grading report for leadership. The upstream plugin's `dump_jira.py` hardcodes JQL to `project={key} ORDER BY key ASC` — it already supports a single project key, which is what we need. The main gap is making the project key easy to configure when run through the rfe-assessor CI pipeline (where `RHAIRFE` is hardcoded).

> **Note:** An earlier assumption was that we'd need multi-project + label filtering (e.g., `ai-generated` tags). This was ruled out — the rfe-creator Path A (which applies labels) is not in use for OpenShift RFEs, so there are no labels to filter by. We score ALL RFEs in the target project. See [[rfe-assessor-data-pipeline]] for the two-pipeline distinction.

### Approach: Upstream Contribution (not fork)

A `--jql` flag would add flexibility for custom queries in the future. The change is small — `get_all_issues()` already accepts JQL internally, it just constructs it from the project key.

**Decision (2026-06-17):** Contribute upstream to `opendatahub-io/assess-rfe` rather than forking. The change is backward-compatible (new optional flags, defaults preserve existing behavior), benefits any team using the plugin, and the sandbox image CI infrastructure picks it up automatically on rebuild. Cross-team contribution is a positive signal.

**Fallback:** Fork + build custom sandbox image with `--image` override if upstreaming is slow.

### Sandbox Image Architecture

The assess-rfe skill is **pre-loaded inside the sandbox container image**, not injected at runtime:
- Image: `quay.io/aipcc/agentic-ci/claude-sandbox:latest`
- Skill location: `/sandbox/.claude-seed/cache/opendatahub-skills/assess-rfe/1.0.0/`
- The pipeline passes `AGENT_ENABLED_PLUGINS=assess-rfe` to activate the skill
- Image is rebuilt frequently via CI (86+ tags, most recent rebuild 2026-06-17)
- `dump_jira.py` lives inside this skill, NOT in the pipeline repo (`rfe-assessor`)

**Open question for RHEL AI team:** Does the sandbox image build pull assess-rfe from `main`/`latest`, or is the skill pinned to a specific version/commit? This determines whether our upstream PR flows through automatically on rebuild or needs a manual bump.

### Data Pipeline Architecture

The [rfe-assessor](https://gitlab.com/redhat/rhel-ai/agentic-ci/rfe-assessor) CI pipeline orchestrates the end-to-end flow. Three repos involved:

1. **rfe-assessor** (GitLab) — pipeline repo with CI jobs and post-processing scripts
2. **assess-rfe** (GitHub) — Claude Code skill baked into sandbox image, does the actual scoring
3. **rfe-assess-data** (GitLab) — results data repo, versioned history of assessments

Pipeline flow: Jira → dump_jira (fetch) → Claude scoring (in OpenShell sandbox) → push-results (commit to data repo) → push-to-org-pulse (POST to bulk API) → Org Pulse dashboard.

For our setup, pipeline runs on `itup-alm-x86` runners behind VPN. Direct connectivity to Org Pulse on OpenShift — no CronJob needed.

**Org Pulse stage is live** (2026-06-17) with Jira, LDAP, and GitHub data flowing. The remaining blocker for RFE scores on the dashboard is porting the AI Impact module into the core images (ENGPROD-10100).

## Jira Tickets

- **Epic:** [ENGPROD-10097](https://redhat.atlassian.net/browse/ENGPROD-10097) — RFE Quality Assessment Pipeline for HP
- **This story:** [ENGPROD-10098](https://redhat.atlassian.net/browse/ENGPROD-10098) — Add `--jql` flag to assess-rfe (upstream contribution)
- **Related:** [ENGPROD-10099](https://redhat.atlassian.net/browse/ENGPROD-10099) — Parameterize rfe-assessor pipeline

## Current Priorities (2026-06-23)

### Pipeline Setup — First Pass (RFE project, existing skill/image)

**Strategy:** Fork the rfe-assessor pipeline to our GitLab, override CI variables to target `RFE` project, use the existing sandbox image as-is. No waiting for upstream changes — get scores flowing now, clean up automation later.

**Pipeline:** `itup-alm-x86` runners on `gitlab.cee.redhat.com`.

| Step | What | Status |
|------|------|--------|
| 1 | Fork `rfe-assessor` to `gitlab.cee.redhat.com` | TODO |
| 2 | Create data store repo on `gitlab.cee.redhat.com` + project access token (`write_repository` scope) | TODO |
| 3 | Deploy `org-pulse-api` Route to stage (app-interface MR) + create `tt_` API token (`ai-impact:write` scope) | TODO |
| 4 | Configure CI variables on fork | TODO |
| 5 | Run pipeline against `RFE` project | TODO |

**CI Variables needed on the fork:**

| Variable | Value | Notes |
|----------|-------|-------|
| `JIRA_PREFIX` | `RFE` | Overrides default `RHAIRFE` |
| `JIRA_API_TOKEN` | Jira bot account token | Already provisioned |
| `GITLAB_HOST` | `gitlab.cee.redhat.com` | Overrides default `gitlab.com` |
| `RESULTS_REPO` | `hcm-engprod/rfe-assess-data` | `gitlab.cee.redhat.com` |
| `RESULTS_PUSH_TOKEN` | Project access token | `write_repository` scope on data repo. Vault: `engineering-productivity/hp-org-pulse/stage/rfe-assessor` key: `results_push_token` |
| `ORG_PULSE_URL` | `https://org-pulse-api.corp.stage.redhat.com` | Direct API route via dedicated IngressController (bypasses OAuth proxy). CNAME → `api.op-runner.apps.rosa.appsres09ue1.24ep.p3.openshiftapps.com`. Pending: CNAME record (UR0205152) + TLS cert from Red Hat IT CA. |
| `ORG_PULSE_API_TOKEN` | `tt_` token | `ai-impact:write` scope, admin user |

**Runner tag:** `itup-alm-x86` (replace `aipcc-small-x86_64` in `.gitlab-ci.yml`)

### Previous Priorities (completed)
1. ~~**AI Impact module port (ENGPROD-10100)**~~ — **Done** (2026-06-22). Jacopo deployed the AI Impact module to stage.
2. ~~**Bulk API validation**~~ — **Done** (2026-06-22). 205/206 RFEs ingested via Tony's CSV.
3. **Parameterize rfe-assessor (ENGPROD-10099)** — MR !1 on `parameterize-jira-prefix` branch. Deferred — using variable overrides for first pass instead.

## Recent Progress
### 2026-07-17
- Explored Agent Control Plane (ACP) as potential solution for running OpenShell on OpenShift. ACP uses a custom `openshell-sandbox` SCC with 7 capabilities (NET_ADMIN, SYS_ADMIN, SYS_PTRACE, SETUID, SETGID, CHOWN, DAC_OVERRIDE) — not fully privileged. Two modes: file mode and gateway mode. Local dev on Kind via `make kind-up`. The `openshift-cronjob` branch of rfe-assessor uses `--backend local` (no sandbox), gap to ACP is moderate. Next: draft an ACP Agent definition YAML for rfe-assessor, test on Kind.

### 2026-06-22
- Jacopo suggested running the rfe-assessor job as multiple parallel instances via GitLab CI, so we can score multiple projects simultaneously instead of sequentially. Since single-project runs already take a long time, this avoids linear growth in total runtime — each project runs in its own CI job concurrently.
- AI Impact module is now deployed to stage — Jacopo's work on ENGPROD-10100 is complete. Next step: data ingestion (push RFE scoring data via the bulk API to validate end-to-end).

- **2026-06-17** — Decision: upstream contribution over fork. Investigated sandbox image architecture — skill is baked in, image rebuilt via CI frequently. Updated ENGPROD-10098 to reflect upstream approach with fallback to fork.
- **2026-06-17** — Created Jira epic ENGPROD-10097 and 6 stories for RFE assessor workstreams
- **2026-06-16** — Reviewed the assess-rfe image; confirmed it is not hardcoded for RHAI and can be used manually on our instance
- **2026-06-16** — Reviewed `dump_jira.py` source: JQL is `project={key} ORDER BY key ASC`, no tag/label/status filtering, single project only.

## Outstanding Tasks
- [ ] Open upstream PR on `opendatahub-io/assess-rfe` adding `--jql` flag to `dump_jira.py`
- [ ] Confirm with RHEL AI team how skill version is pinned in sandbox image build
- [ ] Verify sandbox image rebuild picks up the change after PR merges
- [x] Determine target Jira project — **`RFE`** (OpenShift RFE project, confirmed via Bill/Tony, 2026-06-17)
- [x] Label filtering — **Not needed**. No AI-created labels exist on OpenShift RFEs. Score all RFEs in the project.

## AI Impact Module Config Reference

The AI Impact module in Org Pulse has its own configuration (saved to `ai-impact/config.json`, editable via Settings UI). These settings control which Jira projects/labels/fields the dashboard pulls from. **Leaders/managers need to confirm which values are correct for our deployment.**

Config is grouped by dashboard feature — each feature can be configured independently.

### RFE Review (core metrics — quality scores)

| Field | Current Value | What it controls |
|-------|--------------|-----------------|
| `jiraProject` | `RFE` | Jira project key to pull RFEs from. This is the main data source for the RFE Review dashboard. |
| `excludedStatuses` | `['Closed']` | Jira statuses to filter out of RFE queries. |
| `lookbackMonths` | `0` (all) | How far back to fetch. `0` = all issues, `3` = last 90 days. |
| `trendThresholdPp` | `2` | Percentage-point change needed to flag a trend as "growing"/"declining" vs "stable". Noise filter — default is fine. |

These are the only fields needed for the RFE quality scores we're currently pushing via the bulk API.

### RFE Adoption Labels (AI-created/revised tracking)

| Field | Current Value | What it controls |
|-------|--------------|-----------------|
| `createdLabel` | `ai-generated` | Jira label marking RFEs created by the AI tool. Powers "AI-created %" metrics. |
| `revisedLabel` | `rfe-creator-auto-revised` | Jira label for AI-revised RFEs. Powers revision count and trends. |
| `testExclusionLabel` | `rfe-creator-skill-testing` | Label to exclude test issues from metrics. |

> **For our deployment:** These labels only matter if the team uses the rfe-creator AI tool to write/revise RFEs. Since we're using Path B (batch scoring via rfe-assessor), these adoption metrics will show zero unless rfe-creator is also in use. Not a blocker — the RFE quality scores work independently.

### Feature Linking (RFE → upstream feature mapping)

| Field | Current Value | What it controls |
|-------|--------------|-----------------|
| `linkedProject` | `RHAISTRAT` | Jira project key for linked features. When you click an RFE, the detail modal shows which upstream feature it maps to — this field filters issue links to keys starting with this prefix. |
| `linkTypeName` | `Cloners` | The Jira link type to follow (must match exactly). |

> **Action needed:** Should likely be `HPSTRAT` for our deployment. The feature linking shows up when you click into an individual RFE — the detail modal displays the linked upstream feature (if one exists via a "Cloners" link in Jira). Need to confirm with leadership: (1) is `HPSTRAT` the right project for our linked features? (2) is the link type still "Cloners" or something else?

### Autofix Pipeline (Jira triage automation)

| Field | Current Value | What it controls |
|-------|--------------|-----------------|
| `autofixProjects` | `['RFE']` | Jira project keys to scan for autofix triage labels. |
| `autofixCreatedAfter` | `null` | Optional date filter to skip older issues. |

> **What this does on the dashboard:** The "Jira AutoFix" view shows a pipeline of Jira issues tagged with triage labels (e.g., `jira-triage-pending`, `jira-triage-missing-info`). It tracks how many issues the AI triage tool has processed, their current state in the triage pipeline, and success rates. This is a **separate feature from RFE scoring** — it's about automated bug triage, not RFE quality. If the team isn't using the Jira autofix triage tool, this dashboard will be empty regardless of config. **Needs clarification:** Is there an autofix/triage workflow running against any of our Jira projects? If not, this section can be ignored.

### Documentation Tracking (AI-first docs)

| Field | Current Value | What it controls |
|-------|--------------|-----------------|
| `docProject` | `RHAISTRAT` | Jira project for documentation requests. |
| `docRequiredStatuses` | `['Review', 'Release Pending']` | Which statuses indicate an issue needs docs. |
| `docRequiredFieldId` | `customfield_10665` | Custom field ID for "Product Documentation Required". |
| `docContributedLabel` | `ai1st-doc-contributed` | Label marking issues where docs were completed. |
| `docSkippedLabel` | `ai1st-doc-skip` | Label for intentionally skipped docs. |
| `docInvokedLabel` | `ai1st-doc-invoked` | Label for issues where doc automation was triggered. |
| `docMrFieldId` | `customfield_10875` | Custom field storing MR/PR URLs for doc contributions. |

> **Action needed:** Should `docProject` be `HPSTRAT`? This powers the "Documentation" view which tracks AI-assisted documentation coverage — how many features needing docs have been handled. Like feature linking, it depends on the right Jira project. Also need to confirm: are the custom field IDs (`customfield_10665`, `customfield_10875`) valid on our Jira instance, or are those RHAI-specific?

### Summary of what needs stakeholder input

1. **`linkedProject`** — Change to `HPSTRAT`? (Feature linking in RFE detail modal)
2. **`docProject`** — Change to `HPSTRAT`? (Documentation coverage dashboard)
3. **`autofixProjects`** — Is there a Jira autofix/triage workflow running? If not, ignore.
4. **`linkTypeName`** — Is "Cloners" the right link type in our Jira instance?
5. **Custom field IDs** — Are `customfield_10665` and `customfield_10875` valid on our instance?
6. **Label names** — Are any of the `ai1st-doc-*` or `rfe-creator-*` labels in use?

## Stage API Route — Authentication Model

### Why it's needed

The production frontend pod runs an OAuth proxy sidecar (port 4180) that intercepts **all** incoming requests — including those with `Bearer` tokens in the `Authorization` header. This means external services (the rfe-assessor GitLab CI pipeline, manual `curl` calls, any programmatic API consumer) cannot authenticate to the backend API through the standard frontend Route. The OAuth proxy consumes the auth header and redirects to an OpenShift login page.

### What we created

A **direct Route** (`org-pulse-api`) pointing to the backend Service on port 3001, bypassing the OAuth proxy entirely. Defined in app-interface:

- **Route resource**: `resources/services/rhai-org-pulse/rhai-org-pulse-stage-api.route.yaml`
- **Registered in**: `data/services/rhai-org-pulse/namespaces/rhai-org-pulse-stage.appsres09ue1.yml` (line 44-45)
- **Hostname**: `org-pulse-api.corp.stage.redhat.com` (CNAME → `api.op-runner.apps.rosa.appsres09ue1.24ep.p3.openshiftapps.com`; previously `org-pulse-api-rhai-org-pulse-stage.apps.rosa...`)
- **TLS**: Edge termination (HTTPS to the OpenShift router, HTTP within the cluster — same as the frontend Route)

### How it's authenticated

The backend is **not unauthenticated**. The `proxySecretGuard` middleware (`shared/server/auth.js:265-301`) runs on every request and enforces one of two auth mechanisms:

1. **`X-Proxy-Secret` header** — A shared secret stored in Vault at `engineering-productivity/hp-org-pulse/stage/proxy-auth-secret`. The backend reads it from the `PROXY_AUTH_SECRET` env var. Comparison uses `crypto.timingSafeEqual` to prevent timing attacks. This is how the **CronJob** already authenticates for cluster-internal roster sync and metrics refresh calls.

2. **`Bearer tt_` API tokens** — Per-user tokens generated through the Settings UI in the Org Pulse web app. Each token is:
   - Scoped (e.g., `ai-impact:write` for assessment bulk uploads)
   - Revocable (admin can delete any token via Settings)
   - Tied to a user identity (the user who created it)
   - Validated inline by the `tokenValidator` against the token store (`data/api-tokens.json`)

**Unauthenticated paths** (exempt from guard):
- `OPTIONS` requests (CORS preflight)
- `/healthz` and `/api/healthz` (health checks)
- `/api/docs` (OpenAPI documentation)
- `GET /api/built-in-modules/manifests` (public module metadata)

Everything else — including `POST /api/modules/ai-impact/assessments/bulk` — requires valid auth.

### Security posture summary (for app-sre review)

| Concern | Answer |
|---------|--------|
| Is the route unauthenticated? | **No.** `proxySecretGuard` middleware rejects all unauthenticated requests with 401. |
| What secrets does it use? | Reuses existing `proxy-auth-secret` from Vault — no new secrets needed. |
| Is there precedent? | Yes — the CronJob (`cronjob-sync-refresh.yaml`) uses the same `X-Proxy-Secret` pattern for cluster-internal calls. |
| Is TLS enforced? | Yes — edge termination with `insecureEdgeTerminationPolicy: Redirect`. |
| Can tokens be rotated? | `tt_` tokens are revocable per-user via Settings UI. The proxy secret is rotated by updating Vault + bumping the secret version in the namespace file. |
| What data is exposed? | Same backend API that the OAuth-proxied frontend accesses. No additional endpoints or data. |
| Why not use the OAuth proxy? | OAuth proxy requires browser-based login — incompatible with CI pipelines and programmatic API consumers that use Bearer tokens or shared secrets. |

### Usage examples

**CI pipeline (rfe-assessor)** — uses a `tt_` token with `ai-impact:write` scope:
```bash
curl -X POST \
  -H "Authorization: Bearer tt_<token>" \
  -H "Content-Type: application/json" \
  -d @assessments.json \
  https://org-pulse-api-rhai-org-pulse-stage.apps.rosa.appsres09ue1.24ep.p3.openshiftapps.com/api/modules/ai-impact/assessments/bulk
```

**CronJob (cluster-internal)** — uses the proxy secret:
```bash
curl -H "X-Proxy-Secret: $PROXY_AUTH_SECRET" \
  https://backend:3001/api/modules/team-tracker/sync
```

### Status

- [x] Route YAML created in app-interface
- [x] Route registered in stage namespace config
- [ ] App-interface MR submitted and merged
- [ ] Route deployed to stage cluster
- [ ] Verify `tt_` token auth works end-to-end via the new Route
- [ ] Push Tony's assessment data to stage via the API Route

## Notes
- Part of the opendatahub-io org alongside rfe-creator
- Useful as a manual tool for RFE quality checks even without full automation
- `dump_jira.py` only fetches `summary` and `description` fields — no labels in the payload currently, filtering happens at the JQL level
- The `rfe-assessor` CLI (`cli.py`) accepts `--enabled-plugins` and `--image` flags — if we ever need a custom sandbox image, we can override without changing the pipeline

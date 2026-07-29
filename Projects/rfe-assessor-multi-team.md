---
type: project
status: shelved
tags:
  - project
  - rfe-assessor
  - multi-team
  - org-pulse
  - agentic-ci
created: '2026-06-15'
parent: '[[rhai-org-pulse]]'
---
# RFE Assessor — Multi-Team Support Plan

> **SHELVED (2026-06-16):** Multi-team scope was descoped. The active path is single-team: score all RFEs in the **OpenShift RFE project** using the existing rfe-assessor pipeline with minimal parameterization. See [[assess-rfe]] for the active project note and [[rfe-assessor-data-pipeline]] for the pipeline map. This note is retained as reference for if/when multi-team expansion is revisited.

~~Extend the [rfe-assessor](https://gitlab.com/redhat/rhel-ai/agentic-ci/rfe-assessor) GitLab CI pipeline to assess RFE Jira issues for multiple HP teams beyond the current RHEL AI (`RHAIRFE-*`) scope.~~ This is a prerequisite for RFE quality metrics appearing on [[rhai-org-pulse]] for teams beyond RHEL AI.

### Key Links

- **Parent project**: [[rhai-org-pulse]]
- **Deployment plan**: [[rhai-org-pulse-deployment-plan]]
- **Related knowledge**: [[Org Pulse System Health Module - Hardcoded for RHOAI]], [[Release Registry Jira Projects Config Gap]]
- **Assessor repo**: [rfe-assessor](https://gitlab.com/redhat/rhel-ai/agentic-ci/rfe-assessor)
- **Plugin**: [assess-rfe](https://github.com/opendatahub-io/assess-rfe) (Claude Code skill, baked into sandbox image)
- **Sandbox image**: `quay.io/aipcc/agentic-ci/claude-sandbox:latest` (skill at `/sandbox/.claude-seed/cache/opendatahub-skills/assess-rfe/1.0.0/`)
- **Data repo**: `redhat/rhel-ai/agentic-ci/rfe-assess-data`
- **Jira hierarchy**: [HPSTRAT-2](https://redhat.atlassian.net/browse/HPSTRAT-2) > [PLATENG-108](https://redhat.atlassian.net/browse/PLATENG-108) > [ENGPROD-10097](https://redhat.atlassian.net/browse/ENGPROD-10097) (Epic: RFE Quality Assessment Pipeline)

---

## Context

The rfe-assessor is a **GitLab CI pipeline** that uses **Claude Code** (via Vertex AI, model `claude-opus-4-6`) inside **OpenShell sandboxes** to automatically assess and score Jira RFE issues on a quality rubric (What/Why/How/Task/Size). It runs as a scheduled pipeline (6h timeout) on `aipcc-small-x86_64` runners, invoking the `assess-rfe` Claude Code plugin from [`opendatahub-io/assess-rfe`](https://github.com/opendatahub-io/assess-rfe).

**Recent infrastructure changes** (June 2026):
- **OpenShell migration** — sandbox backend switched from PodmanBackend to OpenShell (`create_backend("openshell", ...)`). Network policy at `.agentic-ci/openshell-policy.yml` whitelists `redhat.atlassian.net:443`.
- **OTEL telemetry** — token/cost tracking via OpenTelemetry. OTEL logs captured as 30-day CI artifacts (`claude-otel.jsonl`). Relevant for per-team cost visibility if multi-team rollout happens.
- **Custom supervisor workaround** — CI uses `quay.io/mprpic/openshell-supervisor:pr1763` until upstream OpenShell PR #1763 merges and the RPM upgrades past 0.0.55. Track this for cleanup.
- **Pending docs MR** — `upstream/readme` branch has README/AGENTS.md/pyproject.toml updates reflecting the above changes, not yet merged to `main`.

**Data flow**: Jira → Claude assessment → results committed to data repo (`rfe-assess-data`) → pushed to org-pulse via `push-to-org-pulse.py` calling the bulk API at `/api/modules/ai-impact/assessments/bulk`.

Today, the entire pipeline is hardcoded to `RHAIRFE-*` only. Extending to other teams requires parameterizing ~20 lines across 3 files — a small refactoring effort, but with several external dependencies to resolve first.

### Critical Blocker: ai-impact Module Layer

The ai-impact module (which hosts the `/api/modules/ai-impact/assessments/bulk` endpoint that `push-to-org-pulse.py` calls) lives in the **AI Eng layer**, not core. HP's org-pulse instance will deploy **core images only** (per [[rhai-org-pulse-deployment-plan]] Section 6). This means RFE assessment data has no home on the HP instance unless:

1. The ai-impact module is extracted to the core layer (upstream work), or
2. HP pushes assessment data to RHEL AI's instance (current behavior, cross-team dependency), or
3. A standalone assessment dashboard is built

This must be resolved before multi-team RFE metrics can flow to HP's org-pulse.

### Org-Pulse Deployment Status

Per [[rhai-org-pulse]], the deployment is currently in **Phase 1 (infrastructure)**, nearly complete:
- All app-interface MRs merged — namespace + RBAC provisioned on cluster
- Konflux onboarded — images building to quay.io
- Credentials provisioned: LDAP, Jira bot, GitHub PAT, OAuth secrets
- **In progress**: OAuth proxy configuration fixes and frontend template updates

RFE assessor parameterization (Phases 1-2 of this plan) can begin **independently** of org-pulse deployment. The integration point is Phase 2/3 of org-pulse (stage deployment + data source configuration).

---

## Runner Infrastructure — Findings from RHAI Thread (2026-06-30)

Context captured from a Google Chat thread with RHAI team members about how they set up their GitLab runners for RFE assessment, and why standard runner options don't work for the rfe-assessor pipeline.

### Why Standard Runners Don't Work

The rfe-assessor pipeline runs Claude Code inside **OpenShell sandboxes**, which require **privileged access to create network devices** for the gateway component. Per Jason Greene: "OpenShell requires privilege to create net devices and so on." This eliminates most standard runner options:

| Runner Type | Why It Fails | Source |
|-------------|-------------|--------|
| **GitLab CEE shared runners** | Rootless podman — insufficient capabilities for OpenShell gateway. Error: gateway fails to come up ([job #55003219](https://gitlab.cee.redhat.com/hcm-engprod/rfe-assessor/-/jobs/55003219)) | Victor M., jgiola |
| **AIPCC K8s runners** (`aipcc-k8s-build`) | Special SCC allows privileged containers but **no CAP_SYS_ADMIN** — still can't handle OpenShell. `podman` fails ([job #55257223](https://gitlab.cee.redhat.com/ai/openshell-k8s-poc/-/jobs/55257223)); `buildah run` works but is the wrong tool for running sandboxes | Victor M. tested both |
| **AIPCC EC2 runners** (`aipcc-small-x86_64`) | These **do** work (RHAI uses them), but they're group runners for `redhat/rhel-ai` on `gitlab.com`, not `gitlab.cee.redhat.com`. Our project is on `gitlab.cee.redhat.com` so they're unreachable | ariobolo clarified the gitlab.com vs gitlab.cee distinction |
| **AI group K8s runners on gitlab.cee** | Same K8s rootless constraints as shared runners — no CAP_SYS_ADMIN | Victor M. confirmed |

**Key technical detail**: Adding `-vvv` to OpenShell commands didn't add useful debug info. The root cause is the container runtime privilege level, not a configuration issue.

### How RHAI Runs Their Runners

RHAI's runners use the **docker machine executor to launch EC2 instances**:
- Runners have a **VPC to access internal systems** (behind the VPN)
- Uses `aipcc-small-x86_64` and `aipcc` runner tags on `gitlab.com`
- EC2 provisioning uses the out-of-the-box GitLab docker machine executor
- "The tricky stuff is having the right images and the maintenance pattern for all of it" — Jason Greene
- Runner setup docs: https://docs.aipcc.redhat.com/productization/infrastructure/gitlab-runners/

**Cost center caveat** (dhellmann): "It's OK to use the AIPCC runners for a PoC, but at some point you're going to need your own tied to your own cost center."

### HP's Path: EC2 Project Runner

Decision (2026-06-26, ENGPROD-10120): Stand up our own EC2 VM runner:
- RHEL 9 m5.large instance with **shell executor** GitLab runner
- Registered as **project runner** (tag `rfe-assessor`) on `gitlab.cee.redhat.com`
- Podman runs natively on the VM — no container-in-container issues
- Requires IT-managed AWS account with VPN/internal network connectivity
- ~$70/month always-on estimate
- Decision (2026-06-29): New IT AWS account (Option 3) — IT-managed accounts get internal VPN/network connectivity automation on request

### Key Contacts from RHAI Thread

| Person | Knowledge Area |
|--------|---------------|
| **Jason Greene** | AIPCC runner architecture — docker machine executor, VPC setup, OpenShell privilege requirements |
| **Victor M. (vmugicag)** | Tested podman/buildah in K8s runners, confirmed K8s path is a dead end, suggested VM-based runners, offered to validate PoC on AIPCC runners |
| **dhellmann** | Runner cost ownership — PoC sharing OK, production needs own cost center |
| **ariobolo** | Clarified AIPCC runners serve `gitlab.com` (rhel-ai group), NOT `gitlab.cee.redhat.com` |
| **Alex Corvin** | Initial contact at RHAI, facilitated connections to runner experts |

### AWS Account & VPN Networking (Internal Thread, 2026-06-30)

**Why VPN matters**: The runner needs to reach org-pulse, which itself needs LDAP (`ldap.rdu.redhat.com`) and GitLab CEE (`gitlab.cee.redhat.com`) — both behind the VPN. So the runner must be in an AWS VPC with internal Red Hat network connectivity.

**Bill Montgomery's position**: Does **not** want a new IT-managed AWS account accounted for separately. Suggested deploying runner VMs alongside existing AppSRE clusters that are already in VPN-connected AWS accounts.

**aweiteka (SRE) response**: AppSRE has a **hard policy** — no unmanaged workloads in their AWS accounts. Could grant an exception but "it's for a developer use case — it's just not a door we want to open." Also confirmed AppSRE doesn't have any clusters behind the VPN that support experimental settings, and ROSA doesn't support it.

**IT's three options for VPN-connected AWS**:
1. Migrate an existing PCO account to IT — risky, those accounts serve ephemeral envs and testing
2. Share external transit gateway from IT — requires manual VPC build, limited connectivity
3. New IT-managed account — standard VPC setup, least risk → **initially chosen (2026-06-29) but Bill pushed back (2026-06-30)**

**Final decision (2026-06-30)**: Proceeding with **new IT-managed AWS account** (Option 3). K8s buildah + SCC was explored as an alternative but the EC2 VM path is the proven approach (RHAI uses it). IT ticket: [UR0198029](https://redhat.service-now.com/help?id=rh_ticket&table=sc_request&sys_id=UR0198029). IT-managed accounts get internal VPN/network connectivity as a standard procedure — runner VM will have access to LDAP, gitlab.cee, and org-pulse behind the VPN.

### K8s Runner Failure Analysis (2026-06-30)

Analyzed the CI failure log from [job #55257223](https://gitlab.cee.redhat.com/ai/openshell-k8s-poc/-/jobs/55257223) — the podman test on `aipcc-k8s-build` runners.

**Root cause**: `crun` (OCI runtime) fails at `mount proc to proc: Permission denied: OCI permission denied`. Podman successfully pulled the container image (`ubi9/ubi-minimal:latest`) but when `crun` tried to mount `/proc` inside the new container's PID namespace, it was denied. This requires `CAP_SYS_ADMIN`.

**Capability bitmask** from `/proc/self/status` in the runner pod:

```
CapEff: 00000000800005fb
```

Decodes to these **granted** capabilities:
- `CAP_CHOWN`, `CAP_DAC_OVERRIDE`, `CAP_FSETID`, `CAP_KILL`
- `CAP_SETGID`, `CAP_SETUID`, `CAP_SETPCAP`, `CAP_SETFCAP`
- `CAP_LINUX_IMMUTABLE`, `CAP_NET_BIND_SERVICE`

**Missing** capabilities needed for OpenShell:
- **`CAP_SYS_ADMIN`** (bit 21) — required for mounting `/proc` in nested PID namespaces, creating new mount/PID/network namespaces. This is the direct cause of the podman failure.
- **`CAP_NET_ADMIN`** (bit 12) — required for OpenShell gateway to create network devices (tun/tap interfaces, veth pairs).

**Why buildah works but podman doesn't**: `buildah run` doesn't create full container namespaces or mount a new `/proc`. It reuses the host's existing mounts and namespace. Podman creates a proper isolated container with its own PID namespace, which requires `CAP_SYS_ADMIN` to mount procfs. OpenShell needs podman's full runtime (detached execution, port binding on gateway port 17670, container lifecycle management) — `buildah run` cannot substitute.

**Implication for K8s path**: To run OpenShell on a K8s runner, the pod's SCC would need at minimum `CAP_SYS_ADMIN` + `CAP_NET_ADMIN`, which is effectively `privileged` SCC territory. On OSD (crc-eph), this requires an SRE request since `dedicated-admin` cannot create custom SCCs. This is a significant privilege escalation ask.

**Runner details from CI log**:
- Runner: `aipcc-build-k8s-runner-gitlab-cee-runner-f566fff99-vrv67` (ID: `ORPKqqU3-`)
- K8s namespace: `aipcc-gitlab-runner--pipeline`
- Node: `worker06.itup-001.preprod.iad2.dc.redhat.com`
- Image: `quay.io/podman/stable:latest` (podman 5.8.2, buildah 1.43.1)
- Runner version: gitlab-runner 19.1.1
- Container ran as `uid=0(root)` with supplemental group `1004810000`

### Alternatives Considered but Rejected (or Paused)

- **K8s runners with buildah + elevated SCC** — Explored as alternative to avoid AWS account. Victor M. confirmed `buildah run` works under `aipcc-k8s-build` SCC but `podman` does not. Unclear if OpenShell can work with buildah's runtime. Dropped in favor of proven EC2 VM approach.
- **EC2 in existing AppSRE AWS accounts** — Hard policy: no unmanaged workloads in AppSRE accounts (aweiteka).
- **OpenShift CronJob** — SRE declined (2026-06-26). Would require removing the OpenShell sandbox component and running Claude directly in a pod. Security concern: no sandbox isolation.
- **Sharing RHAI's EC2 runners** — Wrong GitLab instance (`gitlab.com` vs `gitlab.cee.redhat.com`). Even if reachable, cost center ownership issue.
- **IT-provided VM runner pool** — Unknown if IT provides this for GitLab. Victor M. didn't know either.
- **Migrating project to gitlab.com** — Would solve runner access but adds other complexity; project is established on `gitlab.cee.redhat.com`.

---

## What's Hardcoded

| File | What's Hardcoded | Change Needed |
|------|-----------------|---------------|
| `.gitlab-ci.yml` | `RHAIRFE-*` in CLAUDE_PROMPT (test-rfe job) | Replace with `${JIRA_PREFIX}-*` |
| `.gitlab-ci.yml` | `RHAIRFE-*` in CLAUDE_PROMPT (assess-rfe job) | Replace with `${JIRA_PREFIX}-*` |
| `scripts/push-results.py` | `results_dir / "RHAIRFE"` in `prune_old_runs()` | Use `args.jira_prefix` |
| `scripts/push-results.py` | `results_dir / "RHAIRFE" / "current"` spot check | Use `args.jira_prefix` |
| `scripts/push-results.py` | `"RHAIRFE/current symlink does not exist"` error msg | Use `args.jira_prefix` |
| `scripts/push-results.py` | `"RHAIRFE bulk assessment run"` commit message | Use `f"{args.jira_prefix} bulk assessment run"` |
| `scripts/push-to-org-pulse.py` | `os.path.join(results_dir, "RHAIRFE", "current")` | Use `args.jira_prefix` |
| `scripts/push-to-org-pulse.py` | `"WARNING: RHAIRFE/current is not a symlink"` log msg | Use `args.jira_prefix` |
| `scripts/push-to-org-pulse.py` | `f"INFO: {args.results_dir}/RHAIRFE/current not found"` | Use `args.jira_prefix` |

### Results Repo Authentication

The pipeline authenticates to GitLab using a **project/group access token** stored as the `RESULTS_PUSH_TOKEN` CI variable. The flow:

1. CI `before_script` saves the token to `/root/.tokens/results` and `unset`s it from the environment (so Claude can't access it during assessment)
2. `clone-data-repo.sh` constructs `https://bot:${token}@gitlab.com/${repo}.git` for the clone
3. `push-results.py` re-reads the token before push and sets the remote URL the same way

**Problem**: Both `clone-data-repo.sh` and `push-results.py` hardcode `gitlab.com` as the host. For HP teams using `gitlab.cee.redhat.com`, a `GITLAB_HOST` variable (default `gitlab.com`) is needed alongside `JIRA_PREFIX`.

| File | What's Hardcoded | Change Needed |
|------|-----------------|---------------|
| `scripts/clone-data-repo.sh` | `gitlab.com` in clone URL | Use `${GITLAB_HOST:-gitlab.com}` |
| `scripts/push-results.py` | `gitlab.com` in push remote URL | Use `args.gitlab_host` or env var |

**For HP setup**: Create a project access token on the results repo in `gitlab.cee.redhat.com` with `write_repository` scope, store it as a CI variable (`RESULTS_PUSH_TOKEN`), and set `GITLAB_HOST=gitlab.cee.redhat.com`.

### Org-Pulse API Authentication

The `push-to-org-pulse.py` script calls the bulk endpoint at `/api/modules/ai-impact/assessments/bulk`. This requires a bearer token with admin role and `ai-impact:write` scope.

**Creating the token:**

1. Log in to org-pulse as an admin user
2. Go to **Settings** (gear icon) → **API Tokens** tab
3. Click **Create Token** — name it something like `rfe-assessor-pipeline`
4. Set scope to `ai-impact:write` (add `ai-impact:read` if the pipeline also reads data)
5. Choose expiration: `90d`, `1y`, or no expiration
6. Copy the token immediately — it starts with `tt_` and is only shown once (stored as SHA-256 hash)

**Usage in the pipeline:**

```bash
curl -X POST https://<org-pulse-url>/api/modules/ai-impact/assessments/bulk \
  -H "Authorization: Bearer tt_<token>" \
  -H "Content-Type: application/json" \
  -d '{"assessments": [...]}'
```

**Key constraints:**
- The token owner must have admin role — the token inherits their identity for role checks
- Bulk endpoint accepts up to 5,000 entries per request
- Token format: `tt_` prefix + 32 hex chars
- Scopes available: `ai-impact:read`, `ai-impact:write`

**CI variable:** Store as `ORG_PULSE_API_TOKEN` in the GitLab CI variables (masked, protected). The `push-to-org-pulse.py` script would read this for the `Authorization` header.

### Already Team-Agnostic (no changes needed)

- `scripts/clone-data-repo.sh` — clones any repo given as argument (but hardcodes `gitlab.com` host — see above)
- `scripts/ci-monitor.py` — terminal UI for CI monitoring, generic
- `src/rfe_assessor/cli.py` — CLI entry point, fully parameterized
- `src/rfe_assessor/runner.py` — OpenShell sandbox execution + OTEL telemetry, generic
- OTEL collection and streaming functionality lives in the `agentic-ci` library, not local scripts

---

## Implementation Plan

### Phase 1: Parameterize RHAIRFE (0.5 days)

- Introduce `JIRA_PREFIX` CI variable in `.gitlab-ci.yml` (default: `RHAIRFE`)
- Replace all 2 hardcoded `RHAIRFE-*` patterns in CI prompts with `${JIRA_PREFIX}-*`
- Add `--jira-prefix` CLI argument to both Python scripts
- Replace all 7 hardcoded `RHAIRFE` references in `push-results.py` and `push-to-org-pulse.py` with `args.jira_prefix`
- Thread `--jira-prefix "$JIRA_PREFIX"` through CI script invocations
- Add `GITLAB_HOST` CI variable (default: `gitlab.com`) and thread through `clone-data-repo.sh` and `push-results.py` for teams using `gitlab.cee.redhat.com`
- ~25 lines of changes total, backward-compatible (defaults maintain current behavior)

### Phase 2: Per-Team CI Job Blocks (1 day)

- Add new CI job definitions per pilot team, each extending the base `.claude` template
- Each job overrides `JIRA_PREFIX`, `CLAUDE_PROMPT`, and optionally `JIRA_TOKEN`
- Separate `resource_group` per team to prevent collisions
- Separate pipeline schedules (stagger to manage runner capacity)
- `build-dashboard` trigger (visualize-rfe) is RHEL AI-specific — new teams either skip or get their own

### Phase 3: Inspect assess-rfe Plugin (0.5 days) — DONE 2026-06-16

- ~~Clone `n1hility/assess-rfe.git` and read the source~~ — inspected via container image instead (`quay.io/aipcc/agentic-ci/claude-sandbox:latest`)
- **Confirmed**: Plugin receives Jira prefix as CLI arg to all scripts. Creates `{PREFIX}/` directory structure via parameterized paths. Scoring rubric criteria are generic; calibration examples and platform vocabulary are RHOAI-specific but non-blocking.
- **Key finding**: Skill is usable for HP team RFEs as-is — no code changes needed in the plugin itself. Only the pipeline wrapper files need parameterization.

### Phase 4: Org-Pulse API Contract Check (0.5 days)

- Check org-pulse source for the bulk endpoint handler (`/api/modules/ai-impact/assessments/bulk`)
- Does it auto-route by Jira issue prefix, or need an explicit team identifier in the payload?
- **Resolve the ai-impact layer blocker** — is extraction to core feasible, or do we need an alternative path?

### Phase 5: Per-Team Auth & Onboarding (0.5 days/team)

For each new team:
- Verify Jira API token scope covers the team's RFE project
- Provision per-team token if shared token doesn't have access
- Add CI job definition + pipeline schedule
- Test with a dry run (limit to 5 issues, like the existing `test-rfe` job)

---

## Open Questions

- [x] **assess-rfe plugin internals** — **ANSWERED 2026-06-16**: The plugin is ~90% parameterized. All Python scripts accept the Jira project key as a CLI argument (e.g., `dump_jira.py YOURPROJECT`). Jira connection uses env vars (`JIRA_SERVER`, `JIRA_USER`, `JIRA_TOKEN`). `RHAIRFE` appears only in documentation/examples and in `agent_prompt.md` line 3 (file path), but that path is explicitly overridden by the SKILL.md launch prompt via `{DATA_FILE}` substitution. The MCP `cloudId` is hardcoded to `redhat.atlassian.net` but that's our same instance. The scoring rubric's RHOAI platform vocabulary list may cause slightly harsher HOW scores for non-RHOAI RFEs (unfamiliar tech names won't get the "platform vocabulary" pass), but the 5 criteria themselves are generic PM quality criteria. **Conclusion: skill is usable for our team's Jira project as-is.** Source: inspected `quay.io/aipcc/agentic-ci/claude-sandbox:latest` container image, skill at `/sandbox/.claude-seed/cache/opendatahub-skills/assess-rfe/1.0.0/`.
- [ ] **Org-pulse API contract** — bulk endpoint auto-routes by Jira prefix or needs explicit team ID? **Partial answer (2026-06-16):** Auth is via `tt_`-prefixed bearer token with `ai-impact:write` scope, created in Settings → API Tokens. Token owner must be admin. Endpoint accepts up to 5k entries/request. Still need to confirm whether payload needs an explicit team identifier or auto-routes by issue key prefix.
- [x] **ai-impact module layer** — **RESOLVED 2026-06-17**: Port AI Impact module from AI Eng layer into our fork's core images. [ENGPROD-10100](https://redhat.atlassian.net/browse/ENGPROD-10100). Dev branch started. Also need multi-team filtering on the views ([ENGPROD-10101](https://redhat.atlassian.net/browse/ENGPROD-10101)).
- [ ] **Jira auth token scope** — does the current `JIRA_API_TOKEN` cover other teams' RFE projects?
- [x] **Pilot team RFE projects** — Moot; focus is single-team (OpenShift RFE project), not multi-team piloting.
- [ ] **Runner capacity / cost** — each assessment run is 4-6h of Claude on Vertex AI. Budget ceiling for N teams?
- [ ] **Results repo strategy** — shared `rfe-assess-data` repo with per-prefix subdirs, or separate repos per team?
- [ ] **Dashboard trigger** — does `visualize-rfe` handle multiple prefixes, or do new teams need their own dashboard pipeline?
- [x] **Target Jira project key(s)** — **OpenShift RFE project** confirmed (2026-06-17 via Bill/Tony Slack conversation). Specific Jira project key TBD. Multi-team expansion shelved.

---

## Estimated Effort

| Work Item | Effort | Dependencies |
|-----------|--------|-------------|
| Parameterize `RHAIRFE` in 3 files | 0.5 days | None |
| ~~Inspect assess-rfe plugin~~ | ~~0.5 days~~ DONE | Inspected via container image 2026-06-16 |
| Org-pulse API contract check | 0.5 days | Access to org-pulse source |
| Per-team CI job blocks | 1 day | Phase 1 complete |
| Per-team Jira auth setup | 0.5 days/team | Pilot team identified |
| **Total for first new team** | **~3 days** | |

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-15 | Created as standalone project note | RFE assessor multi-team is its own workstream under org-pulse — deserves dedicated tracking separate from the main deployment effort |
| 2026-06-15 | Status: planned (not active) | Blocking questions remain (ai-impact layer, pilot team identification, Jira project keys TBD) |
| 2026-06-16 | Note corrected after repo review | Removed 5 phantom script references (setup-claude-ci.sh, run-claude.sh, stream-claude.py, otel-collector.py, otel-summary.py — none exist in repo). Fixed line numbers (removed them — they drift). Added OpenShell migration, OTEL telemetry, and supervisor workaround context. Updated Key Files table. |
| 2026-06-16 | assess-rfe plugin confirmed reusable | Inspected skill from container image. Scripts are parameterized (project key as CLI arg, Jira creds from env vars). RHAIRFE refs are documentation/examples only — overridden at runtime. Same cloudId (redhat.atlassian.net). Rubric is generic PM quality criteria. Only caveat: RHOAI platform vocabulary list in HOW criterion may cause slightly stricter scoring for non-RHOAI RFEs. |
| 2026-06-16 | Shelved — multi-team likely descoped | Direction shifted to single-team usage: point the assessor at one HP RFE Jira project (key TBD) rather than parameterizing for N teams. The multi-team CI matrix, per-team auth, and staggered scheduling are no longer needed. Core parameterization (replacing hardcoded RHAIRFE with a single new prefix) is still relevant when the Jira project is created. |
| 2026-06-17 | Upstream contribution over fork for assess-rfe | The assess-rfe skill is baked into the sandbox container image (`claude-sandbox:latest`), rebuilt via CI. Upstreaming `--jql`/`--labels` to `opendatahub-io/assess-rfe` is cleaner than forking — backward-compatible, benefits all users, and image rebuild picks it up. Cross-team contribution is a positive signal. Fallback: fork + custom image. |
| 2026-06-17 | ai-impact module blocker resolved | Will port AI Impact module from AI Eng layer into HP fork's core images (ENGPROD-10100). Also adding multi-team filtering to views (ENGPROD-10101). No upstream dependency needed. |
| 2026-06-17 | Epic and stories created | ENGPROD-10097 (epic) with 6 stories under PLATENG-108. Full dependency chain with blocking links. Stories 10098 (upstream PR) and 10099 (pipeline parameterization) are delegation-ready. |
| 2026-06-25 | GitLab runner setup investigated | Pipeline on gitlab.cee.redhat.com fails at Podman socket — `aipcc-k8s-cicd` runner can't run OpenShell (needs Podman). Need EC2-based runner (`aipcc` or `aipcc-small-x86_64` tag), but those are group runners for `redhat/rhel-ai`, not shared with our group. GCP service account created with Vertex AI permissions; CI vars `GCP_SERVICE_ACCOUNT_KEY` and `ANTHROPIC_VERTEX_PROJECT_ID` configured. Next: request RHAI team share EC2 runner with our group. See "Runner Infrastructure" section for full technical findings from RHAI thread. |
| 2026-06-26 | EC2 project runner approved — ENGPROD-10120 | SRE declined both fixing K8s runners and hosting as OpenShift CronJob — recommended unmanaged EC2 instead. Plan: RHEL 9 m5.large instance with shell executor GitLab runner registered as project runner (tag `rfe-assessor`). Podman runs natively on the VM, no container-in-container hacks. CI changes: swap tag from `aipcc-small-x86_64` to `rfe-assessor`, remove `image:` directive, drop rootless-podman workaround. ~$70/month always-on. Story created: [ENGPROD-10120](https://redhat.atlassian.net/browse/ENGPROD-10120), blocks ENGPROD-10102. |
| 2026-06-29 | New IT AWS account for runner VM (initial pick) | Current AWS account lives in PCO (engineering) org, not IT. Three options evaluated: (1) migrate PCO account to IT, (2) keep in PCO + shared external transit gateway (manual VPC, limited connectivity), (3) new IT-managed AWS account. Initially chose Option 3. IT-managed accounts get internal VPN/network connectivity automation on request. |
| 2026-06-30 | Going with new IT AWS account | Bill initially pushed back on a separately-accounted IT AWS account. Explored alternatives: deploying VMs alongside AppSRE clusters (hard policy — no unmanaged workloads, per aweiteka), K8s runners with buildah + elevated SCC. Ultimately decided to proceed with the new IT-managed AWS account. IT ticket: [UR0198029](https://redhat.service-now.com/help?id=rh_ticket&table=sc_request&sys_id=UR0198029). See "AWS Account & VPN Networking" in Runner Infrastructure section for full context. |
| 2026-06-30 | K8s runner path confirmed blocked without `CAP_SYS_ADMIN` | Analyzed CI job #55257223 failure log. Podman fails at `crun: mount proc to proc: Permission denied`. The `aipcc-k8s-build` SCC grants `CapEff: 00000000800005fb` — missing `CAP_SYS_ADMIN` (bit 21) and `CAP_NET_ADMIN` (bit 12). Buildah works because it doesn't create new namespaces; podman does. OpenShell requires podman's full runtime (detached exec, port binding, lifecycle mgmt). K8s path needs effectively `privileged` SCC — requires SRE request on OSD. EC2 runner remains the path of least resistance. |

---

## Key Files

| File | Purpose |
|------|---------|
| `.gitlab-ci.yml` | CI job definitions — test-rfe and assess-rfe jobs |
| `scripts/push-results.py` | Commits assessment results to data repo, manages retention policy |
| `scripts/push-to-org-pulse.py` | Pushes assessment data to org-pulse bulk API endpoint |
| `src/rfe_assessor/runner.py` | OpenShell sandbox execution engine + OTEL telemetry |
| `src/rfe_assessor/cli.py` | CLI entry point — arg parsing, model validation |
| `scripts/clone-data-repo.sh` | Clones results data repo (already team-agnostic) |

---

## Related Notes

- [[rhai-org-pulse]] — parent project: org-pulse deployment for HP
- [[rhai-org-pulse-deployment-plan]] — phased deployment plan (approved 2026-05-28)
- [[Org Pulse System Health Module - Hardcoded for RHOAI]] — system health module not portable (AI Eng layer)
- [[Release Registry Jira Projects Config Gap]] — release registry hardcoded to RHOAI projects, but has API workaround

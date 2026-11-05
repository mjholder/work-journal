---
type: knowledge
tags:
  - rfe-assessor
  - data-pipeline
  - agentic-ci
  - org-pulse
created: '2026-06-17'
---
# RFE Assessor Data Pipeline

A complete map of how data flows through the RFE quality assessment pipeline — from Jira tickets to Org Pulse dashboard.

> **Active target (2026-06-17):** Score all RFEs in the **OpenShift RFE project** on a quality rubric for leadership reporting. This is Path B below.

## Two Pipelines Feed Org Pulse (Path A vs Path B)

There are two separate systems that both feed the Org Pulse AI Impact module. They share the `assess-rfe` rubric scorer but serve different purposes:

| | Path A: rfe-creator | Path B: rfe-assessor |
|---|---|---|
| **Repo** | `jwforres/rfe-creator` (GitHub) | `redhat/rhel-ai/agentic-ci/rfe-assessor` (GitLab) |
| **What it does** | Developer tool — creates/reviews/submits RFEs, applies Jira labels | Headless CI pipeline — batch-scores all RFEs on quality rubric |
| **How data reaches Org Pulse** | Org Pulse **pulls from Jira** via `rfe-fetcher.js` → reads labels | rfe-assessor **pushes to Org Pulse** via `push-to-org-pulse.py` → bulk API |
| **Dashboard metrics** | Adoption % (AI involvement), label-based classification | Per-criterion quality scores, pass/fail, anti-patterns |
| **Trigger** | Developer runs `/rfe.create` or nightly CI (`/rfe.auto-fix`) | GitLab CI schedule or manual trigger |

**For the OpenShift RFE project, only Path B applies.** Path A is ruled out because no OpenShift RFEs were created using the rfe-creator AI skills — no labels exist, and adding them would require a process change (per Tony, 2026-06-17 Slack conversation).

**Manual scoring run completed** (2026-06-17): Tony and Pratik ran the assess-rfe skill manually and produced CSV + HTML output for the OpenShift RFE project, demonstrating the pipeline works end-to-end.

---

The rest of this note documents **Path B (rfe-assessor)** in detail, as it exists today targeting `RHAIRFE-*`. Parameterizing it for the OpenShift RFE project key is tracked by [[assess-rfe]] and [ENGPROD-10099](https://redhat.atlassian.net/browse/ENGPROD-10099).

## Architecture Overview

```
                         TRIGGER: GitLab CI schedule or manual
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GitLab CI Pipeline (rfe-assessor)                │
│                                                                     │
│  ┌──────────┐    ┌──────────────────────────────────────────────┐  │
│  │  SETUP   │    │            OpenShell Sandbox                  │  │
│  │          │    │  ┌──────────┐    ┌────────────────────────┐  │  │
│  │ Clone    │    │  │dump_jira │    │ Claude (assess-rfe)    │  │  │
│  │ data repo│    │  │          │    │                        │  │  │
│  │ Stage    │───▶│  │ Jira ───▶│───▶│ ~30 scorer agents      │  │  │
│  │ tokens   │    │  │ API      │    │ score each RFE         │  │  │
│  │ Install  │    │  └──────────┘    │ ───▶ .result.md files  │  │  │
│  │ CLI      │    │                  │ ───▶ scores.csv        │  │  │
│  └──────────┘    │                  └────────────────────────┘  │  │
│                  └──────────────────────────────────────────────┘  │
│                                      │                             │
│                           ┌──────────▼──────────┐                 │
│                           │  push-results.py    │                 │
│                           │  (git commit+push)  │────▶ rfe-assess-data repo
│                           └──────────┬──────────┘                 │
│                                      │                             │
│                           ┌──────────▼──────────┐                 │
│                           │push-to-org-pulse.py │                 │
│                           │  (HTTP POST)        │────▶ Org Pulse API
│                           └─────────────────────┘                 │
│                                      │                             │
│                           ┌──────────▼──────────┐                 │
│                           │  build-dashboard    │                 │
│                           │  (trigger job)      │────▶ visualize-rfe pipeline
│                           └─────────────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Three Repos Involved

| Repo | Location | Role |
|------|----------|------|
| **rfe-assessor** | GitLab: `redhat/rhel-ai/agentic-ci/rfe-assessor` | Pipeline orchestration, CLI, post-processing scripts |
| **assess-rfe** | GitHub: `opendatahub-io/assess-rfe` | Claude Code skill baked into sandbox image — does the actual Jira fetch + AI scoring |
| **rfe-assess-data** | GitLab: `redhat/rhel-ai/agentic-ci/rfe-assess-data` | Versioned history of assessment results |

## 1. Trigger Mechanism

**How it starts:** GitLab CI pipeline on the rfe-assessor repo.

Two trigger modes:
- **Scheduled** — `CI_PIPELINE_SOURCE == "schedule"` (configured in GitLab UI)
- **Manual** — click "Play" on the job in the GitLab UI

Constraints:
- `resource_group: assess-rfe` — serializes execution, only one assessment can run at a time
- `timeout: 6h` for the full production run, `1h` for the test job
- Runner tags: `aipcc-small-x86_64`

CI stages (sequential):
1. `lint` — Python tests (only on MRs/main pushes, not on scheduled runs)
2. `assess` — The actual assessment work
3. `trigger` — Downstream dashboard build

## 2. Setup Phase

The CI `.assess-setup` before_script does four things:

**a) Configure podman** — Docker executor lacks user-namespace privileges for rootless podman. Disables namespace remapping and switches to VFS storage driver.

**b) Install rfe-assessor** — `pip install .` installs the Python package, making the `rfe-assessor` CLI available.

**c) Stage the push token** — Saves `$RESULTS_PUSH_TOKEN` to `/root/.tokens/results` then `unset`s it from the environment. This prevents Claude inside the sandbox from accessing it. The post-processing scripts re-read it from file later.

**d) Clone the data repo** — `clone-data-repo.sh` shallow-clones `rfe-assess-data` into `assessments/` using the staged token for HTTPS auth (`https://bot:{token}@gitlab.com/{repo}.git`).

## 3. Assessment Execution (Inside the Sandbox)

The CI script runs: `rfe-assessor "/assess-rfe:assess-rfe RHAIRFE-*"`

### CLI flow (`cli.py` → `runner.py`)

1. **GCP credential normalization** — Copies `AIPCC_CICD_GCP_SERVICE_ACCOUNT_KEY` (GitLab File variable, path to JSON key) to `~/.config/gcloud/application_default_credentials.json`. Sets `ANTHROPIC_VERTEX_PROJECT_ID` from `AIPCC_CICD_GCP_PROJECT_ID`. This is how Claude authenticates to Vertex AI.

2. **Collect environment** — Gathers `JIRA_SERVER`, `JIRA_TOKEN`, `JIRA_USER`. Sets `AGENT_ENABLED_PLUGINS=assess-rfe`.

3. **Create OpenShell backend** — Spins up a containerized sandbox:
   - Image: `quay.io/aipcc/agentic-ci/claude-sandbox:latest`
   - Network policy: only allows `redhat.atlassian.net:443` (`.agentic-ci/openshell-policy.yml`)
   - Custom supervisor: `quay.io/mprpic/openshell-supervisor:pr1763` (GCP provider support, pending upstream merge)

4. **Start OTEL collector** — Listens for OpenTelemetry spans from Claude, tracking token usage and cost in real time. Output saved as `claude-otel.jsonl` artifact (30-day retention).

5. **Run the agent** — `backend.run(prompt="/assess-rfe:assess-rfe RHAIRFE-*", model="claude-opus-4-6", streaming=True)`

### What happens inside the sandbox (assess-rfe skill)

The skill lives at `/sandbox/.claude-seed/cache/opendatahub-skills/assess-rfe/1.0.0/` inside the container image.

a. **`dump_jira.py RHAIRFE`** — Connects to Jira at `redhat.atlassian.net` using passed env vars. JQL: `project=RHAIRFE ORDER BY key ASC`. Fetches `summary` and `description` fields only.

b. **Scorer agents** — Spawns ~30 concurrent Claude sub-agents. Each scores one RFE against five criteria:

| Criterion | Range | What It Measures |
|-----------|-------|-----------------|
| What | 0-2 | Outcome clarity |
| Why | 0-2 | Business justification |
| Open to How | 0-2 | Technical approach without being prescriptive |
| Not a Task | 0-2 | Actually a feature request, not a task |
| Right-sized | 0-2 | Appropriate scope |
| **Total** | **0-10** | Sum of all criteria |

**Pass/Fail rule:** An RFE **fails** if ANY criterion scores 0, regardless of total. This means a total of 8 still fails if one criterion is zero (e.g., RFE-9247: 2,0,2,2,2 = 8 FAIL). Verified against Tony's manual run data (207 RFEs from the `RFE` project).

c. **Output files** — Each agent writes `{ISSUE_KEY}.result.md` with a structured markdown table:

```markdown
| Criterion | Score | Notes |
|-----------|-------|-------|
| What | 2/2 | Clear requirements |
| Why | 1/2 | Business value mentioned but... |
| Open to How | 2/2 | Implementation open |
| Not a Task | 2/2 | Properly scoped |
| Right-sized | 2/2 | Reasonable scope |
| **Total** | **9/10** | **PASS** |

### Verdict
[Assessment summary paragraph]

### Feedback
[Actionable recommendations for the requester]
```

d. **Aggregation** — `parse_results.py` + `summarize_run.py` aggregate into `scores.csv` and create a `current` symlink pointing to the timestamped run directory.

**CSV format note:** The automated pipeline produces `scores.csv` with mixed-case headers: `ID, Title, WHAT, WHY, HOW, Task, Size, Total, Pass_Fail` — this is what `push-to-org-pulse.py` expects (see `parse_scores_csv()`). Tony's manual run (2026-06-17) produced a CSV with **lowercase headers and no Title column**: `id,what,why,how,task,size,total,pass_fail`. To push Tony's data through the existing script, either reformat the CSV headers to match or add case-insensitive header handling to `push-to-org-pulse.py`.

### Result directory structure

```
assessments/RHAIRFE/
├── current -> 20260617-143000      # Symlink to latest run
├── 20260617-143000/                # This run
│   ├── RHAIRFE-1.result.md
│   ├── RHAIRFE-2.result.md
│   ├── ...
│   └── scores.csv
└── 20260616-190000/                # Previous run
```

## 4. Results Storage (`push-results.py`)

After the sandbox completes, runs in the CI job context.

### Spot checks (validation)
- `RHAIRFE/current` symlink must exist and point to valid directory
- At least one `.result.md` file must exist
- `scores.csv` must exist (indicates complete run)

### Retention policy (applied before commit)
- **Last 7 days**: Keep the latest run per day
- **7 days to 1 year**: Keep the latest run per ISO calendar week
- **Older than 1 year**: Delete
- **Protected**: `current` symlink target is never pruned

### Git workflow
1. Re-reads push token from `/root/.tokens/results`
2. Sets remote URL to `https://bot:{token}@gitlab.com/{repo}.git`
3. `git add -A` (stages results + pruned deletions)
4. `git commit -m "RHAIRFE bulk assessment run\n\nCo-Authored-By: Claude Opus 4.6..."`
5. `git push` with retry (3 attempts, `git pull --rebase` between failures, no force push)

## 5. Org Pulse Push (`push-to-org-pulse.py`)

Runs only if `ORG_PULSE_URL` and `ORG_PULSE_API_TOKEN` are both set. **Non-blocking** — on failure, logs a warning and pipeline continues (always exits 0).

### Data transformation pipeline

1. **Find latest run** — Reads `assessments/RHAIRFE/current` symlink
2. **Parse `scores.csv`** — Per-issue scores
3. **Parse `.result.md` files** — Extracts criterionNotes (regex from markdown table), verdict (`### Verdict`), feedback (`### Feedback`)
4. **Name mapping** — Handles LLM case variations: "Open to How" → `how`, "Not a Task" → `task`, "Right-sized" → `size`
5. **Derive anti-patterns** — When any criterion score is 0:

| Score=0 | Anti-Pattern |
|---------|-------------|
| why | "WHY Void" |
| task | "Task Masquerade" |
| what | "Unclear Outcome" |
| how | "Architecture Prescription" |
| size | "Kitchen-Sink Scope" |

6. **Derive timestamp** — From directory name: `20260617-143000` → `2026-06-17T14:30:00Z`
7. **Build payload** — Each assessment becomes:

```json
{
  "id": "RHAIRFE-123",
  "scores": {"what": 2, "why": 1, "how": 2, "task": 1, "size": 0},
  "total": 6,
  "passFail": "PASS",
  "antiPatterns": ["Kitchen-Sink Scope"],
  "criterionNotes": {"what": "Clear outcome", "why": "...", ...},
  "verdict": "This RFE is well-structured...",
  "feedback": "Consider narrowing the scope...",
  "assessedAt": "2026-06-17T14:30:00Z"
}
```

8. **POST in batches of 25** to `{ORG_PULSE_URL}/api/modules/ai-impact/assessments/bulk`
   - Auth: `Authorization: Bearer {ORG_PULSE_API_TOKEN}` (read from env, never CLI arg)
   - Timeout: 60s per request
   - API returns `created`, `updated`, `unchanged` counts per batch

## 6. Dashboard Trigger

`build-dashboard` job runs after `assess-rfe` completes. Triggers downstream `visualize-rfe` pipeline (`redhat/rhel-ai/agentic-ci/visualize-rfe`, `main` branch) — builds a static dashboard from the data repo.

## Auth & Secrets Map

| Secret | Stored In | Used By | Purpose |
|--------|-----------|---------|---------|
| `JIRA_API_TOKEN` | GitLab CI var (Vault backing: `engineering-productivity/hp-org-pulse/JIRA`) | `runner.py` → sandbox env | Jira API auth |
| `JIRA_USER` | GitLab CI var (optional) — bot account email, same Vault entry | `runner.py` → sandbox env | Jira username |
| `AIPCC_CICD_GCP_SERVICE_ACCOUNT_KEY` | GitLab File var | `cli.py` → ADC path | Vertex AI (Claude) auth |
| `AIPCC_CICD_GCP_PROJECT_ID` | GitLab CI var | `cli.py` → `ANTHROPIC_VERTEX_PROJECT_ID` | Vertex AI project |
| `RESULTS_PUSH_TOKEN` | GitLab CI var | `clone-data-repo.sh`, `push-results.py` | Data repo push auth |
| `ORG_PULSE_API_TOKEN` | GitLab CI var | `push-to-org-pulse.py` (env only) | Org Pulse bulk API auth |
| `ORG_PULSE_URL` | GitLab CI var | `push-to-org-pulse.py` | Org Pulse base URL |

**Security pattern**: `RESULTS_PUSH_TOKEN` is saved to file then `unset` from environment before the sandbox starts. Claude can't access it. Post-processing scripts re-read from file.

### Jira token: silent truncation failure mode

**The GitLab CI/CD variable is the live value.** Vault is only the backing
record — rotating the Vault entry does not propagate, the CI variable on
`hcm-engprod/rfe-assessor` has to be updated separately. Jira Cloud caps API
tokens at a 90-day expiry, so this comes round roughly quarterly.

**A bad Jira token does not throw an auth error.** Expired, revoked, or
over-scoped tokens all get `200` back with a silently incomplete result set.
That propagates straight through the pipeline:

```
bad token → dump_jira.py writes a short cache (no error)
          → setup_run.py picks the newest N from whatever is in the cache
          → scorers run, scores.csv is written, push succeeds
          → run looks completely healthy, just missing issues
```

`setup_run.py --limit N --newest` makes this worse rather than louder: it always
finds N keys, so it just reaches further back in time to fill the quota. The
only visible symptom is that the assessed key range spans more keys than the
limit.

Two sightings:

- **2026-09-21** — org-pulse CVE Triage returned ~50 CVEs instead of 100k+. Bot
  account token had been revoked. Confirmed by re-running the same JQL under a
  different token.
- **2026-10-07** — RFE run `20261007-154237` held 500 results spanning keys
  9215..9990 (776 possible). Of 276 absent keys, a 15-key sample split cleanly:
  every absent issue carried Jira security level `10034` ("Red Hat Employee and
  Contractors only"), every present issue carried none. Consistent with the
  pipeline token lacking that security level — a personal account sees all of
  them.

**Diagnostic**: run `dump_jira.py` locally under the CI token and compare its
issue count to the same JQL under a known-good token. Testing with a personal
token will not reproduce it.

## Timing & Lifecycle

| Phase | Duration | What Happens |
|-------|----------|--------------|
| Setup | ~2 min | Clone data repo, install CLI, stage tokens |
| Sandbox startup | ~1 min | Pull image, create OpenShell container |
| Jira fetch | ~1-5 min | `dump_jira.py` queries Jira API |
| AI scoring | **3-5 hours** | ~30 concurrent Claude scorer agents evaluate all RFEs |
| Parse & summarize | ~5 min | Aggregate results into scores.csv |
| Push results | ~1 min | Git commit + push to data repo |
| Org Pulse push | ~1 min | HTTP POST batches to bulk API |
| Dashboard trigger | ~0 min | Trigger downstream pipeline |
| **Total** | **~4-6 hours** | Dominated by AI scoring time |

## Key Source Files

| File | Purpose |
|------|---------|
| `.gitlab-ci.yml` | CI job definitions, triggers, env vars |
| `src/rfe_assessor/cli.py` | CLI entry point, GCP credential handling |
| `src/rfe_assessor/runner.py` | OpenShell sandbox lifecycle, OTEL setup |
| `scripts/clone-data-repo.sh` | Shallow-clone data repo with token auth |
| `scripts/push-results.py` | Retention policy, git commit/push |
| `scripts/push-to-org-pulse.py` | Parse results → JSON, batch POST to API |
| `scripts/ci-monitor.py` | Terminal UI for monitoring runs (~2500 lines) |
| `.agentic-ci/openshell-policy.yml` | Network whitelist (Jira only) |

## Hardcoded References (for parameterization)

All `RHAIRFE` references are in three files:
- `.gitlab-ci.yml` — `RHAIRFE-*` in CLAUDE_PROMPT (2 refs)
- `scripts/push-results.py` — `RHAIRFE` directory path (5 refs)
- `scripts/push-to-org-pulse.py` — `RHAIRFE/current` path (3 refs)

See [[assess-rfe]] for the active project note. The multi-team extension plan ([[rfe-assessor-multi-team]]) is shelved — current focus is single-team (OpenShift RFE project).

## Related Notes

- [[assess-rfe]] — assess-rfe plugin details, upstream contribution plan
- [[rfe-assessor-multi-team]] — multi-team extension plan (shelved)
- [[rhai-org-pulse]] — parent project: Org Pulse deployment

---
type: project
status: active
tags:
  - project
  - org-pulse
  - productization-decision
  - skill-integration
  - ai
created: 2026-08-25
---
# Project: Org Pulse — Productization Decision Maker Skill Integration

## Overview

Integrate the tailwind `productization-decision` (PDM) skill into the [[rhai-org-pulse]] framework. This is **skill integration #1 of 2** proposed by PM Daniel Messer (the Jira Status skill is #2), and it extends Org Pulse's existing "assess planned work" philosophy — the same one behind the RFE Quality Assessment Pipeline ([ENGPROD-10097](https://redhat.atlassian.net/browse/ENGPROD-10097) / `assess-rfe`) — from *"is this RFE well-formed?"* to *"should we productize this capability?"*.

The skill gathers multi-source evidence in parallel (Jira customer demand, upstream/technical readiness, competitive landscape, roadmap alignment) and scores a capability against a **RICE + Kano + TRL + WSJF** rubric to produce a productization recommendation for PMs.

**Epic:** [ENGPROD-10304](https://redhat.atlassian.net/browse/ENGPROD-10304) — In Progress (2026-08-25).

### Key Links

- **Source skill:** `~/git_repos/tailwind/skills/productization-decision/SKILL.md` (local checkout)
- **Synthetic example:** `~/git_repos/tailwind/examples/productization-decision/pda-example.md`
- **Config reference:** `~/git_repos/tailwind/docs/configuration.md` (Tier A = 3 keys)
- **BU-context examples:** `~/git_repos/tailwind/context/red-hat-ai-config.yaml`, `bu-config-template.yaml`
- **Packaging precedent:** `~/git_repos/assess-rfe/` (`Containerfile` + `Makefile` + `.claude-plugin/` + `.skillsaw.yaml`)
- **First captured artifact:** `~/git_repos/tailwind/artifacts/pda/HP-PDA-post-quantum-cryptography-2026-08-25.md`

## Current Status

**Phase: Spike ([ENGPROD-10306](https://redhat.atlassian.net/browse/ENGPROD-10306)) — In Progress.**

Skill recon complete and a first end-to-end **output-capture run** is done (PQC validation capability). The recommendation data model is now concrete and drives the surfacing story. Next: write the spike design note (ADR) and start HP BU-context.

### Skill breakdown (all under the epic)

| Ticket | Type | Scope | Status |
|--------|------|-------|--------|
| [ENGPROD-10306](https://redhat.atlassian.net/browse/ENGPROD-10306) | Spike | Assess skill + design Org Pulse integration | In Progress |
| [ENGPROD-10307](https://redhat.atlassian.net/browse/ENGPROD-10307) | Story | Org Pulse-native config source (replace `tailwind.json`) | New |
| [ENGPROD-10308](https://redhat.atlassian.net/browse/ENGPROD-10308) | Story | Supply HP BU-context | New |
| [ENGPROD-10309](https://redhat.atlassian.net/browse/ENGPROD-10309) | Story | Wire evidence integrations + parameterize hardcoded values | New |
| [ENGPROD-10310](https://redhat.atlassian.net/browse/ENGPROD-10310) | Story | Surface the recommendation output in Org Pulse | New |
| [ENGPROD-10311](https://redhat.atlassian.net/browse/ENGPROD-10311) | Story | Package into sandbox image + write SOP | New |

## Recommendation Data Model (from the first run)

The canonical output is a Markdown artifact at `{artifacts_dir}/pda/[doc_prefix]-PDA-[capability]-[date].md`. This is the schema Org Pulse must surface ([ENGPROD-10310](https://redhat.atlassian.net/browse/ENGPROD-10310)):

- **Header:** `capability`, `recommendation` (Productize / Conditional / Monitor / Defer), `kano`, `weighted_score`, `wsjf`, `trl`, `sp_band`
- **Scoring matrix:** 5 dimensions — Customer Demand (25%), Upstream Readiness/TRL (20%), Competitive Pressure (20%), Strategic Alignment (20%), Engineering Effort/inverse (15%) — each `{score 1–5, weight, evidence}`
- **Evidence sections:** demand (Jira keys + customers), upstream, competitive, strategic, roadmap
- **Risks**, **recommended next steps**
- **Decision-health lifecycle:** Open → Investigating → Decided → Implementing → Validating → Closed

Recommendation bands: 4.0–5.0 Productize · 3.0–3.9 Conditional · 2.0–2.9 Monitor · 1.0–1.9 Defer.

Maps cleanly onto the existing `assess-rfe → AI Impact module` POST pattern — likely an incremental module, matching the epic's "no new dashboard module" constraint.

## Integration Seams / Decoupling Plan

1. **Config surface** — `~/.config/tailwind/tailwind.json`. Tier A is only 3 keys (`strategy_projects`, `doc_prefix`, `gemini_model`). Replace with an Org Pulse-native config source ([ENGPROD-10307](https://redhat.atlassian.net/browse/ENGPROD-10307)).
2. **BU-context** — `overlay/context.yaml` (channels `jira-strats` / `jira-rfes` / `midstream-github` + `component_repos`); currently a `.gitkeep`. Build HP version modeled on `red-hat-ai-config.yaml` ([ENGPROD-10308](https://redhat.atlassian.net/browse/ENGPROD-10308)).
3. **Atlassian MCP tool-name mismatch** — skill calls `mcp__atlassian__*`; our env exposes `mcp__plugin_scrooge_atlassian__*`. Needs a shim/config in the sandbox ([ENGPROD-10309](https://redhat.atlassian.net/browse/ENGPROD-10309)).
4. **Gemini** — **not required**. WebSearch substitutes well for the upstream/competitive research agents and is what the Org Pulse sandbox will realistically have. **De-risks the epic's Gemini cost/availability concern.**
5. **Hardcoded `redhat.atlassian.net`** — epic/spike risk appears **overstated**; grep found none in the skill. Jira base URL is `jira_host` (REST-only fallback) and docs prescribe MCP OAuth (no host needed).
6. **Packaging** — mirror `assess-rfe` sandbox-image bake ([ENGPROD-10311](https://redhat.atlassian.net/browse/ENGPROD-10311)).

## Recent Progress

### 2026-08-25
- Moved epic [ENGPROD-10304](https://redhat.atlassian.net/browse/ENGPROD-10304) and spike [ENGPROD-10306](https://redhat.atlassian.net/browse/ENGPROD-10306) to **In Progress**.
- **Skill recon**: read `SKILL.md`, the synthetic example, and `docs/configuration.md`. Mapped all tailwind coupling points and the packaging precedent.
- **First output-capture run** (PQC certificate support, WebSearch substituted for Gemini): 3 evidence agents in parallel (Demand via Atlassian MCP; Upstream + Competitive via WebSearch). Result **Productize, 4.2/5.0, WSJF 1.5, Kano Must-Have**. Artifact captured.
- **Finding**: PQC demand is dense in Red Hat Jira (~11 named-customer records: DISA, DoD, GSA, Peraton, Entrust, Verizon, Barclays) — stress-tested the pipeline on real evidence. Note: strongest signals live as TRIP trip-report notes, not formal RFEs — affects `jira-rfes` channel design.

## Outstanding Tasks

- [ ] Write the spike design note / ADR (packaging approach + decoupling plan + output-surfacing recommendation) — deliverable for [ENGPROD-10306](https://redhat.atlassian.net/browse/ENGPROD-10306)
- [ ] Build the HP BU-context `context.yaml` and re-run against a real HP capability ([ENGPROD-10308](https://redhat.atlassian.net/browse/ENGPROD-10308))
- [ ] Define the Org Pulse output contract (JSON schema + POST shape vs AI Impact module) ([ENGPROD-10310](https://redhat.atlassian.net/browse/ENGPROD-10310))
- [ ] Resolve the Atlassian MCP tool-name shim in the sandbox ([ENGPROD-10309](https://redhat.atlassian.net/browse/ENGPROD-10309))
- [ ] Convert strongest TRIP customer signals into formal RFEs so demand is structured (data-quality gap)

## Notes

- Related umbrella project: [[rhai-org-pulse]]. This file tracks the PDM skill integration specifically.
- Rubric customization follows the same pattern as `assess-rfe`: fork → tweak rubric → build custom sandbox image → point at it via `--image`.
- Gemini being optional is the single biggest positive finding — it removes the main experimental-maturity risk from the epic.

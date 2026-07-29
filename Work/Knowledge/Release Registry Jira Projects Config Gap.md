---
date: '2026-06-03'
type: knowledge
tags:
  - org-pulse
  - releases
  - jira
  - config-gap
---
# Release Registry — Missing Jira Projects Config UI

## The Problem

The release registry's "Resolve Jira Versions" feature scans Jira projects for version strings and maps them to registry releases. By default it only scans `RHAISTRAT` and `RHOAIENG` (hardcoded in `registry-config.js`). To add other projects, you need to update the config — but there's no UI for it.

## What Exists

The backend is fully wired:

- `GET /api/modules/releases/registry/config` — returns current `jiraProjects` array
- `POST /api/modules/releases/registry/config` — accepts `{ "jiraProjects": ["PROJ1", "PROJ2", ...] }`
- Config stored in `releases/registry-config.json` via storage abstraction
- Defaults: `['RHAISTRAT', 'RHOAIENG']` in `DEFAULT_JIRA_PROJECTS`

The RegistryView has two tabs (Releases, Hygiene Rules) but no settings/config tab.

## Workaround

Call the API directly:

```bash
curl -X POST http://localhost:3001/api/modules/releases/registry/config \
  -H 'Content-Type: application/json' \
  -d '{"jiraProjects": ["RHAISTRAT", "RHOAIENG", "YOURPROJECT"]}'
```

Then re-run "Resolve Jira Versions" from the UI.

## Future Fix

Add a config section to RegistryView — either a third tab or a settings area near the "Resolve Jira Versions" button — so release managers can edit the Jira projects list without hitting the API directly.

## Key Files

- `modules/releases/server/registry-config.js` — config storage + defaults
- `modules/releases/server/registry.js` — resolve endpoint (lines ~616-644)
- `modules/releases/client/views/RegistryView.vue` — UI (no config panel)

## Related

- [[rhai-org-pulse]] — parent project
- [[Org Pulse System Health Module - Hardcoded for RHOAI]] — similar portability issue, but worse (no backend API at all)

---
type: project
status: active
tags:
  - project
---
# Project: Matomo Analytics Fix

## Overview

After the backstage upgrade (RHDH 1.9), the matomo analytics plugin stopped tracking visits. The plugin was changed from `@janus-idp/backstage-plugin-analytics-module-matomo@1.3.1` to the community version via the `rhdh-plugin-export-overlays` OCI registry. The root cause is that the `rhdh-plugin-export-overlays` repo is missing the overlay directory for the matomo plugin, so the OCI package loads as an empty shell — scalprum loads the JS bundle but never registers the analytics API factory.

## Current Status

**Blocked (2026-05-26):** Local e2e test passing with v1.28.2 + overlay, but RHDH is on Backstage 1.49.x and the plugin targets Backstage 1.50.x. Can't proceed with the overlay PR until the version gap is resolved.

Upstream PR #8566 merged, v1.28.2 published to npm with NFS migration. Local testing confirmed the overlay is still required — the NFS migration added `createPlugin({apis: [MatomoAnalyticsApi]})` which auto-registers the analytics API when the module loads, causing "duplicate or forbidden API factory" errors if scalprum also tries to register via `apiFactories` or `analyticsApiExtensions` config. The overlay isolates the export to just `matomoAnalyticsApi` (the factory alone), avoiding the conflict. Matomo tracking events are now flowing from a local RHDH instance to a local Matomo server.

## Root Cause Analysis

The `rhdh-plugin-export-overlays` repo (`workspaces/analytics/plugins-list.yaml`) lists 4 analytics plugins:
- `plugins/analytics-module-ga4` — has overlay directory
- `plugins/analytics-module-matomo` — **MISSING overlay directory**
- `plugins/analytics-module-newrelic-browser` — has overlay directory
- `plugins/analytics-provider-segment` — has overlay directory

Without the overlay directory, the OCI build produces a package where:
- `dist-scalprum/plugin-manifest.json` has `"extensions": []` — nothing for scalprum to auto-register
- The `PluginRoot` exports `MatomoAnalyticsApi` (a legacy `createApiFactory`) but scalprum doesn't know to register it
- The alpha export (new frontend system with `AnalyticsImplementationBlueprint`) exists in `dist/` but scalprum uses `dist-scalprum/`

Result: plugin JS loads, but the analytics API factory is never registered, matomo.js is never injected, and no events reach the matomo server.

## Fix Plan

### Step 1: Contribute overlay files to rhdh-plugin-export-overlays

**Repo:** https://github.com/redhat-developer/rhdh-plugin-export-overlays
**Location:** `workspaces/analytics/plugins/analytics-module-matomo/`

Create three files following the GA4 plugin pattern (`plugins/analytics-module-ga4/`):

**`scalprum-config.json`:**
```json
{
  "name": "backstage-community.plugin-analytics-module-matomo",
  "exposedModules": {
    "PluginRoot": "./src/api.ts"
  }
}
```

**`overlay/src/api.ts`:**
```typescript
import {
  AnyApiFactory,
  analyticsApiRef,
  configApiRef,
  createApiFactory,
  identityApiRef,
} from '@backstage/core-plugin-api';
import { MatomoAnalytics } from './apis/implementations/AnalyticsApi';

export const MatomoAnalyticsApi: AnyApiFactory = createApiFactory({
  api: analyticsApiRef,
  deps: { configApi: configApiRef, identityApi: identityApiRef },
  factory: ({ configApi, identityApi }) =>
    MatomoAnalytics.fromConfig(configApi, { identityApi }),
});
```

**`app-config.dynamic.yaml`:**
```yaml
dynamicPlugins:
  frontend:
    backstage-community.plugin-analytics-module-matomo:
      apiFactories:
        - importName: MatomoAnalyticsApi
```

### Step 2: Wait for new OCI build

Once the PR is merged, a new OCI image will be built with the overlay applied.

### Step 3: Update app-interface

Update `resources/services/backstage/stage/dynamic-plugins.configmap.yml` to reference the new OCI image tag and verify tracking works in stage.

### Step 4: Deploy to prod

Update `resources/services/backstage/prod/dynamic-plugins.configmap.yml` with the same changes.

## Config changes already deployed to stage

These were deployed during investigation. They aren't the fix but are needed for the plugin to work correctly once the overlay is in place:

- Added `enhancedTracking: true`, `identity: optional`, `deferInitialPageView: true` to matomo config
- Added `connect-src` to CSP configuration

## Upstream PR: NFS Migration (2026-04-30)

Changed approach from auto-registration to full NFS migration per maintainer feedback. Key changes:
- Moved NFS code from `module.ts` into `plugin.ts` using `createFrontendPlugin` (not `createFrontendModule`)
- Changed `backstage.role` from `frontend-plugin-module` to `frontend-plugin`
- Deleted `module.ts`, updated `alpha.ts` to export from `./plugin`
- Updated changeset, README, and API reports
- Pattern follows Segment PR #5286 exactly
- `MatomoAnalytics` class already implemented both `AnalyticsApi` and `AnalyticsImplementation` — no changes needed there

## Outstanding Tasks

- [x] Push updated branch and update upstream PR
- [x] Get maintainer approval on NFS migration approach
- [x] Once merged, verify RHDH can consume the `/alpha` export for NFS
- [x] Upstream PR #8566 merged, v1.28.2 published to npm (2026-05-12)
- [x] Verified locally: `rhdh-cli plugin export` produces valid scalprum assets without overlay
- [x] Local e2e test: RHDH loads the plugin from locally-built dist-dynamic (podman-compose setup at `workspaces/analytics/local-e2e/`)
- [x] Confirmed overlay IS still needed — NFS `createPlugin({apis: [...]})` conflicts with scalprum registration (duplicate/forbidden API factory)
- [x] Rebuilt plugin with overlay (`scalprum-config.json` → `apiFactory.ts`), confirmed matomo tracking works end-to-end locally
- [ ] Create PR in rhdh-plugin-export-overlays: update source.json (repo-ref to include v1.28.2), update metadata (role: frontend-plugin, version: 1.28.2), keep overlay (apiFactory.ts + scalprum-config.json + app-config.dynamic.yaml)
- [ ] Update app-interface stage config to test
- [ ] Deploy to prod once verified in stage

## Key References

- **rhdh-plugin-export-overlays repo:** https://github.com/redhat-developer/rhdh-plugin-export-overlays
- **GA4 overlay (pattern to follow):** `workspaces/analytics/plugins/analytics-module-ga4/`
- **Upstream community plugin:** https://github.com/backstage/community-plugins/tree/main/workspaces/analytics/plugins/analytics-module-matomo
- **App-interface matomo config (stage):** `resources/services/backstage/stage/dynamic-plugins.configmap.yml` (lines 912-925)
- **App-interface matomo config (prod):** `resources/services/backstage/prod/dynamic-plugins.configmap.yml` (lines 830-842)
- **App-interface matomo saas:** `data/services/backstage/cicd/saas-matomo.yml`

## Notes

- The old `dynamicPlugins.frontend` config with `janus-idp.backstage-plugin-analytics-module-matomo` was removed during earlier debugging. It can't be re-added because the plugin name changed, and adding it with the old name causes duplicate API registration errors.
- The correct scalprum plugin name is `backstage-community.plugin-analytics-module-matomo` (from `dist-scalprum/plugin-manifest.json`)
- The OCI package was extracted and inspected at `/tmp/matomo-plugin-inspect/extracted/` during the investigation

### NFS Migration Discovery (2026-05-12)

**The overlay is still required even after the NFS migration.** Key findings:

1. **NFS `createPlugin({apis: [MatomoAnalyticsApi]})` causes conflicts:** When scalprum loads the PluginRoot module that includes this call, the analytics API factory gets registered automatically. Any additional config-driven registration (`apiFactories` or `analyticsApiExtensions`) is a duplicate → "duplicate or forbidden API factory" error.

2. **Segment plugin works differently:** The segment plugin's `createPlugin()` does NOT include `apis: [...]`, so `analyticsApiExtensions` config works without conflict. Matomo's NFS migration included `apis: [MatomoAnalyticsApi]` in the legacy `createPlugin` for backward compatibility.

3. **Without any config:** The plugin loads (scalprum serves the JS) but the API factory is not actually activated by the RHDH analytics framework — no tracking occurs. The `createPlugin({apis: [...]})` creates the plugin object but RHDH doesn't install it into the app automatically.

4. **Solution: overlay isolates the export.** The `scalprum-config.json` points PluginRoot to `./src/apiFactory.ts` which only exports `matomoAnalyticsApi` (the `createApiFactory` result). No `createPlugin` in scope = no conflict. Then `apiFactories: [{importName: matomoAnalyticsApi}]` config registers it cleanly.

5. **Matomo `host` config must NOT include protocol.** The plugin prepends `//` to make it protocol-relative. Setting `host: http://localhost:8080` produces `//http://localhost:8080/matomo.js` (malformed). Correct: `host: localhost:8080`.

### Local E2E Test Environment

Podman-compose setup at `rhdh-plugin-export-overlays/workspaces/analytics/local-e2e/`:
- **MariaDB** (mariadb:11) — Matomo database
- **Matomo** (matomo:5-apache) — Analytics server at `localhost:8080`
- **RHDH** (rhdh:next) — Developer Hub at `localhost:7007` with matomo plugin mounted from locally-built `dist-dynamic/`

Plugin built with: `npx @red-hat-developer-hub/cli@1.10.6 plugin export --no-install --scalprum-config <overlay-scalprum-config.json>` after copying `overlay/src/apiFactory.ts` into the upstream source.

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

**Upstream PR updated — migrating plugin to New Frontend System (NFS).**

Initial PR added auto-registration of the API factory via `apis: [MatomoAnalyticsApi]`. Community plugin maintainers reviewed and asked us to instead migrate the plugin to the New Frontend System, following the Segment analytics provider PR (#5286) as a pattern. The branch has been reworked to use `createFrontendPlugin` + `AnalyticsImplementationBlueprint` instead of the legacy auto-registration approach. The overlay approach (rhdh-plugin-export-overlays) may no longer be needed once the NFS migration lands — RHDH should be able to use the plugin's `/alpha` export directly.

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

- [ ] Push updated branch and update upstream PR
- [ ] Get maintainer approval on NFS migration approach
- [ ] Once merged, verify RHDH can consume the `/alpha` export for NFS
- [ ] If RHDH uses NFS: no overlay needed; if still legacy: create overlay PR for rhdh-plugin-export-overlays
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

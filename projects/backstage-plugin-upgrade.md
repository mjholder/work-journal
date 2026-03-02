# Project: Backstage Plugin Upgrade

**JIRA:** ENGPROD-8917

## Overview

Upgrading all backstage plugins to latest versions. Each plugin goes through an 8-step process:
1. Rebootstrap/update locally
2. Test locally
3. Create pre-release
4. Test in ephemeral
5. Push changes and create PR
6. Create official release
7. Deploy to stage
8. Deploy to prod

## Current Status

**Fully Deployed to Prod:** 2/16
- Redhat AI ✓ (completed before journal started)
- Appstage ✓ (completed before journal started)

**PRs Created, Ready for Release/Deploy:** 14/17 🎉
- Visual Qontract ✓ (PR #43)
- Web-RCA ✓ (PR #43)
- Snyk ✓ (PR #1)
- Ibutsu ✓ (PR #6)
- Openshift ✓ (PR #13)
- Firelink ✓ (Juan's work)
- CPT ✓ (Juan's work)
- Kafka-Info ✓ (PR #6)
- Security ✓ (tested locally and ephemeral)
- Metrics-and-Monitoring ✓ (PR #4)
- Progressive-Delivery ✓ (PR #30)
- AI-Search/Convo Frontend ✓ (PR #45 - same plugin, different names)
- Appstage Entity Provider ✓ (MR #7)

**ALL DEVELOPMENT WORK COMPLETE!** Ready for deployment pipeline.

**Removed from Scope:** 2
- Status Page (now maintained by Platform App Dev team)
- IDAP (upstream plugin, no upgrade needed)

## Plugin Status Tracker

| Plugin | Rebootstrap | Local Test | Pre-release | Ephemeral Test | PR | Release | Stage | Prod |
|--------|-------------|------------|-------------|----------------|-----|---------|-------|------|
| Redhat AI | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Appstage | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Visual Qontract | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - |
| Web-RCA | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - |
| Snyk | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - |
| Ibutsu | ✓ | ✓ | - | - | ✓ | - | - | - |
| Openshift | ✓ | ✓ | - | ✓ | ✓ | - | - | - |
| Firelink | ✓ | ✓ | - | - | ✓ | - | - | - |
| CPT | ✓ | ✓ | - | - | ✓ | - | - | - |
| Kafka-Info | ✓ | ✓ | - | ✓ | ✓ | - | - | - |
| Security | ✓ | ✓ | - | ✓ | - | - | - | - |
| Metrics-and-Monitoring | ✓ | ✓ | - | ✓ | ✓ | - | ✓ | - |
| Progressive-Delivery | ✓ | ✓ | - | ⚠ | ✓ | - | - | - |
| AI-Search / Convo Frontend | ✓ | ✓ | - | ⚠ | ✓ | - | - | - |
| Appstage Entity Provider | ✓ | ✓ | - | - | ✓ | - | - | - |
| ~~Status Page~~ | N/A - transferred to Platform App Dev team |
| ~~IDAP~~ | N/A - upstream plugin, no upgrade needed |

## Recent Progress

- 2026-02-24: Starting work on visual-qontract and web-rca plugins
- 2026-02-24: Completed testing of visual-qontract and web-rca plugins both locally and in ephemeral environments. Both plugins working great.
- 2026-02-24: Rebootstrapped snyk plugin, tested locally and in ephemeral (working!)
- 2026-02-25: Created PRs for Visual Qontract/Web-RCA (#43) and Snyk (#1)
- 2026-02-25: Fixed all failing tests in backstage-plugin-visual-qontract. Root cause was tests using plain `render()` from @testing-library/react instead of `renderInTestApp()` from @backstage/frontend-test-utils, which caused "API context is not available" errors. Migrated all test files to use proper Backstage test utilities. Result: 51 tests passing, 3 skipped (URL query param tests with renderInTestApp limitation)
- 2026-02-25: Completed ibutsu plugin upgrade. Resolved cert issue by disabling cert checking for local development. Created PR #6. Plugin tested locally and working.
- 2026-02-26: Fixed openshift plugin proxy config issue for ephemeral testing. Discovered plugin is broken in production due to 401 auth error with GraphQL requests (investigating). Created PR #13.
- 2026-02-26: Reviewed Juan's rebootstrapping of Firelink and CPT plugins. Added local dev wiring and test entities. Both complete.
- 2026-02-26: Status Page plugin transferred to Platform App Dev team - removed from our upgrade scope.
- 2026-02-27: Completed Kafka-Info plugin upgrade. Fixed loggerApiRef compatibility issue. Tested locally and in ephemeral - both working. Created PR #6.
- 2026-02-27: Completed Security plugin upgrade. Rebootstrapped with modern Backstage tooling. Tested locally and in ephemeral - both working.
- 2026-02-27: Clarified that IDAP is an upstream plugin that doesn't need upgrading - removed from scope.
- 2026-03-02: Completed Metrics-and-Monitoring plugin upgrade. Tested locally, in ephemeral, AND in stage - all working without issues. Created PR #4.
- 2026-03-02: Completed Progressive-Delivery plugin upgrade. Rebootstrapped and created PR #30. Note: Ephemeral testing may need additional work for inscope-resources service.
- 2026-03-02: Completed AI-Search/Convo Frontend plugin upgrade (same plugin, different names). Bootstrapped and tested locally successfully. Cannot test in ephemeral due to missing tangerine backend dependency. Created PR #45.
- 2026-03-02: Completed Appstage Entity Provider plugin upgrade. Updated local dev environment, tested locally. Skipped ephemeral testing since plugin itself didn't change. Created MR #7.
- **2026-03-02: ALL 14 PLUGINS COMPLETE! 🎉** Development work finished. Ready to enter deployment phase.

## Next Steps

**Deployment Pipeline (all development complete!):**
1. Create official releases for all 14 completed plugins (Visual Qontract, Web-RCA, Snyk, Ibutsu, Openshift, Firelink, CPT, Kafka-Info, Security, Metrics-and-Monitoring, Progressive-Delivery, AI-Search/Convo-Frontend, Appstage-Entity-Provider)
2. Deploy all completed plugins to stage
3. Deploy all completed plugins to prod
4. Investigate and fix Openshift plugin 401 auth error with GraphQL (can be done during/after deployment)

## Notes

- Not all plugins may need rebootstrapping
- Clowder is primary entity for testing in ephemeral

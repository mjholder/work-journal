---
type: project
status: active
tags:
  - project
---
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

**🎉 PROJECT COMPLETE! 🎉**

**All 13 Plugins Fully Deployed to Production as of 2026-03-31:**
- Redhat AI ✓
- Appstage ✓
- Visual Qontract ✓
- Web-RCA ✓
- Snyk ✓
- Ibutsu ✓
- Openshift ✓
- Firelink ✓
- CPT ✓
- Kafka-Info ✓
- Security ✓
- Metrics-and-Monitoring ✓
- Progressive-Delivery ✓
- AI-Search/Convo Frontend ✓
- Appstage Entity Provider ✓

**Total: 15/15 plugins upgraded (13 active + 2 removed from scope)**

**Removed from Scope:** 2
- Status Page (now maintained by Platform App Dev team)
- IDAP (upstream plugin, no upgrade needed)

## Plugin Status Tracker

| Plugin | Rebootstrap | Local Test | Pre-release | Ephemeral Test | PR | Release | Stage | Prod |
|--------|-------------|------------|-------------|----------------|-----|---------|-------|------|
| Redhat AI | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Appstage | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Visual Qontract | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Web-RCA | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Snyk | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Ibutsu | ✓ | ✓ | - | - | ✓ | ✓ | ✓ | ✓ |
| Openshift | ✓ | ✓ | - | ✓ | ✓ | ✓ | ✓ | ✓ |
| Firelink | ✓ | ✓ | - | - | ✓ | ✓ | ✓ | ✓ |
| CPT | ✓ | ✓ | - | - | ✓ | ✓ | ✓ | ✓ |
| Kafka-Info | ✓ | ✓ | - | ✓ | ✓ | ✓ | ✓ | ✓ |
| Security | ✓ | ✓ | - | ✓ | ✓ | ✓ | ✓ | ✓ |
| Metrics-and-Monitoring | ✓ | ✓ | - | ✓ | ✓ | ✓ | ✓ | ✓ |
| Progressive-Delivery | ✓ | ✓ | - | ⚠ | ✓ | ✓ | ✓ | ✓ |
| AI-Search / Convo Frontend | ✓ | ✓ | - | ⚠ | ✓ | ✓ | ✓ | ✓ |
| Appstage Entity Provider | ✓ | ✓ | - | - | ✓ | ✓ | ✓ | ✓ |
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
- **2026-03-02: ALL 13 PLUGINS COMPLETE! 🎉** Development work finished. Ready to enter deployment phase.
- 2026-03-03: **Started deployment phase.** Created official releases for Firelink and CPT plugins. Deployed both to stage - functioning correctly. Documented follow-up work items for issues identified during testing.
- 2026-03-05: Started investigating LDAP plugin issue (ENGPROD-9542). LDAP plugin occasionally returns incomplete results, deleting users from Backstage.
- 2026-03-06: Created official releases for Snyk and Ibutsu plugins. Deployed both to stage - functioning correctly. **Deployment progress: 4 of 13 plugins in stage.**
- **2026-03-31: 🎉 ALL 13 PLUGINS SUCCESSFULLY DEPLOYED TO PRODUCTION! 🎉** Completed full deployment pipeline for all remaining plugins. All plugins (Visual Qontract, Web-RCA, Snyk, Ibutsu, Openshift, Firelink, CPT, Kafka-Info, Security, Metrics-and-Monitoring, Progressive-Delivery, AI-Search/Convo-Frontend, Appstage-Entity-Provider) are now live in both stage and production. **PROJECT COMPLETE!**

## Next Steps

**✓ PROJECT COMPLETE - No remaining deployment work!**

All 13 plugins have been successfully upgraded, released, and deployed to production as of 2026-03-31.

## Follow-Up Work

Issues identified during testing that require additional work beyond rebootstrapping:

### Openshift Plugin
- [ ] **Investigate and fix 401 auth error with GraphQL requests**
  - Plugin is currently broken in production with this issue
  - Unexpected authentication requirement when retrieving data from GraphQL
  - Identified: 2026-02-26
- [ ] **Fix proxy configuration in stage and prod environments**
  - Proxy config fixed for ephemeral testing
  - Still needs to be updated in stage and prod
  - Identified: 2026-02-26

### Kafka-Info Plugin
- [ ] **Improve UX for "no data" scenarios**
  - Currently displays as an error when no metrics match the consumer group
  - Should display as informational "no data available" message instead
  - Enhancement/future work
  - Identified: 2026-02-27

### Progressive-Delivery Plugin
- [ ] **Complete ephemeral testing setup**
  - May need additional work to get inscope-resources service working properly in ephemeral environments
  - Plugin works locally
  - Identified: 2026-03-02

## Notes

- Not all plugins may need rebootstrapping
- Clowder is primary entity for testing in ephemeral

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

**Fully Deployed to Prod:** 2/15
- Redhat AI ✓ (completed before journal started)
- Appstage ✓ (completed before journal started)

**PRs Created, Ready for Release/Deploy:** 7/15
- Visual Qontract ✓ (PR #43)
- Web-RCA ✓ (PR #43)
- Snyk ✓ (PR #1)
- Ibutsu ✓ (PR #6)
- Openshift ✓ (PR #13)
- Firelink ✓ (Juan's work)
- CPT ✓ (Juan's work)

**In Progress:** 2/15
- Kafka (starting rebootstrap)

**Not Started:** 6/15

**Removed from Scope:** 1
- Status Page (now maintained by Platform App Dev team)

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
| Firelink | ✓ | ✓ | - | - | - | - | - | - |
| CPT | ✓ | ✓ | - | - | - | - | - | - |
| ~~Status Page~~ | N/A - transferred to Platform App Dev team |
| Convo Frontend | - | - | - | - | - | - | - | - |
| Security | - | - | - | - | - | - | - | - |
| Progressive Delivery | - | - | - | - | - | - | - | - |
| IDAP | - | - | - | - | - | - | - | - |
| Kafka | - | - | - | - | - | - | - | - |
| Metrics and Monitoring | - | - | - | - | - | - | - | - |

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

## Next Steps

**Immediate (for PRs in review):**
1. Create official releases for Visual Qontract, Web-RCA, Snyk, Ibutsu, Openshift, Firelink, and CPT
2. Deploy to stage
3. Deploy to prod
4. Investigate and fix Openshift plugin 401 auth error with GraphQL

**Upcoming (remaining 6 plugins):**
1. Continue with Kafka (in progress), Convo Frontend, Security, Progressive Delivery, IDAP, Metrics and Monitoring
2. Follow same 8-step process for each

## Notes

- Not all plugins may need rebootstrapping
- Clowder is primary entity for testing in ephemeral

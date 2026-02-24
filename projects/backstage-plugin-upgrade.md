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

**Completed Plugins (ready for PR/release/deploy):** 3/16
- Visual Qontract ✓
- Web-RCA ✓
- Snyk ✓

**In Progress:** 0/16

**Not Started:** 13/16

## Plugin Status Tracker

| Plugin | Rebootstrap | Local Test | Pre-release | Ephemeral Test | PR | Release | Stage | Prod |
|--------|-------------|------------|-------------|----------------|-----|---------|-------|------|
| Visual Qontract | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| Web-RCA | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| Snyk | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| Status Page | - | - | - | - | - | - | - | - |
| Firelink | - | - | - | - | - | - | - | - |
| Redhat AI | - | - | - | - | - | - | - | - |
| Ibutsu | - | - | - | - | - | - | - | - |
| CPT | - | - | - | - | - | - | - | - |
| Openshift | - | - | - | - | - | - | - | - |
| Convo Frontend | - | - | - | - | - | - | - | - |
| Security | - | - | - | - | - | - | - | - |
| Progressive Delivery | - | - | - | - | - | - | - | - |
| IDAP | - | - | - | - | - | - | - | - |
| Kafka | - | - | - | - | - | - | - | - |
| Metrics and Monitoring | - | - | - | - | - | - | - | - |
| Appstage | - | - | - | - | - | - | - | - |

## Recent Progress

- 2026-02-24: Starting work on visual-qontract and web-rca plugins
- 2026-02-24: Completed testing of visual-qontract and web-rca plugins both locally and in ephemeral environments. Both plugins working great.
- 2026-02-24: Rebootstrapped snyk plugin, tested locally and in ephemeral (working!)

## Next Steps

**Immediate (for completed plugins):**
1. Push changes for Visual Qontract, Web-RCA, and Snyk
2. Create PRs for all three
3. Create official releases
4. Deploy to stage
5. Deploy to prod

**Upcoming (remaining 13 plugins):**
1. Continue with Status Page, Firelink, or Redhat AI plugins
2. Follow same 8-step process for each

## Notes

- Not all plugins may need rebootstrapping
- Clowder is primary entity for testing in ephemeral

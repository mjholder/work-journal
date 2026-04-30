---
type: project
status: active
tags:
  - project
---
# Project: Backstage LDAP Plugin Fix

**JIRA:** ENGPROD-9542

## Overview

The LDAP plugin in our Backstage instance occasionally returns incomplete results during cataloging. When this happens, users that aren't in the latest LDAP run get deleted from Backstage, preventing them from signing in since we use LDAP entities to verify users.

This is an upstream Backstage plugin, so fixing the root cause will likely require a contribution to the upstream Backstage project.

## Current Status

**Investigating:** Understanding the issue and potential solutions

**Short-term goal:** Find a way to trigger the LDAP cataloging process through the API as a bandaid fix. Re-running the cataloging process could quickly bring back deleted users when the issue occurs.

**Long-term goal:** Fix the root cause in the upstream LDAP plugin to prevent incomplete results.

## Progress

- 2026-03-05: Started investigating the issue. Looking into API trigger for LDAP cataloging process as a bandaid fix.

## Next Steps

1. Test if issue exists in current Backstage/RHDH version
   - Run current version of Backstage/RHDH locally
   - Test if LDAP cataloging has the same incomplete results issue
   - If issue is resolved in current version, RHDH upgrade would fix it
2. Investigate how to trigger LDAP cataloging process through the API (bandaid fix)
3. Understand why LDAP plugin occasionally returns incomplete results
4. Check RHDH release notes and LDAP plugin changelog for related fixes
5. Determine if this is a known issue in upstream Backstage
6. Plan contribution to upstream if fix requires code changes

## Notes

- Users are unable to sign in when deleted from LDAP entities
- Issue is intermittent but has significant user impact
- API trigger would be a temporary workaround to quickly restore users
- **RHDH version is significantly behind current releases**
  - RHDH version controls what version of the LDAP plugin we're using
  - Upgrading RHDH might resolve this issue if it's been fixed upstream
  - Should investigate RHDH release notes and LDAP plugin changelog

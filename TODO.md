# TODO

## Today (2026-03-12)

- [ ] Get RHDH 1.8 working in ephemeral environment
  - Resolve LDAP plugin config issue (users being read as list instead of object)
- [ ] Update RHDH version in stage to 1.8 and verify it comes up (after ephemeral success)
- [ ] Deploy all plugins to prod (after RHDH 1.8 verified in stage)

## Upcoming

- [ ] Add dependabot to all plugin repositories (needs JIRA card)
  - Automatically keep dependencies up to date across all 13 plugin repos
  - Reduce manual dependency management overhead
  - Improve security posture with automated dependency updates
- [ ] Automate artifact creation for plugins (needs JIRA card)
  - Start with appstage plugin
  - Expand to remaining plugins
  - Streamline release process and reduce manual steps
- [ ] Fix LDAP plugin intermittent cataloging issue (ENGPROD-9542)
  - LDAP plugin occasionally returns incomplete results, deleting users from Backstage
  - Users can't sign in when their LDAP entities are missing
  - Short-term: Investigate API trigger for LDAP cataloging process as bandaid fix
  - Long-term: Fix root cause in upstream Backstage LDAP plugin
- [ ] Improve kafka-info plugin UX for "no data" scenarios
  - Currently displays as an error when no metrics match the consumer group
  - Should display as informational "no data available" message instead of error state

### Backstage Plugins - All Complete! 🎉
All 13 plugins have been upgraded and are ready for deployment.

**Note:** IDAP plugin is an upstream plugin and does not need to be upgraded

## Courses

## Completed

- [x] Investigate openshift plugin 401 auth error - 2026-03-09
  - Root cause: Backstage now enforces authentication for proxies
  - Solution: Add `credentials: 'dangerously-allow-unauthenticated'` to app-config.yml since the proxied API doesn't require auth
- [x] Appstage Entity Provider plugin upgrade - 2026-03-02
  - Rebootstrapped with modern Backstage tooling
  - Updated local dev environment
  - Tested locally - working correctly
  - Skipped ephemeral testing (plugin itself unchanged, only dev environment updated)
  - PR: https://gitlab.cee.redhat.com/hcm-engprod/backstage-plugin-appstage-entity-provider/-/merge_requests/7
- [x] AI-Search plugin upgrade - 2026-03-02
  - Bootstrapped with modern Backstage tooling
  - Tested locally - works great!
  - Cannot test in ephemeral (tangerine backend dependency not available in ephemeral environments)
  - PR: https://github.com/RedHatInsights/backstage-plugin-ai-search-frontend/pull/45
- [x] Progressive Delivery plugin upgrade - 2026-03-02
  - Rebootstrapped with modern Backstage tooling
  - Tested locally
  - PR: https://github.com/RedHatInsights/backstage-plugin-progressive-delivery/pull/30
  - Note: Ephemeral testing may need more work to get inscope-resources service working properly
- [x] Metrics and Monitoring plugin upgrade - 2026-03-02
  - Rebootstrapped with modern Backstage tooling
  - Tested locally, in ephemeral, and in stage - all working without issues
  - PR: https://github.com/RedHatInsights/backstage-plugin-metrics-and-monitoring/pull/4
- [x] Security plugin upgrade - 2026-02-27
  - Rebootstrapped with modern Backstage tooling
  - Tested locally and in ephemeral - working as expected
- [x] Kafka-Info plugin upgrade - 2026-02-27
  - Rebootstrapped with modern Backstage tooling
  - Fixed loggerApiRef compatibility issue
  - Tested locally and in ephemeral - working as expected
  - PR: https://github.com/RedHatInsights/backstage-plugin-kafka-info/pull/6
- [x] Openshift plugin upgrade - 2026-02-26
  - Fixed proxy config issue preventing cluster API requests
  - Discovered and investigating 401 auth error with GraphQL requests
  - PR: https://github.com/RedHatInsights/backstage-plugin-openshift/pull/13
- [x] Firelink plugin upgrade - 2026-02-26
  - Rebootstrapped by Juan, reviewed and updated local dev wiring
- [x] CPT plugin upgrade - 2026-02-26
  - Rebootstrapped by Juan, reviewed and updated local dev wiring
- [x] Ibutsu plugin upgrade - 2026-02-25
  - Resolved cert issue by disabling cert checking for local development
  - PR: https://github.com/RedHatInsights/backstage-plugin-ibutsu/pull/6
- [x] Reconfigure redhat precommit hook to prevent committing secrets to public repos - 2026-02-25
- [x] Create PRs for all three plugins - 2026-02-25
  - Visual Qontract and Web-RCA: https://github.com/RedHatInsights/backstage-plugin-visual-qontract/pull/43
  - Snyk: https://github.com/RedHatInsights/snyk-plugin-dev/pull/1
  - Fixed all failing tests (51 passing, 3 skipped)
- [x] Push changes for Visual Qontract, Web-RCA, and Snyk plugins - 2026-02-25
- [x] Upgrade snyk plugin for backstage - 2026-02-24
  - Rebootstrapped, tested locally and in ephemeral (working!)
- [x] Get Claude project setup for dev journal in claude.ai - 2026-02-24
  - Decided to use Claude Code only due to policy
- [x] Finish upgrading backstage plugins (ENGPROD-8917) - 2026-02-24
  - Tested visual-qontract and web-rca plugins locally and in ephemeral environments
  - [x] visual-qontract plugin
  - [x] web-rca plugin

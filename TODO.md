# TODO

## Today

## Today

- [ ] Fix clowder bug

## Upcoming

- [ ] Create JIRA cards for outstanding plugin work
  - Dependabot for all plugin repositories
  - Automate artifact creation for plugins
  - Kafka-info UX improvement for "no data" scenarios
  - LDAP plugin intermittent cataloging fix (ENGPROD-9542 exists but may need subtasks)

- [ ] Deploy all plugins to prod (after RHDH 1.9 verified in stage)

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

- [x] Investigate why LDAP plugin isn't running the task to grab users in stage inscope - 2026-03-27
  - Found LDAP plugin config changed after the upgrade
  - Made small adjustment to fix it
  - LDAP plugin now working as expected
- [x] Update RHDH version in stage to 1.9 and verify it comes up - 2026-03-27
  - Removed 6 plugins that were dropped from RHDH 1.9 image
  - Ensured LDAP config is in dynamic-plugins.configmap.yml (not app-config.yaml)
  - RHDH 1.9 is up and running in stage without issues
- [x] Resolve duplicate API registration bug - 2026-03-27
  - Root cause: Part of the matomo config was causing the issue
  - Bug is now fixed
- [x] Bring back plugins that have been dropped by RHDH - 2026-03-27
  - Referenced RHDH wrapper repo for implementation
  - Opened MR: https://gitlab.cee.redhat.com/service/app-interface/-/merge_requests/180470
  - Tested in ephemeral environment - all plugins came back online successfully
- [x] Prepare and record 10 minute demo for backstage - 2026-03-26
- [x] Deploy AppStage Entity Provider Apollo Client 4 migration to stage - 2026-03-17
  - Apollo Client 4 migration complete with rxjs dependency added
  - Tested successfully in ephemeral
  - Released and deployed to stage - ready for RHDH 1.9 upgrade
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

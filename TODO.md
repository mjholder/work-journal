# TODO

## Today (2026-02-27)

- [ ] Investigate openshift plugin 401 auth error
- [ ] Create official releases for all 7 plugins (Visual Qontract, Web-RCA, Snyk, Ibutsu, Openshift, Firelink, CPT)
- [ ] Deploy to stage
- [ ] Deploy to prod

## Upcoming

- [ ] Improve kafka-info plugin UX for "no data" scenarios
  - Currently displays as an error when no metrics match the consumer group
  - Should display as informational "no data available" message instead of error state
- [ ] Fix openshift plugin proxy config in stage and prod environments

### Backstage Plugins - Remaining (3 plugins)
- [ ] Convo Frontend plugin upgrade
- [ ] Progressive Delivery plugin upgrade
- [ ] Metrics and Monitoring plugin upgrade

**Note:** IDAP plugin is an upstream plugin and does not need to be upgraded

## Completed

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

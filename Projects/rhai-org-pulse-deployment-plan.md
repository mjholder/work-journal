---
type: project
status: approved
tags:
  - project
  - org-pulse
  - deployment-plan
created: '2026-05-28'
parent: '[[rhai-org-pulse]]'
---
	# RHAI Org Pulse — Deployment Plan for Hybrid Platforms

**Epic**: [ENGPROD-10017](https://redhat.atlassian.net/browse/ENGPROD-10017)
**Story**: [ENGPROD-10020](https://redhat.atlassian.net/browse/ENGPROD-10020)
**Author**: Matt Holder
**Date**: 2026-05-28
**Status**: Approved

---

## 1. Overview

[RHAI Org Pulse](https://github.com/red-hat-data-services/rhai-org-pulse) is a modular engineering dashboard that connects Jira, GitHub, and GitLab data with a team roster (via LDAP and optionally Google Sheets) to surface delivery insights — sprint metrics, contribution tracking, and team visibility.

**Goal**: Deploy an Org Pulse instance for all of Hybrid Platforms to provide engineering delivery visibility across HP teams, reducing manual reporting and enabling data-driven decision-making for leadership.

The RHEL AI team already operates an instance at [red.ht/rhai-org-pulse](https://red.ht/rhai-org-pulse), which serves as our reference deployment.

## 2. Scope

**In scope**:
- Stand up an Org Pulse instance covering all Hybrid Platforms teams (under Stephen Cuppett)
- Connect HP Jira projects, GitHub orgs, and GitLab instances as data sources
- Configure LDAP-based team roster sync for HP org tree
- Onboard to Konflux (trusted build pipeline) and app-interface (lifecycle management)
- Deploy to App-SRE managed OpenShift clusters

**To be determined**:
- Single instance for all HP, or phased team-by-team onboarding?
- Which specific Jira projects and GitHub/GitLab orgs are in scope?
- Which LDAP org roots (manager UIDs) define the HP roster?
- Which optional modules to enable (see Section 6)

**Out of scope**:
- Custom feature development on top of Org Pulse
- Long-term service lifecycle ownership (TBD — may remain with our team or transition)

## 3. Architecture

Org Pulse is a two-container application with filesystem-based storage:

*[Insert architecture diagram — data sources (Jira, GitHub, GitLab, LDAP, Sheets) → OpenShift cluster with frontend pod (OAuth proxy :4180 → nginx :8080) and backend pod (Express.js :3000 ↔ PVC data cache)]*

| Component | Technology | Notes |
|-----------|-----------|-------|
| Frontend | Vue 3, Vite 6, Tailwind CSS 3, Chart.js 4, served via nginx | |
| Backend | Express.js | API server, handles data source integration |
| Auth | OpenShift OAuth proxy | Sidecar container in frontend pod, port 4180 |
| Storage | PersistentVolumeClaim | Filesystem-based data caching, no database |
| Route | OpenShift Route | TLS reencrypt through OAuth proxy |

## 4. Deployment Footprint

| Resource | Details |
|----------|---------|
| **Deployments** | 2 — frontend (nginx + OAuth proxy sidecar), backend (Express.js) |
| **PVC** | 1 — filesystem-based data cache |
| **Secrets** | Jira API token, GitHub PAT, LDAP bind credentials, OAuth cookie secret, plus optional module tokens |
| **Service + Route** | Standard OpenShift networking, TLS reencrypt through OAuth proxy |
| **AWS resources** | Optional — S3 bucket for backups (see below) |
| **CronJob** | Optional — daily data sync + S3 backup at 06:00 UTC (prod only) |

This is a lightweight deployment compared to other services on these clusters (e.g., Ambient Code Platform requires RDS + S3). The only optional AWS resource is an S3 bucket for backups.

### Optional: S3 Backup

The app includes a built-in backup system that archives the entire `/app/data` directory as a `.tar.gz` file to S3. This is **optional** — the AWS credentials secret is marked optional in the backend deployment, so the app runs fine without it.

| Detail | Value |
|--------|-------|
| **Trigger** | Kubernetes CronJob, daily at 06:00 UTC (prod overlay only) |
| **Format** | `team-tracker/backup-YYYY-MM-DDTHH-MM-SS.tar.gz` |
| **Retention** | 7 most recent daily + all Sunday backups for 28 days |
| **Credentials** | `aws-backup-credentials` secret (access key, secret key, bucket name) |
| **API** | `POST /api/admin/backup`, `GET /api/admin/backup`, `POST /api/admin/backup/restore` |
| **Manual restore** | `scripts/restore-backup.sh` — uses `oc` CLI to copy backup into pod |

**Recommendation**: Include this. It's low-effort to set up (one S3 bucket + one secret) and provides a recovery path if the PVC is lost. The S3 bucket would need to be provisioned through app-interface, but it's a single resource — far simpler than the RDS + S3 setup for Ambient Code Platform.

## 5. Data Sources & Credentials

| Source | Purpose | Credential Type | Required? |
|--------|---------|----------------|-----------|
| Jira | Sprint metrics, issue tracking | API token + service account email | Yes |
| GitHub | Contribution stats, PR tracking | Classic PAT (`read:user` scope) | Yes |
| LDAP (IPA) | Org tree sync — team discovery, identity | IPA bind DN + bind password | Yes |
| GitLab | Contribution stats from GitLab-hosted repos | API token | Yes (for HP) |
| Google Sheets | Roster management — team assignments | Google Service Account key | Optional — app has "in-app" mode |

**Key requirements**:
- All credentials must be **service/bot accounts**, not personal tokens. See Appendix A for step-by-step provisioning instructions per credential.
- LDAP requires **Red Hat VPN access** — the deployment cluster must be behind the VPN. IPA bind DN + password provisioned via ServiceNow ticket to IT IAM.
- Google Sheets can be skipped initially using the app's built-in "in-app" team assignment mode.

| Secret | Where to Go | Lead Time | Self-Service? |
|--------|-------------|-----------|---------------|
| Jira API token | [Bot account request](https://redhat.atlassian.net/wiki/spaces/OMEGA/pages/303600841) + Vault | **Done** (2026-06-02) | Yes |
| GitHub PAT | GitHub settings + Vault (Matt K) | Short | Yes — Matt K has org access |
| GitLab token | GitLab project/group settings + Vault | Short | Yes |
| LDAP bind | Red Hat IT (ServiceNow) + Vault | **Done** (2026-06-01) | No — requires IT ticket |
| OAuth client (ID + secret) | OAuthClient CR in app-interface MR | Tied to app-interface MR | Yes — generate secret, create YAML |
| OAuth cookie secret | Local generation + Vault | **Done** (2026-06-01) | Yes |
| AWS backup (S3) | App-interface namespace YAML (auto-provisioned) | Tied to MR merge | Yes |

**Recommended order**: Start the LDAP IT ticket first (longest lead), generate the OAuth cookie secret (instant), then work through Jira/GitHub/GitLab tokens in parallel as accounts become available.

## 6. Core vs AI Eng Split — Module Strategy

**Upstream PR [#820](https://github.com/red-hat-data-services/rhai-org-pulse/pull/820)** (merging by end of week 2026-06-06) splits Org Pulse into two layers:

| Layer | Modules | Images |
|-------|---------|--------|
| **Core** | Platform shell + team-tracker (Jira, GitHub, GitLab, LDAP roster) | `org-pulse-core-backend`, `org-pulse-core-frontend` |
| **AI Eng** | Extends core with: ai-impact, releases, upstream-pulse, product-builds, system-health | `team-tracker-backend`, `team-tracker-frontend` |

**Decision: Deploy core images only.** Every module we flagged as non-portable for HP (System Health, Product Builds, Release Registry, Upstream Pulse) is in the AI Eng layer. The core layer contains exactly the features we need: Jira sprint metrics, GitHub/GitLab contributions, and LDAP roster sync.

### Impact on Our Deployment

**Dockerfiles change** (after fork rebases on #820):
- `deploy/backend.Dockerfile` → **deleted**, replaced by `deploy/core.backend.Dockerfile`
- `deploy/frontend.Dockerfile` → **deleted**, replaced by `deploy/core.frontend.Dockerfile`
- Konflux component configs must update `dockerfileUrl` accordingly

**Secrets simplified** — core base deployment only needs:
- `team-tracker-secrets`: `JIRA_EMAIL`, `JIRA_TOKEN`, `GITHUB_TOKEN`, `GITLAB_TOKEN` (optional)
- `proxy-auth-secret`: OAuth proxy shared secret
- `ipa-credentials`: `IPA_BIND_DN`, `IPA_BIND_PASSWORD`

**Dropped from core** (moved to AI Eng overlay, we don't need these):
- `PRODUCT_PAGES_CLIENT_ID` / `PRODUCT_PAGES_CLIENT_SECRET`
- `FEATURE_TRAFFIC_GITLAB_TOKEN`
- `GITLAB_CEE_REDHAT_DOCS_TOKEN`
- `SMARTSHEET_API_TOKEN`
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_BACKUP_BUCKET` / `AWS_BACKUP_REGION`
- `google-sa-key` volume mount

**Deploy templates (PR #797)** — need revision to match the simpler core secret set. The current templates reference secrets that won't exist in a core deployment.

### Optional Modules (Future — Phase 4)

| Module | Recommendation | Notes |
|--------|---------------|-------|
| **GitLab** | Yes | Part of core — already included. Need token(s) for relevant instances. |
| **Release Analysis** | Potential | AI Eng layer — would require extending core images if desired. |
| **Upstream Pulse** | TBD | **Standalone application** — separate fork + deployment. Treat as separate workstream. |
| **SmartSheet** | Probably not | AI Eng layer. Unfamiliar tool. |
| **Product Pages** | TBD | AI Eng layer. Requires separate OAuth config. |

**Module expectations**: The RHEL AI team demo'd with all modules active to Cuppett. The core split gives us a clean story — "we're deploying the platform core first, AI Eng modules are RHEL AI-specific." If additional modules are wanted later, we can extend the core images following the pattern in the PR.

## 7. Build & Deployment Pipeline

### Repo Ownership

Fork the upstream repo ([red-hat-data-services/rhai-org-pulse](https://github.com/red-hat-data-services/rhai-org-pulse)) to the **RedHatInsights** GitHub org. This follows the same pattern used by our team for the Ambient Code Platform project. Periodically sync upstream changes from RHEL AI's repo.

**Owner**: Matt K has admin access to the RedHatInsights org (same access used for the Ambient Code Platform fork) and can create the fork and provision the GitHub bot/PAT.

This approach keeps HP build compliance (Konflux) without imposing pipeline requirements on the upstream team's workflow.

### Build — Konflux

- Onboard the RedHatInsights fork to Konflux (HP's trusted build pipeline)
- **2 components**: frontend, backend
- **4 Tekton pipeline files** in `.tekton/`: push + pull-request pipelines per component
- Images publish to `quay.io/redhat-services-prod/hcm-eng-prod-tenant/`
- **After PR #820 merges upstream**: rebase fork and update Konflux component configs to point to `deploy/core.backend.Dockerfile` and `deploy/core.frontend.Dockerfile` (old Dockerfiles deleted)

### Deploy — App-Interface

App-interface manages lifecycle, deployments, and cluster resources. Based on the Ambient Code Platform onboarding (same team, same clusters), the required structure:

*[Insert app-interface directory structure diagram — data/services/org-pulse/ tree showing app.yml, cicd/saas.yaml, namespaces (stage, prod, pipelines), pipelines/tekton definition, routes, vault policies]*

**Key detail**: The repo keeps its existing Kustomize manifests for dev/direct deployment, but we create **OpenShift templates** specifically for app-interface SaaS file consumption. Both coexist in the repo. This is exactly what the Ambient Code Platform team did.

### Target Clusters

| Environment | Cluster | Notes |
|-------------|---------|-------|
| Stage | `appsres09ue1` | Same cluster as InScope stage |
| Production | `appsrep09ue1` | Same cluster as InScope prod |
| Pipelines | `appsrep09ue1` | Konflux build pipelines |

All clusters are behind VPN (required for LDAP access).

## 8. Phased Rollout

### Phase 1: Infrastructure Provisioning
- ~~Fork repo to RedHatInsights org~~ — **Done** (Matt K, 2026-05-28)
- ~~Onboard fork to Konflux (`.tekton/` pipelines)~~ — **Done** (2026-06-02). MR [!18472](https://gitlab.cee.redhat.com/releng/konflux-release-data/-/merge_requests/18472) merged. `.tekton/` pipelines configured (4 files — push + PR per component). Images building and publishing to [quay.io/redhat-services-prod/hcm-eng-prod-tenant/](https://quay.io/repository/redhat-services-prod/hcm-eng-prod-tenant/rhai-org-pulse-backend?tab=tags). Node.js base images upgraded from deprecated `nodejs-20-minimal` to `nodejs-22-minimal` to pass Konflux image checks.
- Rebase fork on upstream PR #820 (core split) — update Konflux `dockerfileUrl` to `deploy/core.backend.Dockerfile` and `deploy/core.frontend.Dockerfile`
- Revise deploy templates (PR #797) to match core secret set — remove AI Eng-specific secret refs, remove `google-sa-key` volume mount
- Create OpenShift templates for app-interface consumption
- Submit app-interface MR: app.yml, namespaces, SaaS file, vault policies — **Submitted**: [!190339](https://gitlab.cee.redhat.com/service/app-interface/-/merge_requests/190339) (2026-06-01). Stage namespace only; prod namespace deferred.
- Provision S3 bucket for backups (via app-interface AWS resource definition)
- Provision service accounts and credentials (Jira bot, GitHub PAT, LDAP bind, OAuth cookie secret, AWS backup credentials)
- Coordinate with App-SRE on namespace provisioning

### Phase 2: Stage Deployment
- Deploy to `appsres09ue1` with real data sources
- Configure LDAP org roots for HP team roster
- Connect Jira projects and GitHub/GitLab orgs
- Validate metrics accuracy against known data
- Test optional modules (GitLab, Release Analysis, etc.)

### Phase 3: Production & Rollout
- Promote to `appsrep09ue1`
- Share with stakeholders for feedback
- Onboard teams (configure roster coverage, verify data sources)
- Document runbook for ongoing maintenance
- Collect stakeholder feedback and iterate

### Phase 4: Feature Expansion
- **Upstream Pulse** — Fork [upstream-pulse](https://github.com/dpanshug/upstream-pulse) to RedHatInsights, onboard to Konflux, deploy to its own namespace on the same cluster. Adds open source contribution impact tracking.
- **Additional modules** — Enable Release Analysis, Product Pages, or other modules based on stakeholder feedback from Phase 4.
- **Google Sheets roster** — If in-app team assignment proves limiting, onboard Google Sheets integration for roster management.

## 9. Timeline

| Milestone | Target Date | Notes |
|-----------|------------|-------|
| Deployment plan delivered | **Done** (2026-06-03) | Reviewed and approved by manager |
| RHEL AI team sync complete | Week of 2026-06-09 | Lessons learned captured |
| Repo forked + Konflux onboarded | **Done** (2026-06-02) | Fork done 2026-05-28, Konflux images building |
| App-interface MR submitted | TBD | Namespace, SaaS file, vault policies |
| Stage deployment live | TBD | First deployment with real data |
| Production deployment | Q3 2026 | Per epic target |

## 10. Open Questions & Risks

### Scope
- [ ] Which Jira projects and GitHub/GitLab orgs are in scope?
- [x] Who are the LDAP org roots (manager UIDs) for HP roster sync? — **Answered**: Derive from [hybrid-platforms/org](https://gitlab.cee.redhat.com/hybrid-platforms/org) repo, which has user and manager mappings. Cyborg is a maintenance tool for that repo — no special integration needed.

### Credentials & Access
- [x] Secret provisioning process — documented per-credential in Appendix A
- [x] LDAP service account — ServiceNow ticket to IT IAM, process documented in Appendix A
- [x] Can we share an existing LDAP bind account (RHEL AI, InScope/Backstage) or do we need our own?
- [x] GitHub bot/PAT — Matt K has RedHatInsights org access, can create fork and PAT (same as Ambient Code Platform)
- [x] Jira bot account — request via [Confluence process](https://redhat.atlassian.net/wiki/spaces/OMEGA/pages/303600841). SSO linking option TBD (asked RHEL AI team)
- [ ] Which GitLab instances and projects/groups are in scope for the GitLab token?

### Modules
- [x] Confirm which modules were active in the RHEL AI demo to Cuppett
- [x] What is the Upstream Pulse API? — **Answered**: Standalone app ([upstream-pulse](https://github.com/dpanshug/upstream-pulse)) for measuring open source contribution impact. Separate fork + deployment in its own namespace. Decision needed on whether to include it.
- [ ] How does Release Analysis handle multiple Jira projects?

### Infrastructure
- [x] App-interface onboarding — blueprint documented in Section 7 (based on Ambient Code Platform)
- [x] ArgoCD — not needed separately; app-interface handles deployments
- [x] Deployment footprint — 2 Deployments, 1 PVC, secrets, no AWS required (S3 optional for backups)
- [ ] Do we need customization beyond the stock dashboard, or vanilla deployment?

### Risks
- **Module expectations gap** — Cuppett may expect all modules from the RHEL AI demo. Need early alignment.
- **LDAP/VPN dependency** — Roster sync requires VPN access from the cluster. Confirmed target clusters are behind VPN.
- **Upstream sync** — Forking means we need a process to pull upstream changes. Drift risk if not maintained.
- **Token rotation** — Jira tokens expire every 90 days, GitHub/GitLab tokens max 1 year. Need rotation reminders or alerting.

---

## Appendix A: Secret Provisioning — Step-by-Step

Org Pulse needs 7 secrets (plus 1 optional) to operate. All secrets land in Vault under the existing `engineering-productivity/` secret engine (same engine Ambient Code Platform uses) and get wired into OpenShift namespaces as `vault-secret` resources in the namespace YAML files. No new Vault policies are needed — the existing `engineering-productivity-approle-policy` already grants read access to `engineering-productivity/*`.

**Vault path convention**: `engineering-productivity/hp-org-pulse/{env}-{secret-name}`

### A.1 Jira API Token

**What you need**: A Jira Cloud bot account email address + an API token tied to that account.

1. **Request a Jira bot account** — Follow the process at [How to request a Bot Account for Red Hat Jira or Confluence](https://redhat.atlassian.net/wiki/spaces/OMEGA/pages/303600841/How+to+request+a+Bot+Account+for+Red+Hat+Jira+or+Confluence). There is an option to link the bot account to a Red Hat SSO account — asking the RHEL AI team whether that's needed for their setup. **Submitted**: [JIRACONFSD-8589](https://redhat.atlassian.net/servicedesk/customer/portal/67/JIRACONFSD-8589) (2026-05-29).
2. **Create the API token** — Log into [Atlassian API token management](https://id.atlassian.com/manage-profile/security/api-tokens) as the bot account. Create a token (not a "token with scopes"). Set a descriptive label like `org-pulse-stage 2026-Q3`. Expiry is **90 days** maximum (Jira Cloud policy).
3. **Store in Vault** — Save the email + token to `engineering-productivity/hp-org-pulse/JIRA` (shared across stage/prod). Vault UI: [vault.devshift.net](https://vault.devshift.net/ui/vault/secrets/engineering-productivity/).

   > **Path note (2026-10-07):** this step originally specified
   > `stage-jira-token` / `prod-jira-token`, but that is not what was actually
   > done — the DONE note below records a single shared `hp-org-pulse/JIRA`
   > entry, and Daily 2026-06-02 agrees. Step updated to match reality. A third
   > path, `engineering-productivity/JIRA-bot`, appears in Daily 2026-06-02 for
   > the bot account *login and 2FA recovery code* (as distinct from the API
   > token). **Unverified** — nobody has confirmed against Vault which of these
   > entries still exist. Worth a cleanup pass.
4. **Rotation reminder** — Token expires every 90 days. Consider setting up a Prometheus alert similar to what App-SRE does (`resources/observability/prometheusrules/app-sre-jira-bot-token.prometheusrules.yml`) or at minimum a calendar reminder.

   **Rotation is not just Vault.** Every consumer holds its own copy and must be
   updated in the same pass:

   | Consumer | Where the copy lives |
   |---|---|
   | org-pulse stage/prod | OpenShift secret, synced from Vault |
   | rfe-assessor pipeline | GitLab CI/CD variable `JIRA_API_TOKEN` on `hcm-engprod/rfe-assessor` (`gitlab.cee.redhat.com`) — **not** synced from Vault |

   Missing one is silent: Jira answers a stale or over-scoped token with `200`
   and a truncated result set rather than an auth error. That is what caused the
   CVE Triage shortfall (2026-09-21) and the RFE assessment gaps (2026-10-07).
   See [[rfe-assessor-data-pipeline]].

**Previously blocked**: Google Group `hcm-pe-engineering-productivity@redhat.com` didn't allow external posts. **Resolved** (2026-06-01) — switched to using `platform-developerproductivity@redhat.com` instead, which already has correct permissions (allows posts from anyone on the web). The team has redundant Google Groups; this is the one with the right settings.

**DONE** (2026-06-02) — Bot account provisioned. Credentials stored in Vault at `engineering-productivity/hp-org-pulse/JIRA` (shared across stage/prod). **2FA note**: Atlassian requires 2FA — can't regenerate the TOTP seed to share the authenticator, so the emergency recovery code is stored in Vault as a fallback for team account access. Current 2FA is on Matt Holder's authenticator.

**Pending**: Asked RHEL AI team whether the SSO-linked bot account option is needed.

### A.2 GitHub PAT

**What you need**: A Classic Personal Access Token with `read:user` scope from a bot account.

**Owner**: Matt K — he has admin access to the RedHatInsights org (same access used for Ambient Code Platform) and can create/manage the bot account and PAT.
	
1. **Create or identify a GitHub bot account** — Per `docs/app-sre/github-bots.md`, follow [GitHub's docs on bots with 2FA](https://docs.github.com/en/organizations/keeping-your-organization-secure/managing-two-factor-authentication-for-your-organization/managing-bots-and-service-accounts-with-two-factor-authentication). The bot needs an informative name. Likely reuse the same bot account used for Ambient Code Platform.
2. **Generate the PAT** — Go to [github.com/settings/tokens](https://github.com/settings/tokens) (logged in as the bot). Create a **Classic** token (not fine-grained). Select the `read:user` scope. Set max expiry (1 year).
3. **Store in Vault** — Save to `engineering-productivity/hp-org-pulse/github-token` (shared across stage/prod — read-only scope, no environment-specific risk).
4. **Create bot file in app-interface** — Create a YAML file like `data/teams/hcm-pe-engineering-productivity/bots/org-pulse-github-bot.yml` using the `/access/bot-1.yml` schema. Example at `data/teams/rhoai/bots/rhods-ci-bot.yml`. May already exist if reusing the Ambient Code bot.
5. **Rotation** — Max 1-year expiry. Manual renewal — create new token, update Vault, update bot file if username changes.

### A.3 GitLab Token

**What you need**: An API access token for the relevant GitLab instance(s) (likely `gitlab.cee.redhat.com`).

1. **Determine which GitLab projects/groups** HP needs org-pulse to pull from. This sets whether you create a project access token or a group access token.
2. **Create the access token** — Go to the project or group Settings > Access Tokens > Add new token. Per `docs/app-sre/gitlab-bots.md`:
   - Role: `developer` (do not exceed — avoids push/merge on protected branches)
   - Scope: `api`
   - Name: descriptive, e.g. `org-pulse-2026-06`
   - Expiry: max 1 year
3. **Get the bot username** — GitLab auto-creates a bot user for the token:
   ```sh
   curl -s --header "PRIVATE-TOKEN: $TOKEN" https://gitlab.cee.redhat.com/api/v4/user | jq -r .username
   ```
4. **Store in Vault** — Save to `engineering-productivity/hp-org-pulse/stage-gitlab-token` (and `prod-gitlab-token`). Store the token and the GitLab instance URL.
5. **Create bot file in app-interface** — Similar to the GitHub bot, create a YAML file using `/access/bot-1.yml` schema with the `org_username` from step 3. Example: `data/services/app-interface/bots/app-interface-osd-fleet-manager-bot.yaml`.
6. **Rotation** — Max 365-day expiry. No renewal process — create a new token when it expires, update Vault and bot file. Two alerts exist if you wire them up: `QontractReconcileGitLabTokenExpiring30Days` and `QontractReconcileGitLabTokenExpiring3Days`.

### A.4 LDAP Bind Credentials

**What you need**: An IPA service account with a bind DN and password that can query the Red Hat LDAP directory.

1. **Submit a ServiceNow ticket to IT** — Red Hat IT/IAM provisions IPA LDAP service accounts. The process is documented at [IT IAM IPA — Testing the IPA LDAP Service](https://source.redhat.com/departments/strategy_and_operations/it/identityaccessmanagement/it_iam_ipa/testing_the_ipa_ldap_service). File a ServiceNow request for an IPA bind account for LDAP queries. **Submitted**: [RITM ticket](https://redhat.service-now.com/help?id=rh_ticket&is_new_order=true&table=sc_request&sys_id=b6524d9747890f504d8b409c716d431d) (2026-05-29).
2. **IT provides the credentials** — You'll receive the bind DN and password from IT once the ticket is fulfilled.
3. **Expected format** — The bind DN will look something like `uid=svc-org-pulse,cn=users,cn=accounts,dc=redhat,dc=com` with a corresponding password.
4. **Store in Vault** — Save `bind_dn` and `bind_password` to `engineering-productivity/hp-org-pulse/stage-ldap-bind` (and `prod-ldap-bind`).
5. **VPN requirement** — The deployment clusters must have network access to `ldap.rdu.redhat.com`. Confirmed: `appsres09ue1` and `appsrep09ue1` are behind VPN.

**DONE** (2026-06-01) — LDAP credentials received and stored in Vault at `engineering-productivity/hp-org-pulse/LDAP`.

### A.5 OAuth Proxy Secrets

**What you need**: Three values for the OAuth2 proxy sidecar — a client ID, client secret (from OpenShift OAuthClient registration), and a cookie secret (random hex for session encryption).

**A.5.1 OAuth2 Proxy Client ID & Client Secret**

These authenticate the OAuth proxy against the cluster's built-in **OpenShift OAuth server** (not `auth.redhat.com` SSO). You create an `OAuthClient` custom resource in app-interface, and qontract-reconcile applies it to the cluster using its cluster-admin privileges.

	**Reference**: [Ambient Code Platform MR !185211](https://gitlab.cee.redhat.com/service/app-interface/-/merge_requests/185211) — same team, same pattern. Also see [OpenShift docs — Configuring OAuth clients](https://docs.redhat.com/en/documentation/openshift_container_platform/4.10/html/authentication_and_authorization/configuring-oauth-clients).

**Procedure:**

1. **Generate the client secret** — You set this yourself; OpenShift does not auto-generate it:
   ```sh
   openssl rand -base64 32
   ```
2. **Create the OAuthClient YAML** in `resources/services/org-pulse/` in app-interface. The `metadata.name` becomes the `client_id`:
   ```yaml
   apiVersion: oauth.openshift.io/v1
   kind: OAuthClient
   metadata:
     name: org-pulse-stage    # This is the client_id
   secret: "<generated-secret>"
   redirectURIs:
     - "https://org-pulse-stage.apps.<cluster-domain>/oauth2/callback"
   grantMethod: auto          # No user approval screen
   ```
   Create **separate OAuthClient resources** for stage and prod (different names, secrets, and redirect URIs).
3. **Add to namespace config** in the namespace YAML:
   - Add `OAuthClient.oauth.openshift.io` to `managedResourceTypes` — this tells qontract-reconcile to manage this cluster-scoped resource
   - Add the OAuthClient name to `managedResourceNames`
   - Reference the OAuthClient YAML in `openshiftResources`
4. **Store in Vault** — Save `client_id` (= OAuthClient name) and `client_secret` (= the generated secret) to `engineering-productivity/hp-org-pulse/stage-oauth-client` (and `prod-oauth-client`). The oauth-proxy sidecar reads these from a Vault-backed OpenShift Secret.
5. **Submit as part of the app-interface MR** — After merge, qontract-reconcile applies the OAuthClient CR to the cluster. No post-merge manual steps needed.

**OAuth proxy configuration**: The proxy sidecar uses `--provider=openshift` with `--client-id` and `--client-secret-file` flags (not `--openshift-service-account`). This gives `user:full` scope, which is required if users need to create resources in their namespaces.

**Note on OAuthClient scope**: The OAuthClient CR is **cluster-scoped** — it doesn't live in your namespace. The `managedResourceTypes` entry in your namespace config tells qontract-reconcile to apply it at the cluster level.

**Rotation**: To rotate the secret, generate a new value, update both the OAuthClient YAML and Vault, bump the `version` in the namespace file, and submit an MR. The OAuthClient CR and Vault secret must stay in sync.

**A.5.2 OAuth Cookie Secret**

A random hex string used by the OAuth proxy to encrypt session cookies.

1. **Generate locally** — No external provisioning needed:
   ```sh
   openssl rand -hex 32
   ```
2. **Store in Vault** — Save to `engineering-productivity/hp-org-pulse/stage-cookie-secret` (and `prod-cookie-secret`). Use **different values** for stage and prod.
3. **No rotation needed** — Rotate only if compromised. Changing it invalidates all active user sessions.

**Reference pattern**: Ambient Code Platform uses exactly this at `engineering-productivity/ambient-code/stage-cookie-secret`. Backstage has a similar one at `app-interface/backstage/stage/tangerine-proxy-cookie-secret`.

**Cookie secret DONE** (2026-06-01) — Stage and prod cookie secrets generated and stored in Vault at `engineering-productivity/stage/oauth2-proxy` and `engineering-productivity/prod/oauth2-proxy`.

**OAuth client** — OAuthClient CR created as part of the app-interface MR. Requires knowing the route hostname for the redirect URI. Generate the client secret upfront, store in Vault, and include the same value in the OAuthClient YAML.

### A.6 AWS Backup Credentials (Optional but Recommended)

**What you need**: An S3 bucket for daily backup archives of the org-pulse data directory, plus IAM credentials to access it.

1. **No manual AWS provisioning** — Unlike the other secrets, this is **automatically provisioned** by app-interface's external resources system. You define an S3 resource in the namespace YAML file, and the terraform integration creates the bucket + IAM credentials.
2. **Add to namespace file** — In the namespace YAML under `externalResources`, add an S3 provider block:
   ```yaml
   externalResources:
   - provider: aws
     provisioner:
       $ref: /aws/app-sre-stage/account.yml
     resources:
     - provider: s3
       identifier: org-pulse-stage-backups
       defaults: /terraform/resources/s3-private-1.yml
       output_resource_name: org-pulse-s3-backup
   ```
3. **Output** — The provisioner creates a secret in the namespace (named per `output_resource_name`) containing `aws_access_key_id`, `aws_secret_access_key`, `bucket`, `region`, and `endpoint`. The org-pulse backend reads these from the `aws-backup-credentials` secret.
4. **Backup behavior** — The app archives `/app/data` as a `.tar.gz` to S3 daily at 06:00 UTC (via a CronJob in the prod overlay). Retention: 7 daily + all Sunday backups for 28 days.

**Reference pattern**: Ambient Code Platform's S3 bucket at `data/services/ambient-code-platform/namespaces/ambient-code.hcmais01ue1.yml`.

### A.7 Wiring Secrets Into the Namespace File

Once all secrets are in Vault, they're referenced in the namespace YAML file as `vault-secret` resources under `openshiftResources`. App-interface's reconciler reads these and creates corresponding OpenShift Secrets in the namespace:

```yaml
openshiftResources:
# Jira API token (shared across stage/prod)
- provider: vault-secret
  name: jira-api-token
  path: engineering-productivity/hp-org-pulse/JIRA
  version: 1
  annotations:
    qontract.recycle: "true"

# GitHub PAT (shared across stage/prod)
- provider: vault-secret
  name: github-token
  path: engineering-productivity/hp-org-pulse/github-token
  version: 1
  annotations:
    qontract.recycle: "true"

# GitLab token
- provider: vault-secret
  name: gitlab-token
  path: engineering-productivity/hp-org-pulse/stage-gitlab-token
  version: 1
  annotations:
    qontract.recycle: "true"

# LDAP bind credentials (shared across stage/prod)
- provider: vault-secret
  name: ldap-bind
  path: engineering-productivity/hp-org-pulse/LDAP
  version: 1
  annotations:
    qontract.recycle: "true"

# OAuth proxy client credentials
- provider: vault-secret
  name: oauth-proxy-client
  path: engineering-productivity/hp-org-pulse/stage-oauth-client
  version: 1
  annotations:
    qontract.recycle: "true"

# OAuth proxy cookie secret
- provider: vault-secret
  name: oauth-cookie-secret
  path: engineering-productivity/stage/oauth2-proxy
  version: 1
  annotations:
    qontract.recycle: "true"
```

No new Vault policies are needed — the existing `engineering-productivity-approle-policy` already grants read access to `engineering-productivity/*`.

To rotate a secret: update it in Vault, then bump the `version` number in the namespace file and submit an MR. The `qontract.recycle: "true"` annotation forces a pod restart when the secret changes.

## References

- [RHAI Org Pulse source](https://github.com/red-hat-data-services/rhai-org-pulse)
- [Live reference instance](https://red.ht/rhai-org-pulse)
- [Epic ENGPROD-10017](https://redhat.atlassian.net/browse/ENGPROD-10017)
- [Story ENGPROD-10020](https://redhat.atlassian.net/browse/ENGPROD-10020)
- [IPA LDAP service account process](https://source.redhat.com/departments/strategy_and_operations/it/identityaccessmanagement/it_iam_ipa/testing_the_ipa_ldap_service)
- Ambient Code Platform — onboarding blueprint (same team, same clusters, same patterns)

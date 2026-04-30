---
type: project
status: active
tags:
  - project
---
# Project: Ephemeral Namespace Operator CI/CD

## Overview

Setup full CI/CD pipeline for the ephemeral namespace operator (ENGPROD-9144). ENO only deploys to CRCD and ephemeral clusters. Goal: auto-deploy to CRCD on merge, bake/test there, then auto-promote to ephemeral.

## Current Status

E2E test suite complete (26 tests passing). App-interface test-and-promote config drafted locally. Next: konflux-release-data MR to onboard rh-eno-ci test image component, then app-interface MR.

## Recent Progress

- 2026-04-20: Project initiated, reviewed clowder operator CI/CD implementation for reference
- 2026-04-20: Cross-referenced ENO repo and app-interface. Identified gaps for CRCD -> ephemeral promotion pipeline.
- 2026-04-21: Created E2E test suite in tests/rh_eno_ci/ (Go/Ginkgo). Mirrors Clowder's rh_clowder_ci pattern. Tests: pool provisioning (with/without ClowdEnv), reservation lifecycle, secret copying, pool status. Includes Dockerfile and K8s Job manifest.
- 2026-04-21: Rewrote E2E tests from Go/Ginkgo to Python/pytest (matching Clowder's rh_clowder_ci pattern). All 25 tests passing in 75s. Found critical wait_for library bug: default fail_condition=False doesn't match None returns (None != False in Python), causing polling to be skipped. Fixed with fail_condition=None. Full suite: pool provisioning (8), pool without ClowdEnv (5), pool status (2), reservation lifecycle (5), secret copying (5).
- 2026-04-21: Built Python E2E test Docker image and successfully ran it as a K8s Job on minikube. All 25 tests passed in 80s. Used podman save | docker load to get image into minikube (registry addon disabled). Created plain Job manifest since minikube lacks OpenShift Template API. Image: localhost:5000/rh-eno-ci:test, SA: ephemeral-namespace-operator-controller-manager.
- 2026-04-29: Cross-checked E2E tests against updated JIRA criteria (ENGPROD-9144). Added 2 tests: expiration duration validation, namespace release after reservation deletion. Suite now 26 tests, all passing on minikube.
- 2026-04-29: Drafted app-interface test-and-promote config (ENGPROD-9833). Created cicd/test.yml and modified deploy.yml with promotion channels. Follows Clowder's two-MR pattern (MR 176369 / MR 176552).
- 2026-04-29: Mapped out Konflux onboarding for rh-eno-ci test image. Found existing ENO config in konflux-release-data repo. Need to add Component + ImageRepository + ReleasePlan for rh-eno-ci, plus update ReleasePlanAdmission mapping. Konflux will auto-generate .tekton pipeline files via PR after merge.

---

## Target Promotion Flow

```
PR merged to main
    |
    v
Konflux builds image --> quay.io/.../ephemeral-namespace-operator:{commit-sha}
Jenkins build_deploy.sh --> quay.io/cloudservices/ephemeral-namespace-operator:{7-char-sha}
Jenkins build_catalog.sh --> bundle + index images (same tag)
    |
    v
CRCD auto-deploy (saas-deploy, ref: main)
    |  Publishes to: eno-crcd-deploy-success-channel (NEW)
    v
E2E tests on CRCD (cicd/test.yml) (NEW)
    |  Subscribes to: eno-crcd-deploy-success-channel
    |  Publishes to: eno-crcd-test-success-channel (NEW)
    v
Ephemeral auto-promotion (NEW)
    |  Subscribes to: eno-crcd-test-success-channel
    |  auto: true on ephemeral target
```

---

## What ENO Already Has

### ENO Repo (`/home/maholder/git_repos/ephemeral-namespace-operator`)

| Component | Status |
|-----------|--------|
| Konflux/Tekton pipelines (.tekton/) | Done - PR and push pipelines |
| GitHub Actions (lint, test, platsec) | Done |
| Dockerfile (multi-stage UBI9) | Done |
| Makefile (build, test, release, bundle, catalog) | Done |
| build_deploy.sh | Done - pushes to quay.io/cloudservices/ephemeral-namespace-operator |
| pr_check.sh | Done - containerized test runner |
| Jenkinsfile | Done - unit tests |
| KUTTL E2E tests (4 suites) | Done |
| manifest.yaml / deploy.yml generation | Done |

### App-Interface Config

| Component | Status | File |
|-----------|--------|------|
| App definition | Done | `data/services/insights/ephemeral/app.yml` (shared with other ephemeral services) |
| Quay repo | Done | `cloudservices/ephemeral-namespace-operator` (private) |
| Jenkins build-master | Done | `data/services/insights/ephemeral/cicd/ci-ext/jobs.yaml` |
| Jenkins catalog build | Done | `data/services/insights/ephemeral/build.yml` |
| CRCD namespace | Done | `data/services/insights/ephemeral/namespaces/crcd-ns-operator.yml` |
| Ephemeral namespace | Done | `data/services/insights/ephemeral/namespaces/ephemeral-ns-operator.yml` |
| CRCD deploy target | Done | In `deploy.yml`, ref: main, Konflux image |
| Ephemeral deploy target | Done | In `deploy.yml`, ref: pinned SHA (needs auto-promote) |
| ServiceMonitors | Done | Both crc-eph and crcd01ue1 |
| NamespacePool resources | Done | 5 pools on crc-eph, 4 on crcd |
| Dashboards | Done | Via saas-dashboards.yaml |

---

## Gap Analysis: What's Missing

### 1. Promotion channels (NEW)

Clowder pattern (reference: `data/services/clowder/deploy-mutate.yml`):
- Defines `publish` and `subscribe` channels on deploy targets
- CRCD target publishes to deploy-success channel on successful deploy
- E2E test subscribes to deploy-success, publishes to test-success
- Downstream targets subscribe to test-success with `auto: true`

ENO needs:
- CRCD target in `deploy.yml` should publish to an `eno-crcd-deploy-success-channel`
- Ephemeral target should subscribe to an `eno-crcd-test-success-channel` with `auto: true`

### 2. Post-deployment E2E test config (NEW)

Clowder pattern (reference: `data/services/clowder/cicd/test.yml`):
```yaml
name: clowder-test
app: (ref to app.yml)
provider: tekton
pipelinesProvider: (ref to pipeline provider)
image: quay.io/.../clowder-e2e-tests  # separate test image
test_source: (GitHub repo path to test job YAML)
target_namespace: crcd01ue1
subscribe: clowder-crcd-deploy-success-channel
publish: clowder-crcd-test-success-channel
```

ENO needs:
- A `cicd/test.yml` (or similar) defining the E2E test
- Subscribes to `eno-crcd-deploy-success-channel`
- Publishes to `eno-crcd-test-success-channel`

### 3. E2E test container image (NEW)

Clowder pattern:
- Dedicated `tests/rh_clowder_ci/Dockerfile` for E2E test image
- Separate Konflux pipelines to build it (`.tekton/clowder-e2e-tests-*.yaml`)
- Output: `quay.io/redhat-user-workloads/hcm-eng-prod-tenant/clowder-e2e-tests`
- Test job YAML at `tests/rh_clowder_ci/deployment/job.yaml`

ENO needs:
- E2E test Dockerfile (what tests to run against CRCD after deploy?)
- Konflux pipelines to build the test image
- Quay repo for the test image
- Test job YAML defining how the test runs as a K8s Job

### 4. Ephemeral target needs auto-promotion

Current state in `deploy.yml`:
```yaml
- namespace:
    $ref: /services/insights/ephemeral/namespaces/ephemeral-ns-operator.yml
  ref: f7b41f8f0e300780b22644ba8ee35e20adcf03c1  # pinned SHA
```

Needs to become (following Clowder's stage pattern):
```yaml
- namespace:
    $ref: /services/insights/ephemeral/namespaces/ephemeral-ns-operator.yml
  ref: main  # or auto-updated by promotion
  subscribe:
  - eno-crcd-test-success-channel
  auto: true  # auto-promote when tests pass
```

---

## Clowder CI/CD Reference Details

### How Clowder's Promotion Channels Work

From `data/services/clowder/deploy-mutate.yml` (CRCD target):
- CRCD target has `publish: [clowder-crcd-deploy-success-channel]`
- When saas-deploy succeeds on CRCD, it publishes to that channel

From `data/services/clowder/cicd/test.yml`:
- E2E test subscribes to `clowder-crcd-deploy-success-channel` (triggers on deploy success)
- On test success, publishes to `clowder-crcd-test-success-channel`
- Test image: `quay.io/redhat-services-prod/hcm-eng-prod-tenant/clowder-e2e-tests`

From `data/services/clowder/deploy.yml` (stage targets):
- Stage targets subscribe to `clowder-crcd-test-success-channel`
- Have `auto: true` to auto-update ref when channel fires

### Clowder's Jenkins Jobs (for reference)

| Job | Template | Purpose |
|-----|----------|---------|
| build-master | insights-gh-build-master | Build + push operator image |
| catalog build master | gh-build-catalog-master-with-upstream | Build OLM bundle + catalog images |

ENO already has both of these equivalents.

### Clowder's Managed Resource Types

Standard: CustomResourceDefinition, Deployment, Service, ClusterRole, Role, ConfigMap, ServiceAccount, RoleBinding, ClusterRoleBinding, ValidatingWebhookConfiguration, ConsolePlugin

ENO's parent saas-deploy manages: CustomResourceDefinition, Deployment, DeploymentConfig, Service, ClusterRole, Role, ConfigMap, ServiceAccount, RoleBinding, ClusterRoleBinding, Frontend, ServiceMonitor

---

## Outstanding Tasks

- [x] Review clowder operator CI/CD setup to understand the pattern
- [x] Cross-reference ENO repo and app-interface entries
- [x] Identify gaps for CRCD -> ephemeral promotion
- [x] Decide what E2E tests should run against CRCD after deploy
- [x] Create E2E test Dockerfile and test job YAML in ENO repo
- [x] Create promotion channels in app-interface (drafted locally)
- [x] Add publish channel to CRCD deploy target (drafted locally)
- [x] Create cicd/test.yml in app-interface for post-deploy E2E (drafted locally)

### Remaining Steps (in order)

#### Step 1: ENO repo — commit pending changes and open PR
- Branch: `eno-cicd`
- Changes: enhanced E2E tests (expiration duration validation, namespace release test), defensive envtest fix
- Must merge before Konflux test image can reference correct job.yaml

#### Step 2: konflux-release-data MR — onboard rh-eno-ci component
- Repo: `gitlab.cee.redhat.com/releng/konflux-release-data`
- Branch from main, modify these files:

**a) `tenants-config/cluster/stone-prd-rh01/tenants/hcm-eng-prod-tenant/ephemeral-namespace-operator.yaml`**
Add three new resources (append to existing file):
1. **Component** for `rh-eno-ci` — same application (`ephemeral-namespace-operator`), different component pointing to `tests/rh_eno_ci/Dockerfile` with `context: tests/rh_eno_ci`
2. **ImageRepository** for `rh-eno-ci` — `hcm-eng-prod-tenant/ephemeral-namespace-operator/rh-eno-ci`, public visibility
3. **ReleasePlan** for `rh-eno-ci` — auto-release, targets `rhtap-releng-tenant`

**b) `config/stone-prd-rh01.pg1f.p1/service/ReleasePlanAdmission/hcm-eng-prod/ephemeral-namespace-operator.yaml`**
Add `rh-eno-ci` to the `mapping.components` list with repository `quay.io/redhat-services-prod/hcm-eng-prod-tenant/rh-eno-ci`

**c) Run `build-manifests.sh`** to regenerate auto-generated files

**d) Open MR, wait for releng review and merge**

Reference: Clowder pattern in same repo (`clowder.yaml`), Konflux docs at `users/modules/end-to-end/pages/onboard-containers-for-app-interface.adoc`

#### Step 3: ENO repo — merge auto-generated .tekton PR
- After konflux-release-data MR merges, Konflux auto-creates a PR on the ENO GitHub repo with `.tekton/rh-eno-ci-push.yaml` and `.tekton/rh-eno-ci-pull-request.yaml`
- Review and merge that PR
- This triggers the first build of the test image

#### Step 4: Verify test image builds and releases
- Konflux builds to `quay.io/redhat-user-workloads/hcm-eng-prod-tenant/ephemeral-namespace-operator/rh-eno-ci`
- Release pipeline pushes to `quay.io/redhat-services-prod/hcm-eng-prod-tenant/rh-eno-ci`
- Verify image is accessible at the redhat-services-prod location

#### Step 5: app-interface MR 1 — test-and-promote config (ENGPROD-9833)
- Repo: `gitlab.cee.redhat.com/service/app-interface`
- Already drafted locally on app-interface clone

**a) Create `data/services/insights/ephemeral/cicd/test.yml`** (NEW)
- Test saas-file: subscribes to `eno-crcd-deploy-success-channel`, runs E2E test Job, publishes to `eno-crcd-test-success-channel`
- References ENO repo path `/tests/rh_eno_ci/deployment/job.yaml`
- Image pattern: `quay.io/redhat-services-prod/hcm-eng-prod-tenant/rh-eno-ci`

**b) Modify `data/services/insights/ephemeral/deploy.yml`**
- CRCD target: add `promotion.publish: [eno-crcd-deploy-success-channel]`
- crc-eph target: add commented-out `promotion: auto: true, subscribe: [eno-crcd-test-success-channel]`

#### Step 6: Verify end-to-end flow on CRCD
- Deploy ENO to CRCD (merge to main triggers deploy)
- Verify `eno-crcd-deploy-success-channel` fires
- Verify test Job is created in `ephemeral-namespace-operator-system` on CRCD
- Verify tests run and pass
- Verify `eno-crcd-test-success-channel` fires

#### Step 7: app-interface MR 2 — enable auto-promotion
- Uncomment the promotion block on the crc-eph target in `deploy.yml`
- After merge: deploy to CRCD -> tests pass -> auto-promote to crc-eph

- [ ] Step 1: Commit and merge ENO repo changes
- [ ] Step 2: Open konflux-release-data MR for rh-eno-ci component
- [ ] Step 3: Merge auto-generated .tekton PR on ENO repo
- [ ] Step 4: Verify test image builds and releases to redhat-services-prod
- [ ] Step 5: Open app-interface MR 1 (test.yml + promotion channels)
- [ ] Step 6: Verify full flow on CRCD
- [ ] Step 7: Open app-interface MR 2 (enable auto-promotion)

## Key File Paths

### ENO Repo
| File | Purpose |
|------|---------|
| `.tekton/ephemeral-namespace-operator-push.yaml` | Konflux push pipeline |
| `.tekton/ephemeral-namespace-operator-pull-request.yaml` | Konflux PR pipeline |
| `Makefile` | Build targets (release, bundle, catalog-build) |
| `deploy.yml` | Deployment template (95.7 KB) |
| `build_deploy.sh` | Jenkins build script |
| `tests/kuttl/` | KUTTL E2E tests (4 suites) |
| `tests/rh_eno_ci/` | E2E test suite (Python/pytest, mirrors Clowder's rh_clowder_ci) |
| `tests/rh_eno_ci/deployment/job.yaml` | OpenShift Template for running E2E tests as a Job |
| `tests/rh_eno_ci/Dockerfile` | Test image Dockerfile |

### App-Interface (ENO - current)
| File | Purpose |
|------|---------|
| `data/services/insights/ephemeral/app.yml` | App definition (shared) |
| `data/services/insights/ephemeral/deploy.yml` | Saas-deploy (ENO + other ephemeral services) |
| `data/services/insights/ephemeral/build.yml` | Jenkins catalog build |
| `data/services/insights/ephemeral/cicd/ci-ext/jobs.yaml` | Jenkins build-master |
| `data/services/insights/ephemeral/namespaces/crcd-ns-operator.yml` | CRCD namespace |
| `data/services/insights/ephemeral/namespaces/ephemeral-ns-operator.yml` | Ephemeral namespace |

### App-Interface (Clowder - reference for what to replicate)
| File | What to copy |
|------|-------------|
| `data/services/clowder/deploy-mutate.yml` | Promotion channel pattern on CRCD target |
| `data/services/clowder/cicd/test.yml` | Post-deploy E2E test structure |
| `data/services/clowder/deploy.yml` | Auto-promote pattern (subscribe + auto: true) |

## Notes

- JIRA: ENGPROD-9144
- ENO only needs CRCD and ephemeral - no stage/prod clusters
- ENO deploys to namespace `ephemeral-namespace-operator-system`
- ENO's saas-deploy is shared in the `insights-ephemeral` file, not a dedicated file like Clowder
- E2E tests validate ENO-specific behavior only (pool provisioning, reservations, secret copying, status tracking). ClowdEnv reconciliation is Clowder's concern -- tests verify ENO creates the CR correctly but don't wait for Clowder readiness.
- ENO's image: `quay.io/redhat-services-prod/hcm-eng-prod-tenant/ephemeral-namespace-operator` (Konflux) and `quay.io/cloudservices/ephemeral-namespace-operator` (Jenkins)

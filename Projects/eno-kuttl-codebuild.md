---
type: project
status: complete
tags:
  - project
  - eno
  - kuttl
  - codebuild
  - cicd
created: '2026-05-12'
---
# Project: ENO KUTTL Tests in AWS CodeBuild

## Overview

Add KUTTL E2E tests for the Ephemeral Namespace Operator (ENO) that run in AWS CodeBuild, triggered via `/test-e2e` on PRs. This replicates the pattern established for the Clowder operator. Includes writing new KUTTL tests to expand coverage beyond the existing 3 suites, and building the full CodeBuild pipeline infrastructure.

**JIRA:** ENGPROD-9832
**Reference:** Clowder's CodeBuild implementation (same pattern to replicate)

## Current Status

Phase 1, 2, & 3 complete — AWS infrastructure, CodeBuild pipeline, and 7 new KUTTL test suites written and passing locally. All 10 test suites pass in Kind cluster (42s total). Moving to Phase 4 (validation in CodeBuild).

## Clowder Reference Implementation

Clowder's CodeBuild setup consists of three main pieces:

### 1. GitHub Actions Workflow (`.github/workflows/pr-e2e-codebuild.yml`)
- Triggered by `/test-e2e` comment on PRs
- Checks commenter has write/admin/maintain permission
- Creates pending commit status check ("CodeBuild / E2E Tests")
- Authenticates to AWS via OIDC (`aws-actions/configure-aws-credentials@v4`)
- Triggers CodeBuild project (`aws-actions/aws-codebuild-run-build@v1`)
- Updates commit status on success/failure with link to CodeBuild logs
- Requires secrets: `AWS_CODEBUILD_ROLE_ARN`, `AWS_REGION`

### 2. BuildSpec (`buildspec.yml`)
Phases:
- **install** — install dependencies (kind, kubectl, kuttl, go, etc.)
- **pre_build** — create Kind cluster
- **build** — install dependent operators, build operator, deploy it, run KUTTL tests
- **post_build** — delete Kind cluster (always runs)

Key env vars: `CLUSTER_NAME`, `K8S_VERSION`, `KINDEST_NODE_IMAGE`, `KUTTL_VERSION`, `ARTIFACTS_DIR`

### 3. Build Steps (`build/buildspec_steps/`)
- `install_dependencies.sh` — installs tools
- `create_kind_cluster.sh` — creates Kind cluster with correct K8s version
- `install_operators.sh` — installs CRDs and dependent operators (for Clowder: Strimzi, Cyndi, etc.)
- `build_clowder.sh` — builds the operator binary/image
- `deploy_clowder.sh` — deploys operator to Kind cluster
- `run_kuttl_tests.sh` — runs `build/run_kuttl.sh --report xml`, collects logs/metrics

### 4. AWS Infrastructure (pre-existing)
- CodeBuild project in AWS (e.g., `clowder-pr-check`)
- IAM role for GitHub OIDC auth
- S3 bucket for artifacts
- Needs to be created/configured for ENO separately

## ENO's Existing KUTTL Tests

3 test suites in `tests/kuttl/`:

| Suite | What it tests |
|-------|--------------|
| `test-pool-with-clowdenv` | Pool provisioning with ClowdEnvironment reference |
| `test-pool-without-clowdenv` | Pool provisioning without ClowdEnvironment |
| `test-reservation-secret-source` | Secret copying from source namespace to reserved namespace |

Config: `tests/kuttl/kuttl-test.yaml` — `startControlPlane: false`, timeout 300s, parallel 2
Runner: `build/run_kuttl.sh` — applies CRDs from `config/crd/bases/` and `config/crd/static/`

## ENO-Specific Considerations

### Differences from Clowder
- ENO has fewer dependent operators (may not need Strimzi, Cyndi, etc.)
- ENO's CRDs: NamespacePool, NamespaceReservation, ClowdEnvironment (optional reference)
- ENO runs in namespace `ephemeral-namespace-operator-system`
- ENO's existing `build/run_kuttl.sh` already handles CRD installation
- Need to determine if ENO tests need a running Clowder instance for ClowdEnv tests

### New KUTTL Tests to Write
Areas that need coverage beyond the existing 3 suites:

- [ ] **Reservation lifecycle** — create reservation, verify it gets a namespace from pool, verify status transitions
- [ ] **Reservation expiration** — verify reservations expire after TTL
- [ ] **Pool scaling** — verify pool creates the right number of ready namespaces
- [ ] **Pool status** — verify pool status fields (ready, size, creating counts)
- [ ] **Multiple pools** — verify reservations pick from the correct pool
- [ ] **Reservation deletion cleanup** — verify namespace is released back to pool on deletion
- [ ] **Error cases** — reservation referencing non-existent pool, invalid TTL values

## Outstanding Tasks

### Phase 1: AWS Infrastructure Setup
- [x] Create CodeBuild project for ENO in AWS (`eno-pr-check`)
- [x] Set up IAM role for GitHub OIDC auth (reused existing role, added ENO repo to trust policy)
- [x] Configure S3 bucket for test artifacts
- [x] Add `AWS_CODEBUILD_ROLE_ARN` and `AWS_REGION` secrets to ENO GitHub repo

### Phase 2: CodeBuild Pipeline Files
- [x] Create `buildspec.yml` in ENO repo (adapted from Clowder's)
- [x] Create `build/buildspec_steps/install_dependencies.sh`
- [x] Create `build/buildspec_steps/create_kind_cluster.sh`
- [x] Create `build/buildspec_steps/install_operators.sh` (ENO-specific: static CRDs only)
- [x] Create `build/buildspec_steps/build_eno.sh`
- [x] Create `build/buildspec_steps/deploy_eno.sh`
- [x] Create `build/buildspec_steps/run_kuttl_tests.sh`
- [x] Create `.github/workflows/pr-e2e-codebuild.yml` (adapted from Clowder's)

### Phase 3: New KUTTL Tests
- [x] Write reservation lifecycle test suite (`test-reservation-lifecycle`) — verifies namespace ownership transfer, annotations, pool status, and cascade deletion cleanup
- [x] Write pool scaling test suite (`test-pool-scaling`) — verifies pool creates 3 namespaces, scales down to 1
- [x] Write pool status test suite (`test-pool-status`) — verifies ready/reserved counts with sizeLimit=2, tracks counts through 2 reservations
- [x] Write multiple pools test suite (`test-multiple-pools`) — verifies reservations pick from correct pool with sizeLimit isolation
- [x] Write non-existent pool test suite (`test-reservation-nonexistent-pool`) — reservation targeting missing pool stays in "waiting" with no namespace
- [x] Write exhausted pool test suite (`test-reservation-exhausted-pool`) — second reservation on sizeLimit=1 pool goes to "waiting"
- [x] Write default pool test suite (`test-reservation-default-pool`) — reservation with no pool specified defaults to "default" pool
- [x] All 10 suites (3 existing + 7 new) pass locally in Kind cluster (42s, 2026-05-13)
- [ ] Reservation expiration test — deferred (poller timing makes KUTTL flaky; unit tested instead)

### Phase 4: Validation
- [ ] Run CodeBuild manually to verify pipeline works
- [ ] Test `/test-e2e` trigger on a PR — **blocked**: `issue_comment` workflow runs from main, so needs workflow merged first. PR #583 open, consulting team on approach.
- [ ] Verify artifacts are uploaded to S3
- [ ] Verify commit status updates (pending/success/failure)

## Key File Paths

### ENO Repo (existing + new)
| File | Purpose |
|------|---------|
| `tests/kuttl/kuttl-test.yaml` | KUTTL test suite config |
| `tests/kuttl/test-pool-with-clowdenv/` | Pool + ClowdEnv test |
| `tests/kuttl/test-pool-without-clowdenv/` | Pool without ClowdEnv test |
| `tests/kuttl/test-reservation-secret-source/` | Secret copying test |
| `tests/kuttl/test-pool-scaling/` | Pool scaling up/down (size 3→1) |
| `tests/kuttl/test-pool-status/` | Ready/reserved status tracking with sizeLimit |
| `tests/kuttl/test-reservation-lifecycle/` | Full reservation lifecycle + cascade cleanup |
| `tests/kuttl/test-multiple-pools/` | Multi-pool reservation isolation |
| `tests/kuttl/test-reservation-nonexistent-pool/` | Reservation for missing pool stays waiting |
| `tests/kuttl/test-reservation-exhausted-pool/` | Exhausted pool blocks second reservation |
| `tests/kuttl/test-reservation-default-pool/` | No-pool reservation defaults to "default" |
| `build/run_kuttl.sh` | KUTTL test runner script |
| `config/crd/bases/` | CRD definitions |
| `config/crd/static/` | Static CRD definitions |

### ENO Repo (to create)
| File | Purpose |
|------|---------|
| `buildspec.yml` | CodeBuild build specification |
| `build/buildspec_steps/*.sh` | Modular build step scripts |
| `.github/workflows/pr-e2e-codebuild.yml` | GitHub Actions workflow for `/test-e2e` |

### Clowder Repo (reference)
| File | Purpose |
|------|---------|
| `buildspec.yml` | Reference buildspec |
| `.github/workflows/pr-e2e-codebuild.yml` | Reference GH Actions workflow |
| `build/buildspec_steps/` | Reference build step scripts |

## Design Decisions (2026-05-13)

- **Default CodeBuild project type** (not runner) — matches Clowder's setup exactly. Environment: Linux container, EC2 compute, `aws/codebuild/standard:7.0` image.
- **Reused existing IAM role** for GitHub OIDC auth — added ENO repo to the trust policy's `StringLike` condition alongside Clowder.
- **No ECR auth needed** — ENO builds locally and loads into Kind, no private registry images.
- **No ingress-nginx/helm** — ENO tests don't require ingress, unlike Clowder.
- **Static CRDs installed separately** — `install_operators.sh` applies `config/crd/static/` (ClowdEnvironment, FrontendEnvironment) since those aren't included in the kustomize CRD build. No external operators needed.
- **ClowdEnv tests don't need running Clowder** — tests only verify ENO creates the ClowdEnvironment CR, not that Clowder reconciles it.
- **Hardcoded CodeBuild project URL** in workflow — consistent with Clowder's approach.

## Design Decisions (2026-05-13, Phase 3)

- **sizeLimit in tests** — Pool controller always replenishes ready namespaces to maintain `size`. Without `sizeLimit`, reserved namespaces don't reduce the ready count. Tests use `sizeLimit` to cap total namespaces and verify status count transitions (e.g., sizeLimit=2 with size=2 means ready decreases as reservations are made).
- **Cascade cleanup test** — `test-reservation-lifecycle` saves namespace name to `/tmp` in step 02, then verifies namespace deletion in step 04 after reservation delete. Polls up to 120s for cleanup including CAPI finalizer processing.
- **Expiration test deferred** — Poller runs every 10s, minimum practical TTL ~30s. KUTTL timing makes this flaky. Poller logic is unit tested instead.
- **Error case tests deferred** — Triggering error states requires ClowdEnv failures (needs running Clowder) or namespace resource creation failures (hard to simulate declaratively).

## Notes

- Clowder uses `kindest/node:v1.29.4` — ENO should match or use appropriate K8s version for its compatibility matrix
- Clowder's KUTTL version: 0.19.0
- Clowder collects operator logs, cluster events, and Prometheus metrics as artifacts — ENO should do the same
- ENO's existing `run_kuttl.sh` already handles CRD manifest installation, which simplifies the build step

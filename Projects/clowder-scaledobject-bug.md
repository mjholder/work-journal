---
type: project
status: active
tags:
  - project
---
# Project: Clowder ScaledObject Reconciliation Bug

## Overview

Investigating and fixing a bug where Clowder's autoscaler provider silently ignores the `serverAddress` specified in a ClowdApp's prometheus trigger metadata, always overwriting it with the ClowdEnvironment's `env.Status.Prometheus.ServerAddress`. The notifications-engine team hit this in production when they updated `serverAddress` in `clowdapp-engine.yaml` — reconciliation reported success but the ScaledObject was never updated.

**Branch:** `scaledobject-reconcile`

## Current Status

Fix implemented and verified in minikube (2026-04-13). All kuttl tests pass. PR not yet created.

## Timeline

### 2026-04-06 — Initial Investigation & Local Env Setup

- Set up minikube for local Clowder development
- Discovered minikube registry addon has persistent connection issues (`connection refused` to `192.168.49.2:5000`)
- **Workaround:** Use `podman save | docker load` instead of pushing to registry:
  ```bash
  make docker-build-no-test IMG=localhost:5000/clowder:latest && \
  eval $(minikube docker-env) && podman save localhost:5000/clowder:latest | docker load && \
  make deploy IMG=localhost:5000/clowder:latest && \
  kubectl rollout status deployment/clowder-controller-manager -n clowder-system
  ```
- Documented common issues: old pods lingering (force delete), image not found (re-run load step)
- Started looking at autoscaler reconciliation code

### 2026-04-13 — Bug Reproduced End-to-End

**Root cause identified:** `controllers/cloud.redhat.com/providers/autoscaler/keda.go:101`

```go
case "prometheus":
    result["serverAddress"] = env.Status.Prometheus.ServerAddress
```

The `getTriggerRoute` function always returns the env-level `serverAddress`, and the merge loop at lines 72-74 overwrites whatever the ClowdApp specified:

```go
for k, v := range triggerType {
    trigger.Metadata[k] = v  // overwrites app-level serverAddress
}
```

**Reproduction steps (simplified ClowdApp in minikube):**

1. Deploy Clowder from `scaledobject-reconcile` branch
2. Apply `clowder-config.yaml` with `enableKedaResources: true` (default is `false` which marks ScaledObject as a protected GVK — the cache won't manage it)
3. Create ClowdEnvironment with `metrics.mode: app-interface` and `appInterfaceInternalURL: https://env-level-prometheus.example.com:9090`
4. Deploy ClowdApp with prometheus trigger metadata `serverAddress: https://app-level-custom-prometheus.example.com:9090`
5. ScaledObject gets `https://env-level-prometheus.example.com:9090` (env value) — app value silently discarded
6. Update ClowdApp serverAddress and re-apply — ScaledObject unchanged, reconciliation reports success

**Key YAML files used for reproduction are in the clowder repo:** `test-env.yaml`, `test-app.yaml`

### 2026-04-13 — Fix Implemented & Verified

**Fix:** Changed the merge loop in `keda.go:72-74` from unconditional overwrite to "set if not present":

```go
for k, v := range triggerType {
    if _, exists := trigger.Metadata[k]; !exists {
        trigger.Metadata[k] = v
    }
}
```

App-level trigger metadata now takes precedence over auto-injected env-level values. If the ClowdApp doesn't set a field, the env value fills in as a default. This applies to all trigger types (prometheus, kafka, etc.).

**Kuttl test added:** `tests/kuttl/test-autoscaler-prometheus-app-serveraddress/` — verifies app-specified `serverAddress` is preserved and updates propagate to the ScaledObject.

**Verification:**
- Deployed fixed Clowder to minikube, manual check confirmed ScaledObject now uses app-level serverAddress
- New kuttl test: PASS
- Existing tests (app-interface, status-only-update): PASS — no regressions
- Note: `make deploy` overwrites the `clowder-config` ConfigMap — must re-apply `clowder-config.yaml` with `enableKedaResources: true` after each deploy

### Local Environment Notes

Things learned while getting the local dev environment working:

- **Minikube registry addon is unreliable** — `make deploy-minikube-quick` fails because it tries to push to `192.168.49.2:5000`. Always use the `podman save | docker load` approach.
- **`enableKedaResources` must be `true`** — The default `config/manager/clowder_config.yaml` has it `false`. The kustomization doesn't include a clowder-config ConfigMap. Must manually apply the repo-root `clowder-config.yaml` to `clowder-system` and restart the controller.
- **KEDA is installed by `build/kube_setup.sh`** — Installs KEDA v2.12.0 from GitHub releases. No separate install needed.
- **Existing kuttl test (`test-autoscaler-prometheus-serveraddress-update`) tests a different scenario** — It tests updating the *ClowdEnvironment's* `appInterfaceInternalURL`, not the *ClowdApp's* trigger metadata. That test should pass.

## Outstanding Tasks

- [x] Implement fix in `keda.go` — respect app-level `serverAddress` when present in trigger metadata (don't overwrite if already set)
- [x] Add kuttl test for the app-level serverAddress scenario
- [x] Verify existing kuttl tests still pass after fix
- [ ] Create PR for the fix
- [ ] Clean up test resources from minikube (`test-so-bug` namespace, `test-env.yaml`, `test-app.yaml`)

## Key Files

| File | Role |
|------|------|
| `controllers/cloud.redhat.com/providers/autoscaler/keda.go` | Bug location (line 101, lines 69-77) |
| `controllers/cloud.redhat.com/providers/autoscaler/router.go` | Provider dispatch |
| `controllers/cloud.redhat.com/clowdenvironment_reconciliation.go` | `setPrometheusStatus()` (lines 425-437) |
| `controllers/cloud.redhat.com/run.go` | ProtectedGVKs gating (lines 71-74) |
| `notifications-backend/.rhcicd/clowdapp-engine.yaml` | Real-world affected ClowdApp (lines 232-238) |
| `tests/kuttl/test-autoscaler-prometheus-app-serveraddress/` | New kuttl test for app-level serverAddress |

---
type: project
status: active
tags:
  - project
---
# Project: ENO AWS Sandbox Provisioning

## Overview

Adding AWS sandbox account provisioning capability to work with ephemeral namespaces. This will enable ephemeral environments to automatically provision and configure AWS sandbox accounts for testing and development.

**Key Services Involved:**
- **ENO (Ephemeral Namespace Operator)** - Core orchestration for ephemeral namespace lifecycle
  - Local: `/home/maholder/git_repos/ephemeral-namespace-operator`
- **Bonfire** - CLI/deployment tooling that interacts with ephemeral environments
  - Local: `/home/maholder/git_repos/bonfire`
- **Babylon** - Infrastructure layer (potentially via CLI)
  - Local: `/home/maholder/git_repos/babylon`
  - See PR#3210 for CLI approach
- **Sandbox API** - Backend API for provisioning AWS sandbox accounts
- **demo.redhat.com** - Service layer providing usage tracking, chargeback, and lifecycle management

This project file serves as the central knowledge hub for tracking progress across multiple Claude sessions and different service repositories.

## Current Status

🟡 Planning / Requirements Gathering

## Recent Progress

- 2026-04-22: Project file created, initial scope defined
- 2026-04-22: Documented three architectural approaches (direct API, service-mediated, babylon CLI)
- 2026-04-22: Captured stakeholder concerns around chargeback, cost tracking, and operational reporting
- 2026-04-22: Identified key stakeholders (@mamorim, @Johnathan Kupferer, @gucore)
- 2026-04-24: Completed deep exploration of babylon CLI (PR #3210). Discovered the CLI creates ResourceClaims via Catalog API rather than calling Sandbox API directly. Documented full provisioning chain: ResourceClaim → Poolboy → AnarchySubject → Anarchy → AWX → AgnosticD → AWS. Updated project doc with ResourceClaim construction patterns, comparison matrix, and recommendation that ENO create ResourceClaims directly via K8s API following babylon CLI's OrderService() patterns. This approach reuses all Babylon infrastructure (cost tracking, lifecycle, chargeback) and avoids auth complexity.
- 2026-04-24 (continued): Discovered critical architectural constraint: **ResourceClaims must be created on the Babylon cluster** (where Poolboy/Anarchy operators run), not on the ephemeral cluster where ENO runs. This means ENO cannot use simple in-cluster K8s API access. Investigated babylon CLI authentication flow - it uses pure HTTP client with OAuth browser flow. **Decision: Build custom HTTP client for ENO** similar to babylon CLI's approach but with service account token authentication instead of browser OAuth. This allows ENO (running on ephemeral cluster) to create ResourceClaims on remote Babylon cluster via Catalog API. Full lifecycle (provision, monitor, modify, delete) happens via HTTP operations (POST/GET/PATCH/DELETE on ResourceClaim endpoints). Babylon CLI code serves as reference implementation, not used as binary.

## Outstanding Tasks

### Architecture Decision
- [x] Investigate babylon CLI capabilities (PR #3210)
- [ ] Evaluate pros/cons of each approach with stakeholders
- [ ] Decide between direct API, service-mediated, or babylon ResourceClaim approach
- [ ] Document chargeback/cost tracking requirements (✅ addressed via Option 3)
- [ ] Get alignment with @mamorim on operational reporting needs
- [ ] Validate approach with @Johnathan Kupferer and @gucore
- [ ] Ask @gurnben what manual tests were run locally
- [ ] Review Brandon's ROSA integration pattern in bonfire
- [ ] Determine integration pattern to follow for sandbox provisioning (leaning toward ResourceClaim pattern)

### Prerequisites (dependent on architecture choice)

**For Option 3 (HTTP Client via Catalog API) — RECOMMENDED:**
- [ ] Get Catalog API base URL from Babylon team (e.g., `https://babylon-catalog.apps.demo.redhat.com`)
- [ ] Request service account token for Catalog API access (app-role JWT, long-lived)
- [ ] Clarify if OAuth proxy cookies are required for service accounts (babylon CLI requires both token + cookies)
- [ ] Identify target namespace on Babylon cluster for ResourceClaims (e.g., `user-ephemeral-namespaces`)
- [ ] Identify CatalogItem name for AWS sandbox provisioning (e.g., `sandbox-aws`)
- [ ] Get catalog namespace (e.g., `babylon-catalog-prod`)

**For Options 1 & 2 (NOT recommended):**
- [ ] Request `app`-role JWT for production Sandbox API from RHDP admin (if direct API)
- [ ] Get the external Route URL (https://sandbox-api.<something>.redhat.com)
- [ ] Configure forced annotations for cost tracking (if direct API)
- [ ] (Optional) Request access to private `rhpds/sandbox` repo for full API surface understanding

### Implementation (Option 3: HTTP Client via Catalog API)
**Authentication & Prerequisites:**
- [ ] Request service account token from Babylon team (long-lived app-role JWT)
- [ ] Clarify if OAuth cookies are required for service accounts (CLI requires token + cookies)
- [ ] Get Catalog API base URL (e.g., `https://babylon-catalog.apps.demo.redhat.com`)
- [ ] Store service account token in K8s secret in ENO namespace
- [ ] Identify which CatalogItem/AnarchyGovernor is used for AWS sandbox provisioning

**HTTP Client Development:**
- [ ] Create `pkg/babylon/client.go` in ENO repo (copy structure from babylon CLI's `cli/pkg/api/client.go`)
- [ ] Create `pkg/babylon/types.go` for ResourceClaim type definitions (copy from babylon CLI's `cli/pkg/types/`)
- [ ] Implement `CreateResourceClaim()` following babylon CLI's `OrderService()` pattern
- [ ] Implement `GetResourceClaim()` for status checking
- [ ] Implement `PatchResourceClaim()` for lifespan extension
- [ ] Implement `DeleteResourceClaim()` for cleanup
- [ ] Add error handling for HTTP status codes (401, 403, 404, 409, 5xx)
- [ ] Add token refresh logic (if needed for service accounts)

**ENO Integration:**
- [ ] Determine the required ResourceClaim labels/annotations for sandbox services
- [ ] Map ENO ephemeral namespace lifecycle events to ResourceClaim HTTP operations
- [ ] Integrate Babylon HTTP client into ENO reconciler
- [ ] Implement ResourceClaim status polling/watching
- [ ] Handle provisioning failures and expose status to ENO users
- [ ] Add finalizer for cleanup (ensure DELETE is called when ENO namespace is deleted)

**Testing & Validation:**
- [ ] Unit test HTTP client with mock responses
- [ ] Integration test: create ResourceClaim via Catalog API
- [ ] Validate that ResourceClaim creation triggers full provisioning chain on Babylon cluster
- [ ] Test lifecycle end-to-end: create → provision → running → cleanup
- [ ] Verify cost tracking works (cost-tracker operator picks up sandbox_account from AnarchySubject)
- [ ] Test error scenarios (provisioning failure, network failure, auth failure)

### Integration Points (All Options)
- [ ] Determine bonfire changes needed (how does bonfire request sandbox-backed ephemeral environments?)
- [ ] Configure tighter TTLs for sandbox resources (lifespan.end on ResourceClaim)
- [ ] Define resource cleanup/lifecycle management strategy

## Notes

### Architectural Approaches Under Discussion

#### Option 1: Direct Sandbox API Integration
- Get API-level access to the demo/sandbox API
- Provision resources from a service account with `app`-role JWT
- Wrap provisioned resources in the ephemeral namespace workflow

**Benefits:**
- ✅ Leverages existing ephemeral integrations throughout CI
- ✅ Works with existing devtools integrations
- ✅ Compatible with agent integrations
- ✅ Allows setting tighter TTLs on sandbox resources
- ✅ Gets all ephemeral namespace lifecycle management for free

**Concerns:**
- ⚠️ Bypasses demo.redhat.com service layer
- ⚠️ Reduces visibility into usage tracking
- ⚠️ Impacts operational and financial reports
- ⚠️ Chargeback model needs proper setup via forced annotations

**Mitigation (per gucore):**
- Sandbox API can force annotations if particular app token is used
- Chargeback can still be tracked with proper token configuration

#### Option 2: Service-Mediated Approach (demo.redhat.com)
Keep demo.redhat.com as intermediary service that wraps sandbox API

**Benefits:**
- ✅ Maintains existing chargeback model
- ✅ Preserves usage tracking and lifecycle management
- ✅ All metadata flows through same funnel
- ✅ Consistent operational and financial reporting
- ✅ No reduction in visibility

**Trade-offs:**
- ❓ May not get all ephemeral integrations "for free"
- ❓ Potentially tighter coupling to demo.redhat.com service

#### Option 3: HTTP Client Approach via Catalog API (RECOMMENDED)
Build custom HTTP REST client for ENO that creates ResourceClaims via Babylon's Catalog API, following babylon CLI's patterns

**Resources:**
- PR: https://github.com/redhat-cop/babylon/pull/3210
- Branch: `cli` in babylon repo
- Local repo: `/home/maholder/git_repos/babylon`

**Critical Architecture Constraint:**

ResourceClaims **must be created on the Babylon cluster** (where Poolboy/Anarchy operators run), not on the ephemeral cluster where ENO runs. This means ENO cannot use simple in-cluster K8s API access.

**Cross-Cluster Architecture:**

```
┌─────────────────────┐         ┌──────────────────────────────┐
│ EPHEMERAL CLUSTER   │         │  BABYLON CLUSTER             │
│                     │         │  (demo.redhat.com)           │
│  ┌──────────────┐  │  HTTPS  │  ┌────────────────────┐     │
│  │     ENO      │──┼─────────┼─►│   Catalog API      │     │
│  │   operator   │  │  :443   │  │  (REST wrapper)    │     │
│  │ (HTTP client)│  │         │  └─────────┬──────────┘     │
│  └──────────────┘  │         │            │                 │
└─────────────────────┘         │            ▼                 │
                                │   ┌──────────────────┐      │
                                │   │  ResourceClaim   │      │
                                │   │       CRD        │      │
                                │   └────────┬─────────┘      │
                                │            │                 │
                                │            ▼                 │
                                │   Poolboy → AnarchySubject  │
                                │            │                 │
                                │            ▼                 │
                                │   Anarchy → AWX → AgnosticD │
                                └────────────┼─────────────────┘
                                             │
                                             ▼
                                    Sandbox API → AWS
```

**How the Babylon CLI Actually Works:**

The babylon CLI uses a **pure HTTP client** (`net/http` in Go), NOT `client-go` or direct K8s API access:
- HTTP client talks to Catalog API via HTTPS (port 443)
- Authentication via Bearer token + OAuth proxy cookies
- Catalog API is a REST wrapper around the Kubernetes API
- Creates ResourceClaims which trigger the Babylon provisioning chain

**Full Provisioning Chain (After ResourceClaim Creation):**

```
ResourceClaim (created on Babylon cluster)
    ↓
Poolboy operator (assigns ResourceHandle)
    ↓
AnarchySubject (automation state)
    ↓
Anarchy operator (triggers Ansible jobs)
    ↓
Ansible Tower/AWX (runs AgnosticD playbooks)
    ↓
AgnosticD (Ansible framework)
    ↓
AWS (sandbox account provisioning via Sandbox API)
```

**Recommended ENO Integration Pattern:**

ENO should **build a custom HTTP REST client** (similar to babylon CLI's client) that talks to the Catalog API:

- **ENO's HTTP client** sends REST calls to Catalog API (POST/GET/PATCH/DELETE)
- **Authentication** via service account token (long-lived, from K8s secret) instead of browser OAuth
- **ResourceClaim construction** follows babylon CLI's `OrderService()` patterns (labels, annotations, params, lifespan)
- **Lifecycle operations** via HTTP:
  - `POST /apis/poolboy.../resourceclaims` — provision sandbox
  - `GET /apis/poolboy.../resourceclaims/{name}` — check status
  - `PATCH /apis/poolboy.../resourceclaims/{name}` — extend lifespan
  - `DELETE /apis/poolboy.../resourceclaims/{name}` — cleanup sandbox
- **Poolboy/Anarchy/AWX/AgnosticD** handle actual provisioning (no changes needed)
- **Cost tracking works automatically** — cost-tracker operator watches ResourceClaims on Babylon cluster
- **No CLI binary dependency** — ENO copies the HTTP client pattern, doesn't shell out to CLI binary

**Key Reference Files in Babylon Repo:**

**HTTP Client Implementation:**
- `cli/pkg/api/client.go` — HTTP client structure, request/response handling, auth headers
- `cli/pkg/api/service.go:75-109` — `CreateResourceClaim()`, `GetResourceClaim()`, `PatchResourceClaim()`, `DeleteResourceClaim()`
- `cli/pkg/api/service.go:198-343` — **OrderService()** — ResourceClaim construction (labels, annotations, params, lifespan)
- `cli/pkg/types/resourceclaim.go` — ResourceClaim type definitions
- `cli/pkg/config/config.go` — Config structure (token, cookies storage)
- `cli/cmd/login.go` — Browser OAuth flow (ENO won't use this, but shows how tokens are obtained)
- `cli/cmd/service_order.go` — Parameter handling and catalog item lookup
- `cli/cmd/service_status.go` — Status polling and lifecycle state mapping
- `cli/cmd/root.go:63-65` — Shows both token AND cookies are required for CLI auth

**Babylon Platform:**
- `catalog/api/app.py:707-777` — Server-side sandbox availability check integration
- `cost-tracker/operator/` — How cost tracking works with sandbox accounts (watches for `job_vars.sandbox_account`)
- `docs/design/cli-design.adoc` — Complete CLI design doc showing REST API architecture

**Benefits:**
- ✅ Leverages entire existing Babylon infrastructure stack (Poolboy, Anarchy, AWX, AgnosticD)
- ✅ Avoids direct Sandbox API integration (goes through Babylon's service layer)
- ✅ Gets cost tracking, lifecycle management, chargeback tracking for free
- ✅ Consistent operational and financial reporting through existing Babylon systems
- ✅ No CLI binary dependency (ENO builds own HTTP client using CLI as reference)
- ✅ Clean separation of concerns (ENO manages ephemeral namespaces, Babylon manages AWS provisioning)
- ✅ Catalog API designed for remote access (HTTPS port 443, likely allowed through firewalls)
- ✅ Standard REST API patterns (easier to debug than K8s API port 6443)
- ✅ Complete reference implementation in babylon CLI to copy from
- ✅ Native Go integration (typed structs, controller-runtime context, easy testing)

**Trade-offs:**
- ⚠️ Requires understanding Babylon's ResourceClaim schema (but CLI code provides clear reference)
- ⚠️ Coupled to Babylon platform availability (but that's already our target platform)
- ⚠️ Need service account token from Babylon team (app-role JWT or similar)
- ⚠️ Need to clarify if OAuth cookies are required for service accounts (CLI requires both token + cookies)
- ⚠️ Need to identify which CatalogItem/AnarchyGovernor is used for sandbox provisioning
- ⚠️ Token management/refresh logic (though likely long-lived for service accounts)

### Reference Implementations

**Brandon's ROSA Integration:**
- Bonfire can stand up ROSA clusters
- This could serve as a pattern for how to integrate external service provisioning
- Need to review implementation details for integration approach

**Gurney's Local Testing:**
- Ran manual tests locally (need details on what was tested)
- Validation approach could inform testing strategy

### Key Stakeholders
- **@mamorim** - Cost allocation, operational reporting concerns
- **@Johnathan Kupferer** - Architecture, service mediation preference
- **@gucore** - Sandbox API capabilities, annotation forcing
- **@gurnben, @kirk -vvv** - Potential babylon CLI users, local testing validation
- **Brandon** - ROSA integration reference implementation

### ResourceClaim Construction Details (Option 3)

**Required Labels** (from `babylon.gpte.redhat.com` and `gpte.redhat.com` domains):
```yaml
babylon.gpte.redhat.com/catalogItemName: <catalog-item-name>
babylon.gpte.redhat.com/catalogItemNamespace: <catalog-namespace>
gpte.redhat.com/asset-uuid: <uuid-from-catalog-item>
demo.redhat.com/white-glove: "false"
```

**Required Annotations**:
```yaml
babylon.gpte.redhat.com/catalogDisplayName: <catalog-namespace-display-name>
babylon.gpte.redhat.com/catalogItemDisplayName: <catalog-item-display-name>
babylon.gpte.redhat.com/category: <catalog-item-category>
babylon.gpte.redhat.com/url: https://babylon.../services/<namespace>/<name>
demo.redhat.com/requester: <user-email-or-service-account>
demo.redhat.com/orderedBy: <user-email-or-service-account>
demo.redhat.com/scheduled: "false"
demo.redhat.com/provide_salesforce-id_later: "true"
```

**Spec Structure**:
```yaml
spec:
  provider:
    name: <catalog-item-name>
    parameterValues:
      purpose: "Development"  # or "Production", "Testing", etc.
      # ... other catalog-item-specific parameters
  lifespan:
    end: <RFC3339-timestamp>  # e.g., "2026-04-25T16:30:00Z"
```

**Name Generation**: Kubernetes-compliant name = sanitized catalog item name + "-" + 5-char random suffix (consonants/digits only, max 63 chars total)

**Reference**: `babylon/cli/pkg/api/service.go:198-343` — OrderService() function shows the complete construction logic

**Quick-Start Pseudocode for ENO** (Go, using controller-runtime):

```go
// In ENO reconciler, when ephemeral namespace requests AWS sandbox:
func (r *EphemeralNamespaceReconciler) provisionSandbox(ctx context.Context, ns *eno.EphemeralNamespace) error {
    // 1. Construct ResourceClaim following babylon CLI patterns
    rc := &unstructured.Unstructured{
        Object: map[string]interface{}{
            "apiVersion": "poolboy.gpte.redhat.com/v1",
            "kind": "ResourceClaim",
            "metadata": map[string]interface{}{
                "name": generateName(ns.Name), // sanitized + random suffix
                "namespace": getUserNamespace(ns), // or target service namespace
                "labels": map[string]interface{}{
                    "babylon.gpte.redhat.com/catalogItemName": "sandbox-aws", // TODO: determine actual catalog item
                    "babylon.gpte.redhat.com/catalogItemNamespace": "babylon-catalog-prod", // TODO: verify
                    "gpte.redhat.com/asset-uuid": "<uuid>", // from catalog item
                },
                "annotations": map[string]interface{}{
                    "babylon.gpte.redhat.com/catalogItemDisplayName": "AWS Sandbox",
                    "demo.redhat.com/requester": "eno-operator@redhat.com", // service account
                    "demo.redhat.com/orderedBy": ns.Spec.Requester,
                    // ... see ResourceClaim Construction Details above
                },
            },
            "spec": map[string]interface{}{
                "provider": map[string]interface{}{
                    "name": "sandbox-aws", // catalog item name
                    "parameterValues": map[string]interface{}{
                        "purpose": "Development",
                        // ... other params from catalog item
                    },
                },
                "lifespan": map[string]interface{}{
                    "end": calculateEndTime(ns.Spec.TTL), // RFC3339 timestamp
                },
            },
        },
    }
    
    // 2. Create ResourceClaim via K8s API
    if err := r.Create(ctx, rc); err != nil {
        return fmt.Errorf("creating ResourceClaim: %w", err)
    }
    
    // 3. Store ResourceClaim name in EphemeralNamespace status for tracking
    ns.Status.SandboxResourceClaim = rc.GetName()
    
    return nil
}

// Separate reconciler watches ResourceClaim status for provisioning progress
func (r *EphemeralNamespaceReconciler) checkSandboxStatus(ctx context.Context, ns *eno.EphemeralNamespace) error {
    rc := &unstructured.Unstructured{}
    rc.SetAPIVersion("poolboy.gpte.redhat.com/v1")
    rc.SetKind("ResourceClaim")
    
    if err := r.Get(ctx, client.ObjectKey{
        Namespace: getUserNamespace(ns),
        Name: ns.Status.SandboxResourceClaim,
    }, rc); err != nil {
        return err
    }
    
    // Read status.summary.provision_state: new, provisioning, started, provision-failed, etc.
    state := getNestedString(rc.Object, "status", "summary", "provision_state")
    
    // Update ENO status accordingly
    switch state {
    case "started":
        ns.Status.SandboxReady = true
        // Extract sandbox details from status.resources or status.summary
    case "provision-failed":
        ns.Status.SandboxError = "Provisioning failed"
    }
    
    return nil
}
```

### HTTP Client Implementation for ENO (Recommended Approach)

**HTTP Client Structure** (copy from babylon CLI):

```go
// pkg/babylon/client.go
package babylon

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
    "time"
)

// Client talks to Babylon Catalog API via HTTPS
type Client struct {
    BaseURL    string        // e.g., "https://babylon-catalog.apps.demo.redhat.com"
    Token      string        // Service account token (from K8s secret)
    HTTPClient *http.Client
}

// NewClient creates a Babylon API client
func NewClient(baseURL, token string) *Client {
    return &Client{
        BaseURL: baseURL,
        Token:   token,
        HTTPClient: &http.Client{Timeout: 30 * time.Second},
    }
}

// doRequest performs HTTP request with auth headers
func (c *Client) doRequest(method, path string, body interface{}) ([]byte, error) {
    var bodyReader io.Reader
    if body != nil {
        data, _ := json.Marshal(body)
        bodyReader = bytes.NewReader(data)
    }
    
    req, _ := http.NewRequest(method, c.BaseURL+path, bodyReader)
    req.Header.Set("Authorization", "Bearer "+c.Token)
    req.Header.Set("Content-Type", "application/json")
    
    resp, err := c.HTTPClient.Do(req)
    if err != nil {
        return nil, fmt.Errorf("request failed: %w", err)
    }
    defer resp.Body.Close()
    
    if resp.StatusCode >= 400 {
        return nil, fmt.Errorf("API error %d", resp.StatusCode)
    }
    
    return io.ReadAll(resp.Body)
}

// CreateResourceClaim provisions a sandbox (POST)
func (c *Client) CreateResourceClaim(claim *ResourceClaim) (*ResourceClaim, error) {
    path := fmt.Sprintf("/apis/poolboy.gpte.redhat.com/v1/namespaces/%s/resourceclaims",
        claim.Metadata.Namespace)
    data, err := c.doRequest("POST", path, claim)
    if err != nil {
        return nil, err
    }
    
    var result ResourceClaim
    json.Unmarshal(data, &result)
    return &result, nil
}

// GetResourceClaim checks status (GET)
func (c *Client) GetResourceClaim(namespace, name string) (*ResourceClaim, error) {
    path := fmt.Sprintf("/apis/poolboy.gpte.redhat.com/v1/namespaces/%s/resourceclaims/%s",
        namespace, name)
    data, err := c.doRequest("GET", path, nil)
    if err != nil {
        return nil, err
    }
    
    var claim ResourceClaim
    json.Unmarshal(data, &claim)
    return &claim, nil
}

// PatchResourceClaim extends lifespan (PATCH)
func (c *Client) PatchResourceClaim(namespace, name string, patch interface{}) (*ResourceClaim, error) {
    path := fmt.Sprintf("/apis/poolboy.gpte.redhat.com/v1/namespaces/%s/resourceclaims/%s",
        namespace, name)
    data, err := c.doRequest("PATCH", path, patch)
    if err != nil {
        return nil, err
    }
    
    var result ResourceClaim
    json.Unmarshal(data, &result)
    return &result, nil
}

// DeleteResourceClaim cleans up sandbox (DELETE)
func (c *Client) DeleteResourceClaim(namespace, name string) error {
    path := fmt.Sprintf("/apis/poolboy.gpte.redhat.com/v1/namespaces/%s/resourceclaims/%s",
        namespace, name)
    _, err := c.doRequest("DELETE", path, nil)
    return err
}
```

**ENO Reconciler Integration:**

```go
// controllers/ephemeralnamespace_controller.go
type EphemeralNamespaceReconciler struct {
    client.Client
    BabylonClient *babylon.Client
}

// Lifecycle: Create sandbox
func (r *EphemeralNamespaceReconciler) provisionSandbox(ctx context.Context, ns *EphemeralNamespace) error {
    claim := &babylon.ResourceClaim{
        Metadata: babylon.ObjectMeta{
            Name:      generateName("sandbox-aws"),
            Namespace: "user-ephemeral-namespaces", // On Babylon cluster
            Labels: map[string]string{
                "babylon.gpte.redhat.com/catalogItemName": "sandbox-aws",
                "eno.redhat.com/ephemeral-namespace": ns.Name,
            },
            Annotations: map[string]string{
                "demo.redhat.com/requester": "eno-operator@redhat.com",
                "demo.redhat.com/orderedBy": ns.Spec.RequestedBy,
            },
        },
        Spec: babylon.ResourceClaimSpec{
            Provider: &babylon.ResourceClaimProvider{
                Name: "sandbox-aws",
                ParameterValues: map[string]interface{}{
                    "purpose": "Development",
                },
            },
            Lifespan: &babylon.ResourceClaimLifespan{
                End: time.Now().Add(ns.Spec.TTL).Format(time.RFC3339),
            },
        },
    }
    
    result, err := r.BabylonClient.CreateResourceClaim(claim)
    if err != nil {
        return err
    }
    
    ns.Status.SandboxResourceClaimName = result.Metadata.Name
    return nil
}

// Lifecycle: Check status
func (r *EphemeralNamespaceReconciler) checkSandboxStatus(ctx context.Context, ns *EphemeralNamespace) error {
    claim, err := r.BabylonClient.GetResourceClaim(
        "user-ephemeral-namespaces",
        ns.Status.SandboxResourceClaimName,
    )
    if err != nil {
        return err
    }
    
    switch claim.Status.Summary.ProvisionState {
    case "started":
        ns.Status.SandboxReady = true
        ns.Status.SandboxAccountID = claim.Status.Summary.ProvisionData["sandbox_account"]
    case "provision-failed":
        ns.Status.SandboxError = "Provisioning failed"
    }
    
    return nil
}

// Lifecycle: Extend TTL
func (r *EphemeralNamespaceReconciler) extendSandbox(ctx context.Context, ns *EphemeralNamespace, newTTL time.Duration) error {
    patch := map[string]interface{}{
        "spec": map[string]interface{}{
            "lifespan": map[string]interface{}{
                "end": time.Now().Add(newTTL).Format(time.RFC3339),
            },
        },
    }
    
    _, err := r.BabylonClient.PatchResourceClaim(
        "user-ephemeral-namespaces",
        ns.Status.SandboxResourceClaimName,
        patch,
    )
    return err
}

// Lifecycle: Delete sandbox
func (r *EphemeralNamespaceReconciler) cleanupSandbox(ctx context.Context, ns *EphemeralNamespace) error {
    return r.BabylonClient.DeleteResourceClaim(
        "user-ephemeral-namespaces",
        ns.Status.SandboxResourceClaimName,
    )
}
```

**Why NOT Use the Babylon CLI Binary Directly:**

- ❌ **Authentication**: CLI requires browser-based OAuth (can't work in pods)
- ❌ **Shell execution**: Anti-pattern for K8s operators (hard to debug, test, maintain)
- ❌ **Token expiry**: CLI sessions expire every ~10 minutes
- ❌ **Binary distribution**: Need to bundle CLI in container, manage versions
- ❌ **Integration**: Shell output parsing is fragile vs. native Go types
- ✅ **Instead**: Copy HTTP client patterns, use service account auth, native Go integration

### Technical Requirements (Options 1 & 2)

**Sandbox API Access:**
1. **Route URL**: `https://sandbox-api.<something>.redhat.com` (need actual hostname)
2. **JWT Token**: Issued by RHDP admin with `app` role
   - Sufficient for `POST /api/v1/placements` (create sandbox)
   - Sufficient for `GET /api/v1/placements/{uuid}` (check status)

**API Endpoints to Use:**
- `POST /api/v1/placements` - Provision new sandbox account
- `GET /api/v1/placements/{uuid}` - Query placement status

**Documentation:**
- API docs available at pkg.go.dev
- Private repo: `rhpds/sandbox` (optional, for full API surface)

### Architecture Considerations
- How will AWS credentials be managed and rotated?
- What AWS resources need to be created per ephemeral namespace?
- How does resource cleanup work when namespaces are destroyed?
- Integration with existing AWS account structure?
- Service account permissions and scope for demo/sandbox API access
- **Chargeback/Cost Tracking**: How to ensure usage is properly attributed for financial reporting
- **Operational Visibility**: Must maintain visibility into who used resources and when
- **Metadata Consistency**: Lifespan, cost allocation, usage tracking through consistent funnel

### Critical Requirements
- **Cost Allocation**: Must support chargeback model for AWS sandbox usage
- **Usage Tracking**: Need visibility into resource consumption for operational reports
- **Lifecycle Management**: Consistent tracking of sandbox lifespan and cleanup
- **Financial Reporting**: Must not break existing operational and financial reporting

### Approach Comparison Matrix

| Aspect | Option 1 (Direct API) | Option 2 (Service-Mediated) | Option 3 (HTTP Client + Catalog API) |
|--------|----------------------|----------------------------|-------------------------|
| **Integration Point** | ENO → Sandbox API | ENO → demo.redhat.com → Sandbox API | ENO (HTTP) → Catalog API → ResourceClaim → Babylon stack → AWS |
| **Network Path** | HTTPS to Sandbox API | HTTPS to demo.redhat.com | HTTPS to Catalog API (port 443) |
| **Cross-Cluster** | Yes | Yes | Yes (ENO on ephemeral cluster, Babylon on separate cluster) |
| **Auth Complexity** | Need app-role JWT | Need demo.redhat.com integration | Service account token (+ possibly OAuth cookies) |
| **Sandbox API Exposure** | Direct | Via demo.redhat.com | Via Babylon (Catalog API → AgnosticD → Sandbox API) |
| **Cost Tracking** | Manual (forced annotations) | Automatic (service layer) | Automatic (cost-tracker operator on Babylon cluster) |
| **Chargeback** | Via forced annotations | Via demo.redhat.com | Via ResourceClaim annotations |
| **Operational Visibility** | Reduced | Full | Full (via Babylon) |
| **ENO Coupling** | Sandbox API schema | demo.redhat.com API | ResourceClaim schema + Catalog API REST endpoints |
| **Infrastructure Reuse** | Minimal | Some | Full (Poolboy, Anarchy, AWX, AgnosticD) |
| **Lifecycle Management** | ENO implements | Service layer | Babylon stack (via HTTP operations) |
| **Client Type** | HTTP client | HTTP client | HTTP client (copy babylon CLI pattern) |
| **Status Updates** | Poll Sandbox API | Poll service | HTTP GET ResourceClaim status |
| **Dependencies** | Sandbox API availability | demo.redhat.com + Sandbox API | Babylon Catalog API + platform (Poolboy, Anarchy, AWX) |
| **Development Effort** | Medium (API integration) | Medium-High (service integration) | Medium (HTTP client + ResourceClaim construction) |
| **Operational Risk** | Bypasses service layer | Service dependency | Platform dependency (Catalog API must be reachable) |
| **Reference Implementation** | None | Unknown | babylon CLI (HTTP client, ResourceClaim construction, full code) |
| **Testing** | Mock HTTP requests | Mock HTTP requests | Mock HTTP requests (easier with typed Go structs) |

**Recommendation**: Option 3 (HTTP Client via Catalog API) is the best fit for ENO because:
1. **Cross-cluster reality**: ResourceClaims must be created on Babylon cluster, not ephemeral cluster where ENO runs
2. **Catalog API designed for this**: Remote access via HTTPS (port 443), already handles OAuth proxy, routing
3. **Full infrastructure reuse**: Babylon stack handles provisioning, lifecycle, cost tracking automatically
4. **Clean separation of concerns**: ENO manages ephemeral namespaces, Babylon manages AWS provisioning
5. **Complete reference implementation**: babylon CLI provides full HTTP client code to copy patterns from
6. **Preserves operational visibility**: Cost tracking, chargeback, reporting all work through Babylon
7. **Standard REST patterns**: Easier to debug than direct K8s API (port 6443), likely allowed through firewalls
8. **Native Go integration**: Typed structs, testable with mocks, fits standard operator patterns

### Questions to Answer

**Architecture & Integration:**
- What is the expected lifecycle of AWS sandbox accounts?
- Are sandbox accounts shared or dedicated per namespace?
- What AWS services need to be accessible?
- What are the specific API endpoints available in the demo/sandbox API?
- What authentication mechanism does the demo/sandbox API use?
- How are forced annotations configured in sandbox API for cost tracking?
- What metadata is required for chargeback and operational reporting?
- Does babylon CLI provide the needed integration points for ephemeral workflow?
- How do we want to integrate other technologies in ENO/bonfire services?

**Testing & Validation:**
- What manual tests did @gurnben run locally to validate the approach?
- What test scenarios are needed for sandbox provisioning integration?
- How can we replicate local testing for development/validation?

**Reference Implementations:**
- Brandon's work on bonfire standing up ROSA clusters - can this pattern be followed?
- What integration patterns exist in bonfire for external service provisioning?

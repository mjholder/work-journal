---
type: reference
created: 2026-10-14
tags:
  - org-pulse
  - dataverse
  - sdlc-report-card
  - meeting-agenda
---
# Dataverse Discovery Meeting Agenda

**Meeting Purpose:** Define the integration contract between Org Pulse and Dataverse for SDLC Report Card metrics

**Attendees:**
- **Dataverse Team:** Eric Rich (primary), Brad Tweardy (primary), John Kyros (secondary)
- **Org Pulse Team:** [Your names here]

**Related Jira Ticket:** [ENGPROD-10433](https://redhat.atlassian.net/browse/ENGPROD-10433) — Define the Dataverse query contract for SDLC Report Card metrics

**Background:**
Dataverse (Snowflake-backed) will own all metric calculations for the 33 SDLC Report Card measurements. Org Pulse becomes visualization-only: query Dataverse, cache locally, render dashboard with four-tier rubric.

---

## API & Integration Basics

### 1. What is the Dataverse API surface?
- REST endpoints? GraphQL? gRPC? Direct Snowflake connection?
- Base URL for the SDLC metrics endpoint(s)?
- Is there API documentation or OpenAPI spec we can review?

### 2. Authentication & Authorization
- What auth mechanism: API keys, OAuth 2.0, mTLS, service account?
- How do we provision credentials for Org Pulse production environment (OpenShift)?
- Credential rotation policy and process?
- Rate limits or quotas per credential?

### 3. Query Patterns
- Do we query all 33 metrics in a single call, or separate endpoints per metric?
- Can we filter by team/component/altitude server-side, or do we pull everything and filter client-side?
- What query parameters are supported (date ranges, team filters, metric IDs)?

---

## Data Model & Schema

### 4. Metric Identification
- How are the 33 SDLC Report Card metrics identified in Dataverse?
- Do you use the row numbers from the leadership spreadsheet, or custom metric IDs?
- Mapping between leadership's Goal Groups/Attributes and Dataverse metric names?

### 5. Response Format
- JSON? Protobuf? CSV? Parquet?
- Can you provide example responses for:
  - A flow metric (e.g., Cycle Time at Epic altitude)
  - A work mix metric (e.g., Reactive Work %)
  - A sustained-threshold metric (e.g., Net Delivery Flow with 3+ quarters)

### 6. Tier Calculation
- Does Dataverse return pre-calculated tiers ("does-not-meet", "meets-some", "meets", "surpasses")?
- Or raw values that Org Pulse scores against the CSV thresholds?
- If pre-calculated, how are tier thresholds configured in Dataverse?

---

## Historical Data & Sustained Thresholds

### 7. Quarterly Historical Data
- Can Dataverse provide trailing quarterly snapshots for sustained-threshold metrics?
- How many quarters of history are available today?
- If history is incomplete, when did metric calculation start, and when will 3+ quarters be available?

### 8. Sustained Threshold Evaluation
- Do you calculate "3+ consecutive quarters" thresholds, or does Org Pulse?
- If Dataverse calculates: what's the field name in the response?
- If Org Pulse calculates: what granularity of history do you provide (daily? monthly? quarterly snapshots)?

---

## Refresh Cadence & Freshness

### 9. Data Update Frequency
- How often does Dataverse recalculate SDLC metrics? Daily? Weekly? Real-time?
- What's the recommended polling interval for Org Pulse?
- Is there a "last updated" timestamp in the response to detect staleness?

### 10. Change Notifications
- Is there a webhook or event stream when metrics update, or do we poll?
- If polling: what's the acceptable request rate without hitting limits?

---

## Error Handling & Reliability

### 11. Error Scenarios
- What HTTP status codes / error messages for: missing data, auth failure, rate limiting, server errors?
- If a specific metric fails to calculate (e.g., insufficient Jira data), how is that indicated?
- Partial failure handling: if 32/33 metrics succeed, do we get the 32, or does the whole request fail?

### 12. SLAs & Availability
- What's the expected uptime for the Dataverse SDLC metrics API?
- Maintenance windows or known outage periods?
- Support contact if Org Pulse encounters integration issues?

---

## Scope & Coverage

### 13. Team/Component Filtering
- The leadership spreadsheet has empty columns for scope definition (which Jira projects, GitHub orgs, LDAP roots, teams).
- How does Dataverse define the denominator for each metric?
- Can we filter results to specific teams or components, or is it HP-wide only?

### 14. Future Expansion
- Are additional metrics beyond the current 33 planned?
- Schema versioning strategy for breaking changes?
- Deprecation process for endpoints or fields?

---

## Action Items from Meeting

### 15. Next Steps
- Can we get sandbox/staging credentials to test integration before production?
- Example queries we can run to validate our understanding?
- Review cycle for the integration spec we'll write in `docs/DATAVERSE-INTEGRATION.md`?
- Timeline for production credential provisioning?

---

## Expected Outcomes

1. **Contract specification** for `docs/DATAVERSE-INTEGRATION.md`
2. **Three example queries** with request/response payloads
3. **Historical data answer** for sustained-threshold metrics
4. **Authentication approach** (credentials, rotation, storage)
5. **Client architecture recommendation** (refresh cadence, caching)
6. **Follow-up tickets** for implementation

---

## Critical Unknown: The "3+ Quarters" Problem

~10 of the 33 metrics require sustaining a level for **3+ consecutive quarters** to reach "Surpasses" tier:
- Row 29: WIP-to-Throughput within target range for 3+ consecutive quarters
- Row 33: Net Delivery Flow Ratio between 80–110% for 3+ consecutive quarters

**Question:** Does Dataverse retain quarterly snapshots? If not, when does the clock start?

**Leadership impact:** If quarterly history is unavailable, the dashboard cannot evaluate Surpasses tier for these metrics until Q4 (9+ months from now). This needs to be communicated early.

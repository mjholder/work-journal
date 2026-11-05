---
type: knowledge
tags:
  - dataverse
  - snowflake
  - org-pulse
  - sdlc-report-card
  - data-pipeline
  - metrics
created: 2026-10-16
---
# Dataverse `dataproduct-config` — Structure, Access, and Integration Mechanics

How Dataverse data products are declared, how access is granted, and how a consuming
application actually reads the data. Derived from a direct read of the config repo on
**2026-10-16**, not from documentation.

- **Repo:** `gitlab.cee.redhat.com/dataverse/dataverse-config/dataproduct-config`
- **Local clone:** `~/git_repos/dataproduct-config`
- **Scale:** ~190 source products, ~120 aggregate products, 3 platform, ~200 unstructured; 420 prod service accounts
- **Activity:** commits daily, mostly automated `[Consumer Access]` / `[Developer Access]` MRs from the `dataverseconsole` bot

Context for why this matters: [[org-pulse-sdlc-report-card]] · [[rhai-org-pulse]]

## Anatomy of a Data Product

Every product — source or aggregate — is a directory with the same shape:

```
dataproducts/<source|aggregate|platform|unstructured>/<name>/
├── .cruft.json              # links to cookiecutter template; `just update-projects`
├── info.yaml                # just `name: <name>`
├── README.md                # team name, manager, description, AppCode, ESS/PIA notes
├── data_elements.md         # PII checklist against the Snowflake Privacy Impact Assessment
├── developers.yaml          # owners list → CODEOWNERS → MR approval rights
├── promotion_checklist.md
├── groups/                  # rover group definitions (bulk membership)
├── access-requests/groups/<group>/<user>.yaml   # Ludo self-service, one file per user
└── {dev,sandbox,preprod,prod,platformtest}/
    ├── product.yaml         # schemas exposed + who may consume them
    ├── sourcebinding.yaml   # raw landing zone — SOURCE PRODUCTS ONLY
    ├── fivetran/fivetranconnector.yaml   # ingestion method A
    ├── snowpipeconfig.yaml               # ingestion method B
    ├── migrations/VN__name.sql           # schemachange; R__ prefix = repeatable
    └── pii_string_data_masking.yaml, tag_pii_data_masking.yaml
```

Only `sandbox` and `dev` are provisioned by default. Promotion is
`just promote <product> <source-env> <target-env>` (copies `product.yaml`) or a manual copy.

## Source vs Aggregate

The distinction is structural, not cosmetic.

| | Source (`kind: source-aligned`) | Aggregate (`kind: aggregated`) |
|---|---|---|
| `sourcebinding.yaml` | **Yes** — binds to `fivetran_db.<schema>` or `snowpipe_db.<schema>` | **No** — verified absent across all envs for `openshift`, `healthindex`, `engmetrics` |
| Ingests raw data | Yes (Fivetran or Snowpipe) | No |
| Rover group | `dataverse-source-<name>` | `dataverse-aggregate-<name>` |
| Publishes | `<name>_db.<mart_schema>` | `<name>_db.<mart_schema>` |
| Transformation | Minimal — extract/load | DBT models (the calculations live here) |

**An aggregate product is where DBT models live.** It carries `service_account: {dbt: true}`,
needs an `<name>_astro_<env>_appuser`, and is scheduled via Astro (Airflow). So "Dataverse
runs the calculations" means *on Dataverse infrastructure* — **whoever owns the aggregate
product writes and maintains the DBT**. This is the single most commonly mis-set expectation
about the platform.

## Dependency Direction: Producer-Side

Access between products is declared **by the producer, not the consumer**. To let aggregate
`orgpulse` read Jira, the change goes in `dataproducts/source/jira/prod/product.yaml`:

```yaml
data_product_db:
- database: jira_db
  presentation_schemas:
  - name: cloud_marts
    consumers:
    - name: orgpulse
      kind: data_product        # or: consumer_group | service_account
```

Consequence: **every upstream source is a separate MR against that team's directory,
approved by the owners in their `developers.yaml`.** The integration cost is social
(N conversations, N approvals), not technical. The named product or service account must
already exist, or be created in the same MR.

## Two Ingestion Mechanisms

| | Fivetran | Snowpipe |
|---|---|---|
| Lands in | `fivetran_db.<schema>` | `snowpipe_db.<schema>` |
| Config | `<env>/fivetran/fivetranconnector.yaml` | `<env>/snowpipeconfig.yaml` + migration SQL |
| Good for | SaaS/DB sources with a managed connector | **Pushing your own data** |
| Credentials | `vault:<path>#TOKEN` reference in the connector YAML | — |

The Snowpipe path is the one to copy if a team ever needs to *push* data in (e.g. repo
posture scan results, which no SaaS connector can produce). Working example —
`source/engmetricssource`, parquet → S3 external stage → pipe → `variant` table:

```sql
create or replace table SNOWPIPE_DB.ENGMETRICSSOURCE.OWNERS_COMPONENTS (RAW_RECORD variant);
create or replace pipe SNOWPIPE_DB.ENGMETRICSSOURCE.PIPE_OWNERS_COMPONENTS auto_ingest=false
  as copy into SNOWPIPE_DB.ENGMETRICSSOURCE.OWNERS_COMPONENTS (RAW_RECORD)
  from @ENGMETRICSSOURCE_EXTERNAL_SANDBOX_STG/owners/components
  file_format = (type = parquet) pattern = '.*\.parquet$';
alter pipe PIPE_OWNERS_COMPONENTS refresh;
```

## Access Model

Three independent layers; effective access is the union.

**1. Rover groups (`groups/*.yaml`)** — bulk membership, approvers, backends, LDAP queries.

| Group type | Naming |
|---|---|
| Core team | `dataverse-{type}-{product}` |
| Consumer | `dataverse-consumer-{product}-{mart}` (mart name with `_` stripped) |
| Business owners / Product owners / Maintainers | `dataverse-{type}-{product}-{role}` |

Groups can resolve membership dynamically from LDAP — this is a ready-made answer to
"how do we scope a metric to an org":

```yaml
members:
  ldap_query:
    options: {include_indirect_reports: true, include_manager: true}
    operator: and
    filters:
    - {key: manager, criteria: equals, value: agk}
```

**2. Access requests (`access-requests/groups/<group>/<user>.yaml`)** — created by the Ludo
console for individual self-service requests. One file per user, deliberately, to avoid
merge conflicts at volume. Content is two lines: `name:` and `data_product:`.

**3. Consumer declarations in `product.yaml`** — product-to-product and service-account
access, as above.

**Masking is a fourth, orthogonal layer.** `pii_string_data_masking.yaml` defines a policy
that replaces strings with `==MASKED==` for everyone *except* an explicit allow-list:

```yaml
kind: MaskingPolicy
name: github_pii_string_policy
mask: "==MASKED=="
cases:
  - strategy: UNMASKED
    consumers:
      - {kind: consumer_group, name: dataverse-source-github}
      - {kind: consumer_group, name: dataverse-aggregate-tpserviceusage}
```

Being a declared consumer of a mart does **not** mean you see unmasked values. Unmasking is
a separate grant. On `github` only two consumers hold it.

Marts may also carry `access_policy: rh_internal` (e.g. `jira.rhai_marts`,
`gitlab.marts`, `releasecompliance.marts`).

## Service Accounts

Path: `serviceaccounts/<env>/<product>_<tool>_<env>_appuser.yaml`. Tiny files:

```yaml
name: orgpulse_dashboard_prod_appuser
comment: "What this reads and why"
email: owner@redhat.com
role: ORGPULSE_DASHBOARD_ROLE
warehouse: DATAVERSE_ORGPULSE_XS_WH   # optional
```

Field usage across all 420 prod accounts: `name`/`email`/`comment` 420, `role` 305,
`warehouse` 15, `expires_on_date` 3, `database` 1. 224 of 420 are `_astro_` (DBT
orchestration); the remainder are app/BI consumers.

For an Astro service account, the role grant also needs a migration in the product:

```sql
SET ASTRO_ROLE = '<product>_ASTRO_ROLE';
SET DBT_ROLE = '<product>_DBT_<env>_APPUSER_ROLE';
USE ROLE SECURITYADMIN;
GRANT ROLE IDENTIFIER($DBT_ROLE) TO ROLE IDENTIFIER($ASTRO_ROLE);
```

## How a Consuming Application Reads the Data

**There is no Dataverse data-access API.** Searched the repo for REST/GraphQL/endpoint
references — every hit is a *source system's* own API feeding ingestion (PagerDuty,
Cloudoscope), never an outward-facing query surface. "Gateway" in service account names
(`candlepin_gateway`, `cloudmarketplace_gateway`) refers to the consuming application
being a gateway, not to a Dataverse gateway.

The path is a **direct Snowflake connection with key-pair JWT auth**:

| | |
|---|---|
| Host | `gdadclc-rhprod.snowflakecomputing.com` (also `-rhpreprod`, `-rhdev`, `-rhsandbox`) |
| Protocol | Snowflake driver — SQL. Not REST, not GraphQL |
| Auth | RSA key-pair / JWT. Not OAuth, not API keys |
| Credential storage | Vault, `ddis-asteroid-infra/rh<env>/snowflake/serviceaccounts/...` |
| Rotation | `dice sync serviceaccounts --environment=rhprod --rotate-keys` |

Stated plainly in the `candlepin_gateway_prod_appuser` comment:

> Authentication: Snowflake JWT (key-pair). Credentials will be stored in Bitwarden and
> wired into Entitlement Gateway configuration via Vault.

**Keys rotate**, via a manually-triggered pipeline gated on `ROTATE_KEYS == "true"`. A
consuming app must read the private key from Vault at runtime rather than baking it into a
static secret.

**Network policies are per-user and need their own migration.** If an app's egress isn't
covered by an existing policy, add one:

```sql
USE ROLE USERADMIN;
ALTER USER JIRA_TABLEAU_PREPROD_APPUSER SET NETWORK_POLICY = TABLEAU_APPUSER_NW_POLICY;
```

## Tooling

- **`dice`** — the reconciler (`images.paas.redhat.com/ddis-asteroid/dice`).
  `dice validate|sync serviceaccounts|dataproducts --environment=rh<env>`. Runs in GitLab CI.
- **`just`** — `create-dataproduct` (cruft/cookiecutter), `promote`, `check-projects`,
  `update-projects`, `update-codeowners`, `create-connector`, `validate-groups`, `list-groups`
- **Ludo** — the Dataverse console; writes `access-requests/` files and consumer-access MRs
- **`schemachange`** — applies `migrations/VN__*.sql`
- **Force reconcile** — web-triggered `force-reconcile-dataproduct` pipeline with
  `ENVIRONMENT`, `DATAPRODUCT_KIND`, `DATAPRODUCT_NAME`

## Product Inventory Relevant to the SDLC Report Card

Status as of 2026-10-16. "Live" = `prod/product.yaml` exists and the connector is unpaused.

| Product | Kind | Status | Ingestion | Notes |
|---|---|---|---|---|
| `jira` | source | **Live** | Fivetran `aurora_postgres`, **15 min** | `ai_ready: true`. 5 marts: `marts`, `rhai_marts`, `cloud_marts`, `cloudrhai_marts`, `consolidated_marts` |
| `github` | source | **Live** | Fivetran ×4, 60 min | ~75 tables each. Strict PII masking |
| `gitlab` | source | **Live** | Snowpipe | gitlab.cee. Only declared consumer is `releasecompliance` — thin |
| `gitlabsaas` | source | **Live** | Snowpipe | ITBPS-owned |
| `brew` | source | **Live** | Fivetran `aurora`, daily | Build data |
| `errata` | source | **Live** | Fivetran `mongo`, daily | Advisories / release |
| `pyxis` | source | **Live** | Fivetran `mongo`, 6 h | Certification framing |
| `roverpeople` | source | **Live** | Fivetran `aurora_postgres`, daily | Org hierarchy — needed for team/manager rollups |
| `sonarqubecorp` | source | **Live** | Snowpipe | **User and licence data only — not code quality** |
| `osidb` | source | **Sandbox only** | — | ProdSec flaw data (jvang) |
| `prodsecrisks` | source | **Sandbox only** | — | PRODSECRM risk register (Vincent Danen) |
| `engmetricssource` | source | **Dev/sandbox** | Snowpipe (parquet) | agk's team. `OWNERS_COMPONENTS`, `OWNERS_RPMS` |
| `engmetrics` | aggregate | **Dev/sandbox** | — | agk, lichen, podvody, ahills |
| `openshift` | aggregate | **Live** | — | Telemetry + Insights Operator fleet data |
| `healthindex` | aggregate | **Live** | — | Data-quality scoring — a working "report card" precedent |
| `jiraconsolidated` | aggregate | **No envs** | — | Stub; group file only |

**No Konflux and no Quay product exists anywhere in the repo.**

### GitHub table manifest

The Fivetran connector enumerates every synced table. Relevant groups:

- **PRs/review:** `pull_request`, `pull_request_review`, `pull_request_review_comments`,
  `pull_request_review_dismissed`, `pull_request_ready_for_review_history`,
  `pull_request_auto_merge`, `pull_request_merge_queue`, `requested_reviewer_history`
- **Commits:** `commit`, `commit_file`, `commit_parent`, `commit_pull_request`,
  `commit_check_run`, `commit_status`, `branch_commit_relation`
- **CI:** `workflow`, `workflow_run`, `workflow_run_pull_request`
  (`workflow_run_attempt`, `workflow_run_job`, `workflow_run_job_step` are **disabled**)
- **Security:** `security_alert`, `security_advisory`, `security_advisory_vulnerability`,
  `security_vulnerability`, `security_cwe`, `security_reference`
- **Repo/org:** `repository`, `repository_language`, `repository_topic`,
  `repository_property`, `repo_collaborator`, `repo_team`, `team`, `team_membership`, `release`
- **Copilot:** 12 `copilot_*` tables (org/user metrics by feature, IDE, language, model)
- **Issues:** `issue` + 11 `issue_*` history/relation tables

No table carries file *contents* or a repo tree snapshot. `commit_file` gives paths touched
per commit — enough to infer that a file was once committed, not that it exists today.

## Precedents Worth Copying

| Service account | Owner | Why it matters |
|---|---|---|
| `hpai_jiraauto_preprod_appuser` | skyros (John Kyros) | **HP already has a Dataverse SA.** `role: dataverse_consumer_jira_rhaimarts_role`, `warehouse: DATAVERSE_JIRA_XS_WH`. Preprod only — no prod counterpart |
| `jira_shipshape_prod_appuser` | bleanhar | "Statistical tool for predicting feature completion dates" — flow metrics on Jira marts, already approved |
| `jira_devprod_prod_appuser` | ascerra (Konflux DevProd) | Moved from a PAT to a service account for Snowflake MCP access |
| `releasecompliance_report_prod_appuser` | coberle | Report generation off an aggregate's marts |
| `openshift_ocpusagedashboard_prod_appuser` | ddelcian | Streamlit dashboard reading `openshift_db` marts |

## Gotchas

1. **`dataverse-consumer-jira-marts` is decommissioned** — the group file says so in a
   header comment: *"new users should request access to jira-cloudmarts instead."* It still
   has ~85 members, so it looks healthy from the inside.
2. **Jira MCP server service accounts were decommissioned** in Oct 2026
   (PANI-551 prod, PANI-554 preprod). `jira_devprod` survives.
3. **Being a consumer ≠ seeing unmasked data.** Separate grant, separate allow-list.
4. **GitHub ingestion scope is per-connector, not org-wide.** Four separate connectors
   (`github`, `github_omegaprime`, `github_codechain`, `github_securesign`) imply
   per-GitHub-App-install scope. Which orgs and repos are covered is **not** discoverable
   from this repo — it depends on the PAT/JWT's visibility.
5. **No product owns code quality or test coverage.** `sonarqubecorp` is licence
   administration, despite the name.
6. **Timeline:** raw source data is queryable immediately; a new aggregate product with
   custom DBT is 2–4 weeks (per Eric Rich, 2026-10-14).

## Open Questions

- Which GitHub orgs/repos the `github` connectors actually cover — ask tdeanton
- Which columns carry the `github_pii` tag, and whether author/reviewer identity is among
  them (per-team attribution depends on it)
- Whether a custom application reading Snowflake under a service account and rendering
  results to other people satisfies the governance model that Preset was chosen to enforce.
  A service account flattens per-viewer RBAC into one role — this is the gap, not an
  implementation detail
- Whether `engmetrics` (agk) intends to cover engineering/SDLC metrics, which would make a
  separate Org Pulse aggregate redundant

## Related Notes

- [[org-pulse-sdlc-report-card]] — the 33-row report card this research serves
- [[rhai-org-pulse]] — parent project
- [[rfe-assessor-data-pipeline]] — contrasting pattern: push to Org Pulse's own bulk API
  rather than pull from a warehouse

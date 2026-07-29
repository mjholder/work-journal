---
type: knowledge
tags:
  - clowder
  - bug
  - disaster-recovery
  - export-service
created: '2026-06-11'
---
# Clowder DB Secret DR Reconciliation Bug

## Problem

During disaster recovery of a database, the export-service team brings up a recovery DB from an AWS snapshot via Terraform in app-interface. The app-interface resource definition uses the `clowder/database` annotation on the generated secret so Clowder can match DB creds to the correct service.

**What goes wrong:** When the DR secret is created/updated with the `clowder/database` annotation, Clowder does not update the `cdappconfig` to reference the new secret. The secret itself may be correct, but the app keeps using stale DB connection info from the old `cdappconfig`.

**Current workaround:** Manual intervention — bounce pods or delete the `cdappconfig` to force Clowder to reconcile and pick up the new secret.

## Expected Behavior

Clowder should detect when a secret with the `clowder/database` annotation changes (or a new one appears matching a ClowdApp's DB) and automatically update the `cdappconfig` to reflect the new credentials — no manual pod bounce or config deletion needed.

## Affected Team

- **export-service** — hit this during DR exercises

## Related

- [[clowder-scaledobject-bug]] — different Clowder reconciliation bug (ScaledObject serverAddress), but same general area: Clowder not reconciling changes it should
- The fix likely lives in Clowder's database provider or the main ClowdApp reconciliation loop — need to investigate how secret watches and `cdappconfig` generation interact

## Status

Not yet investigated. Want to fix this for the export-service team.

---
type: sop
tags:
  - sop
  - rfe-assessor
  - rubric
  - org-pulse
created: 2026-08-06
project: rfe-assessor
---
# SOP: Customizing the RFE Assessment Rubric

This SOP covers end-to-end rubric changes — from editing the grading criteria to having the agent use them and having results display correctly in [[org-pulse]].

## Data Flow Overview

```
assess-rfe agent (rfe-scorer)
    reads agent_prompt.md (rubric)
    writes .result.md per issue
        │
        ▼
parse_results.py
    extracts scores → scores.csv
    columns: ID, Title, WHAT, WHY, HOW, Task, Size, Total, Pass_Fail
        │
        ▼
push-to-org-pulse.py (rfe-assessor CI pipeline)
    reads scores.csv + .result.md
    maps display names → API field names (e.g. "Open to HOW" → "how")
    derives anti-patterns from zero scores
    POSTs to org-pulse bulk API
        │
        ▼
org-pulse server (validation.js → storage.js)
    validates criteria names, score ranges, total
    upserts to assessments.json (latest + history)
        │
        ▼
org-pulse frontend (8 Vue components)
    hardcodes CRITERIA_LABELS, score ranges, /10 display, pass/fail thresholds
```

## Determine Your Change Type

| You want to change... | Path |
|---|---|
| Criterion descriptions, what counts as a 0/1/2 | Path 1 (content-only) |
| Calibration examples | Path 1 |
| Platform vocabulary list (technologies that don't count as "prescribing HOW") | Path 1 |
| Pass/fail threshold (currently ≥7 with no zeros) | Path 1 (rubric only) + Path 2 (org-pulse display thresholds) |
| Add, remove, or rename a criterion | Path 2 (structural) |
| Change scoring range (e.g. 0-3 instead of 0-2) | Path 2 (structural) |

---

## Path 1: Content-Only Changes

**Scope:** Single file edit. No code changes downstream.

### Steps

1. **Edit the rubric**
   - File: `assess-rfe/skills/assess-rfe/scripts/agent_prompt.md`
   - This is the single source of truth. The scorer agent reads it at runtime.
   - Modify criterion descriptions, scoring guidance, calibration examples, smell tests, or platform vocabulary as needed.

2. **Test locally**
   - Run a single-issue assessment: `/assess-rfe RHAIRFE-1234`
   - Verify the `.result.md` output reflects your updated scoring logic.
   - Check that `parse_results.py` still extracts scores correctly (it pattern-matches on criterion names like WHAT, WHY, HOW, Task, Size — these must stay the same for Path 1).

3. **Commit and publish**
   - Commit to `assess-rfe` repo.
   - The plugin cache updates when the skill registry picks up the new version.

4. **Re-run bulk assessment**
   - Trigger a bulk run: `/assess-rfe RHAIRFE-*` (or via CI pipeline in `rfe-assessor`).
   - The CI pipeline automatically runs `parse_results.py` and `push-to-org-pulse.py`.
   - Results appear in org-pulse with no display changes needed.

### What you DON'T need to touch
- `parse_results.py` — criterion name matching is unchanged
- `summarize_run.py` — column names are unchanged
- `push-to-org-pulse.py` — field mapping is unchanged
- org-pulse server or client — no API or display changes

---

## Path 2: Structural Changes

**Scope:** Rubric + pipeline scripts + org-pulse server + org-pulse client. Four repos involved.

### Repo 1: assess-rfe (rubric + parsing)

**`skills/assess-rfe/scripts/agent_prompt.md`**
- Add/remove/rename criteria in the scoring table
- Update the total range (e.g. /12 if adding a criterion)
- Update pass/fail rule
- Update calibration examples for new/changed criteria

**`skills/assess-rfe/scripts/parse_results.py`**
- Criterion matching (~lines 62-70): update the pattern-match names
- CSV fieldnames (~line 171): update column headers
- Pass/fail rule (~lines 89-94): update threshold and zero-check logic
- `extract_scores()` function: add/remove criterion extraction

**`skills/assess-rfe/scripts/summarize_run.py`**
- Column names (~lines 31, 52): match new CSV headers
- What-if thresholds (~lines 75-76): update if pass/fail rule changed
- Score distribution buckets: update if total range changed

### Repo 2: rfe-assessor (CI pipeline)

**`scripts/push-to-org-pulse.py`**
- `CRITERION_NAME_MAP` (~line 73): maps display names (from .result.md) to API field names
  - e.g. `"Open to HOW": "how"`, `"Not a task": "task"`, `"Right-sized": "size"`
- `ANTI_PATTERN_RULES` (~line 64): maps zero-score criteria to anti-pattern labels
  - e.g. `why=0 → "WHY Void"`, `task=0 → "Task Masquerade"`
- `parse_scores_csv()` (~lines 116-138): CSV column → API field mapping

### Repo 3: rhai-org-pulse server

**`modules/ai-impact/server/assessments/validation.js`**
- `CRITERIA` array (line 1): `['what', 'why', 'how', 'task', 'size']`
- Score range validation (line 23): `val > 2` — update if range changes
- Total range validation (line 28): `body.total > 10` — update if total changes

**`modules/ai-impact/server/assessments/routes.js`**
- No structural changes unless you modify the API shape

### Repo 4: rhai-org-pulse client

All of these components hardcode criterion labels and/or scoring ranges:

| Component | What to update |
|---|---|
| `AssessmentBreakdown.vue` | `CRITERIA_LABELS` map (~line 15), dot rendering (assumes 0-2), `/10` text |
| `CriteriaBreakdownChart.vue` | `CRITERIA` and `CRITERIA_LABELS` (~lines 21-22), Y-axis max of 2 |
| `ScoreDistributionChart.vue` | Bucket count (`Array(11)` ~line 21), pass threshold coloring (~line 34: `i < 5`), labels 0-10 |
| `AssessmentHistory.vue` | `CRITERIA` (~line 65), Y-axis max of 10, pass threshold of 5 |
| `ForYouCard.vue` | Dimension label array (~lines 47-53), `scoreColor` thresholds |
| `AssessmentGuideModal.vue` | Hardcoded criterion descriptions table (~lines 130-149) |
| `RFEListItem.vue` | `/10` display text (~line 72) |
| `RfeBacklogTable.vue` (team-tracker module) | `/10` display text (~line 89) |

### Tests and fixtures to update

- `modules/ai-impact/__tests__/server/assessment-validation.test.js`
- `modules/ai-impact/__tests__/server/assessment-routes.test.js`
- `modules/ai-impact/__tests__/server/assessment-storage.test.js`
- `modules/ai-impact/__tests__/client/useAssessments.test.js`
- `modules/ai-impact/__tests__/client/ForYouCard.test.js`
- `modules/ai-impact/__tests__/client/useForYou.test.js`
- `modules/ai-impact/__tests__/client/RFEReviewNavigation.test.js`
- `modules/team-tracker/__tests__/client/RfeBacklogTable.test.js`
- `fixtures/ai-impact/assessments.json`

### Deployment order

1. **org-pulse first** — deploy updated server validation + client display so it can accept the new shape. Make the validation accept BOTH old and new shapes during transition if you want zero-downtime.
2. **rfe-assessor pipeline** — update `push-to-org-pulse.py` to emit the new shape.
3. **assess-rfe** — publish the updated rubric and parsing scripts.
4. **Re-run bulk assessment** — new results flow through the updated pipeline into the updated display.

---

## Checklist

### Path 1 (content-only)
- [ ] Edit `agent_prompt.md` in assess-rfe
- [ ] Test single-issue assessment locally
- [ ] Verify `parse_results.py` still extracts correctly
- [ ] Commit and publish assess-rfe
- [ ] Run bulk assessment
- [ ] Verify results in org-pulse

### Path 2 (structural)
- [ ] Edit `agent_prompt.md` in assess-rfe
- [ ] Update `parse_results.py` criterion matching + CSV columns + pass/fail
- [ ] Update `summarize_run.py` column names + thresholds
- [ ] Test single-issue assessment locally
- [ ] Update `push-to-org-pulse.py` in rfe-assessor (name map, anti-patterns, CSV mapping)
- [ ] Update `validation.js` in org-pulse (CRITERIA array, score ranges)
- [ ] Update all 8 Vue components in org-pulse (labels, ranges, display text)
- [ ] Update `AssessmentGuideModal.vue` criterion descriptions
- [ ] Update tests and fixtures
- [ ] Deploy org-pulse (server + client)
- [ ] Deploy rfe-assessor pipeline
- [ ] Publish assess-rfe skill
- [ ] Run bulk assessment
- [ ] Verify end-to-end in org-pulse

## Related Notes
- [[assess-rfe]]
- [[org-pulse]]
- [[rhai-org-pulse]]
- [[rfe-assessor]]

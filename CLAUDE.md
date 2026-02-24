# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a development work journal system for tracking daily progress, project summaries, and task management. The journal is designed to work purely conversationally with Claude Code - no scripts or automation, just natural conversation throughout the workday.

## Architecture

### Directory Structure

- `entries/YYYY/MM/DD.md` - Daily journal entries organized hierarchically by year/month/day
- `projects/` - Project-specific summary markdown files (named with lowercase-kebab-case)
- `templates/` - Templates for daily entries and project summaries
- `TODO.md` - Running TODO list with today's tasks, upcoming tasks, and completed items

### Templates

- `templates/daily.md` - Template for daily entries with sections for tasks, progress, notes, blockers, and tomorrow's focus
- `templates/project.md` - Template for project summaries with overview, status, progress, and tasks

### Entry Organization

Daily entries use a three-level hierarchy: `entries/YYYY/MM/DD.md` where directories are created as needed. This keeps the structure organized chronologically while remaining easy to navigate.

## Creating and Managing Entries

### Creating Today's Entry

When the user asks to create today's entry:
1. Calculate today's date (YYYY-MM-DD)
2. Create the directory structure: `entries/YYYY/MM/` (if it doesn't exist)
3. Use the template from `templates/daily.md`
4. Replace `{date}` with the formatted date like "2026-02-24 (Tuesday)"
5. Write the file to `entries/YYYY/MM/DD.md`
6. Confirm to the user that the entry was created

### Creating Project Summaries

When the user asks to create a project summary:
1. Use the template from `templates/project.md`
2. Replace `{project_name}` with the provided project name
3. Create a filename using lowercase-kebab-case (e.g., "My Project" → "my-project.md")
4. Write to `projects/{filename}.md`
5. Confirm to the user that the project was created

### No Scripts Required

This journal uses a conversational workflow - there are no scripts to run. All entry creation and management happens through direct file operations based on user requests.

## Workflow with Claude Code

### Daily Entry Workflow

1. User asks Claude to create today's entry (e.g., "Create today's entry")
2. User shares JIRA tasks or work items in conversation with Claude
3. Claude helps organize tasks into the "Tasks for Today" section
4. Throughout the day, Claude updates Progress sections as user completes work
5. Claude assists in identifying blockers and planning tomorrow's focus

### Project Summary Workflow

1. Create project summaries for each active work project
2. Update project files as significant progress is made
3. Use project summaries to track multi-day/multi-week efforts
4. Reference project summaries when creating daily task lists

### Key Patterns

- **Read before writing**: Always read the current day's entry before making updates
- **Preserve existing content**: When updating entries, preserve user's notes and formatting
- **Cross-reference**: Link between daily entries and project summaries when relevant
- **Date awareness**: Use the current date to locate today's entry at `entries/YYYY/MM/DD.md`
- **Task management**: Help translate JIRA items into actionable daily tasks with appropriate detail level
- **Continuity**: Check yesterday's "Tomorrow's Focus" section when planning today's tasks
- **Incremental updates**: Expect users to add information throughout the day, not all at once
- **Natural language**: Respond to requests like "add this to my progress" or "mark that task done"

## Working with Entries

### Reading Today's Entry

To read today's entry, calculate the current date and read the file at `entries/YYYY/MM/DD.md`. For example, for 2026-02-24, read `entries/2026/02/24.md`.

### Updating Entries

When updating an entry:
1. Read the current content first
2. Preserve the user's existing notes and structure
3. Add new tasks/progress in the appropriate sections
4. Maintain markdown formatting consistency

### Project References

When work relates to a specific project, mention the project name in the daily entry's Progress section and consider updating the corresponding project summary file in `projects/`.

## TODO.md Conventions

### Completed Task Format

When marking tasks complete and moving them to the Completed section, use this format:

```markdown
- [x] Task description - YYYY-MM-DD
  - Additional details or notes on indented lines
```

**Example:**
```markdown
## Completed

- [x] Finish upgrading backstage plugins (ENGPROD-8917) - 2026-02-24
  - Tested visual-qontract and web-rca plugins locally and in ephemeral environments
  - [x] visual-qontract plugin
  - [x] web-rca plugin
```

This date-stamping allows looking back to see exactly when tasks were completed, which is useful for:
- Performance reviews and status reports
- Tracking how long certain types of work take
- Referencing when features were delivered
- Understanding project timelines

### Task Completion Workflow

1. Mark task complete in daily entry (`- [ ]` → `- [x]`)
2. Move task from "## Today" to "## Completed" in TODO.md
3. Add completion date in format `- 2026-02-24`
4. Preserve any details or sub-tasks on indented lines below

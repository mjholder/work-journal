# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a development work journal system for tracking daily progress, project summaries, and task management. The journal is designed to work purely conversationally with Claude Code - no scripts or automation, just natural conversation throughout the workday.

## Architecture

### Directory Structure

- `entries/YYYY/MM/DD.md` - Daily journal entries organized hierarchically by year/month/day
- `projects/` - Project-specific summary markdown files (named with lowercase-kebab-case)
- `courses/` - Course learning notes and progress tracking (named with lowercase-kebab-case)
- `templates/` - Templates for daily entries, project summaries, and course notes
- `TODO.md` - Running TODO list with today's tasks, upcoming tasks, and completed items

### Templates

- `templates/daily.md` - Template for daily entries with sections for tasks, progress, notes, blockers, and tomorrow's focus
- `templates/project.md` - Template for project summaries with overview, status, progress, and tasks
- `templates/course.md` - Template for course learning with link, progress, notes, and takeaways

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

### Creating Course Entries

When the user asks to create a course entry:
1. Use the template from `templates/course.md`
2. Replace `{course_name}` with the provided course name (title case)
3. Replace `{course_url}` with empty (user will fill in) or provided URL
4. Replace `{progress}` with "0% - Just Started" or provided progress
5. Create a filename using lowercase-kebab-case (e.g., "React Fundamentals" → "react-fundamentals.md")
6. Write to `courses/{filename}.md`
7. Confirm to the user that the course was created

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

### Course Learning Workflow

1. Create course entries for active learning courses
2. Add detailed notes organized by lesson/module in the course file
3. Update course progress in the header as modules are completed
4. Brief mentions automatically appear in daily entries (Course Work section) for timeline context
5. Add course-related tasks to TODO.md Courses section for learning goals

**Typical course interaction:**
- User takes notes during learning: `/journal course react "Learned about useCallback for memoization"`
- User updates progress: `/journal course react progress "50% - Module 5 complete"`
- User adds quick lesson notes: `/journal lesson "Custom hooks must start with 'use' prefix"`
- Claude automatically updates both course file and today's daily entry

### Key Patterns

- **Read before writing**: Always read the current day's entry before making updates
- **Preserve existing content**: When updating entries, preserve user's notes and formatting
- **Cross-reference**: Link between daily entries and project summaries when relevant
- **Date awareness**: Use the current date to locate today's entry at `entries/YYYY/MM/DD.md`
- **Task management**: Help translate JIRA items into actionable daily tasks with appropriate detail level
- **Continuity**: Check yesterday's "Tomorrow's Focus" section when planning today's tasks
- **Incremental updates**: Expect users to add information throughout the day, not all at once
- **Natural language**: Respond to requests like "add this to my progress" or "mark that task done"
- **Course organization**: Course files parallel projects but focus on learning vs. deliverables
- **Course progress**: Flexible format (percentage, modules, status) updated in header
- **Course notes**: Organized chronologically with timestamps in course file, brief mentions in daily entries
- **Course cross-reference**: Brief mentions in daily Progress > Course Work, detailed notes stay in courses/
- **Course tasks**: Separate "## Courses" section in TODO.md for learning-related tasks distinct from work tasks

### Intelligent Update Detection

Claude Code should **automatically detect and update** relevant journal files based on user messages, even when not explicitly instructed. Analyze each user message for journal-relevant content and update appropriate files proactively.

**Detect these patterns and auto-update:**

1. **Progress updates** - User describes work completed, in-progress, or issues encountered
   - Keywords: "I fixed", "working on", "updated", "found an issue", "tested", "deployed", "started", "completed"
   - Actions: Update today's entry Progress section; update relevant project file if applicable
   - Example: "I fixed the failing tests" → Add to Progress section in daily entry

2. **Task completions** - User indicates they finished a task
   - Keywords: "done", "finished", "completed", "shipped", "merged", "deployed"
   - Actions: Mark task complete in daily entry; move from "Today" to "Completed" in TODO.md with date stamp
   - Example: "The PR is merged" → Mark PR task complete in both files

3. **New tasks discovered** - User mentions new work that needs doing
   - Keywords: "need to", "should", "TODO", "next I'll", "have to", "going to"
   - Actions: Add to daily entry Tasks section if for today, otherwise add to TODO.md Upcoming section
   - Example: "I need to reconfigure the precommit hook" → Add to TODO.md Upcoming

4. **Blockers/Issues** - User mentions problems, errors, or things blocking progress
   - Keywords: "blocked", "error", "failing", "broken", "issue", "problem", "can't"
   - Actions: Add to Blockers/Issues section in daily entry; consider adding remediation task to TODO
   - Example: "The API is returning 500 errors" → Add to Blockers section

5. **Project context** - User mentions specific projects or tickets
   - Patterns: JIRA ticket numbers (e.g., "ENGPROD-1234"), project names mentioned in recent daily entries
   - Actions: Update relevant project summary file in `projects/` if significant progress
   - Determine project file by: checking recent daily entries for project names, looking at TODO.md task context

**Multi-file update strategy:**

When user provides an update, determine which files need updating and update them all:
- **Daily entry** (almost always): Add progress notes, mark tasks complete, note blockers
- **TODO.md**: Mark tasks complete with date stamp, add new urgent tasks, move completed items
- **Project files**: Update if significant milestone reached or status changes for an active project

**Context-aware decision making:**

- Use conversation history and recent daily entries to infer which project is being discussed
- If multiple projects are active, determine which one based on recent context
- Default to creating/updating a project file if work spans multiple days or has substantial scope
- Only ask for clarification if the update is ambiguous AND could lead to incorrect documentation

**Examples of automatic updates:**

| User Message | Automatic Actions |
|--------------|-------------------|
| "I rebootstrapped the ibutsu plugin and it's working now" | • Add to daily entry Progress section<br>• Update backstage-plugin-upgrade project if exists |
| "The tests are all passing now, that's done" | • Mark test-related task complete in daily entry<br>• Move task to Completed in TODO.md with date<br>• Add completion note to Progress |
| "Found a bug in the auth flow, need to investigate tomorrow" | • Add to Blockers/Issues in daily entry<br>• Add investigation task to TODO.md Upcoming |
| "Starting work on the firelink plugin upgrade" | • Add to daily entry Progress section<br>• Update task in TODO.md to in-progress if exists<br>• Update backstage-plugin-upgrade project |
| "Completed Module 3 of the React course" | • Add to daily entry Course Work section<br>• Update course file with module completion note<br>• Ask if progress should be updated |

**Confirmation approach:**

- **Always ask clarifying questions** to help the user articulate exactly what they mean
- Detect what needs updating, but present the user with what you plan to update and ask if it's correct
- Use questions to help disambiguate:
  - "Sounds like you fixed the tests - should I mark that task complete and add the details to your progress?"
  - "Is this a blocker that's preventing you from moving forward, or just a note about what you discovered?"
  - "Should I update the backstage-plugin-upgrade project file with this progress?"
- Help the user refine their wording if it seems unclear or could be documented more precisely
- Present what you understood from their update and let them correct or confirm before writing
- The goal is collaborative documentation - working together to capture the work accurately

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

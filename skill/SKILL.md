# journal

Update work journal with progress, tasks, or notes from anywhere.

## Description

Updates the work journal at `~/git_repos/work-journal/` with progress updates, task management, project updates, or notes. Works from any repository.

## Configuration

```yaml
context: fork
autoInvoke: true
```

## Usage

**Quick progress update (default):**
```
/journal "Completed authentication refactor for backstage"
```

**Add a new task:**
```
/journal task "Review PR #123"
```

**Mark task as done:**
```
/journal done "visual-qontract upgrade"
```

**Update a project:**
```
/journal project backstage-plugin-upgrade "Completed web-rca, blocked on visual-qontract CI"
```

**Add a note:**
```
/journal note "Important: new API endpoint requires auth headers"
```

**Update a course:**
```
/journal course react-fundamentals "Completed Module 3: Advanced Hooks"
```

**Update course progress:**
```
/journal course react-fundamentals progress "30% - Module 3 complete"
```

**Add lesson note (uses most recent course):**
```
/journal lesson "useCallback prevents unnecessary re-renders by memoizing function references"
```

## Instructions

You are updating the work journal at `/home/maholder/git_repos/work-journal/`.

### Context and Structure

The journal has:
- Daily entries at `entries/YYYY/MM/DD.md` with sections: Tasks for Today, Progress (with Project and Course Work subsections), Notes, Blockers/Issues, Tomorrow's Focus
- Project summaries in `projects/*.md` (kebab-case filenames)
- Course learning notes in `courses/*.md` (kebab-case filenames)
- Running TODO list in `TODO.md` with Today, Upcoming, Courses, and Completed sections
- Templates at `templates/daily.md`, `templates/project.md`, and `templates/course.md`
- Project guidelines in `CLAUDE.md`

Current date is 2026-02-24, so today's entry is at `/home/maholder/git_repos/work-journal/entries/2026/02/24.md`.

### Parsing Arguments

The user's input after `/journal` determines the action:

1. **Starts with "task "** → Add new task to today's entry and TODO.md
2. **Starts with "done "** → Mark task complete in today's entry and TODO.md
3. **Starts with "project "** → Update project summary (format: `project <project-name> "<update>"`)
4. **Starts with "note "** → Add to Notes section
5. **Starts with "course "** → Update course summary or create new course
   - Format: `course <course-name> "<note>"` - Add notes to course file
   - Format: `course <course-name> progress "<update>"` - Update progress header
6. **Starts with "lesson "** → Add to most recently updated course (context-aware)
7. **Default** → Add to Progress section

### Step-by-Step Process

#### For Progress Updates (default)

1. Read today's entry at `/home/maholder/git_repos/work-journal/entries/2026/02/24.md`
   - If it doesn't exist, create directories and file from `/home/maholder/git_repos/work-journal/templates/daily.md`
   - Replace `{date}` with "2026-02-24 (Monday)"
2. Add the update to the Progress section
   - If the update mentions a project name, create a subsection like `### Project: <name>`
   - Otherwise add under a general subsection or create `### General`
3. Preserve all existing content
4. Confirm the update with the file path

#### For Task Management

**Adding task (`/journal task "Review PR #123"`):**

1. Read today's entry
2. Add checkbox item to "Tasks for Today" section: `- [ ] Review PR #123`
3. Read `/home/maholder/git_repos/work-journal/TODO.md`
4. Add same checkbox item under "## Today (2026-02-24)" section
5. Confirm task added to both files

**Marking done (`/journal done "visual-qontract upgrade"`):**

1. Read today's entry
2. Find task containing "visual-qontract upgrade" in "Tasks for Today"
3. Change `- [ ]` to `- [x]`
4. Read TODO.md
5. Find same task under "## Today" and mark complete
6. Move task to "## Completed" section in TODO.md with date stamp format:
   - Format: `- [x] Task description - YYYY-MM-DD`
   - Any additional details on indented lines below
   - Example: `- [x] Finish upgrading backstage plugins - 2026-02-24`
7. Confirm task marked complete in both files

#### For Project Updates

Format: `/journal project backstage-plugin-upgrade "Completed web-rca, blocked on visual-qontract CI"`

1. Extract project name (second word) and update text (quoted string)
2. Convert project name to kebab-case if needed
3. Read `/home/maholder/git_repos/work-journal/projects/<project-name>.md`
   - If doesn't exist, create from template with proper project name
4. Add update to "## Recent Progress" section with timestamp
5. Optionally update "## Current Status" if the update indicates a status change
6. Confirm project updated

#### For Notes

1. Read today's entry
2. Add bullet point to "## Notes" section
3. Confirm note added

#### For Course Updates

**Format:** `/journal course react-fundamentals "Completed Module 3: Advanced Hooks"`

**Progress Update Format:** `/journal course react-fundamentals progress "30% - Module 3 complete"`

**Lesson Notes (context-aware):** `/journal lesson "useCallback prevents unnecessary re-renders"`

**Process:**

1. Extract course name (second word after "course") and update text (quoted string)
2. Convert course name to kebab-case
3. Determine if this is a progress update (has "progress" keyword after course name)
4. Read `/home/maholder/git_repos/work-journal/courses/<course-name>.md`
   - If doesn't exist, create from `/home/maholder/git_repos/work-journal/templates/course.md`
   - Replace `{course_name}` with title-case course name
   - Replace `{course_url}` with empty (user fills later)
   - Replace `{progress}` with "0% - Just Started"

**If progress update:**
5. Update the **Progress:** line in header with new progress text
6. Optionally add milestone to Notes section with timestamp: `### YYYY-MM-DD - Progress Update: 30% complete`

**If regular course note:**
5. Add to "## Notes" section with timestamp: `### YYYY-MM-DD - Module 3: Advanced Hooks`
6. Add the note text below the timestamp

**For both:**
7. Read today's entry at `/home/maholder/git_repos/work-journal/entries/YYYY/MM/DD.md`
8. Add brief summary to "## Progress" > "### Course Work:" section:
   - Format: `- [Course Name] - [Brief summary]`
   - Example: `- React Fundamentals - Completed Module 3: Advanced Hooks`
9. Confirm course updated with file paths

**For lesson notes (`/journal lesson "text"`):**
1. Find most recently modified file in `courses/` directory (use modification time)
2. If no courses exist, prompt user to create one with `/journal course <name> "..."`
3. Add note to that course's Notes section with timestamp
4. Update today's daily entry Course Work section
5. Confirm which course was updated

### Important Guidelines

- **Always read before writing** to preserve existing content
- **Create entry if missing** using the template
- **Maintain markdown formatting** and section structure
- **Be smart about project detection** - if update mentions a project name, organize accordingly
- **Provide clear confirmation** showing what was updated and where
- **Handle partial matches** for task completion (fuzzy matching on task text)
- **Date calculations** - Use current date for file paths (calculate YYYY/MM/DD dynamically in actual use)

### Example Confirmations

**Progress update:**
```
✓ Added to journal progress: "Completed authentication refactor for backstage"
  File: /home/maholder/git_repos/work-journal/entries/2026/02/24.md
```

**Task added:**
```
✓ Added task: "Review PR #123"
  Files: entries/2026/02/24.md, TODO.md
```

**Task completed:**
```
✓ Marked complete: "visual-qontract upgrade" (2026-02-24)
  Files: entries/2026/02/24.md, TODO.md (moved to Completed with date)
```

**Project updated:**
```
✓ Updated project: backstage-plugin-upgrade
  File: projects/backstage-plugin-upgrade.md
```

**Note added:**
```
✓ Added note: "Important: new API endpoint requires auth headers"
  File: entries/2026/02/24.md
```

**Course created:**
```
✓ Created course: React Fundamentals
  File: /home/maholder/git_repos/work-journal/courses/react-fundamentals.md
  Added to daily: entries/2026/03/06.md
```

**Course note added:**
```
✓ Updated course: React Fundamentals
  File: courses/react-fundamentals.md
  Added to daily: entries/2026/03/06.md
```

**Course progress updated:**
```
✓ Updated progress: React Fundamentals → 30% - Module 3 complete
  File: courses/react-fundamentals.md
```

**Lesson note added (context-aware):**
```
✓ Added lesson note to: React Fundamentals
  File: courses/react-fundamentals.md
  Updated: entries/2026/03/06.md
```

## Auto-Invocation Hints

Suggest this skill when user says things like:
- "I just finished [something]"
- "I completed [task]"
- "That's done"
- "I need to remember [something]"
- Mentions completing work on a specific project
- Makes an important technical decision worth documenting

Don't auto-invoke for:
- Questions about the journal itself (they're probably in the journal repo)
- General conversation
- Planning future work (unless they want to add tasks)

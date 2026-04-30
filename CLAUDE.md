# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a development work journal system backed by an Obsidian vault, using the `@bitbonsai/mcpvault` MCP server for all file operations. The journal combines the webby plugin (from [ducky](https://github.com/ciaranRoche/ducky)) for daily notes, session logging, kanban, and vault operations with custom skills for project and course tracking.

## Architecture

### Obsidian Vault Structure

- `Daily/YYYY-MM-DD.md` — Daily journal entries (Obsidian Daily Notes format)
- `Projects/` — Project-specific summary files (kebab-case filenames)
- `Courses/` — Course learning notes and progress tracking (kebab-case filenames)
- `Work/Kanban.md` — Kanban task board (Obsidian Kanban plugin format)
- `Work/Tasks/` — Per-task notes linked from the kanban board
- `templates/` — Templates for daily entries, projects, and courses
- `blogs/` — Longer-form retrospectives and lessons learned

### MCP Server

All vault file operations go through the `obsidian` MCP server (`@bitbonsai/mcpvault`), configured at user scope. Use MCP tools (`mcp__obsidian__read_note`, `mcp__obsidian__write_note`, `mcp__obsidian__patch_note`, etc.) instead of direct Read/Write/Edit.

### Templates

All templates include YAML frontmatter (`date`, `type`, `tags`, etc.):
- `templates/daily.md` — Daily entry with tasks, progress, notes, blockers, tomorrow's focus, and related notes
- `templates/project.md` — Project summary with overview, status, progress, and tasks
- `templates/course.md` — Course learning with progress and link in frontmatter

### Skills

**From webby plugin:**
- `/webby:daily` — Read today's daily note for orientation
- `/webby:todo` — Manage todos in daily note (add, done, pick)
- `/webby:session-log` — Log session activity to daily note
- `/webby:standup` — Generate standup recap from recent logs
- `/webby:vault-query` — Search vault notes with synthesis
- `/webby:vault-save` — File knowledge to the right vault location
- `/webby:kanban` — Manage the kanban board
- `/webby:kanban-log` — Log activity to kanban task notes
- `/webby:work` — Pick a todo and start working with context
- `/webby:vault-setup` — One-time MCP server configuration

**Custom skills (`.claude/skills/`):**
- `/project` — Update project summaries with timestamped progress
- `/course` — Track course learning: notes, progress, and lesson notes

## Conventions

### Wiki-Links

Use Obsidian `[[Note Name]]` syntax when referencing other vault notes. Daily entries should link to projects and courses in the `## Related Notes` section.

### Frontmatter

All new files include YAML frontmatter:
- `type` — daily, project, or course
- `tags` — for Obsidian filtering and Dataview queries
- `date` or `created` — ISO date
- Course files: `progress` and `link` in frontmatter (not inline markdown)

### File Naming

- Daily notes: `Daily/YYYY-MM-DD.md` (flat, no subdirectories)
- Projects: `Projects/kebab-case-name.md`
- Courses: `Courses/kebab-case-name.md`
- Task notes: `Work/Tasks/Task Name.md`

## Workflow with Claude Code

### Daily Entry Workflow

1. Use `/webby:daily` for morning orientation — see open todos, session history, kanban items
2. Use `/webby:todo add "task"` to add tasks throughout the day
3. Use `/webby:session-log "progress"` to capture work done
4. Use `/webby:standup` before standup to get a recap

### Project Summary Workflow

1. Use `/project <name> "update"` to add timestamped progress
2. Project files are created automatically from template if they don't exist
3. Projects are linked in daily entries via `[[project-name]]` wiki-links

### Course Learning Workflow

1. Use `/course <name> "note"` to add timestamped learning notes
2. Use `/course <name> progress "50%"` to update course progress
3. Use `/course lesson "note"` for quick notes to the most recently modified course
4. Course work automatically appears in daily entries

### Kanban Workflow

1. Use `/webby:kanban add "task"` to add items to the board
2. Use `/webby:kanban move "task" "In Progress"` to track work
3. Use `/webby:kanban done "task"` when complete
4. Use `/webby:kanban-log "task" "progress note"` for per-task activity logs

### Key Patterns

- **MCP tools for all I/O**: Use `mcp__obsidian__read_note`, `mcp__obsidian__write_note`, `mcp__obsidian__patch_note` — never direct file Read/Write/Edit
- **Read before writing**: Always read the current content via MCP before patching
- **Preserve existing content**: When updating entries, preserve user's notes and formatting
- **Wiki-links for cross-reference**: Link between daily entries, projects, and courses using `[[Note Name]]`
- **Date awareness**: Today's entry is at `Daily/YYYY-MM-DD.md`
- **Continuity**: Check yesterday's "Tomorrow's Focus" when planning today
- **Incremental updates**: Expect users to add information throughout the day
- **Course progress in frontmatter**: Use `mcp__obsidian__update_frontmatter` for course progress, not inline markdown

### Intelligent Update Detection

Claude Code should **automatically detect and update** relevant journal files based on user messages. Analyze each user message for journal-relevant content and suggest appropriate skills.

**Detect these patterns:**

1. **Progress updates** — "I fixed", "working on", "updated", "tested", "deployed"
   - Suggest: `/webby:session-log` for the daily entry, `/project` for project updates

2. **Task completions** — "done", "finished", "completed", "shipped", "merged"
   - Suggest: `/webby:todo done` and `/webby:kanban done`

3. **New tasks** — "need to", "should", "TODO", "have to"
   - Suggest: `/webby:todo add` or `/webby:kanban add`

4. **Blockers** — "blocked", "error", "failing", "broken"
   - Add to Blockers/Issues in daily entry via session-log

5. **Project context** — JIRA ticket numbers, project names
   - Suggest: `/project <name> "update"`

6. **Course work** — course names, learning references
   - Suggest: `/course <name> "note"`

**Confirmation approach:**

- Detect what needs updating, present the plan, and ask for confirmation
- Help the user articulate exactly what they mean
- Present what you understood and let them correct before writing

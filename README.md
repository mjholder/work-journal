# Work Journal

A conversational development journal for tracking daily progress, project summaries, and task management with Claude Code.

## Workflow

Simply ask Claude Code to:
- **"Create today's entry"** - Claude will create a new daily entry with the template
- **"Add these JIRA tasks to today's entry"** - Claude will organize tasks into your current entry
- **"Update my progress on [project]"** - Claude will add to the Progress section
- **"What did I work on yesterday?"** - Claude will read and summarize recent entries
- **"Create a project summary for [project]"** - Claude will create a new project file

## Structure

- `entries/YYYY/MM/DD.md` - Daily journal entries organized by date
- `projects/` - Project-specific summary files
- `templates/` - Templates Claude uses for new entries and projects

## Daily Entry Sections

Each daily entry includes:
- **Tasks for Today** - Checkbox list of tasks (from JIRA or elsewhere)
- **Progress** - What was accomplished, organized by project
- **Notes** - Important information, decisions, or observations
- **Blockers/Issues** - Anything blocking progress
- **Tomorrow's Focus** - Plans for the next day

## Using the Journal Skill

The journal skill (`/journal`) allows you to update your journal from **any directory** without switching repos. It runs in isolated context so it doesn't pollute your current project's conversation.

### Quick Commands

| Command | What it does | Example |
|---------|-------------|---------|
| `/journal "text"` | Add progress update | `/journal "Completed authentication refactor"` |
| `/journal task "text"` | Add new task | `/journal task "Review PR #123"` |
| `/journal done "text"` | Mark task complete | `/journal done "authentication refactor"` |
| `/journal project name "text"` | Update project | `/journal project backstage "Finished web-rca plugin"` |
| `/journal note "text"` | Add note | `/journal note "API requires auth headers"` |

### Benefits

- **Works from anywhere** - Update journal from any git repo
- **Fast** - No need to switch directories or open files manually
- **Date-stamped completions** - Completed tasks automatically get date stamps
- **Consistent** - Updates both daily entry and TODO.md automatically

### Example Usage

**While working in another repo:**
```bash
cd ~/git_repos/my-project
# Just finished something
/journal "Fixed bug in login flow (PROJ-456)"

# Add tomorrow's task without switching repos
/journal task "Deploy fix to staging"

# Mark current task done
/journal done "bug in login flow"
```

**Update project progress:**
```bash
/journal project my-project "Completed phase 1: authentication system refactor"
```

All updates go to `~/git_repos/work-journal/` automatically.

## Conversational Workflow Examples

**Morning:**
> "Claude, create today's entry and add these JIRA tasks: ABC-123, ABC-124"

**During the day:**
> "Add to my progress: completed the authentication refactor for Project X"

**End of day:**
> "Mark ABC-123 as done and add to tomorrow's focus: start on ABC-125"

**Planning:**
> "What was I working on last week? Summarize my progress on Project X"

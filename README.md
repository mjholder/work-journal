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

## Examples

**Morning:**
> "Claude, create today's entry and add these JIRA tasks: ABC-123, ABC-124"

**During the day:**
> "Add to my progress: completed the authentication refactor for Project X"

**End of day:**
> "Mark ABC-123 as done and add to tomorrow's focus: start on ABC-125"

**Planning:**
> "What was I working on last week? Summarize my progress on Project X"

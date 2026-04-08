# Journal Skill

Cross-repository work journal updater for Claude Code.

## Quick Reference

| Command | Action | Example |
|---------|--------|---------|
| `/journal "text"` | Add progress update | `/journal "Completed authentication refactor"` |
| `/journal task "text"` | Add new task | `/journal task "Review PR #123"` |
| `/journal done "text"` | Mark task complete | `/journal done "authentication refactor"` |
| `/journal project name "text"` | Update project | `/journal project backstage "Finished web-rca plugin"` |
| `/journal note "text"` | Add note | `/journal note "API requires auth headers"` |
| `/journal course name "text"` | Add course notes | `/journal course react "Module 5 notes"` |
| `/journal course name progress "text"` | Update course progress | `/journal course react progress "50%"` |
| `/journal lesson "text"` | Add to recent course | `/journal lesson "Hook memoization"` |

## How It Works

The skill:
- Works from **any directory** (not just the journal repo)
- Runs in **isolated context** (doesn't pollute current project conversation)
- Auto-creates today's entry if it doesn't exist
- Preserves existing content when updating
- Updates both daily entry AND TODO.md for tasks

## Files Modified

- `~/git_repos/work-journal/entries/YYYY/MM/DD.md` - Today's entry
- `~/git_repos/work-journal/TODO.md` - For task management
- `~/git_repos/work-journal/projects/<name>.md` - For project updates

## Testing

### Test 1: Basic Progress Update
```bash
cd ~/some-other-repo
# In Claude Code:
/journal "Test entry from another repo"
```

Expected: Entry appears in today's Progress section

### Test 2: Task Management
```bash
/journal task "Test task"
/journal done "Test task"
```

Expected: Task added to Today section, then moved to Completed with date stamp (YYYY-MM-DD)

### Test 3: Project Update
```bash
/journal project test-project "Initial setup complete"
```

Expected: Creates/updates `projects/test-project.md`

### Test 4: Note
```bash
/journal note "This is a test note"
```

Expected: Added to Notes section of today's entry

### Test 5: Cross-Repo Usage
```bash
cd /tmp
/journal "Testing from completely different directory"
```

Expected: Still updates work journal, not /tmp

### Test 6: Course Management
```bash
# Create and update a course
/journal course test-course "Starting Module 1: Basics"

# Update progress
/journal course test-course progress "25% - Module 1 complete"

# Add context-aware lesson note
/journal lesson "This is an important concept"

# Verify files
cat ~/git_repos/work-journal/courses/test-course.md
cat ~/git_repos/work-journal/entries/$(date +%Y/%m/%d).md
```

Expected:
- Creates `courses/test-course.md` from template
- Adds notes with timestamps
- Updates progress header
- Updates today's daily entry Course Work section
- Lesson note goes to most recent course (test-course)

## Permissions

The skill has pre-approved permissions in `~/.claude/settings.json` for:
- Reading work-journal files
- Writing entries, TODO.md, and projects
- Editing any journal files

This prevents repeated permission prompts.

## Auto-Invocation

Claude may suggest using `/journal` when you mention:
- Completing work
- Finishing tasks
- Important decisions
- Things to remember

You can accept the suggestion or invoke manually.

## Troubleshooting

**Skill not found:**
- Restart Claude Code to reload skills
- Verify file exists at `~/.claude/skills/journal/SKILL.md`

**Permission prompts:**
- Check `~/.claude/settings.json` has correct permissions
- Permissions are optional but improve UX

**Wrong date:**
- Skill uses system date - check `date` command output
- Date format in SKILL.md may need updating for current year

**Entry not created:**
- Verify templates exist at `~/git_repos/work-journal/templates/`
- Check directory permissions for creating entries/YYYY/MM/

## Customization

Edit `~/.claude/skills/journal/SKILL.md` to:
- Change journal path
- Modify update formats
- Add new update types
- Adjust auto-invocation triggers

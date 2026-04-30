name: project

description: Update a project summary in the Obsidian vault with timestamped progress notes.

allowed-tools:
  - mcp__obsidian__read_note
  - mcp__obsidian__write_note
  - mcp__obsidian__patch_note
  - Bash

argument-hint: <project-name> "<update>"

# Project: Update Project Summary

Update or create a project summary in the vault with timestamped progress notes and wiki-links.

## Parsing Arguments

Format: `/project <project-name> "<update text>"`

1. Extract project name (first argument after `/project`)
2. Extract update text (everything after the project name, quoted or unquoted)
3. Convert project name to kebab-case for the filename, title-case for display

## Process

### 1. Get today's date

Run `date +%Y-%m-%d` via Bash.

### 2. Read the project file

Use `mcp__obsidian__read_note` with path `Projects/<project-name>.md`.

### 3. If the project file doesn't exist, create it

Read the template via `mcp__obsidian__read_note` path `templates/project.md`.

Replace placeholders:
- `{project_name}` → title-case project name (e.g., "backstage-plugin-upgrade" → "Backstage Plugin Upgrade")
- `{date_iso}` → `YYYY-MM-DD`

Write via `mcp__obsidian__write_note` with mode `overwrite`.

### 4. Add the update to Recent Progress

Use `mcp__obsidian__patch_note` to insert a timestamped entry in the `## Recent Progress` section.

Format:
```
### YYYY-MM-DD
- <update text>
```

If there's already a `### YYYY-MM-DD` header for today, append the bullet under it instead of creating a duplicate header.

### 5. Optionally update Current Status

If the update text indicates a clear status change (e.g., "completed", "blocked", "deployed to prod"), also patch the `## Current Status` section.

### 6. Update today's daily note

Read `Daily/YYYY-MM-DD.md` via `mcp__obsidian__read_note`.

If it exists, patch the `## Related Notes` section to include `[[<project-name>]]` if not already present.

### 7. Confirm

Report what was updated:
```
Updated project: <Project Name>
  File: Projects/<project-name>.md
  Added to Recent Progress (YYYY-MM-DD)
```

## Notes

- Always read before writing to preserve existing content
- Use `[[wiki-links]]` when referencing other vault notes
- Keep progress entries concise and action-oriented

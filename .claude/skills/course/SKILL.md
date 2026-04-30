name: course

description: Track course learning — add notes, update progress, or log a lesson to the most recent course.

allowed-tools:
  - mcp__obsidian__read_note
  - mcp__obsidian__write_note
  - mcp__obsidian__patch_note
  - mcp__obsidian__update_frontmatter
  - mcp__obsidian__list_directory
  - mcp__obsidian__get_notes_info
  - Bash

argument-hint: <course-name> "<note>" | <course-name> progress "<update>" | lesson "<note>"

# Course: Track Learning Progress

Add notes to a course, update course progress, or log a lesson to the most recently modified course.

## Parsing Arguments

The input after `/course` determines the action:

1. **`<course-name> "<note>"`** → Add notes to the specified course
2. **`<course-name> progress "<text>"`** → Update progress for the specified course
3. **`lesson "<note>"`** → Add note to the most recently modified course (context-aware)

Convert course names to kebab-case for filenames, title-case for display.

## Process

### Adding Course Notes

Format: `/course react-fundamentals "Completed Module 3: Advanced Hooks"`

1. Get today's date via Bash: `date +%Y-%m-%d`
2. Read `Courses/<course-name>.md` via `mcp__obsidian__read_note`
3. If the file doesn't exist, create it:
   - Read template via `mcp__obsidian__read_note` path `templates/course.md`
   - Replace `{course_name}` with title-case name
   - Replace `{course_url}` with empty string
   - Replace `{date_iso}` with today's date
   - Write via `mcp__obsidian__write_note` mode `overwrite`
4. Patch the `## Notes` section to add a timestamped entry:
   ```
   ### YYYY-MM-DD - <topic>
   - <note text>
   ```
5. Update today's daily note:
   - Read `Daily/YYYY-MM-DD.md` via `mcp__obsidian__read_note`
   - Patch `### Course Work:` section to add: `- [[<course-name>]] - <brief summary>`
   - Patch `## Related Notes` to include `[[<course-name>]]` if not present
6. Confirm:
   ```
   Updated course: <Course Name>
     File: Courses/<course-name>.md
     Added to daily: Daily/YYYY-MM-DD.md
   ```

### Updating Course Progress

Format: `/course react-fundamentals progress "50% - Module 5 complete"`

1. Get today's date
2. Read `Courses/<course-name>.md`
3. Update the `progress` field in frontmatter via `mcp__obsidian__update_frontmatter`:
   ```json
   {"frontmatter": {"progress": "50% - Module 5 complete"}, "merge": true}
   ```
4. Optionally add a milestone note to the Notes section:
   ```
   ### YYYY-MM-DD - Progress Update
   - 50% - Module 5 complete
   ```
5. Confirm:
   ```
   Updated progress: <Course Name> → 50% - Module 5 complete
     File: Courses/<course-name>.md
   ```

### Context-Aware Lesson Notes

Format: `/course lesson "useCallback prevents unnecessary re-renders"`

1. Get today's date
2. List courses via `mcp__obsidian__list_directory` path `Courses`
3. Get modification times via `mcp__obsidian__get_notes_info` for all course files
4. Select the most recently modified course
5. If no courses exist, tell the user to create one first
6. Read the selected course file
7. Patch the `## Notes` section with a timestamped entry:
   ```
   ### YYYY-MM-DD - Lesson Note
   - <note text>
   ```
8. Update today's daily note Course Work section
9. Confirm which course was updated:
   ```
   Added lesson note to: <Course Name>
     File: Courses/<course-name>.md
     Updated: Daily/YYYY-MM-DD.md
   ```

## Notes

- Always read before writing to preserve existing content
- Use `[[wiki-links]]` when referencing courses in daily entries
- Course progress lives in YAML frontmatter, not inline markdown
- Keep notes concise and timestamped

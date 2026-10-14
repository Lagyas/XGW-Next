# Stage 66 — Explicit arrangement clip regions (session-only)

Added editor/clip_regions.py with split_region, merge_regions and reset_regions. Unlike split_sustained_notes and close_clip_gap, these operations leave note, controller, SysEx and tempo event bytes untouched. Track View clip dialog now exposes Split region, Merge with next region and Reset regions. Undo snapshots retain the session state.

Important limitations: clip_regions is a transient attribute of Track and is **not saved into Standard MIDI Files**; reopening an SMF restores gap-inferred clips. Region boundaries can become stale if MIDI notes are subsequently moved, deleted or trimmed; a durable project-level clip object model and integration with every editing operation remain future work. GUI interactions are not hardware/Windows tested. Staff editor remains out of scope. No Git changes.

Tests: 725 passed, 83 subtests passed.

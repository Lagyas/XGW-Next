# Stage 74 – shared selection safety

- SharedNoteSelection.reconcile removes note-event index pairs no longer in a supplied note collection.
- Piano Roll prunes stale selected event pairs when rendering after edits.
- Global Undo/Redo clears shared selection to prevent pointing to old event indices.
- Three regression tests for selection reconciliation.

## Block C status
Not closed. MIDI event indices are not persistent note identities; clip identity and complete cross-editor GUI validation remain unfinished. Real Windows GUI tests have not been run.

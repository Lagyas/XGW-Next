# Stage 233 — Atomic Event List commit

- Batch event operations now validate and stage the edit once on an isolated Song copy, then commit the staged tracks to the live Song after creating one Undo snapshot.
- Copied event UIDs are created only once, rather than separately during validation and live commit.
- Zero-offset, same-track moves are true no-ops: they do not create Undo entries, invalidate Redo or mark the Song dirty.
- Generator selections are supported without exhaustion between validation and commit.
- Three new regression tests. Full suite: 1135 passed, 8 skipped, 136 subtests passed.
- Windows EXE and hardware MIDI remain untested; stages 234–250 not completed.
- GitHub unchanged.

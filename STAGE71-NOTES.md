# Stage 71 – explicit clip-region transfers

- Preserve manually split/merged clip boundaries during same-track copies, cross-track moves/copies and multiselection, where resulting regions do not overlap.
- Derive destination's existing clip boundaries from the original arrangement; keep its prior MIDI notes and intervals.
- If a destination region conflicts, revert only that track to note-derived clips; other tracks retain their valid region layouts.
- Updated four older regression assertions to reflect the new behavior; added four transfer/collision tests.
- Limitations: region objects are still intervals rather than independently identified MIDI clips; some edits can invalidate intervals. GUI/Windows and physical MIDI hardware tests remain pending.
- Staff editor deferred. No Git operations.

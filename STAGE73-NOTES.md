# Stage 73 – Shared note selection

Piano Roll and Drum Editor now exchange selected note-on/off event index pairs
for the same track. Other tracks do not inherit the selection; a view only
selects notes it actually displays (the drum view is channel/pitch filtered).

The new SharedNoteSelection model rejects invalid pairs atomically. It does not
persist selection into MIDI files. Note event indices can change after editing;
full automatic selection reconciliation across every edit path remains future work.

GUI and hardware tests on Windows have not yet been run. Staff Editor remains paused.

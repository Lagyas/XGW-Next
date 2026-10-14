# Stage 39 – Track View keyboard navigation

- Focus Track View with a click, then use Left/Right to move the transport cursor by a quarter note.
- Shift+Left/Right moves by one sixteenth note. Home jumps to zero; End jumps to last MIDI event.
- Uses existing app seek callback, preserving transport/loop validation and playback behavior.
- Tick positions are bounded to the supported MIDI timeline.
- Five pure regression tests added.
- Staff Editor unchanged. No Git commit or push.

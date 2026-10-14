# Stage 130 – Fixed ruler and two-axis arrangement zoom

- The timeline ruler is now a fixed viewport overlay, so vertical scrolling moves tracks but not the bar numbers, playhead or locator handles at the top.
- The ruler follows horizontal scrolling and zoom and forwards ruler pointer interactions to existing seek/locator logic.
- Added independent X and Y zoom buttons and Reset 100% next to Snap/Grid.
- Y zoom changes track row height (24–168 px) and associated clip/note-preview layout without modifying MIDI data.
- Fixed left track inspector continues to track vertical scrolling.
- GitHub not updated. Windows GUI behavior requires validation in the built EXE.

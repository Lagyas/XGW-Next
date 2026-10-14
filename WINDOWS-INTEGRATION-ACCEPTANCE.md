# XGW Next — Windows integration acceptance checklist

Status: **not executed on Windows**. Automated Linux headless tests do not certify Windows GUI or MIDI hardware.

1. Build with `build-local-windows.bat`; verify `dist\\XGW-Next.exe` exists and starts without traceback.
2. Open a multi-track MIDI file; switch track in Sequencer, open Piano Roll, and verify the selected track.
3. Select notes in Piano Roll; Alt+Up/Down transposes by one semitone; Alt+Left/Right nudges by current Snap grid. Test Undo/Redo and save/reopen.
4. Test note boundaries: pitch 0/127 and tick 0; invalid nudges must leave data unchanged.
5. During playback, seek using the Sequencer ruler; verify Piano Roll and Transport cursor agree.
6. Test L/R locators and looping while playing, paused and stopped.
7. In Mixer, change CC7, CC10, CC11, CC91, CC93; apply, save, reopen and inspect resulting MIDI events. Verify unchanged channels stay unchanged.
8. Select MIDI output port, play a GM and XG file on actual hardware, check channel/port routing and note-off behavior.
9. Import XWS, export MIDI, reopen, and compare track count, event count, timing and channel assignments.
10. Close/reopen Mixer and Piano Roll repeatedly, including while playback runs; check for Tkinter errors and hanging timers.

Blocking release criteria: all critical steps above pass on a supported Windows PC; no MIDI data loss or stuck notes; EXE starts without Python installed; reproducible smoke-test record exists.

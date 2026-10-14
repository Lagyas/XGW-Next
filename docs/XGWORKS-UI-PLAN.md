# XGworks-inspired workspace

The reference screenshot establishes a classic multi-window editing workflow:
Track View, Piano Roll, List Editor, and transport are accessible concurrently.

## Implemented in this iteration
- Window menu opens/focuses the seven supported editor types.
- Editor windows are reused instead of opening duplicates of the same type.
- Geometry is restored per editor type and persisted in the user settings file.
- Close all editors command.
- Existing Piano Roll CC lane and MIDI OUT preference are retained.

## Still to implement
- Multiple editor windows of the same type for different tracks.
- Docking/tiling and coordinated selection across windows.
- Separate floating transport panel and measure/beat/tick location.
- Full XGworks track grid, block colors, detailed list columns and toolbars.
- Visual/manual verification on Windows.

## Musical transport location

The transport now displays a 1-based bar:beat:tick location (e.g.
`0002:01:000`) alongside absolute MIDI ticks. It handles 4/4, other time
signatures and changes at arbitrary ticks. MIDI tick positions are preserved;
this is a display-only change. The screenshot reference also shows separate
staff notation and Yamaha XG effects panels; those remain future work.

## Staff / notation preview (2026-10-13)

A new **Staff** editor opens from View or Window and renders paired MIDI notes
on a treble or bass staff. It shares the global playback position, with a red
playhead and horizontal follow. This is a **read-only preview**, not a full
XGworks notation editor: rhythm spelling, rests, beams, key signatures,
accidental context, multi-voice notation and note editing are not yet supported.
MIDI tracks and notes are never modified by the preview.


## Staff rhythmic symbols (next iteration)

The Staff preview now draws whole, half, quarter, eighth, sixteenth,
thirty-second and sixty-fourth notes, including dotted forms. Durations
are approximated to the nearest conventional notation value; the original
MIDI timing and velocity are never modified. This is still not a score
engraver: rests, ties, beams, key-signature-aware spelling, multiple
voices, and direct note editing are pending. MIDI playback remains
independent of the staff rendering.

## Staff rests

The read-only Staff view now draws approximate rest symbols in genuinely
silent regions before and between notes. Overlapping notes are merged when
computing silence so a chord does not create spurious rests. Durations are
mapped to the nearest standard rest value; long gaps are currently represented
by a single approximate symbol rather than measure-aware rest sequences.
Remaining work: bar-aligned rests, beaming, ties, key signatures, multiple
voices and direct staff editing. MIDI event data is not changed.


## XG Variation Send

The Part Editor now exposes Variation Send (0–127) for each of 16 parts.
Its XG multipart parameter-change address is 08 nn 14, and it participates
in send and song SysEx import alongside Reverb and Chorus sends. This is a
per-part send amount, **not** the Variation effect type or algorithm editor.


## Windows build and XG device number

The Windows build script now sets `PYTHONPATH` to its own `editor` folder
so `unittest discover` finds `app_settings.py` regardless of the shell's
working directory. The XG Part Editor also exposes device number 0–15,
used in the Yamaha XG SysEx header (`43 1n 4C`). Select the number that
corresponds to the target device; the MIDI port alone does not select it.

## XG system effect types (experimental)

The Part Editor now opens a System Effect Types dialog with editable Reverb,
Chorus and Variation type MSB/LSB values. It can reconstruct recognized XG
system-effect type messages from the current song up to a selected tick, and
can send the three type messages to a selected MIDI output after confirmation.
This does not yet implement per-algorithm parameters, routing, or a verified
hardware preset catalogue. Test on a suitable Yamaha XG device before use.

## Raw XG effect parameter inspection

`xg_effects.inspect_effect_parameter_changes(song, through_tick=None, device=None)`
reads native Yamaha XG system-effect SysEx changes in the Reverb, Chorus,
Variation address blocks without assigning unverified parameter names.
It does not modify the song. Model-specific parameter labels, validation,
and editing UI remain future work; avoid writing unknown parameters to hardware.

## Read-only XG effect parameter inspector

The system effect window now offers a read-only Treeview listing raw XG
Reverb/Chorus/Variation parameter changes found in the song for the selected
XG device. Addresses and data are shown in hexadecimal. Unknown offsets are
not assigned speculative meanings; this does not edit or transmit MIDI data.

## Raw XG effect parameter writing

`write_effect_parameter_to_song` in `editor/xg_effects.py` provides a
validated, atomic MIDI-song insertion/replacement operation for raw XG
system-effect parameter bytes. It is a backend operation only; it does not
assert any model-specific parameter names, scales or compatibility, and is
not yet wired into the graphical effect inspector. Hardware verification is
still required.

## Mixer channel strips

The MIDI Mixer now shows 16 horizontally scrollable channel strips with
vertical volume faders, horizontal pan controls, and expression/reverb/chorus
controls. Changes remain staged until Apply; opening or reloading the mixer
does not modify the MIDI file. Variation Send is not yet integrated into the
mixer (Yamaha XG Variation Send uses a separate XG SysEx path).

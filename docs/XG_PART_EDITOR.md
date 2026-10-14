# Experimental Yamaha XG Part Editor

Open **View → Yamaha XG Part Editor...** and select a Part (1–16).

The first implementation exposes Bank MSB, Bank LSB, Program, Volume, Pan,
Reverb Send and Chorus Send. These are represented as XG Native Parameter
Change SysEx messages using multipart address `08 pp xx`.

**Important:** This is an experimental direct-to-device panel. It does not
yet inspect or modify XG SysEx already present in the opened MIDI file,
and changes are not saved to the MIDI song. The 16 Parts are a model
independent of the MIDI track list. Bank and program numbers in the UI
are zero-based, unlike many instrument manuals.

To send settings, first choose a MIDI output from **Transport**. Click
**Send Part settings to MIDI output** and confirm the destination. The
editor does not send anything on opening the panel. Do not use on a live
performance rig before testing with the actual Yamaha device.

Hardware compatibility and exact parameter mappings should be verified
against the manual for each targeted XG module before relying on the
result. This prototype does not yet implement effect algorithms, full
instrument definitions, variation sends, drum setup or voice names.


Effect type import now respects the selected Yamaha XG Device number (0–15).
Messages addressed to other XG devices in the same MIDI file are ignored.
The low-level API retains `device=None` for callers explicitly wanting all devices.

### Effect type save: replace or append

When writing Reverb, Chorus and Variation type messages to a MIDI song,
the dialog now offers **Yes** to replace matching effect-type SysEx at the
same tick, on track 1, for the selected XG device; **No** to append three
messages without removing existing events; or **Cancel** to abort. Other
SysEx, devices, tracks and positions remain unchanged. This does not edit
algorithm-specific effect parameters or routing.

# Transport and MIDI Input (work in progress)

## Loop playback

Select **Loop** in the transport bar, enter **From** and **To** absolute MIDI ticks, and press Play. The end is exclusive. Timing honors the song tempo map, including tempo changes inside the loop. Each repeat restores bank/program/controller state from before loop start; sustaining notes are released at the loop boundary. Loop playback is available only with an external MIDI output port.

## MIDI input capture

Install `mido` and `python-rtmidi`. Use Transport → Choose MIDI input, select a port, enter a **Start tick** and fixed **Rec BPM**, press **Record**, and then **Finish Rec**. By default the take is stored on a new MIDI 1.0 track. Enable **Overdub selected** before recording to merge the take into the currently selected track without deleting existing events. The destination track is remembered at Record time, even if selection later changes. Both modes support Undo. MIDI status messages (notes, CC, program, pressure, pitch bend) are recorded; SysEx and realtime clock are not. Recording uses its own wall-clock timeline at the chosen BPM, **not** the song's changing tempo map. Simultaneous playback during recording, punch-in, metronome, live quantization, and live MIDI 2.0 recording are not yet provided. Overdub here means merging a separately recorded take into an existing track, not monitoring accompaniment while recording.

## Limitations

The loop resets pedals/notes on each boundary, so notes crossing the loop boundary are truncated. MIDI Chase does not recover SysEx state. Hardware and Windows MIDI device validation remains necessary; passing automated tests is not hardware verification.

## Punch recording (basic)

Enable **Punch** and enter absolute start/end ticks in the transport bar. Record only accepts input within `[Punch start, Punch end)`; recording starts from **Start tick** using the fixed **Rec BPM** clock. Notes started inside the punch range but not released before its end get a synthetic Note Off at the end boundary. Note Off messages without a corresponding recorded Note On are omitted in punch mode. This is capture-window filtering, **not** automatic transport-controlled punch-in/out or playback monitoring; the recording worker continues running until **Finish Rec**. If recording into an existing track, use **Overdub selected**. Punch does not replace existing notes inside the range.

### Playback metronome (new)

The **Click** checkbox enables an audible MIDI metronome during playback and
loop playback. Beat positions follow time-signature changes, while timestamps
follow the complete song tempo map. Downbeats use MIDI note 76 and other beats
note 77, on MIDI channel 10 (zero-based channel 9). These notes are sent to the
selected MIDI output and therefore depend on its drum map; channel 10 may
conflict with existing percussion tracks. The click is currently playback-only:
recording is not yet synchronized with backing-track playback.

### Safe recording stop

When **Finish Rec** is pressed, any still-held notes receive synthetic Note Off
messages at the actual stop position, preventing stuck notes in the saved take.
In punch mode, notes remain clipped at the punch-out boundary. The stop time
is captured before waiting for the MIDI input worker to finish, so worker
shutdown latency does not extend note durations. This does not yet provide
synchronized accompaniment or monitoring.

### Recording with tempo changes

The **Follow song tempo** checkbox (enabled by default) maps input timestamps
through the existing SMF tempo events, including changes while recording and
starting in the middle of a tempo segment. Turn it off to use the fixed **Rec BPM**
value instead. This corrects recording tick positions but does not yet start
accompaniment playback or provide live monitoring.

### Shared-clock accompaniment (experimental)

The **Play accompaniment** checkbox starts playback and recording using one
scheduled monotonic timestamp. Enable **Follow song tempo** and select MIDI IN
and OUT ports. Playback excludes the overdub target track to avoid doubling
its existing notes. **Finish Rec** stops playback and saves the take.

Limitations: this is a shared start clock, not hardware timestamp synchronization;
MIDI port initialization may take longer than the 300 ms lead-in. No audio
monitoring, input echo, loop recording, count-in, or latency calibration yet.
Physical Windows MIDI devices still need end-to-end testing.

### MIDI input latency compensation

The **Input latency ms** field offsets recorded MIDI event timestamps, without
changing accompaniment playback. Positive values move captured notes earlier
(e.g. 100 ms compensates for 100 ms of input delay); negative values move
notes later. Accepted range is -500 to +500 ms, default 0. The offset is
applied in seconds *before* conversion through the song tempo map, so it also
works across tempo changes. Events are clamped to the recording start.
This is manual calibration, not automatic hardware latency measurement.

### Recording MIDI channels

The transport offers **MIDI IN ch** (All or 1–16) and **Record ch**
(Keep or 1–16). Input filtering happens before optional channel remapping.
Both recorded channel messages and generated Note Off events use the selected
recording channel. This is useful when a keyboard transmits on a different
channel than the intended Yamaha XG part. No changes are made to existing
tracks.

### Count-in before recording

Set **Count-in bars** to 0–8 and enable **Play accompaniment**. The playback worker sends metronome clicks before the shared song/recording start time. The count-in follows the time signature and tempo at the recording start tick. The recorder starts at the shared song epoch, so count-in clicks are not recorded. A MIDI output and hardware test are required.

### MIDI Monitor (experimental)

Enable **MIDI Monitor** during recording to forward accepted incoming channel messages immediately to the selected MIDI output. Input-channel filtering and Record-ch remapping also apply to monitoring. Any monitored notes still held at stop are sent Note Off. For now monitoring and **Play accompaniment** are mutually exclusive to avoid competing RtMidi output handles. MIDI Monitor is opt-in and has not been verified on Windows hardware. This is MIDI forwarding, not audio monitoring.

### Quantize recorded note starts

The **Rec quantize** dropdown offers Off or tick grids (30, 60, 120, 240, 480). Quantization happens only when a take is finished, before insertion or overdub. Note On events move to the nearest grid point relative to the recording start tick; matched Note Off events move by the same number of ticks, preserving note duration. Controllers and other MIDI events are not quantized. The original recording buffer remains unchanged. This is tick-based quantization, not swing/groove quantization.

### Quantization strength (core API)

`quantize_take_onsets(take, grid, origin=0, strength=100)` supports 0–100% onset correction while preserving paired note durations. The recording UI currently uses 100%; a strength control in the UI is still pending.

### Playhead and Piano Roll Ctrl-drag

The transport now displays the estimated current song tick during playback. A red playhead follows the song in the arrangement and Piano Roll, scrolling when needed, including loops. Timing is derived from the monotonic software clock and tempo map, not hardware MIDI output feedback. In Piano Roll, Ctrl + left mouse drag on a note copies it to the snapped destination; ordinary left drag still moves the note. These GUI changes require manual Windows testing.

### Piano Roll CC lane and MIDI OUT preference

Click the lower lane label (Velocity) or right-click the lower lane to choose Velocity or CC 0–127. The lane shows existing events of the chosen CC and permits editing their values by dragging the displayed bars. Insert new controller events in Controller Editor. MIDI OUT selection is saved in `%APPDATA%\\XGW Next\\settings.json` on Windows and restored when the application starts; a disconnected device must still be reconnected or another output selected. GUI behavior requires manual Windows testing.

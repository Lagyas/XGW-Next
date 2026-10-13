# External MIDI output — prototype

This is an **experimental** hardware MIDI transport for the Python/Tkinter GUI.

## Installation

Install Python 3 and Tkinter, then:

```sh
python3 -m pip install -r requirements-midi.txt
python3 editor/app.py
```

On Windows you can usually use `py -3 -m pip install -r requirements-midi.txt`.

## Playback

1. Connect a MIDI interface and select the Yamaha XG device's MIDI IN port.
2. Open a Standard MIDI File.
3. Choose **Transport → Choose MIDI output...** and select the correct output.
4. Choose **Transport → Play**. **Transport → Stop** stops playback and sends CC 123 (All Notes Off) on all 16 channels.

## Important limitations

- **SysEx is not transmitted yet.** This includes XG System On, multipart settings and effects, so full Yamaha XG sound reproduction is not yet supported.
- Only MIDI channel messages are played. Meta events are used for tempo but are not transmitted.
- SMF PPQN timing only; SMPTE division is not supported.
- Playback starts at the beginning, with no pause, seek, loop, metronome or recording.
- The scheduler uses Python and is not designed for sample-accurate timing.
- A connected MIDI device is needed for actual output. Hardware behavior has not been verified.
- Do not modify a song during playback; the transport snapshots event timing at start.
- Stop sends All Notes Off, which may also silence notes on other parts of the selected device.

Avoid selecting a MIDI output used for a live performance until the transport is tested on your setup.

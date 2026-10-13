# Yamaha XG SysEx — initial implementation

The editor now has an independent `xg_sysex.py` module supporting:

- Yamaha XG parameter-change messages (manufacturer 0x43, model 0x4C)
- XG System On: `F0 43 10 4C 00 00 7E 00 F7`
- Decoding of complete parameter-change messages
- Opt-in transmission of complete F0 SysEx events stored in SMF tracks

## Sending from the GUI

In **Transport**, first choose a MIDI output. Enable **Send complete SysEx (advanced)** to send complete SysEx events in the opened MIDI file during playback. This option defaults to **off**.

**Caution:** SysEx messages can reset or substantially reconfigure connected devices. Test on a non-critical setup. The editor does not send XG System On automatically.

## Known limitations

- SMF F7 continuation and escaped events are skipped; segmented SysEx reconstruction is not implemented.
- The transport has no pacing/throttling between SysEx messages and channel events.
- No interactive XG multipart mixer, bank/voice database, effects panel, or MIDI device inquiry yet.
- The module does not assume Yamaha XG parameter-change messages use a checksum.
- The device number is 0..15, encoded in the low nibble of the 0x1n device byte.
- Actual Yamaha hardware compatibility has not been verified.

Next: parse XG multipart parameter changes into a structured part state, and add device-specific bank/voice definitions with documented provenance.

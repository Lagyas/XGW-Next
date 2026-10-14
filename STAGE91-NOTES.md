# Stage 91 — XWS event ordering and track names

- Import first validated label from each named S4WT block as standard MIDI Track Name (FF 03) metadata. Unrecognized metadata is ignored rather than guessed.
- Insert generated Note Off events before simultaneous re-trigger Note On events, while preserving zero-duration Note On / Note Off order.
- Verified with `A Dream of a Dream.XWS`: 24 tracks, 17 recognized track names, 10,941 MIDI events including names.
- Import of other XWS metadata (mix, clips, GUI state) remains unsupported.

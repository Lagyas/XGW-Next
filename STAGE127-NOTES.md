# Stage 127 – Unified Transport / Sjednocený Transport

- Removed redundant Finish Rec / End Rec controls from toolbar, Transport menu and floating Transport window.
- Stop continues to finalize recording through the existing `stop_midi` -> `finish_recording` path.
- Space toggles Play/Stop and stops active recording; text entry widgets retain normal typing.
- Numeric keypad shortcuts: KP_0 start, KP_1 L, KP_2 stored cursor bookmark (first press stores), KP_3 R.
- Shortcut jumps allow visiting R even when loop is enabled; playback does not auto-restart outside active loop.
- Entry and text widgets ignore these shortcuts.
- Four new targeted unit tests.

Windows keyboard behavior (Num Lock on/off) and real MIDI recording must still be tested manually.

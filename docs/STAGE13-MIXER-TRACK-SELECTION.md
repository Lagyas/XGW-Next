# Stage 13 – Track View / Mixer destination sync

- Mixer follows selected Track View track as the destination for **Apply changed values**.
- New **Follow Track View** checkbox allows users to pin the destination manually.
- Selection is 0-based internally and 1-based in the Mixer; invalid selections are ignored.
- No MIDI data is changed by selecting a track; changes still require Apply.
- Six new pure regression tests; 410 total.
- Remaining: GUI/hardware tests, broader track/mixer playback integration, Yamaha XG and Windows beta.

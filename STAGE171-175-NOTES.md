# Stage 171–175 – D2: XWS compatibility and mixer evidence

- Cross-check at least two independently controlled XWS S4WT comparisons; return stable fixed-byte candidate offsets only when target track is isolated and values differ in distinct transitions.
- Never interpret unverified S4WT offsets as actual mixer parameters or write them back to XWS.
- Fix undefined `source_properties` in recovery restore path.
- Preserve verified XWS source channel observations in autosave recovery `.xgwn` bundle, and reload from recovery archive.
- Add nine regression cases for corroboration, contaminated evidence, invalid comparisons, and recovery metadata.

**Limitations:** Native Yamaha XWS write-back and mixer parameter decoding remain unsupported until independent reference projects prove the byte layout. Source XWS files are not modified. Windows GUI has not been manually tested. Staff Editor paused. No Git commit/push.

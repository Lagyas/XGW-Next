# Stage 30 — transport locator dragging

- Ruler L/R handles clamp when dragged across the opposite locator, instead of moving both markers unexpectedly.
- Transport-window `L ← Cursor` and `R ← Cursor` buttons preserve their previous range-expanding behavior.
- Invalid locator values are validated centrally with `transport_ops.tick_value`.
- Eight new tests for drag boundaries and malformed inputs.
- Full suite: 497 passed, 68 subtests passed.
- Staff Editor untouched; no Git commit or push.
- Windows interactive GUI and physical MIDI hardware still require hands-on verification.

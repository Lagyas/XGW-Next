# Stage 116 — Yamaha XG parameter validation

- Reject boolean part indices and values in XG Part operations (Python bool is a subclass of int).
- Apply strict byte-sequence input types in Yamaha XG SysEx parameter encoding.
- Add four regression tests for invalid and valid XG parameter operations.
- No undocumented XWS mixer mapping inferred. Staff Editor paused; no commit or push.

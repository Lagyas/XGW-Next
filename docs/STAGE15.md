# Stage 15 — XG effect inspector validation

- Reject malformed effect-type rows (the native type requires two data bytes).
- Reject unsupported address shapes and empty parameter payloads before formatting.
- Preserve formatting for valid raw effect parameters.
- Four new regression tests; `PYTHONPATH=editor python -m unittest discover -s tests -q` => 417 passing.
- No Staff Editor changes; no commits or GitHub pushes.

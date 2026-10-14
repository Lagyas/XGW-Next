# XGW Next Stage 89

- Read-only XWS inspection can offer export of the first detected embedded SMF candidate.
- Extraction checks complete consecutive MTrk chunks and validates the result with Song.from_bytes.
- Source XWS is never modified. This is *not* full XWS project import.
- Five additional extraction tests.
- Run: PYTHONPATH=editor python -m pytest -q
- No git changes or hardware tests.

# Stage 241 — Windows full regression preflight

The Windows build and verification scripts previously ran `unittest discover`, which does not collect pytest-style tests. Both scripts now run `python -m pytest tests -q`; the build installs pytest into its venv. The existing static build tests were updated and three new regression tests enforce this contract.

Linux/headless full suite: see accompanying run log. This does not establish that the Windows EXE starts or that MIDI devices work. Run `build-local-windows.bat`, `verify-windows-beta.bat`, and manual GUI/hardware acceptance on Windows before calling this a release candidate.

No Git commit or push; Staff Editor and standalone Validator remain paused.

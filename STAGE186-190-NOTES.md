# XGW Next — D5 / Stage 186–190

Windows build and release hardening:
- Use checked-in XGW-Next.spec as single source of PyInstaller settings, avoiding divergent command-line build configuration.
- Fail fast on missing Python launcher, venv, dependencies, or failing unit tests.
- Verify that generated Windows EXE exists and is nonempty.
- Windows launcher uses project .venv Python when available and reports startup errors.
- Five static build-contract regression tests added.

Verification: 1090 passed, 8 skipped, 136 subtests passed (Linux environment). Python compile and ZIP CRC checks performed.

Limitations: Windows EXE was not built or executed in this environment; actual Windows GUI, MIDI devices and mixer/transport must be manually checked. No git commit/push. Staff Editor and MIDI Validator remain paused.

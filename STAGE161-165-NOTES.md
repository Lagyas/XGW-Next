# Stage 161–165 — Windows GUI stabilization

- **161**: Piano Roll stops its periodic playhead callback when the window is closed; late Tk callbacks are guarded.
- **162**: Undo/Redo key handlers consume handled shortcuts, avoiding event propagation. Added lowercase Shift+Z binding alongside existing uppercase variant.
- **163**: Main app tracks and cancels its transport and autosave timers during shutdown; repeat close calls are ignored.
- **164**: Transport/autosave callbacks no longer reschedule after shutdown; Tk destruction race is guarded.
- **165**: Added six headless GUI-lifecycle regression tests, full pytest run, Python compilation and ZIP integrity check.

## Results
1048 passed, 8 skipped, 136 subtests passed (Linux headless). Windows GUI and EXE build are **not** verified. Windows acceptance tests remain required before stable beta sign-off.

## Install
Close XGW Next. Extract over F:\\XGW-Next, run build-local-windows.bat. Test opening and closing Piano Roll repeatedly, Undo/Redo shortcuts, transport playhead, app close during playback, and autosave behavior. Send any traceback.

No GitHub commit/push. Staff Editor paused.

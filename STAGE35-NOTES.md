# Stage 35 — Transport clock validation

- Reject non-finite clock values (NaN, infinity) before binary-search tick conversion or playback cursor updates.
- Reject invalid tick limits, including booleans, and nonnumeric elapsed times.
- Reject non-finite loop locator times in transport calculations.
- Six new regression tests; 529 passed and 68 subtests passed.
- No Staff Editor changes. No Git operations. GUI and hardware tests deferred.

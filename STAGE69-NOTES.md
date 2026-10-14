# Stage 69 – Preserve explicit clip regions on safe same-track moves

A normal move on the same track now translates the selected region boundaries, retaining earlier Split/Merge work whenever the resulting regions remain non-overlapping and in the supported tick range. Multiple selected regions are translated together and sorted. Copy, cross-track operations, and moves producing region overlaps still invalidate explicit regions and safely fall back to inferred clips; they are not yet full clip-identity operations.

Regression tests cover preserved boundaries, safe fallback, cross-track moves, duplication and zero-offset operations. The older regression expectation was updated to reflect the new supported behavior.

**Block C is not complete:** full persistent clip identities, advanced Piano Roll/Drum Editor workflow, cross-editor cursor/selection sync and interactive Windows testing remain. Staff Editor stays deferred. No Git operations performed.

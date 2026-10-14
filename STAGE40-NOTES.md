# Stage 40 – Track View timeline zoom

- Ctrl+mouse wheel zooms horizontally around the pointer.
- Ctrl+plus/minus zooms around viewport center; Ctrl+0 resets to 28 px/beat.
- The tick under the zoom anchor is preserved by updating horizontal scrolling.
- All Track View coordinates, clip drag snapping, ruler seeking, locator hit tests and playhead follow use the current scale.
- Six tests cover zoom factors, limits, invalid values, anchor and locator hit testing.
- No changes to Staff Editor or Git; interactive Windows/hardware verification deferred.

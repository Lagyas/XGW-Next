"""Pure transport range validation shared by UI and playback."""
from midi import MidiError
from math import isfinite

MAX_TICK = 0x0fffffff


def tick_value(value, label='Tick'):
    if isinstance(value, bool):
        raise MidiError(f'{label} must be an integer tick')
    try:
        tick = int(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise MidiError(f'{label} must be an integer tick') from exc
    if str(value).strip() != str(tick) and not isinstance(value, int):
        raise MidiError(f'{label} must be an integer tick')
    if not 0 <= tick <= MAX_TICK:
        raise MidiError(f'{label} must be between 0 and {MAX_TICK}')
    return tick


def playback_region(start, loop_enabled=False, left=None, right=None):
    start = tick_value(start, 'Start')
    if not loop_enabled:
        return start, None, None
    left = tick_value(left, 'Left locator')
    right = tick_value(right, 'Right locator')
    if left >= right:
        raise MidiError('Right locator must be after left locator')
    if start >= right:
        raise MidiError('Start position must be before right locator')
    return start, left, right


def elapsed_song_seconds(start_seconds, elapsed_seconds, left_seconds=None, right_seconds=None):
    """Map elapsed playback time to song time, honoring the first partial loop.

    Playback starts at the cursor, not at L; after reaching R it wraps to L.
    """
    try:
        elapsed = float(elapsed_seconds)
        start = float(start_seconds)
    except (TypeError, ValueError, OverflowError) as exc:
        raise MidiError('Invalid transport clock') from exc
    if not isfinite(elapsed) or not isfinite(start):
        raise MidiError('Invalid transport clock')
    elapsed = max(0.0, elapsed)
    if left_seconds is None or right_seconds is None:
        return start + elapsed
    try:
        left, right = float(left_seconds), float(right_seconds)
    except (TypeError, ValueError, OverflowError) as exc:
        raise MidiError('Invalid loop clock region') from exc
    if not isfinite(left) or not isfinite(right) or not left < right or start >= right:
        raise MidiError('Invalid loop clock region')
    first_leg = right - start
    if elapsed < first_leg:
        return start + elapsed
    return left + ((elapsed - first_leg) % (right - left))


def seek_position(value, loop_enabled=False, left=None, right=None):
    """Validate a seek target against the active playback loop.

    A cursor may be before L for the first pass, but cannot be at/after R
    while a loop is active, because there is no first playback leg.
    """
    return playback_region(value, loop_enabled, left, right)[0]


def move_locator(which, tick, left, right, division):
    """Move one ruler locator without unexpectedly moving the other.

    Keep at least one MIDI tick between L and R. Crossing the opposite
    marker clamps the dragged marker, rather than pushing the other marker.
    """
    tick = tick_value(tick, 'Locator position')
    left = tick_value(left, 'Left locator')
    right = tick_value(right, 'Right locator')
    if left >= right or right > MAX_TICK:
        raise MidiError('Right locator must be after left locator and within MIDI range')
    if which == 'L':
        return min(tick, right - 1), right
    if which == 'R':
        return left, min(MAX_TICK, max(tick, left + 1))
    raise MidiError('Unknown locator; expected L or R')

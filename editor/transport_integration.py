"""Pure seek/loop policy for synchronizing independent editor windows."""
from transport_ops import tick_value
from midi import MidiError

def normalized_seek(tick, *, loop=False, left=None, right=None):
    tick = tick_value(tick)
    if not loop:
        return tick
    left, right = tick_value(left, 'Left locator'), tick_value(right, 'Right locator')
    if left >= right:
        raise MidiError('Invalid loop locators')
    # A seek outside the active loop restarts at L; the cursor may precede L
    # during the first pass, but cannot start at or beyond R.
    return left if tick >= right else tick

def clamp_note_range(start, duration):
    start = tick_value(start)
    duration = tick_value(duration, 'Duration')
    if duration < 1 or start + duration > 0x0fffffff:
        raise MidiError('Invalid note duration')
    return start, start + duration

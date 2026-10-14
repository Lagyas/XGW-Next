"""Track/channel ownership diagnostics for safe future live track mixing."""


def track_channels(song):
    """Return the MIDI channels actually used by each SMF track (0-based)."""
    return {index: frozenset(event.status & 0x0f for event in track.events
                             if 0x80 <= event.status <= 0xef)
            for index, track in enumerate(song.tracks)}


def shared_channels(song):
    """Map channels shared by two or more tracks to their track indices."""
    owners = {}
    for track, channels in track_channels(song).items():
        for channel in channels:
            owners.setdefault(channel, set()).add(track)
    return {channel: frozenset(tracks) for channel, tracks in owners.items()
            if len(tracks) > 1}


def unsafe_live_track_changes(song, tracks):
    """Tracks whose MIDI channels overlap other tracks, requiring note ownership.

    A channel-wide All Notes Off would otherwise cut notes on another track.
    """
    shared = shared_channels(song)
    return {track: frozenset(channel for channel, owners in shared.items()
                             if track in owners)
            for track in tracks if any(track in owners for owners in shared.values())}


def audible_channels(song, muted_tracks=(), solo_tracks=(), muted_channels=(), solo_channels=()):
    """Return channels that can be played without leaking muted track events.

    Shared channels are permitted when every owning track has the same audible
    state. Conflicting states require per-track event/note ownership instead.
    """
    channels = track_channels(song)
    muted_tracks, solo_tracks = set(muted_tracks), set(solo_tracks)
    muted_channels, solo_channels = set(muted_channels), set(solo_channels)
    owners = {}
    for index, used in channels.items():
        audible = index not in muted_tracks and (not solo_tracks or index in solo_tracks)
        for ch in used:
            owners.setdefault(ch, set()).add(audible)
    if any(len(states) > 1 for states in owners.values()):
        raise ValueError("Conflicting track Mute/Solo on a shared MIDI channel")
    active = {ch for ch, states in owners.items() if True in states}
    return {ch for ch in active if ch not in muted_channels and
            (not solo_channels or ch in solo_channels)}

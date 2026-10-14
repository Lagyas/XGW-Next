"""Conservative read-only evidence for XGworks track-channel edits."""
from xws_import import _chunks, compare_s4wt_records
from midi import MidiError


def compare_track_channel_edit(before: bytes, after: bytes):
    """Locate S4WT channel candidates without assigning unverified semantics."""
    if not isinstance(before, bytes) or not isinstance(after, bytes):
        raise TypeError('XWS files must be bytes')
    if max(len(before), len(after)) > 32 * 1024 * 1024:
        raise MidiError('XWS exceeds safe import limit')
    a, b = list(_chunks(before)), list(_chunks(after))
    if len(b) < len(a) or [x[0] for x in a] != [x[0] for x in b[:len(a)]]:
        raise MidiError('Incompatible XWS chunk structure')
    changed = [(i + 1, tag.decode('ascii', 'replace'))
               for i, ((tag, old), (_, new)) in enumerate(zip(a, b)) if old != new]
    rows = compare_s4wt_records(before, after)
    return {'changed_chunks': changed, 's4wt_candidates': rows,
            'added_chunks': [tag.decode('ascii', 'replace') for tag, _ in b[len(a):]],
            'verified_channel_decoder': False}

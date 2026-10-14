"""Read-only, reproducible experiments for undocumented XWS S4WT fields.

Never infer mixer semantics from a single project or an uncontrolled edit.
"""
from pathlib import Path
from midi import MidiError
from xws_import import compare_s4wt_records, format_s4wt_comparison


def controlled_s4wt_experiment(before: bytes, after: bytes, *, track: int, parameter: str,
                               before_value: int, after_value: int):
    """Locate candidates after exactly one *declared* setting change.

    This is evidence collection, not a verified decoder. Callers must ensure
    the files were produced by changing only that setting in XGworks.
    """
    if not isinstance(track, int) or isinstance(track, bool) or track < 1:
        raise ValueError('track must be a positive one-based integer')
    if not isinstance(parameter, str) or not parameter.strip():
        raise ValueError('parameter must describe the controlled setting')
    if not all(isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 127
               for v in (before_value, after_value)) or before_value == after_value:
        raise ValueError('distinct MIDI-range setting values required')
    rows = compare_s4wt_records(before, after)
    unrelated = [row['track'] for row in rows if row['track'] != track]
    target = next((row for row in rows if row['track'] == track), None)
    candidates = [] if target is None else target['fixed_prefix_changes']
    return {'parameter': parameter, 'track': track, 'before_value': before_value,
            'after_value': after_value, 'candidate_offsets': candidates,
            'other_changed_tracks': unrelated,
            'controlled_candidate': bool(candidates) and not unrelated and
                not target['variable_tail_changed'],
            'verified_decoder': False}


def format_controlled_experiment(before, after, **kwargs):
    result = controlled_s4wt_experiment(before, after, **kwargs)
    lines = [f"Controlled XWS experiment: {result['parameter']}, track {result['track']}",
             f"Declared edit: {result['before_value']} -> {result['after_value']}",
             format_s4wt_comparison(before, after),
             f"Candidate fixed offsets: {result['candidate_offsets']}",
             f"Other changed tracks: {result['other_changed_tracks']}",
             'Candidates are NOT confirmed mixer fields; no import settings changed.']
    return '\n'.join(lines)


def compare_xws_binary_evidence(before: bytes, after: bytes):
    """Report byte-level evidence without guessing undocumented XWS metadata.

    A length difference makes absolute offsets after the first insertion unsafe
    to compare. The common prefix/suffix bounds isolate the edit region.
    """
    from xws_import import _chunks, _decode_track
    if not isinstance(before, bytes) or not isinstance(after, bytes):
        raise TypeError('XWS comparisons require bytes')
    if len(before) > 32 * 1024 * 1024 or len(after) > 32 * 1024 * 1024:
        raise MidiError('XWS exceeds safe import limit')
    left = list(_chunks(before))
    right = list(_chunks(after))
    common = min(len(left), len(right))
    if [tag for tag, _ in left[:common]] != [tag for tag, _ in right[:common]]:
        raise MidiError('XWS chunk sequences differ')
    prefix = 0
    while prefix < min(len(before), len(after)) and before[prefix] == after[prefix]:
        prefix += 1
    suffix = 0
    while (suffix < min(len(before), len(after)) - prefix and
           before[len(before)-1-suffix] == after[len(after)-1-suffix]):
        suffix += 1
    changes = []
    for i, ((tag, old), (_, new)) in enumerate(zip(left, right), 1):
        if old != new:
            entry = {'chunk': i, 'kind': tag.decode('ascii', errors='replace'),
                     'before_length': len(old), 'after_length': len(new)}
            if tag == b'S4WB':
                a = _decode_track(old).events
                b = _decode_track(new).events
                old_cc = [(e.tick, e.status & 15, e.data[0], e.data[1]) for e in a
                          if e.status & 0xf0 == 0xb0 and len(e.data) == 2]
                new_cc = [(e.tick, e.status & 15, e.data[0], e.data[1]) for e in b
                          if e.status & 0xf0 == 0xb0 and len(e.data) == 2]
                entry['cc_before'] = old_cc
                entry['cc_after'] = new_cc
            changes.append(entry)
    for i, (tag, body) in enumerate(left[common:], common + 1):
        changes.append({'chunk': i, 'kind': tag.decode('ascii', errors='replace'),
                        'before_length': len(body), 'after_length': None, 'removed': True})
    for i, (tag, body) in enumerate(right[common:], common + 1):
        changes.append({'chunk': i, 'kind': tag.decode('ascii', errors='replace'),
                        'before_length': None, 'after_length': len(body), 'added': True})
    return {'before_length': len(before), 'after_length': len(after),
            'common_prefix': prefix, 'common_suffix': suffix,
            'before_edit_span': (prefix, len(before)-suffix),
            'after_edit_span': (prefix, len(after)-suffix),
            'changed_chunks': changes,
            's4wt_changes': compare_s4wt_records(before, after)}


def corroborate_s4wt_experiments(experiments):
    """Cross-check independent one-setting XWS comparisons, without decoding bytes.

    Each entry is (before_bytes, after_bytes, track, parameter, before_value,
    after_value). A stable fixed offset across >=2 different value transitions
    is evidence only, never proof of the mixer parameter's encoding.
    """
    if type(experiments) not in (list, tuple) or len(experiments) < 2:
        raise ValueError('At least two controlled experiments required')
    if len(experiments) > 32:
        raise ValueError('Too many experiments')
    observations = []
    for item in experiments:
        if type(item) not in (list, tuple) or len(item) != 6:
            raise ValueError('Invalid controlled experiment entry')
        before, after, track, parameter, old, new = item
        result = controlled_s4wt_experiment(before, after, track=track,
                    parameter=parameter, before_value=old, after_value=new)
        observations.append(result)
    first = observations[0]
    if any(r['track'] != first['track'] or r['parameter'] != first['parameter']
           for r in observations):
        raise ValueError('Experiments must target the same track and parameter')
    if len({(r['before_value'], r['after_value']) for r in observations}) < 2:
        raise ValueError('At least two distinct setting transitions required')
    candidates = [set(offset for offset, _, _ in r['candidate_offsets'])
                  if r['controlled_candidate'] else set() for r in observations]
    stable = sorted(set.intersection(*candidates))
    return {'track': first['track'], 'parameter': first['parameter'],
            'experiments': len(observations), 'stable_candidate_offsets': stable,
            'all_isolated': all(r['controlled_candidate'] for r in observations),
            'verified_decoder': False}

"""Pure helpers for searchable Event List and safe Yamaha XG parameter edits."""
from event_descriptions import describe_event
from xg_sysex import decode_parameter_change, parameter_change


def matches_event(event, category='All events', query=''):
    status = event.status
    kind = status & 0xf0
    categories = {
        'All events': True,
        'Notes': status < 0xf0 and kind in (0x80, 0x90),
        'Control changes': status < 0xf0 and kind == 0xb0,
        'Program changes': status < 0xf0 and kind == 0xc0,
        'Pitch bend': status < 0xf0 and kind == 0xe0,
        'Aftertouch': status < 0xf0 and kind in (0xa0, 0xd0),
        'Meta': status == 0xff,
        'SysEx': status in (0xf0, 0xf7),
    }
    if category not in categories:
        raise ValueError('Unknown event category')
    if not categories[category]:
        return False
    needle = query.strip().casefold()
    if not needle:
        return True
    haystack = f'{event.tick} {event.label()} {describe_event(event)} {bytes(event.data).hex(" ")}'
    return needle in haystack.casefold()


def rewrite_xg_parameter(event, *, address=None, values=None, device=None):
    """Return a replacement SMF SysEx payload, preserving unspecified fields.

    Reject incomplete/unknown SysEx rather than corrupting it. The caller is
    responsible for recording Undo and replacing the event atomically.
    """
    if event.status != 0xf0:
        raise ValueError('Not an F0 SysEx event')
    from xg_sysex import smf_sysex_to_wire
    decoded = decode_parameter_change(smf_sysex_to_wire(event.status, event.data))
    if decoded is None:
        raise ValueError('Not a complete Yamaha XG parameter change')
    target_address = decoded['address'] if address is None else address
    target_values = decoded['data'] if values is None else values
    target_device = decoded['device'] if device is None else device
    return parameter_change(target_address, target_values, target_device)[1:]

import pytest
from midi import Song, Track, Event, MidiError
from xg_export import export_xg, XG_SYSTEM_ON


def example():
    return Song(1, 480, [Track([Event(0, 0x90, b'\x3c\x64'),
                                 Event(480, 0x80, b'\x3c\x00')])])


@pytest.mark.parametrize('level,fmt', [(1,0),(2,1),(3,1)])
def test_level_export_roundtrip(level,fmt):
    source=example()
    out=export_xg(source,level)
    parsed=Song.from_bytes(out.to_bytes())
    assert parsed.fmt==fmt
    assert any(e.status==0xf0 and e.data==XG_SYSTEM_ON for t in parsed.tracks for e in t.events)
    assert any(e.status==0xb0 and e.data==b'\x0b\x7f' for t in parsed.tracks for e in t.events)
    assert any(e.tick==1920 and e.status==0x90 for t in parsed.tracks for e in t.events)
    assert source.tracks[0].events[0].tick==0


def test_preserves_existing_cc_setup_and_meta():
    source=example()
    source.tracks[0].events.extend([Event(0,0xb0,b'\x07\x37'), Event(0,0xff,b'\x07\xa1\x20',0x51)])
    out=export_xg(source)
    events=[e for t in out.tracks for e in t.events]
    assert any(e.status==0xb0 and e.data==b'\x07\x37' for e in events)
    assert not any(e.status==0xb0 and e.data==b'\x07\x64' for e in events)
    assert any(e.status==0xff and e.meta_type==0x51 and e.tick==0 for e in events)


def test_rejects_smpte_and_type2():
    with pytest.raises(MidiError): export_xg(Song(1,0xe728,[Track([])]))
    with pytest.raises(MidiError): export_xg(Song(2,480,[Track([])]))

"""SMF reader/editor/writer. No external dependencies. Preserves untouched files byte-for-byte."""
from dataclasses import dataclass, field
from pathlib import Path
import struct

class MidiError(ValueError): pass

def vlq_read(data, pos, end):
    v = 0
    for _ in range(4):
        if pos >= end: raise MidiError('Truncated variable-length quantity')
        b = data[pos]; pos += 1
        v = (v << 7) | (b & 127)
        if not b & 128: return v, pos
    raise MidiError('Invalid variable-length quantity')

def vlq_write(value):
    if not 0 <= value <= 0x0fffffff: raise MidiError('Delta exceeds SMF VLQ range')
    a = [value & 127]; value >>= 7
    while value: a.insert(0, (value & 127) | 128); value >>= 7
    return bytes(a)

@dataclass
class Event:
    tick: int
    status: int
    data: bytes
    meta_type: int = -1
    order: int = 0
    def label(self):
        s = self.status
        if s == 0xff:
            return {0x01:'Text',0x02:'Copyright',0x03:'Track name',0x04:'Instrument',0x05:'Lyric',0x06:'Marker',0x07:'Cue',0x2f:'End of track',0x51:'Tempo',0x58:'Time signature',0x59:'Key signature',0x7f:'Sequencer specific'}.get(self.meta_type, f'Meta {self.meta_type:02X}')
        if s in (0xf0,0xf7): return 'SysEx'
        return {0x80:'Note off',0x90:'Note on',0xa0:'Poly aftertouch',0xb0:'Control change',0xc0:'Program change',0xd0:'Aftertouch',0xe0:'Pitch bend'}.get(s&0xf0,'Unknown')
    def channel(self): return (self.status & 15) + 1 if self.status < 0xf0 else None
    def description(self):
        if self.status == 0xff and self.meta_type in (1,2,3,4,5,6,7):
            return self.data.decode('latin-1',errors='replace')
        if self.status == 0xff and self.meta_type == 0x51 and len(self.data)==3:
            micro=int.from_bytes(self.data,'big'); return f'{60000000/micro:.2f} BPM' if micro else 'Invalid tempo'
        if self.status == 0xff and self.meta_type == 0x58 and len(self.data)>=2:
            return f'{self.data[0]}/{2**self.data[1]}'
        if self.status == 0xb0 or self.status & 0xf0 == 0xb0:
            return f'CC {self.data[0]} = {self.data[1]}'
        if self.status & 0xf0 in (0x80,0x90): return f'Note {self.data[0]}, velocity {self.data[1]}'
        if self.status & 0xf0 == 0xc0: return f'Program {self.data[0]}'
        return self.data.hex(' ').upper()[:120]

@dataclass
class Track:
    events: list[Event] = field(default_factory=list)
    def name(self):
        for e in self.events:
            if e.status == 0xff and e.meta_type == 3: return e.data.decode('latin-1',errors='replace')
        return 'Untitled'

class Song:
    def __init__(self, fmt, division, tracks, original=None, header_extra=b'', extra_chunks=None):
        self.fmt=fmt; self.division=division; self.tracks=tracks
        self.original=original; self.header_extra=header_extra; self.extra_chunks=extra_chunks or []
        self.dirty=False
    @classmethod
    def from_bytes(cls, data):
        if data[:4] != b'MThd' or len(data)<14: raise MidiError('Not an SMF file')
        hlen=int.from_bytes(data[4:8],'big')
        if hlen<6 or 8+hlen>len(data): raise MidiError('Invalid header length')
        fmt,ntracks,division=struct.unpack_from('>HHH',data,8)
        if fmt not in (0,1,2): raise MidiError('Unsupported SMF format')
        if division==0: raise MidiError('Invalid time division')
        pos=8+hlen; tracks=[]; extras=[]
        while pos<len(data):
            if pos+8>len(data): raise MidiError('Truncated chunk header')
            typ=data[pos:pos+4]; length=int.from_bytes(data[pos+4:pos+8],'big'); pos+=8
            if pos+length>len(data): raise MidiError('Truncated chunk')
            body=data[pos:pos+length]; pos+=length
            if typ != b'MTrk': extras.append((len(tracks),typ,body)); continue
            p=0; tick=0; running=0; events=[]
            while p<len(body):
                delta,p=vlq_read(body,p,len(body)); tick+=delta
                if p>=len(body): raise MidiError('Truncated event')
                status=body[p]
                if status & 128:
                    p+=1
                    if status<0xf0: running=status
                    else: running=0
                else:
                    if not running: raise MidiError('Running status without preceding status')
                    status=running
                meta=-1
                if status==0xff:
                    if p>=len(body): raise MidiError('Truncated meta type')
                    meta=body[p]; p+=1
                    size,p=vlq_read(body,p,len(body))
                elif status in (0xf0,0xf7): size,p=vlq_read(body,p,len(body))
                elif 0x80<=status<=0xef: size=1 if status&0xf0 in (0xc0,0xd0) else 2
                else: raise MidiError(f'Unsupported SMF status {status:02x}')
                if p+size>len(body): raise MidiError('Truncated event payload')
                payload=body[p:p+size]; p+=size
                if status<0xf0 and any(x&128 for x in payload): raise MidiError('Invalid channel data byte')
                events.append(Event(tick,status,payload,meta,len(events)))
            tracks.append(Track(events))
        if len(tracks)!=ntracks: raise MidiError('Track count mismatch')
        return cls(fmt,division,tracks,bytes(data),data[14:8+hlen],extras)
    @classmethod
    def read(cls,path): return cls.from_bytes(Path(path).read_bytes())
    def to_bytes(self):
        if not self.dirty and self.original is not None: return self.original
        out=bytearray(b'MThd'+struct.pack('>IHHH',6+len(self.header_extra),self.fmt,len(self.tracks),self.division)+self.header_extra)
        for i,track in enumerate(self.tracks):
            for at,typ,payload in self.extra_chunks:
                if at==i: out+=typ+struct.pack('>I',len(payload))+payload
            body=bytearray(); last=0
            for ev in sorted(track.events,key=lambda e:(e.tick,e.order)):
                if ev.tick<last: raise MidiError('Invalid event ordering')
                body+=vlq_write(ev.tick-last); last=ev.tick
                body.append(ev.status)
                if ev.status==0xff: body.append(ev.meta_type); body+=vlq_write(len(ev.data))
                elif ev.status in (0xf0,0xf7): body+=vlq_write(len(ev.data))
                body+=ev.data
            out+=b'MTrk'+struct.pack('>I',len(body))+body
        for at,typ,payload in self.extra_chunks:
            if at>=len(self.tracks): out+=typ+struct.pack('>I',len(payload))+payload
        return bytes(out)
    def save(self,path): Path(path).write_bytes(self.to_bytes())
    def set_event(self,track_idx,event_idx,*,tick=None,data=None):
        e=self.tracks[track_idx].events[event_idx]
        if tick is not None:
            if tick<0: raise MidiError('Negative tick')
            e.tick=tick
        if data is not None:
            if e.status in (0xff,0xf0,0xf7): raise MidiError('Raw SysEx/meta editing not enabled in this version')
            expected=1 if e.status&0xf0 in (0xc0,0xd0) else 2
            if len(data)!=expected or any(not 0<=v<=127 for v in data): raise MidiError('Invalid MIDI data bytes')
            e.data=bytes(data)
        self.dirty=True
    def transpose(self,track_idx,semitones):
        changes=[]
        for e in self.tracks[track_idx].events:
            if e.status&0xf0 in (0x80,0x90):
                note=e.data[0]+semitones
                if not 0<=note<=127: raise MidiError('Transpose would exceed MIDI note range')
                changes.append((e,note))
        for e,note in changes: e.data=bytes([note])+e.data[1:]
        if changes: self.dirty=True
        return len(changes)

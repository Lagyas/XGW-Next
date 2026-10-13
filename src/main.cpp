#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>
using Bytes = std::vector<uint8_t>;
static uint32_t be(const Bytes& b, size_t p, int n) {
    if (p + n > b.size()) throw std::runtime_error("Truncated integer");
    uint32_t v=0; for(int i=0;i<n;i++) v=(v<<8)|b[p+i]; return v;
}
static uint32_t vlq(const Bytes& b, size_t& p, size_t end) {
    uint32_t v=0;
    for(int i=0;i<4;i++) {
        if(p>=end) throw std::runtime_error("Truncated VLQ");
        uint8_t x=b[p++]; v=(v<<7)|(x&127);
        if(!(x&128)) return v;
    }
    throw std::runtime_error("Invalid VLQ (over 4 bytes)");
}
struct Counts { uint64_t events=0, notes=0, controllers=0, programs=0, sysex=0, meta=0; };
static Counts parseTrack(const Bytes& b, size_t start, size_t end) {
    Counts c; size_t p=start; uint8_t running=0; uint64_t tick=0;
    while(p<end) {
        tick+=vlq(b,p,end);
        if(p>=end) throw std::runtime_error("Missing event status");
        uint8_t status=b[p];
        if(status&128) { ++p; if(status<0xF0) running=status; else running=0; }
        else { if(!running) throw std::runtime_error("Invalid running status"); status=running; }
        c.events++;
        if(status==0xFF) {
            if(p>=end) throw std::runtime_error("Missing meta type");
            ++p; auto len=vlq(b,p,end); if(len>end-p) throw std::runtime_error("Truncated meta payload");
            p+=len; c.meta++;
        } else if(status==0xF0 || status==0xF7) {
            auto len=vlq(b,p,end); if(len>end-p) throw std::runtime_error("Truncated SysEx payload");
            p+=len; c.sysex++;
        } else if(status>=0x80 && status<=0xEF) {
            int hi=status&0xF0; int n=(hi==0xC0||hi==0xD0)?1:2;
            if(static_cast<size_t>(n)>end-p) throw std::runtime_error("Truncated channel event");
            for(int j=0;j<n;j++) if(b[p+j]&128) throw std::runtime_error("Invalid MIDI data byte");
            p+=n;
            if(hi==0x80||hi==0x90) c.notes++;
            if(hi==0xB0) c.controllers++;
            if(hi==0xC0) c.programs++;
        } else throw std::runtime_error("Unsupported event status in SMF");
    }
    return c;
}
static void inspect(const Bytes& b) {
    if(b.size()<14 || std::string(b.begin(),b.begin()+4)!="MThd") throw std::runtime_error("Not a Standard MIDI File");
    auto hlen=be(b,4,4); if(hlen<6 || hlen>b.size()-8) throw std::runtime_error("Invalid MIDI header");
    auto format=be(b,8,2), tracks=be(b,10,2), division=be(b,12,2);
    std::cout<<"SMF format="<<format<<" tracks="<<tracks<<" division="<<division<<"\n";
    size_t p=8+hlen; unsigned parsed=0;
    while(p<b.size()) {
        if(b.size()-p<8) throw std::runtime_error("Truncated chunk header");
        std::string id(b.begin()+p,b.begin()+p+4); auto len=be(b,p+4,4); p+=8;
        if(len>b.size()-p) throw std::runtime_error("Truncated chunk");
        if(id=="MTrk") {
            auto c=parseTrack(b,p,p+len); parsed++;
            std::cout<<"track "<<parsed<<": events="<<c.events<<" note-events="<<c.notes
                     <<" CC="<<c.controllers<<" PC="<<c.programs<<" sysex="<<c.sysex<<" meta="<<c.meta<<"\n";
        } else std::cout<<"preserved unknown chunk: "<<id<<" ("<<len<<" bytes)\n";
        p+=len;
    }
    if(parsed!=tracks) throw std::runtime_error("Declared track count mismatch");
}
static Bytes read(const std::string& path) {
    std::ifstream f(path,std::ios::binary);
    if(!f) throw std::runtime_error("Cannot open input file");
    return Bytes(std::istreambuf_iterator<char>(f),{});
}
int main(int argc,char** argv) {
    try {
        if(argc!=3 && argc!=4) {
            std::cerr<<"Usage: xg-midi-core inspect FILE.mid | roundtrip INPUT.mid OUTPUT.mid\n"; return 2;
        }
        std::string cmd=argv[1]; auto b=read(argv[2]);
        if(cmd=="inspect" && argc==3) inspect(b);
        else if(cmd=="roundtrip" && argc==4) {
            inspect(b);
            std::ofstream out(argv[3],std::ios::binary);
            if(!out) throw std::runtime_error("Cannot create output file");
            out.write(reinterpret_cast<const char*>(b.data()),static_cast<std::streamsize>(b.size()));
            if(!out) throw std::runtime_error("Write failed");
            std::cout<<"Lossless no-edit roundtrip: "<<b.size()<<" bytes\n";
        } else { std::cerr<<"Invalid command\n"; return 2; }
        return 0;
    } catch(const std::exception& e) { std::cerr<<"Error: "<<e.what()<<"\n"; return 1; }
}

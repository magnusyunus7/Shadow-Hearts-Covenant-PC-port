import sys,struct,collections,rabbitizer as rz
R=rz.InstrCategory.R5900
elf=open(sys.argv[1],'rb').read()
def load(f):
    d=open(f,'rb').read(); _,oid,la,t,ds,b,_,_=struct.unpack_from('<4sI6I',d,0); return d,la,t
ovs={f:load(f) for f in sys.argv[2:]}
# own-target set & prologue ratio per overlay
for f,(d,la,t) in ovs.items():
    own=set(); 
    for i in range(t//4):
        x=rz.Instruction(struct.unpack_from('<I',d,0x40+i*4)[0],la+i*4,R)
        if x.uniqueId==rz.InstrId.cpu_jal:
            tt=x.getInstrIndexAsVram()
            if la<=tt<la+t: own.add(tt)
    firsts=collections.Counter(rz.Instruction(struct.unpack_from('<I',d,0x40+tt-la)[0],tt,R).getOpcodeName() for tt in own)
    print(f, "own targets", len(own), "first-instr:", firsts.most_common(5))
    ovs[f]=(d,la,t,own)
# main jal into overlay region: where are those call sites, and are targets in any overlay's own-target set
W=struct.unpack('<%dI'%((0x417000-0x200000)//4),elf[0x100:0x100+0x217000])
sites=[]
for i,w in enumerate(W):
    x=rz.Instruction(w,0x200000+i*4,R)
    if x.uniqueId==rz.InstrId.cpu_jal and x.getInstrIndexAsVram()>=0x45ea80: sites.append((0x200000+i*4,x.getInstrIndexAsVram()))
hit=collections.Counter()
for s,tt in sites:
    k=[f for f,(d,la,t,own) in ovs.items() if tt in own]; hit[tuple(k)]+=1
print("main call sites:",len(sites),"match overlay-own function starts:",dict(hit))
# cluster call sites
import itertools
blocks=collections.Counter(s>>12 for s,_ in sites); print("site 4KB blocks:",sorted((hex(k<<12),v) for k,v in blocks.items())[:30])

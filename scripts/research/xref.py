import sys,struct,rabbitizer as rz
R=rz.InstrCategory.R5900
d=open(sys.argv[1],'rb').read(); OFF,VA=0x100,0x200000
def va(off): return off-OFF+VA
targets={}
for s in sys.argv[2:]:
    i=d.find(s.encode())
    while i!=-1: targets[va(i)]=s; i=d.find(s.encode(),i+1)
print({hex(k):v for k,v in targets.items()})
W=struct.unpack('<%dI'%((0x417000-VA)//4),d[OFF:OFF+0x417000-VA])
lui={}
for i,w in enumerate(W):
    x=rz.Instruction(w,VA+i*4,R); n=x.getOpcodeName()
    if n=='lui': lui[x.rt]=(x.getProcessedImmediate()<<16)&0xffffffff, i
    elif n in('addiu','ori') and x.rs in lui and i-lui[x.rs][1]<16:
        imm=x.getProcessedImmediate(); full=(lui[x.rs][0]+(imm if n=='addiu' else imm))&0xffffffff
        for t,s in targets.items():
            if full==t: print("ref to %r at %08x"%(s,VA+i*4))

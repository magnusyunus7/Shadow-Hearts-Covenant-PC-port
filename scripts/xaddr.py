import sys,struct,rabbitizer as rz
R=rz.InstrCategory.R5900
d=open(sys.argv[1],'rb').read(); OFF,VA=0x100,0x200000
T=set(int(x,16) for x in sys.argv[2:])
W=struct.unpack('<%dI'%((0x417000-VA)//4),d[OFF:OFF+0x417000-VA])
lui={}
for i,w in enumerate(W):
    x=rz.Instruction(w,VA+i*4,R); n=x.getOpcodeName()
    if n=='lui': lui[x.rt]=((x.getProcessedImmediate()<<16)&0xffffffff,i); continue
    try: rs=x.rs
    except Exception: continue
    if x.isIType() and rs in lui and i-lui[rs][1]<24 and n!='lui':
        imm=x.getProcessedImmediate()
        full=(lui[rs][0]+imm)&0xffffffff
        if full in T: print("%08x  %s"%(VA+i*4,x.disassemble()))

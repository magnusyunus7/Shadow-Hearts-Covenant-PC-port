import sys, struct, collections, rabbitizer as rz
path=sys.argv[1]
data=open(path,'rb').read()
OFF,SIZE,VA=0x100,0x23fc00,0x200000
seg=data[OFF:OFF+SIZE]
words=struct.unpack('<%dI'%(SIZE//4),seg)
cat=rz.InstrCategory.R5900
# pass1: jal targets -> function starts
targets=set()
for i,w in enumerate(words):
    ins=rz.Instruction(w,VA+i*4,cat)
    if ins.uniqueId==rz.InstrId.cpu_jal:
        t=ins.getInstrIndexAsVram()
        if VA<=t<VA+SIZE: targets.add(t)
# keep targets referenced >=2 times-ish: approximate by density
ts=sorted(targets)
print("jal targets in segment:",len(ts),"min %x max %x"%(ts[0],ts[-1]))
# block validity profile
blk=0x10000
for b in range(0,SIZE,blk):
    n=v=0
    for i in range(b//4,min((b+blk)//4,len(words))):
        ins=rz.Instruction(words[i],VA+i*4,cat); n+=1
        if ins.isValid(): v+=1
    tcount=sum(1 for t in ts if VA+b<=t<VA+b+blk)
    print("%08x valid=%.2f jaltargets=%d"%(VA+b,v/n,tcount))

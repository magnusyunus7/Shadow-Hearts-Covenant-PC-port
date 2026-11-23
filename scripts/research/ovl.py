import sys,struct,collections,rabbitizer as rz
data=open(sys.argv[1],'rb').read(); OFF,VA,END=0x100,0x200000,0x417000
W=struct.unpack('<%dI'%((END-VA)//4),data[OFF:OFF+END-VA])
out=collections.Counter(); jr=0
for i,w in enumerate(W):
    ins=rz.Instruction(w,VA+i*4,rz.InstrCategory.R5900)
    if ins.uniqueId==rz.InstrId.cpu_jal:
        t=ins.getInstrIndexAsVram()
        if t>=0x45ea80: out[t>>16]+=1
    if ins.getOpcodeName()=='jalr': jr+=1
print("direct jal into region >=0x45ea80:",sum(out.values()),dict(sorted(out.items())))
print("indirect calls (jalr):",jr)

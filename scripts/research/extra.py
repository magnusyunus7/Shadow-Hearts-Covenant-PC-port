import sys, struct, collections, rabbitizer as rz
data=open(sys.argv[1],'rb').read()
OFF,VA=0x100,0x200000; END=0x417000
n=(END-VA)//4
words=struct.unpack('<%dI'%n,data[OFF:OFF+END-VA])
cat=rz.InstrCategory.R5900
c=collections.Counter(); sysno=collections.Counter()
for i,w in enumerate(words):
    ins=rz.Instruction(w,VA+i*4,cat); nm=ins.getOpcodeName()
    if nm in('vcallms','vcallmsr','ctc2','cfc2','eret'): c[nm]+=1
    if nm=='syscall':
        for j in range(1,4):
            p=rz.Instruction(words[i-j],VA+(i-j)*4,cat)
            if p.getOpcodeName() in('addiu','ori','li') and 'v1' in p.disassemble():
                imm=p.getProcessedImmediate(); sysno[imm & 0xffff if imm>=0 else imm]+=1; break
print(dict(c))
print("syscall ids:",sorted(sysno.items()))
# VIF MPG (cmd 0x4A) scan over whole loaded image
full=data[OFF:OFF+0x23fc00]
W=struct.unpack('<%dI'%(len(full)//4),full)
mpg=[(VA+i*4,(w>>16)&0xff,w&0xffff) for i,w in enumerate(W) if (w>>24)&0x7f==0x4a and ((w>>16)&0xff)>=8]
print("possible VIF MPG headers:",len(mpg))
for a,num,addr in mpg[:20]: print(" %08x num=%d instrs, vuaddr=%d"%(a,num or 256,addr))

import sys, struct, collections, rabbitizer as rz
data=open(sys.argv[1],'rb').read()
OFF,VA=0x100,0x200000; END=0x417000
words=struct.unpack('<%dI'%((END-VA)//4),data[OFF:OFF+END-VA])
cat=rz.InstrCategory.R5900
c=collections.Counter(); sysno=collections.Counter(); invalid=0
prev=None
for i,w in enumerate(words):
    ins=rz.Instruction(w,VA+i*4,cat)
    if not ins.isValid(): invalid+=1; continue
    name=ins.getOpcodeName(); c[name]+=1
    if name=='syscall' and prev is not None and prev.getOpcodeName() in('addiu','ori') and prev.rt==rz.RegGprO32.v1 if hasattr(rz,'RegGprO32') else False:
        sysno[prev.getProcessedImmediate()]+=1
    prev=ins
print("words",len(words),"invalid",invalid)
groups={
 'MMI (128-bit integer SIMD)':lambda n:n.startswith('p') and n not in('pref',),
 '128-bit load/store lq/sq':lambda n:n in('lq','sq'),
 'COP2/VU0 macro & transfers':lambda n:n.startswith('v') or n in('qmfc2','qmtc2','lqc2','sqc2','cfc2','ctc2','bc2f','bc2t','bc2fl','bc2tl'),
 'COP1 FPU':lambda n:n.endswith('.s') or n in('lwc1','swc1','mfc1','mtc1','cfc1','ctc1','bc1f','bc1t','bc1fl','bc1tl'),
 'pipeline-1 mult/div (mult1,div1,mfhi1..)':lambda n:n.endswith('1') and n[:-1] in('mult','multu','div','divu','mfhi','mflo','mthi','mtlo','madd','maddu'),
 'COP0 / kernel (mfc0,mtc0,ei,di,eret,tlb*)':lambda n:n in('mfc0','mtc0','ei','di','eret','tlbr','tlbwi','tlbwr','tlbp','bc0f','bc0t','mfbpc','mtbpc','mfps','mtps','mfpc','mtpc'),
 'sync / cache':lambda n:n.startswith('sync') or n=='cache',
 'syscall':lambda n:n=='syscall',
}
for g,f in groups.items():
    items=[(n,k) for n,k in c.items() if f(n)]
    tot=sum(k for _,k in items)
    top=', '.join('%s:%d'%x for x in sorted(items,key=lambda x:-x[1])[:14])
    print(f"\n{g}: {tot}\n  {top}")
print("\nTOTAL distinct opcodes:",len(c))

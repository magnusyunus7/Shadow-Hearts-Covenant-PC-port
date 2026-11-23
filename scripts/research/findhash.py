import sys,struct,rabbitizer as rz
R=rz.InstrCategory.R5900
d=open(sys.argv[1],'rb').read(); OFF,VA=0x100,0x200000
lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
ins=[rz.Instruction(struct.unpack_from('<I',d,a-VA+OFF)[0],a,R) for a in range(lo,hi,4)]
# split into functions at 'addiu sp,sp,-N'
starts=[i for i,x in enumerate(ins) if x.getOpcodeName()=='addiu' and x.disassemble().startswith('addiu       $sp, $sp, -')]
# also leaf funcs: after jr ra + delay
for i,x in enumerate(ins):
    if x.getOpcodeName()=='jr' and 'ra' in x.disassemble() and i+2<len(ins): starts.append(i+2)
starts=sorted(set(starts))
for s,e in zip(starts,starts[1:]+[len(ins)]):
    names=[x.getOpcodeName() for x in ins[s:e]]
    if 'lbu' in names or 'lb' in names:
        ops=set(names)
        score=sum(o in ops for o in('xor','multu','mult','sll','srl','sra','addu','nor'))
        back=any(x.isBranch() and x.getBranchVramGeneric()<x.vram for x in ins[s:e] if hasattr(x,'getBranchVramGeneric') and x.isBranch())
        if score>=3 and e-s<120:
            print("%08x len=%d score=%d ops=%s"%(lo+s*4,e-s,score,sorted(o for o in ops if o in('xor','multu','mult','sll','srl','sra','nor','div','divu'))))

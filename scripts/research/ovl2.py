import sys,struct,collections,rabbitizer as rz
R=rz.InstrCategory.R5900
elf=open(sys.argv[1],'rb').read()
ov={}
for f in sys.argv[2:]:
    d=open(f,'rb').read()
    magic,oid,la,tsz,dsz,bsz,c0,c1=struct.unpack_from('<4sI6I',d,0)
    ov[f]=dict(d=d,id=oid,la=la,t=tsz,ds=dsz,b=bsz,c0=c0,c1=c1)
    assert 0x40+tsz+dsz==len(d), f
    print(f"{f}: magic={magic} id={oid} load=0x{la:x} text=0x{tsz:x} data=0x{dsz:x} bss=0x{bsz:x} ctors=0x{c0:x}-0x{c1:x} end=0x{la+tsz+dsz+bsz:x}")
def ins_at(o,a): 
    w=struct.unpack_from('<I',o['d'],0x40+a-o['la'])[0]; return rz.Instruction(w,a,R)
# main->overlay jal targets: does each target look like a prologue in which overlay?
W=struct.unpack('<%dI'%((0x417000-0x200000)//4),elf[0x100:0x100+0x217000])
tg=set()
for i,w in enumerate(W):
    x=rz.Instruction(w,0x200000+i*4,R)
    if x.uniqueId==rz.InstrId.cpu_jal and x.getInstrIndexAsVram()>=0x45ea80: tg.add(x.getInstrIndexAsVram())
for f,o in ov.items():
    inside=[t for t in tg if o['la']<=t<o['la']+o['t']]
    pro=sum(1 for t in inside if ins_at(o,t).disassemble().startswith('addiu       $sp, $sp, -'))
    print(f"  main->{f}: {len(inside)} targets in text, {pro} start with 'addiu sp,sp,-N'")
# per-overlay histogram + jal/jalr + VU1
groups={'FPU':lambda n:n.endswith('.s') or n in('lwc1','swc1','mfc1','mtc1','cfc1','ctc1','bc1f','bc1t','bc1fl','bc1tl'),
 'VU0 macro':lambda n:n.startswith('v') or n in('qmfc2','qmtc2','lqc2','sqc2','cfc2','ctc2'),
 'MMI':lambda n:n.startswith('p') and n!='pref','lq/sq':lambda n:n in('lq','sq'),
 'COP0':lambda n:n in('mfc0','mtc0','ei','di','eret'),'syscall':lambda n:n=='syscall',
 'jalr':lambda n:n=='jalr','vcallms':lambda n:n.startswith('vcallms')}
for f,o in ov.items():
    d=o['d']; n=o['t']//4; c=collections.Counter(); inv=0; jt=0; ext=collections.Counter()
    for i in range(n):
        w=struct.unpack_from('<I',d,0x40+i*4)[0]; x=rz.Instruction(w,o['la']+i*4,R)
        if not x.isValid(): inv+=1; continue
        c[x.getOpcodeName()]+=1
        if x.uniqueId==rz.InstrId.cpu_jal:
            t=x.getInstrIndexAsVram()
            ext['own' if o['la']<=t<o['la']+o['t'] else ('main' if 0x200000<=t<0x417000 else 'other')]+=1
            if o['la']<=t<o['la']+o['t']: jt+=1
    g={k:sum(v for nm,v in c.items() if fn(nm)) for k,fn in groups.items()}
    print(f"\n{f}: {n} words, invalid {inv}, distinct {len(c)}, jal targets {dict(ext)}\n  {g}")
    # VU1 mpg scan in data+text
    blob=d[0x40:]; base=o['la']; a=0; progs=[]; cur=None
    while a<len(blob)-4:
        x=struct.unpack_from('<I',blob,a)[0]
        if (x>>24)&0x7f==0x4a:
            num=(x>>16)&0xff or 256; addr=x&0xffff; nxt=a+4+num*8
            if a>=o['t']-0 and addr<2048 and addr+num<=2048 and nxt<=len(blob):
                if cur and a-cur['end']<=12 and addr==cur['last']: cur['n']+=num; cur['last']=addr+num; cur['end']=nxt
                else: cur={'s':base+a,'n':num,'last':addr+num,'end':nxt}; progs.append(cur)
                a=nxt; continue
        a+=4
    progs=[p for p in progs if p['n']>=32]
    print(f"  VU1 microprograms in data: {len(progs)}, instrs {sum(p['n'] for p in progs)}")

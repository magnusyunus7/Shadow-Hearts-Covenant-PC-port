import sys,struct
data=open(sys.argv[1],'rb').read(); OFF,VA=0x100,0x200000
def w(a): return struct.unpack_from('<I',data,a-VA+OFF)[0]
a=0x417000; progs=[]; cur=None
while a<0x200000+0x23fc00-4:
    x=w(a)
    if (x>>24)&0x7f==0x4a:
        num=(x>>16)&0xff or 256; addr=x&0xffff
        nxt=a+4+num*8
        if addr<2048 and addr+num<=2048:
            if cur and cur['end'] in (a,a-4,a-8,a-12) and addr==cur['last']:
                cur['n']+=num; cur['last']=addr+num; cur['end']=nxt
            else:
                cur={'start':a,'n':num,'last':addr+num,'end':nxt,'base':addr}; progs.append(cur)
            a=nxt; continue
    a+=4
print("VU1 microprograms found:",len(progs))
print("total micro-instructions:",sum(p['n'] for p in progs))
for p in progs: print("  %08x-%08x  %4d instrs (%5d bytes) load@%d"%(p['start'],p['end'],p['n'],p['n']*8,p['base']))

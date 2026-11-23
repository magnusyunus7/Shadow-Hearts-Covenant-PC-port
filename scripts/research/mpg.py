import sys,struct
data=open(sys.argv[1],'rb').read(); OFF,VA=0x100,0x200000
full=data[OFF:OFF+0x23fc00]; W=struct.unpack('<%dI'%(len(full)//4),full)
hits=[]
for i,w in enumerate(W):
    a=VA+i*4
    if a<0x417000: continue
    if (w>>24)&0x7f==0x4a:
        num=(w>>16)&0xff or 256; addr=w&0xffff
        if addr<2048 and addr+num<=2048: hits.append((a,num,addr))
print(len(hits))
for h in hits[:40]: print(" %08x num=%d vuaddr=%d"%h)

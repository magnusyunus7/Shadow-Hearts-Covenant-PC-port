"""Collect likely function entry points for a Shadow Hearts: Covenant overlay so PS2Recomp emits a
callable entry for each. Sources: JAL targets and lui/addiu constants in the main ELF and in the
overlay, 32-bit words in data that point into the overlay code, and the overlay's static ctors.
A candidate is kept only if it looks like a function start (preceded by `jr ra` + delay slot, or
by nop padding that follows a `jr ra`).
Usage: python ovlentries.py SLUS_210.41 OVERLAY.BIN out.txt   (one 0xADDR per line)"""
import sys,struct
main=open(sys.argv[1],'rb').read(); ov=open(sys.argv[2],'rb').read()
magic,oid,la,tsz,dsz,bsz,c0,c1=struct.unpack_from('<4sI6I',ov,0)
H=0x40; cs=la+H; ce=cs+tsz; de=ce+dsz
ctors=[struct.unpack_from('<I',ov,c0-la+4*i)[0] for i in range((c1-c0)//4)]
init=(min(ctors),c0) if ctors else None
def incode(a): return a%4==0 and (cs<=a<ce or (init and init[0]<=a<init[1]))
def w(a): return struct.unpack_from('<I',ov,a-la)[0]
def looks_like_start(a):
    p=a-4
    while p>=cs and w(p)==0: p-=4
    if p<cs: return True
    # p is last non-zero word; accept `jr ra` with its delay slot (nop or real instr) right before
    return w(p)==0x03E00008 or (p-4>=cs and w(p-4)==0x03E00008)
def scan_code(blob,off,va,n):
    out=set(); lui={}
    for i in range(n//4):
        x=struct.unpack_from('<I',blob,off+i*4)[0]; op=x>>26
        if op==3: out.add(((va+i*4)&0xF0000000)|((x&0x3FFFFFF)<<2))
        rt=(x>>16)&31; rs=(x>>21)&31; imm=x&0xFFFF
        if op==0xF: lui[rt]=(imm<<16,i)
        elif op in (9,0xD) and rs in lui and i-lui[rs][1]<16:
            v=lui[rs][0]+((imm-0x10000) if (op==9 and imm&0x8000) else imm); out.add(v&0xFFFFFFFF)
    return out
def scan_data(blob,off,n):
    return {struct.unpack_from('<I',blob,off+i*4)[0] for i in range(n//4)}
cand=set()
MO,MV=0x100,0x200000          # SLUS_210.41: file offset 0x100 == 0x200000
cand|=scan_code(main,MO,MV,0x416F80-MV)
cand|=scan_data(main,MO+0x416F80-MV,0x45EA80-0x416F80 if len(main)>=MO+0x45EA80-MV else len(main)-MO-(0x416F80-MV))
cand|=scan_code(ov,H,cs,tsz)
if init: cand|=scan_code(ov,init[0]-la,init[0],init[1]-init[0])
cand|=scan_data(ov,H+tsz,dsz)
cand|=set(ctors)
keep=sorted(a for a in cand if incode(a) and (a in ctors or looks_like_start(a)))
open(sys.argv[3],'w').write(''.join('0x%X\n'%a for a in keep))
print(f"{sys.argv[2]}: id={oid} {len(keep)} entry candidates (ctors {[hex(c) for c in ctors]})")

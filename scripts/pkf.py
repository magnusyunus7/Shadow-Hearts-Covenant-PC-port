"""Shadow Hearts: Covenant (USA) PKFINFO.TBL / *.PKB lister & extractor.
Format reverse-engineered from SLUS_210.41 (func_0022A360 name decoder, package open loop ~0x228C80).
Usage:
  python pkf.py list    <PKFINFO.TBL>                         -> prints every path
  python pkf.py extract <PKFINFO.TBL> <disc_dir> <out_dir> [PACKAGE ...]
  python pkf.py scan    <PKFINFO.TBL> <disc_dir>    -> report files that start with code-overlay
                                                        ("MWo3") or ELF magic, and sub-archive headers
"""
import sys,struct,os
ALPHA=".0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_"
def decode(b8):
    v1=int.from_bytes(b8[0:4],'big'); v0=int.from_bytes(b8[4:8],'big'); hi=v1>>16
    A=[v1&0xffff,v0>>16,v0&0xffff]; B=[hi%40,(hi//40)%40,(hi//1600)%40]; s=''
    for k in range(3):
        t=(B[k]<<16)|A[k]
        for dv in (1,40,1600,64000):
            c=(t//dv)%40
            if c: s+=ALPHA[c-1]
    return s
def load(tbl):
    d=open(tbl,'rb').read(); n=struct.unpack_from('<I',d,4)[0]//16
    E=[]
    for i in range(n):
        e=d[16+i*16:32+i*16]; w2,w3=struct.unpack_from('<II',e,8)
        E.append(dict(name=decode(e[:8]),isdir=bool(w3>>31),off=w2,val=w3&0x7fffffff))
    return E
def walk(E):
    """Yield (path, package, abs_offset_bytes, size) for every file.
    Lists are stored breadth-first and contiguously; a directory's children start at
    (start of the directory's own list) + (w3 & 0x7fffffff) >> 4."""
    from collections import deque
    known={0}; q=deque([(0,'',None,0)]); res=[]
    while q:
        s,prefix,pkg,base=q.popleft()
        i=s
        while i<len(E):
            bound=min([k for k in known if k>s],default=len(E))
            if i>=bound: break
            e=E[i]
            if e['isdir']:
                c=s+(e['val']>>4); known.add(c)
                if pkg is None: q.append((c,'',e['name'],0))
                else: q.append((c,prefix+e['name']+'/',pkg,base+e['off']*16))
            else:
                res.append((prefix+e['name'],pkg,base+e['off']*16,e['val']))
            i+=1
    return res

if __name__=='__main__':
    cmd=sys.argv[1]; E=load(sys.argv[2])
    if cmd=='list':
        for p,pkg,off,sz in walk(E): print(f"{(pkg or '-'):9} {off:#011x} {sz:#010x}  {p}")
    elif cmd=='extract':
        disc,out=sys.argv[3],sys.argv[4]; want=set(a.upper() for a in sys.argv[5:])
        fh={}
        for p,pkg,off,sz in walk(E):
            if pkg is None or (want and pkg not in want): continue
            if pkg not in fh: fh[pkg]=open(os.path.join(disc,pkg+'.PKB'),'rb')
            f=fh[pkg]; f.seek(off); data=f.read(sz)
            dst=os.path.join(out,pkg,*p.split('/')); os.makedirs(os.path.dirname(dst),exist_ok=True)
            open(dst,'wb').write(data)
        print("done")
    elif cmd=='scan':
        disc=sys.argv[3]; fh={}; from collections import Counter; kinds=Counter()
        for p,pkg,off,sz in walk(E):
            if pkg is None: continue
            if pkg not in fh:
                fp=os.path.join(disc,pkg+'.PKB')
                fh[pkg]=open(fp,'rb') if os.path.exists(fp) else None
                if fh[pkg] is None: print("skip (not found):",fp)
            f=fh[pkg]
            if f is None: continue
            f.seek(off); h=f.read(16)
            if h[:4]==b'MWo3': print("CODE OVERLAY (MWo3):",pkg,p); kinds['MWo3']+=1
            elif h[:4]==b'\x7fELF': print("ELF:",pkg,p); kinds['ELF']+=1
            elif len(h)>=12 and h[8:12].rstrip(b'\0').isalpha() and 0<struct.unpack_from('<I',h,0)[0]<4096: kinds['subarchive:'+h[8:12].rstrip(b'\0').decode()]+=1
            else: kinds['other']+=1
        print(dict(kinds))

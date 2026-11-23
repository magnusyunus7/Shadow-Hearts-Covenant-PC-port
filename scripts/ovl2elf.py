"""Wrap a Shadow Hearts: Covenant MWo3 overlay (FIELD/BATTLE/OPENING.BIN) in a minimal
PS2 ELF so ELF-based tools (PS2Recomp, Ghidra) can load it at its real address.
Usage: python ovl2elf.py FIELD.BIN FIELD.elf"""
import sys,struct
src,dst=sys.argv[1],sys.argv[2]
d=open(src,'rb').read()
magic,oid,la,tsz,dsz,bsz,c0,c1=struct.unpack_from('<4sI6I',d,0)
assert magic==b'MWo3'
# The game loads the WHOLE file, header included, at the load address (verified against a RAM
# dump: OPENING.BIN matches byte-for-byte at 0x45EA80, and main code calls 0x45EB60 = file
# offset 0xE0, a function prologue). So the header occupies la..la+0x40 and text starts at la+0x40.
H=0x40
body=d[:H+tsz+dsz]
shstr=b'\0.text\0.data\0.bss\0.shstrtab\0.ovlhdr\0.text.init\0'
EH,PH,SH=52,32,40
off_body=0x100
off_shstr=off_body+len(body)
off_sh=(off_shstr+len(shstr)+3)&~3
def sec(name,typ,flags,addr,off,size,align): return struct.pack('<10I',name,typ,flags,addr,off,size,0,0,align,0)
# Static-constructor code (MW .init) sits inside the "data" part, between the first ctor and the
# ctor table (BATTLE: 0x6E7C80..0x6E83B0). Give it its own executable section so it gets recompiled.
ctors=[struct.unpack_from('<I',d,c0-la+4*i)[0] for i in range((c1-c0)//4)] if c1>c0 else []
ds=la+H+tsz
sh=sec(0,0,0,0,0,0,0)+sec(1,1,6,la+H,off_body+H,tsz,64)
if ctors:
    i0=min(ctors); o=lambda a: off_body+(a-la)
    sh+=sec(7,1,3,ds,o(ds),i0-ds,16)+sec(36,1,6,i0,o(i0),c0-i0,16)+sec(7,1,3,c0,o(c0),la+H+tsz+dsz-c0,16)
else:
    sh+=sec(7,1,3,ds,off_body+H+tsz,dsz,16)
sh+=sec(13,8,3,la+H+tsz+dsz,off_body+H+tsz+dsz,bsz,16)+sec(18,3,0,0,off_shstr,len(shstr),1)+sec(28,1,2,la,off_body,H,16)
nsec=len(sh)//40
shdrs=sh
eh=b'\x7fELF\x01\x01\x01'+b'\0'*9+struct.pack('<HHIIIIIHHHHHH',2,8,1,la+H,EH,off_sh,0x20924000,EH,PH,1,SH,nsec,nsec-2)
ph=struct.pack('<8I',1,off_body,la,la,len(body),len(body)+bsz,7,0x40)
out=bytearray(eh+ph); out+=b'\0'*(off_body-len(out)); out+=body+shstr; out+=b'\0'*(off_sh-len(out)); out+=shdrs
open(dst,'wb').write(out); print(f"{src}: id={oid} load=0x{la:x} code=0x{la+H:x} text=0x{tsz:x} data=0x{dsz:x} bss=0x{bsz:x} -> {dst}")
if c1>c0:
    print("static ctors (add to entry_points):",[hex(struct.unpack_from('<I',d,c0-la+4*i)[0]) for i in range((c1-c0)//4)])

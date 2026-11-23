"""Re-section SLUS_210.41 (Shadow Hearts: Covenant USA).

The retail ELF has one unnamed merged section, so tools treat data as code. This emits an
equivalent ELF with named sections at the verified boundaries. Program headers (incl. the
three overlay regions) are copied unchanged, so the loaded memory image is identical.

Code ranges (VERIFIED):
  0x200000-0x416F80  main code
  0x437300-0x437E80  34 static-constructor functions (CodeWarrior placed them among the
                     data; called through the pointer table at 0x437E80 during startup)
Not marked as code (HYPOTHESIS): 0x429CE8-~0x42B200 looks like a kernel patch copied to
0x8007xxxx at boot; nothing in the game calls it directly.

Usage: python main2elf.py SLUS_210.41 MAIN.elf
"""
import sys, struct

src, dst = sys.argv[1], sys.argv[2]
d = open(src, 'rb').read()
assert d[:4] == b'\x7fELF'

VA, OFF, FSZ, MSZ = 0x200000, 0x100, 0x23fc00, 0x25ea80
TEXT, DATA = (1, 6), (1, 3)  # (sh_type, sh_flags): PROGBITS AX / PROGBITS WA

# (name, start, end, kind)
layout = [
    ('.text',      0x200000, 0x416F80, TEXT),
    ('.data',      0x416F80, 0x437300, DATA),
    ('.text.init', 0x437300, 0x437E80, TEXT),
    ('.data2',     0x437E80, VA + FSZ, DATA),
]

phoff = struct.unpack_from('<I', d, 28)[0]
phnum = struct.unpack_from('<H', d, 44)[0]
phdrs = d[phoff:phoff + 32 * phnum]          # original program headers, verbatim
body = d[OFF:OFF + FSZ]
reginfo = d[0x23fd58:0x23fd58 + 0x18]

names = [n for n, *_ in layout] + ['.bss', '.shstrtab', '.reginfo']
shstr = b'\0'; idx = {}
for n in names:
    idx[n] = len(shstr); shstr += n.encode() + b'\0'

off_body = 0x100
off_reg = off_body + FSZ
off_shstr = off_reg + len(reginfo)
off_sh = (off_shstr + len(shstr) + 3) & ~3

def sec(n, t, f, a, o, s, al):
    return struct.pack('<10I', n, t, f, a, o, s, 0, 0, al, 0)

sh = sec(0, 0, 0, 0, 0, 0, 0)
for n, s, e, (t, f) in layout:
    sh += sec(idx[n], t, f, s, off_body + (s - VA), e - s, 16)
sh += sec(idx['.bss'], 8, 3, VA + FSZ, off_body + FSZ, MSZ - FSZ, 16)
sh += sec(idx['.shstrtab'], 3, 0, 0, off_shstr, len(shstr), 1)
sh += sec(idx['.reginfo'], 0x70000006, 2, 0, off_reg, len(reginfo), 4)
shnum = 1 + len(layout) + 3

eh = bytearray(d[:52])
struct.pack_into('<I', eh, 28, 52)                       # e_phoff
struct.pack_into('<I', eh, 32, off_sh)                   # e_shoff
struct.pack_into('<HHH', eh, 46, 40, shnum, shnum - 2)   # shentsize, shnum, shstrndx

out = bytearray(eh + phdrs)
out += b'\0' * (off_body - len(out))
out += body + reginfo + shstr
out += b'\0' * (off_sh - len(out))
out += sh
assert out[off_body:off_body + FSZ] == d[OFF:OFF + FSZ]
open(dst, 'wb').write(out)
for n, s, e, k in layout:
    print(f"{n:11} 0x{s:x}-0x{e:x}{'  (code)' if k == TEXT else ''}")
print(f"{'.bss':11} 0x{VA+FSZ:x}-0x{VA+MSZ:x}\n-> {dst}")

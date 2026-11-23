"""Add the 34 static constructors of SLUS_210.41 (pointer table at 0x437E80) to a PS2Recomp
config's entry_points, so each is recompiled as its own callable entry. Needed because three
of them (0x437450, 0x4376C0, 0x437990) are leaf functions with no prologue that are only
reached through the pointer table, and the analyzer merges them into the previous function.
Usage: python addctors.py SLUS_210.41 main.toml"""
import sys, struct, re
elf, cfg = sys.argv[1], sys.argv[2]
d = open(elf, 'rb').read()
W = lambda a: struct.unpack_from('<I', d, a - 0x200000 + 0x100)[0]
ctors = []
a = 0x437E80
while W(a): ctors.append(W(a)); a += 4
s = open(cfg, encoding='utf-8').read()
m = re.search(r'^entry_points\s*=\s*\[\n', s, re.M)
assert m, "entry_points not found"
have = {int(x, 16) for x in re.findall(r'@0x([0-9A-Fa-f]+)"', s)}
new = [c for c in ctors if c not in have]
ins = ''.join(f'  "static_ctor_{c:08X}@0x{c:08X}",\n' for c in new)
s = s[:m.end()] + ins + s[m.end():]
open(cfg, 'w', encoding='utf-8').write(s)
print(f"{len(ctors)} constructors in table, added {len(new)} entry points")

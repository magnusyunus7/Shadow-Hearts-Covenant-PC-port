"""Wrap very large PS2Recomp-generated function files in compiler pragmas that disable
optimisation for that file only. Functions whose jump tables could not be resolved get an
entry label on every instruction; optimising such a function can take hours or exhaust
memory (MSVC C1002). Only files at or above the size threshold are touched; re-running is safe.
Usage: python deopt_huge.py <generated_output_dir> [min_megabytes=1.0]"""
import os, sys
d = sys.argv[1]; mb = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
HEAD = ('// deopt_huge: optimisation disabled for this oversized generated function\n'
        '#if defined(_MSC_VER)\n#pragma optimize("", off)\n'
        '#elif defined(__GNUC__) && !defined(__clang__)\n#pragma GCC push_options\n#pragma GCC optimize("O0")\n'
        '#elif defined(__clang__)\n#pragma clang optimize off\n#endif\n')
TAIL = ('\n#if defined(_MSC_VER)\n#pragma optimize("", on)\n'
        '#elif defined(__GNUC__) && !defined(__clang__)\n#pragma GCC pop_options\n'
        '#elif defined(__clang__)\n#pragma clang optimize on\n#endif\n')
n = 0
for f in sorted(os.listdir(d)):
    p = os.path.join(d, f)
    if not ((f.startswith('sub_') or f.startswith('zz_ovl_')) and '_sub_' in '_'+f and f.endswith('.cpp')) or os.path.getsize(p) < mb * 1024 * 1024:
        continue
    s = open(p, encoding='utf-8').read()
    if s.startswith('// deopt_huge'):
        continue
    # Insert just before the function's '// Address:' header comment, i.e. after all includes and
    # preprocessor blocks, so headers keep their normal optimisation.
    lines = s.split('\n')
    at = next((i for i, l in enumerate(lines) if l.startswith('// Address:')), None)
    if at is None:
        print(f"  skip (no '// Address:' marker): {f}"); continue
    s = '\n'.join(lines[:at]) + '\n' + HEAD + '\n'.join(lines[at:]) + TAIL
    s = '// deopt_huge\n' + s
    open(p, 'w', encoding='utf-8').write(s); n += 1
    print(f"{os.path.getsize(p)/1048576:6.1f} MB  {f}")
print(f"{n} file(s) updated")

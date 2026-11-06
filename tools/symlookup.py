# main.sym からアドレス→シンボル逆引きツール
# 使い方: python symlookup.py 143D 1475 ...
import re, sys

sym_path = r'c:\tools\mz1500action\src\sideb\main.sym'
addr = {}
for line in open(sym_path, encoding='utf-8', errors='replace'):
    m = re.match(r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\$([0-9A-Fa-f]+)', line)
    if m:
        addr[int(m.group(2), 16)] = m.group(1)

print('symbols:', len(addr))
for arg in sys.argv[1:]:
    t = int(arg, 16)
    lo = [k for k in addr if k <= t][-4:]
    hi = [k for k in addr if t < k <= t + 48][:5]
    print(f'--- {hex(t)} ---')
    print('  before:', [(hex(k), addr[k]) for k in lo])
    print('  after :', [(hex(k), addr[k]) for k in hi])

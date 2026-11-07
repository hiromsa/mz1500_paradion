import re
import sys

# Compare the code region in RAM after the run with the built sideb.bin
# (the emulator --dump prints "Memory dump XXXXh-YYYYh:" followed by lines
#  "XXXX: hh hh ...  ascii").
def parse_dump(path):
    dump = {}
    start = None
    with open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
        for line in f:
            m = re.match(r'^Memory dump ([0-9A-Fa-f]{4})h', line)
            if m:
                start = int(m.group(1), 16)
                continue
            m = re.match(r'^([0-9A-Fa-f]{4}): ((?:[0-9A-Fa-f]{2} )+[0-9A-Fa-f]{2}|(?:[0-9A-Fa-f]{2} )+)', line)
            if m:
                addr = int(m.group(1), 16)
                hexpart = m.group(2).split()
                vals = [int(v, 16) for v in hexpart]
                for i, v in enumerate(vals):
                    dump[addr + i] = v
    return dump

binpath = r'c:\tools\mz1500action\out\sideb.bin'
logpath = sys.argv[1] if len(sys.argv) > 1 else r'c:\tools\mz1500action\tmp\coderun.log'

body = open(binpath, 'rb').read()
LOAD = 0x1200
dump = parse_dump(logpath)

print(f'sideb.bin: {len(body)} bytes (load 1200h -> {LOAD + len(body):04X}h)')
print(f'dump: {len(dump)} bytes captured ({min(dump):04X}h-{max(dump):04X}h)')

diffs = 0
for i, expected in enumerate(body):
    addr = LOAD + i
    if addr in dump and dump[addr] != expected:
        diffs += 1
        if diffs <= 40:
            print(f'DIFF {addr:04X}h: expected {expected:02X}h, RAM has {dump[addr]:02X}h')
missing = sum(1 for i in range(len(body)) if (LOAD + i) not in dump)
print(f'total diffs in code region: {diffs}, bytes missing from dump: {missing}')

"""QDF (.qdf) block parser - MZ-1500 QuickDisk raw image (CSP compatible).

SYNC = 0x16. Block: SYNC*8 + A5 + flag + size(L,H) + data... + CRC(L,H) + SYNC*4.
BLOCK-FILE (first): A5 + count(1B) + CRC(2B).
CRC-16/ARC: poly 0xA001 (reflected), init 0, applied to A5..data end, stored LE.
"""
import struct, sys, os

SYNC = 0x16

def crc16_arc(data):
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc

def parse_qdf(path, outdir):
    data = open(path, 'rb').read()
    print(f'== {path} ({len(data)} bytes)')
    pos = 2700
    n = 0
    total = None
    files = []          # (name, attr, size, load, exec)
    curfile = None
    payloadidx = 0
    while pos < len(data) - 8:
        if data[pos] == 0xA5 and all(data[pos-1-k] == SYNC for k in range(4)):
            if total is None:
                count = data[pos+1]
                crc_st = data[pos+2] | (data[pos+3] << 8)
                calc = crc16_arc(data[pos:pos+2])
                print(f'   BLOCK-FILE @0x{pos:04X}: total_blocks={count} (0x{count:02X}) crc_stored=0x{crc_st:04X} calc=0x{calc:04X} {"OK" if crc_st==calc else "NG"}')
                total = count
                pos += 4
            else:
                flag = data[pos+1]
                size = data[pos+2] | (data[pos+3] << 8)
                end = pos + 4 + size
                if end + 2 > len(data):
                    print(f'   block @0x{pos:04X}: flag=0x{flag:02X} size={size} TRUNCATED, stop')
                    break
                payload = data[pos+4:end]
                crc_st = data[end] | (data[end+1] << 8)
                calc = crc16_arc(data[pos:end])
                ok = 'OK' if crc_st == calc else f'NG(calc 0x{calc:04X})'
                if size == 64 and flag == 0:
                    attr = payload[0]
                    name = bytes([payload[1]]).decode('ascii', 'replace') + payload[2:18].split(b'\x00')[0].decode('ascii', 'replace').rstrip('\r')
                    lock, secret = payload[18], payload[19]
                    fsize, load, ex = struct.unpack('<HHH', payload[20:26])
                    print(f'   hdr   @0x{pos:04X}: flag=0x{flag:02X} size=64 crc=0x{crc_st:04X} {ok}')
                    print(f'      file: attr=0x{attr:02X} name={name!r} size={fsize}(0x{fsize:04X}) load=0x{load:04X} exec=0x{ex:04X}')
                    curfile = name
                    payloadidx = 0
                else:
                    print(f'   data  @0x{pos:04X}: flag=0x{flag:02X} size={size} crc=0x{crc_st:04X} {ok}')
                    fn = os.path.join(outdir, f'{os.path.basename(path)}_{payloadidx:02d}.bin')
                    with open(fn, 'wb') as f:
                        f.write(payload)
                    print(f'      -> {fn}')
                    payloadidx += 1
                n += 1
                p2 = end + 2
                while p2 < len(data) and data[p2] == SYNC:
                    p2 += 1
                pos = p2
        else:
            pos += 1
    print(f'   {n} data/hdr blocks parsed')

outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'parsed')
os.makedirs(outdir, exist_ok=True)
for p in sys.argv[1:]:
    parse_qdf(p, outdir)


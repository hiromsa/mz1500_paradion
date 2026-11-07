import struct

path = r'c:\tools\mz1500action\out\ParadionB.mzt'
data = open(path, 'rb').read()
print(f'file size: {len(data)}')
hdr = data[:0x80]
name = hdr[0:17].rstrip(b'\x0d')
size, load, ex = struct.unpack('<HHH', hdr[0x12:0x18])
print(f'name={name!r} size={size} (0x{size:04X}) load=0x{load:04X} exec=0x{ex:04X}')
body = data[0x80:0x80 + size]
print(f'body bytes: {len(body)}')

# find read_keys: first strobe store 32 00 E0 followed later by ret
pats = {
    'ld(B0E9),a': b'\x32\xe9\xb0',
    'ld(B0EA),a': b'\x32\xea\xb0',
    'ld(B0EB),a': b'\x32\xeb\xb0',
    'ld(B0EC),a': b'\x32\xec\xb0',
    'ld(B0ED),a': b'\x32\xed\xb0',
    'ld(B0EE),a': b'\x32\xee\xb0',
    'ld(B001),a (W_KEYS)': b'\x32\x01\xb0',
    'ld(E000),a (strobe)': b'\x32\x00\xe0',
}
for nm, p in pats.items():
    hits = []
    i = body.find(p)
    while i >= 0 and len(hits) < 8:
        hits.append(hex(load + i))
        i = body.find(p, i + 1)
    print(f'{nm:22s} {hits}')

# hexdump of read_keys region (first strobe store -8 .. +0x100)
i = body.find(b'\x32\x00\xe0')
if i >= 0:
    start = max(0, i - 8)
    end = min(len(body), i + 0x110)
    print(f'--- read_keys hexdump (org {load+start:04X}h) ---')
    for off in range(start, end, 16):
        chunk = body[off:off + 16]
        hexs = ' '.join(f'{b:02X}' for b in chunk)
        print(f'{load + off:04X}: {hexs}')

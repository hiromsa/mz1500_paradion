import struct, sys, os

def parse_mzt(path, outdir):
    data = open(path, 'rb').read()
    pos = 0
    idx = 0
    os.makedirs(outdir, exist_ok=True)
    while pos + 128 <= len(data):
        hdr = data[pos:pos+128]
        attr = hdr[0]
        name = hdr[1:18].split(b'\x00')[0].decode('ascii', 'replace')
        size, load, ex = struct.unpack('<HHH', hdr[0x12:0x18])
        body = data[pos+128:pos+128+size]
        print(f'file[{idx}] attr=0x{attr:02X} name={name!r} size={size} (0x{size:04X}) load=0x{load:04X} exec=0x{ex:04X}')
        with open(os.path.join(outdir, f'f{idx}_{name.replace(" ","_")}.bin'), 'wb') as f:
            f.write(body)
        pos += 128 + size
        idx += 1
    print(f'total {idx} files, {pos}/{len(data)} bytes')

parse_mzt(sys.argv[1], sys.argv[2])

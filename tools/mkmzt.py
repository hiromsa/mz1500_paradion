"""MZT (.mzt) tape image builder for the MZ-1500.

128-byte header: attr(1) + name(17, 0Dh pad) + size/load/exec (LE 16-bit x3 at 0x12)
+ comment area (zeros). Body follows.
Usage: python tools/mkmzt.py --name "PARADION A" --load 2000 --exec 2000 -o out.mzt body.bin
"""
import argparse
import struct


def build(name: str, load: int, ex: int, body: bytes) -> bytes:
    header = bytearray(128)
    header[0] = 0x01                       # attr: MZ machine code
    name_bytes = name.encode('ascii')[:16]
    header[1:1 + len(name_bytes)] = name_bytes
    for i in range(len(name_bytes), 17):   # 0Dh padding like real MZ tapes
        header[1 + i] = 0x0D
    struct.pack_into('<HHH', header, 0x12, len(body), load, ex)
    header[0x3E] = 0                       # lock
    header[0x3F] = 0                       # secret
    return bytes(header) + body


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', required=True)
    ap.add_argument('--load', required=True, type=lambda x: int(x, 16))
    ap.add_argument('--exec', required=True, type=lambda x: int(x, 16))
    ap.add_argument('-o', '--out', required=True)
    ap.add_argument('body')
    args = ap.parse_args()

    with open(args.body, 'rb') as f:
        body = f.read()
    image = build(args.name, args.load, args.exec, body)
    with open(args.out, 'wb') as f:
        f.write(image)
    print(f'{args.out}: name={args.name!r} size={len(body)} (0x{len(body):04X}) '
          f'load=0x{args.load:04X} exec=0x{args.exec:04X}')


if __name__ == '__main__':
    main()

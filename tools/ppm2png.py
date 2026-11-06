# PPM -> PNG 変換 (2x 拡大オプション付き観察ツール)
import sys, os
from PIL import Image

def read_ppm(path):
    with open(path, 'rb') as f:
        data = f.read()
    # P6 ヘッダ解析 (コメント対応)
    assert data[:2] == b'P6', 'not P6 ppm'
    idx = 2
    vals = []
    while len(vals) < 3:
        # skip whitespace/comments
        while idx < len(data) and data[idx:idx+1].isspace():
            idx += 1
        if data[idx:idx+1] == b'#':
            while idx < len(data) and data[idx] != 10:
                idx += 1
            continue
        start = idx
        while idx < len(data) and not data[idx:idx+1].isspace():
            idx += 1
        vals.append(int(data[start:idx]))
    w, h, maxv = vals
    idx += 1  # 単一空白
    img = Image.frombytes('RGB', (w, h), data[idx:idx + w*h*3])
    return img

if __name__ == '__main__':
    scale = 2
    args = sys.argv[1:]
    if args and args[0] == '-s':
        scale = int(args[1]); args = args[2:]
    for p in args:
        img = read_ppm(p)
        if scale > 1:
            img = img.resize((img.width*scale, img.height*scale), Image.NEAREST)
        out = os.path.splitext(p)[0] + '.png'
        img.save(out)
        print(out, img.size)

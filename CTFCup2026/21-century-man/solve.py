#!/usr/bin/env python3
"""Recover the coordinate cloud embedded in the original iCE40 bitstream."""
import csv
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BITSTREAM = ROOT / 'g.bin'
OUT = ROOT / 'artifacts'
# Logical 16-bit word uses the bit-reversed four-bit memory lane index.
LANE = [0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15]
# Pairs found by tracing the two coordinate selector trees; indices refer to
# 256x16 ROMs in the order emitted by icebox_vlog.
PAIRS = [(1,22), (21,4), (2,14), (15,18), (9,23), (13,20), (5,12),
         (0,24), (19,6), (3,8), (17,16), (11,25), (7,10)]

def signed_word(physical):
    v = sum(((physical >> lane) & 1) << bit for bit, lane in enumerate(LANE))
    return v - 65536 if v >= 32768 else v

def main():
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        asc = Path(tmp) / 'g.asc'
        subprocess.run(['iceunpack', str(BITSTREAM), str(asc)], check=True)
        v = subprocess.run(['icebox_vlog','-s','-l','-d','sg48',str(asc)],
                           check=True, capture_output=True, text=True).stdout
    roms = []
    pattern = r'SB_RAM40_4K #\((.*?)\) (\w+) \((.*?)\n\);'
    for m in re.finditer(pattern, v, re.S):
        params, name, ports = m.groups()
        if 'n346, n352, n315, n347, n427, n350, n64, n351' not in ports:
            continue
        blocks = re.findall(r"INIT_[0-9A-F]\(256'h([0-9a-f]+)\)",params)
        if len(blocks) != 16:
            raise ValueError(f'invalid initialization on {name}')
        words = [signed_word((int(block, 16) >> (16*i)) & 0xffff)
                 for block in blocks for i in range(16)]
        roms.append(words)
    if len(roms) != 26:
        raise ValueError(f'expected 26 coordinate ROMs, got {len(roms)}')
    points = [(roms[x][i], roms[y][i]) for y,x in PAIRS for i in range(256)]
    # The selector order puts poles in pair (13,20) and addresses 124..255
    # of pair (7,10). The transition was checked against the UART simulator.
    zeros = [(roms[x][i], roms[y][i]) for y,x in PAIRS if (y,x)!=(13,20)
             for i in range(124 if (y,x)==(7,10) else 256)]
    csv_path = OUT / 'coordinates.csv'
    with csv_path.open('w', newline='') as f:
        w=csv.writer(f); w.writerow(['x_q12','y_q12']); w.writerows(points)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(8, 1, figsize=(20, 16))
    for i,ax in enumerate(axes):
        ax.scatter([p[0] for p in zeros], [p[1] for p in zeros], s=3, c='black')
        ax.set_xlim(-16000 + 4000*i, -12000 + 4000*i)
        ax.set_ylim(-500, 500); ax.set_aspect('equal'); ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(OUT/'recovered.png', dpi=160)
    print(f'{len(points)} coordinate pairs: {csv_path}')
    print(f'Visualization: {OUT / "recovered.png"}')
if __name__ == '__main__':
    main()

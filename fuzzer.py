"""Toy altitude packet: magic byte A5, then unsigned big-endian meters, 0..500."""
import random
import struct
from collections import Counter
from pathlib import Path

def legacy(packet):
    magic, altitude = struct.unpack('>BH', packet)
    return altitude

def patched(packet):
    if len(packet) != 3 or packet[0] != 0xa5:
        return None
    altitude = int.from_bytes(packet[1:], 'big')
    return altitude if altitude <= 500 else None

def cases():
    rng = random.Random(42)
    for _ in range(2000):
        altitude = rng.randrange(501)
        valid = struct.pack('>BH', 165, altitude)
        yield 'Valid (including 0 and 500)', valid, altitude
        yield 'Truncated', valid[:rng.randrange(3)], None
        yield 'Trailing bytes', valid + rng.randbytes(rng.randint(1,8)), None
        yield 'Wrong magic', bytes([rng.randrange(165)]) + valid[1:], None
        yield 'Above ceiling', struct.pack('>BH',165,rng.choice([501,65535,rng.randint(501,65535)])), None

def main():
    counts = Counter()
    for kind, packet, expected in cases():
        for name,parse in [('Legacy',legacy),('Patched',patched)]:
            try:
                outcome = 'correct' if parse(packet) == expected else 'wrong'
            except struct.error:
                outcome = 'exception'
            counts[kind,name,outcome] += 1
    rows = ['# Packet campaign','Seed 42 · 10,000 inputs per parser. An escaped exception would stop an unguarded receive loop.','','| Input | Parser | Correct | Invalid accepted | Escaped exception |','|---|---|---:|---:|---:|']
    for kind,name in dict.fromkeys((k,n) for k,n,_ in counts):
        rows.append(f'| {kind} | {name} | ' + ' | '.join(str(counts[kind,name,o]) for o in ['correct','wrong','exception'])+' |')
    Path('fuzz-report.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
if __name__ == '__main__':
    main()

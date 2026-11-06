# Packet campaign
Seed 42 · 10,000 inputs per parser. An escaped exception would stop an unguarded receive loop.

| Input | Parser | Correct | Invalid accepted | Escaped exception |
|---|---|---:|---:|---:|
| Valid (including 0 and 500) | Legacy | 2000 | 0 | 0 |
| Valid (including 0 and 500) | Patched | 2000 | 0 | 0 |
| Truncated | Legacy | 0 | 0 | 2000 |
| Truncated | Patched | 2000 | 0 | 0 |
| Trailing bytes | Legacy | 0 | 0 | 2000 |
| Trailing bytes | Patched | 2000 | 0 | 0 |
| Wrong magic | Legacy | 0 | 2000 | 0 |
| Wrong magic | Patched | 2000 | 0 | 0 |
| Above ceiling | Legacy | 0 | 2000 | 0 |
| Above ceiling | Patched | 2000 | 0 | 0 |

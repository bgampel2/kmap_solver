from kmap import KMap
from solver import solve

k = KMap(4)
# Set minterms 0, 1, 2, 3 to 1 — should simplify to A'B'
for minterm in [0, 1, 2, 3]:
    k.cells[minterm] = 1

print(solve(k))  # expected: A'B'
# solver.py

from itertools import combinations

VAR_NAMES = ['A', 'B', 'C', 'D']

def get_prime_implicants(ones, dont_cares, num_vars):
    """Find all prime implicants using the Quine-McCluskey method."""
    all_terms = set(ones) | set(dont_cares)
    
    # Each implicant is (frozenset of minterms it covers, mask of fixed bits)
    # We represent each group as a set of minterms
    implicants = [frozenset([m]) for m in all_terms]
    prime_implicants = set()
    
    def can_combine(a, b):
        """Two groups can combine if their minterms differ by exactly one bit pattern."""
        # Get representative minterms
        a_list = sorted(a)
        b_list = sorted(b)
        if len(a_list) != len(b_list):
            return False
        # XOR each pair - all should be the same power of 2
        xors = [x ^ y for x, y in zip(a_list, b_list)]
        return len(set(xors)) == 1 and (xors[0] & (xors[0] - 1)) == 0

    def combine(a, b):
        return a | b

    current_level = implicants
    while current_level:
        next_level = []
        used = set()
        for i, a in enumerate(current_level):
            for j, b in enumerate(current_level):
                if i >= j:
                    continue
                if can_combine(a, b):
                    combined = combine(a, b)
                    if combined not in next_level:
                        next_level.append(combined)
                    used.add(i)
                    used.add(j)
        # Any implicant that wasn't combined is a prime implicant
        for i, imp in enumerate(current_level):
            if i not in used:
                # Only keep if it covers at least one 'one' (not just dont-cares)
                if imp & set(ones):
                    prime_implicants.add(imp)
        current_level = next_level

    return list(prime_implicants)


def find_minimal_cover(prime_implicants, ones):
    """Select the minimum set of prime implicants that covers all ones."""
    ones_set = set(ones)
    essential = []
    covered = set()

    # Find essential prime implicants (the only one covering a minterm)
    for minterm in ones_set:
        covering = [pi for pi in prime_implicants if minterm in pi]
        if len(covering) == 1:
            if covering[0] not in essential:
                essential.append(covering[0])
                covered |= covering[0]

    # Cover any remaining minterms with largest available groups
    remaining = ones_set - covered
    remaining_pis = [pi for pi in prime_implicants if pi not in essential]
    remaining_pis.sort(key=len, reverse=True)

    while remaining:
        best = max(remaining_pis, key=lambda pi: len(pi & remaining))
        essential.append(best)
        covered |= best
        remaining -= best
        remaining_pis.remove(best)

    return essential


def implicant_to_term(implicant, num_vars):
    """Convert a set of minterms to a Boolean term string like AB'C."""
    minterms = sorted(implicant)
    term = []
    for bit in range(num_vars - 1, -1, -1):
        values = set((m >> bit) & 1 for m in minterms)
        var = VAR_NAMES[num_vars - 1 - bit]
        if len(values) == 1:
            if values == {1}:
                term.append(var)
            else:
                term.append(var + "'")
        # If both 0 and 1 appear, the variable is eliminated
    return ''.join(term) if term else '1'


def solve(kmap):
    ones = kmap.get_ones()
    dont_cares = kmap.get_dont_cares()

    if not ones:
        return '0'

    prime_implicants = get_prime_implicants(ones, dont_cares, kmap.num_vars)
    cover = find_minimal_cover(prime_implicants, ones)
    terms = [implicant_to_term(pi, kmap.num_vars) for pi in cover]
    return ' + '.join(terms)

def solve_with_groups(kmap):
    """Returns (expression_string, list of groups as sets of (row,col) tuples)."""
    ones = kmap.get_ones()
    dont_cares = kmap.get_dont_cares()

    if not ones:
        return '0', []

    prime_implicants = get_prime_implicants(ones, dont_cares, kmap.num_vars)
    cover = find_minimal_cover(prime_implicants, ones)
    terms = [implicant_to_term(pi, kmap.num_vars) for pi in cover]
    expression = ' + '.join(terms)

    # Convert each prime implicant (set of minterms) to set of (row, col)
    reverse_map = {v: k for k, v in kmap.index_map.items()}
    groups = []
    for pi in cover:
        cells = {reverse_map[m] for m in pi if m in reverse_map}
        groups.append(cells)

    return expression, groups
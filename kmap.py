# kmap.py

# Gray code ordering for K-map axes
GRAY_2 = [0, 1]
GRAY_4 = [0, 1, 3, 2]  # 00, 01, 11, 10

# Maps (row, col) -> minterm index for each variable count
def build_index_map(num_vars):
    if num_vars == 2:
        # 2 vars: 1 row var, 1 col var -> 2x2 grid
        row_codes = GRAY_2  # A
        col_codes = GRAY_2  # B
    elif num_vars == 3:
        row_codes = GRAY_4  # AB
        col_codes = GRAY_2  # C
    elif num_vars == 4:
        # 4 vars: 2 row vars, 2 col vars -> 4x4 grid
        row_codes = GRAY_4  # AB
        col_codes = GRAY_4  # CD

    index_map = {}
    for r, row_val in enumerate(row_codes):
        for c, col_val in enumerate(col_codes):
            minterm = (row_val << (num_vars // 2)) | col_val
            index_map[(r, c)] = minterm

    return index_map


class KMap:
    def __init__(self, num_vars=4):
        self.num_vars = num_vars
        self.num_minterms = 2 ** num_vars
        # Cell values: 0, 1, or 'X'
        self.cells = {i: 0 for i in range(self.num_minterms)}
        self.index_map = build_index_map(num_vars)

    def set_cell(self, row, col, value):
        minterm = self.index_map[(row, col)]
        self.cells[minterm] = value

    def get_cell(self, row, col):
        minterm = self.index_map[(row, col)]
        return self.cells[minterm]

    def get_ones(self):
        return [m for m, v in self.cells.items() if v == 1]

    def get_dont_cares(self):
        return [m for m, v in self.cells.items() if v == 'X']

    def grid_size(self):
        if self.num_vars == 2:
            return (2, 2)
        elif self.num_vars == 3:
            return (4, 2)
        elif self.num_vars == 4:
            return (4, 4)
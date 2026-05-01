import tkinter as tk
from kmap import KMap
from solver import solve, solve_with_groups

CELL_SIZE = 80
PADDING = 40

VAR_LABELS_4 = {
    'row_vars': 'AB',
    'col_vars': 'CD',
    'row_headers': ["00", "01", "11", "10"],
    'col_headers': ["00", "01", "11", "10"],
}

VAR_LABELS_3 = {
    'row_vars': 'AB',
    'col_vars': 'C',
    'row_headers': ["00", "01", "11", "10"],
    'col_headers': ["0", "1"],
}

VAR_LABELS_2 = {
    'row_vars': 'A',
    'col_vars': 'B',
    'row_headers': ["0", "1"],
    'col_headers': ["0", "1"],
}

GROUP_COLORS = [
    '#FF6B6B',  # red
    '#4ECDC4',  # teal
    '#FFD93D',  # yellow
    '#6C5CE7',  # purple
    '#FF8B94',  # pink
    '#2ECC71',  # green
    '#E67E22',  # orange
    '#3498DB',  # blue
]

THEMES = {
    'light': {
        'bg': '#F0F0F0',
        'canvas_bg': 'white',
        'text': 'black',
        'subtext': '#888888',
        'cell_0': 'white',
        'cell_1': '#90EE90',
        'cell_X': '#D3D3D3',
    },
    'dark': {
        'bg': '#1E1E1E',
        'canvas_bg': '#2D2D2D',
        'text': 'white',
        'subtext': '#AAAAAA',
        'cell_0': '#3C3C3C',
        'cell_1': '#2E7D32',
        'cell_X': '#555555',
    }
}

class KMapGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("K-Map Solver")
        self.num_vars = tk.IntVar(value=4)
        self.kmap = KMap(4)
        self.theme = 'light'
        self._build_ui()

    def _build_ui(self):
        # 1. Variable selector
        control_frame = tk.Frame(self.root, pady=10)
        control_frame.pack()

        tk.Label(control_frame, text="Variables:").pack(side=tk.LEFT, padx=5)
        for v in [2, 3, 4]:
            tk.Radiobutton(
                control_frame, text=str(v),
                variable=self.num_vars, value=v,
                command=self._on_var_change
            ).pack(side=tk.LEFT)

        # Theme toggle
        toggle_frame = tk.Frame(self.root)
        toggle_frame.pack(pady=2)
        self.theme_btn = tk.Button(
            toggle_frame, text="🌙 Dark Mode",
            command=self._toggle_theme, padx=10
        )
        self.theme_btn.pack()

        # Minterm input
        minterm_frame = tk.Frame(self.root, pady=5)
        minterm_frame.pack()

        tk.Label(minterm_frame, text="Minterms:").pack(side=tk.LEFT, padx=5)
        self.minterm_entry = tk.Entry(minterm_frame, width=20)
        self.minterm_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(minterm_frame, text="Don't cares:").pack(side=tk.LEFT, padx=5)
        self.dc_entry = tk.Entry(minterm_frame, width=20)
        self.dc_entry.pack(side=tk.LEFT, padx=5)

        tk.Button(
            minterm_frame, text="Load",
            command=self._on_load_minterms
        ).pack(side=tk.LEFT, padx=5)

        # 2. Canvas (grid)
        self.canvas = tk.Canvas(self.root, bg='white')
        self.canvas.pack(padx=20, pady=10)
        self.canvas.bind("<Button-1>", self._on_click)

        # 3. Result label
        self.result_var = tk.StringVar(value="")
        tk.Label(
            self.root, textvariable=self.result_var,
            font=('Arial', 14), pady=10
        ).pack()

        # 4. Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)

        tk.Button(
            button_frame, text="Solve", font=('Arial', 12, 'bold'),
            command=self._on_solve, bg='#4CAF50', fg='white', padx=20
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            button_frame, text="Clear", font=('Arial', 12, 'bold'),
            command=self._on_reset, bg='#F44336', fg='white', padx=20
        ).pack(side=tk.LEFT, padx=10)

        self._draw_grid()

    def _get_color_map(self):
        t = THEMES[self.theme]
        return {
            0: t['cell_0'],
            1: t['cell_1'],
            'X': t['cell_X']
        }

    def _on_load_minterms(self):
        self.kmap = KMap(self.num_vars.get())
        max_minterm = 2 ** self.num_vars.get() - 1

        try:
            minterm_text = self.minterm_entry.get().strip()
            ones = [int(x.strip()) for x in minterm_text.split(',') if x.strip()]

            dc_text = self.dc_entry.get().strip()
            dont_cares = [int(x.strip()) for x in dc_text.split(',') if x.strip()]

            for m in ones + dont_cares:
                if m < 0 or m > max_minterm:
                    raise ValueError(f"{m} is out of range for {self.num_vars.get()} variables")
            if set(ones) & set(dont_cares):
                raise ValueError("A minterm can't be both a 1 and a don't care")

            for m in ones:
                self.kmap.cells[m] = 1
            for m in dont_cares:
                self.kmap.cells[m] = 'X'

            self.canvas.delete('group')
            self.result_var.set("")
            self._draw_grid()

        except ValueError as e:
            self.result_var.set(f"Error: {e}")

    def _on_reset(self):
        self.kmap = KMap(self.num_vars.get())
        self.canvas.delete('group')
        self.result_var.set("")
        self._draw_grid()

    def _on_var_change(self):
        self.kmap = KMap(self.num_vars.get())
        self.result_var.set("")
        self._draw_grid()

    def _get_labels(self):
        n = self.num_vars.get()
        if n == 4: return VAR_LABELS_4
        if n == 3: return VAR_LABELS_3
        return VAR_LABELS_2

    def _draw_grid(self):
        self.canvas.delete("all")
        rows, cols = self.kmap.grid_size()
        labels = self._get_labels()
        t = THEMES[self.theme]
        color_map = self._get_color_map()

        # Resize canvas
        width = PADDING * 2 + cols * CELL_SIZE + 40
        height = PADDING * 2 + rows * CELL_SIZE + 40
        self.canvas.config(width=width, height=height, bg=t['canvas_bg'],
                           highlightbackground=t['bg'])

        # Draw variable labels
        self.canvas.create_text(
            PADDING + cols * CELL_SIZE // 2 + 20, 15,
            text=labels['col_vars'], font=('Arial', 12, 'bold'), fill=t['text']
        )
        self.canvas.create_text(
            15, PADDING + rows * CELL_SIZE // 2 + 20,
            text=labels['row_vars'], font=('Arial', 12, 'bold'), fill=t['text']
        )

        # Draw column headers
        for c, header in enumerate(labels['col_headers']):
            x = PADDING + 40 + c * CELL_SIZE + CELL_SIZE // 2
            self.canvas.create_text(x, PADDING, text=header,
                                    font=('Arial', 10), fill=t['text'])

        # Draw row headers
        for r, header in enumerate(labels['row_headers']):
            y = PADDING + 40 + r * CELL_SIZE + CELL_SIZE // 2
            self.canvas.create_text(PADDING, y, text=header,
                                    font=('Arial', 10), fill=t['text'])

        # Draw cells
        self.cell_rects = {}
        self.cell_texts = {}
        for r in range(rows):
            for c in range(cols):
                x1 = PADDING + 40 + c * CELL_SIZE
                y1 = PADDING + 40 + r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                value = self.kmap.get_cell(r, c)
                color = color_map[value]
                rect = self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline='black', width=2
                )
                text = self.canvas.create_text(
                    x1 + CELL_SIZE // 2, y1 + CELL_SIZE // 2,
                    text=str(value) if value != 'X' else 'X',
                    font=('Arial', 16, 'bold'), fill=t['text']
                )
                minterm = self.kmap.index_map[(r, c)]
                self.canvas.create_text(
                    x1 + 16, y1 + 16,
                    text=f'm{minterm}',
                    font=('Arial', 8),
                    fill=t['subtext']
                )
                self.cell_rects[(r, c)] = rect
                self.cell_texts[(r, c)] = text

    def _on_click(self, event):
        rows, cols = self.kmap.grid_size()
        col = (event.x - PADDING - 40) // CELL_SIZE
        row = (event.y - PADDING - 40) // CELL_SIZE
        if 0 <= row < rows and 0 <= col < cols:
            current = self.kmap.get_cell(row, col)
            next_val = {0: 1, 1: 'X', 'X': 0}[current]
            self.kmap.set_cell(row, col, next_val)
            color_map = self._get_color_map()
            self.canvas.itemconfig(
                self.cell_rects[(row, col)],
                fill=color_map[next_val]
            )
            self.canvas.itemconfig(
                self.cell_texts[(row, col)],
                text=str(next_val) if next_val != 'X' else 'X'
            )
            self.canvas.delete('group')
            self.result_var.set("")

    def _on_solve(self):
        self.canvas.delete('group')
        result, groups = solve_with_groups(self.kmap)
        self.result_var.set(f"Result:  {result}")
        self._draw_groups(groups)

    def _draw_groups(self, groups):
        rows, cols = self.kmap.grid_size()
        for i, group in enumerate(groups):
            color = GROUP_COLORS[i % len(GROUP_COLORS)]
            self._draw_group(group, color, rows, cols)

    def _draw_group(self, group, color, rows, cols):
        group_rows = sorted(set(r for r, c in group))
        group_cols = sorted(set(c for r, c in group))

        row_wrap = self._is_wrapped(group_rows, rows)
        col_wrap = self._is_wrapped(group_cols, cols)

        row_segments = self._get_segments(group_rows, rows, row_wrap)
        col_segments = self._get_segments(group_cols, cols, col_wrap)

        for r_seg in row_segments:
            for c_seg in col_segments:
                self._draw_rect(r_seg, c_seg, color)

    def _is_wrapped(self, indices, size):
        return 0 in indices and (size - 1) in indices and len(indices) < size

    def _get_segments(self, indices, size, wrapped):
        if not wrapped:
            return [indices]
        low = [i for i in indices if i == 0]
        high = [i for i in indices if i == size - 1]
        return [low, high]

    def _draw_rect(self, row_indices, col_indices, color):
        if not row_indices or not col_indices:
            return
        OFFSET = 4
        x1 = PADDING + 40 + min(col_indices) * CELL_SIZE + OFFSET
        y1 = PADDING + 40 + min(row_indices) * CELL_SIZE + OFFSET
        x2 = PADDING + 40 + (max(col_indices) + 1) * CELL_SIZE - OFFSET
        y2 = PADDING + 40 + (max(row_indices) + 1) * CELL_SIZE - OFFSET

        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline=color, width=3, fill='', tags='group'
        )

    def _toggle_theme(self):
        self.theme = 'dark' if self.theme == 'light' else 'light'
        self.theme_btn.config(
            text="☀️ Light Mode" if self.theme == 'dark' else "🌙 Dark Mode"
        )
        self._apply_theme()
        self._draw_grid()

    def _apply_theme(self):
        t = THEMES[self.theme]
        self.root.config(bg=t['bg'])
        self.canvas.config(bg=t['canvas_bg'], highlightbackground=t['bg'])
        for widget in self.root.winfo_children():
            self._apply_theme_to_widget(widget, t)

    def _apply_theme_to_widget(self, widget, t):
        widget_type = widget.winfo_class()
        try:
            if widget_type == 'Frame':
                widget.config(bg=t['bg'])
            elif widget_type == 'Label':
                widget.config(bg=t['bg'], fg=t['text'])
            elif widget_type == 'Radiobutton':
                widget.config(bg=t['bg'], fg=t['text'],
                              selectcolor=t['bg'],
                              activebackground=t['bg'],
                              activeforeground=t['text'])
            elif widget_type == 'Entry':
                widget.config(bg=t['cell_0'], fg=t['text'],
                              insertbackground=t['text'])
            elif widget_type == 'Button':
                # Don't restyle Solve/Clear, they have their own colors
                if widget.cget('text') not in ('Solve', 'Clear'):
                    widget.config(bg=t['bg'], fg=t['text'],
                                  activebackground=t['cell_0'],
                                  activeforeground=t['text'])
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._apply_theme_to_widget(child, t)


if __name__ == "__main__":
    root = tk.Tk()
    app = KMapGUI(root)
    root.mainloop()
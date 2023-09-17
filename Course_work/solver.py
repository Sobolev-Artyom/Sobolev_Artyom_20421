coordinates = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
for i in range(1, 4):
    coordinates.append((i, i))
    coordinates.append((i, -i))
    coordinates.append((-i, i))
    coordinates.append((-i, -i))


class ChessBoard:
    def __init__(self, n_cells):
        self.n_cells = n_cells
        self.board = [[0 for i in range(n_cells)] for j in range(n_cells)]
        self.is_piece = [[False for i in range(n_cells)] for j in range(n_cells)]
        self.remaining_cells = n_cells ** 2

    def get_pieces_coordinates(self):
        pieces = []
        for i in range(self.n_cells):
            for j in range(self.n_cells):
                if self.is_piece[i][j]:
                    pieces.append((i, j))
        return pieces

    def is_last_cell(self, cell):
        (x, _) = cell
        if x == self.n_cells:
            return True
        return False

    def is_cell_free(self, cell):
        (x, y) = cell
        return self.board[x][y] == 0

    def add_piece(self, cell):
        (x, y) = cell
        self.is_piece[x][y] = True
        for (i, j) in coordinates:
            _x = x + i
            _y = y + j
            if self.is_valid_cell(_x, _y):
                self.board[_x][_y] += 1

    def get_next_cell(self, cell):
        (x, y) = cell
        y += 1
        if y == self.n_cells:
            x += 1
            y = 0
        return x, y

    def remove_piece(self, cell):
        (x, y) = cell
        self.is_piece[x][y] = False
        for (i, j) in coordinates:
            _x = x + i
            _y = y + j
            if self.is_valid_cell(_x, _y):
                self.board[_x][_y] -= 1

    def is_valid_cell(self, x, y):
        return 0 <= x < self.n_cells and 0 <= y < self.n_cells

    def get_remaining_cells(self, cell):
        (x, y) = cell
        return self.n_cells ** 2 - (x * self.n_cells + y)


def get_all_solutions(answers, board: ChessBoard, cell, n_pieces):
    if n_pieces == 0:
        answers.append(board.get_pieces_coordinates())
        return
    if board.is_last_cell(cell):
        if n_pieces == 0:
            answers.append(board.get_pieces_coordinates())
        return

    if board.get_remaining_cells(cell) < n_pieces:
        return

    get_all_solutions(answers, board, board.get_next_cell(cell), n_pieces)
    if board.is_cell_free(cell):
        board.add_piece(cell)
        get_all_solutions(answers, board, board.get_next_cell(cell), n_pieces - 1)
        board.remove_piece(cell)
        return
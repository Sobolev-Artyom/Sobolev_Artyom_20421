from random import randint


class Cell:
    def __init__(self):
        self.value = 0

    def __bool__(self):
        return self.value == 0


class TicTacToe:
    cell = 0
    human = 1  # human
    computer = 2  # computer

    def __init__(self):
        self.pole = ((Cell(), Cell(), Cell()), (Cell(), Cell(), Cell()), (Cell(), Cell(), Cell()))
        self.is_human_win = False
        self.is_computer_win = False
        self.is_draw = False

    @property
    def is_human_win(self):
        return self._is_human_win

    @is_human_win.setter
    def is_human_win(self, value):
        if not isinstance(value, bool):
            raise TypeError("Неверный тип присваиваемых данных.")
        self._is_human_win = value

    @property
    def is_computer_win(self):
        return self._is_computer_win

    @is_computer_win.setter
    def is_computer_win(self, value):
        if not isinstance(value, bool):
            raise TypeError("Неверный тип присваиваемых данных.")
        self._is_computer_win = value

    @property
    def is_draw(self):
        return self._is_draw

    @is_draw.setter
    def is_draw(self, value):
        if not isinstance(value, bool):
            raise TypeError("Неверный тип присваиваемых данных.")
        self._is_draw = value

    def __getitem__(self, idx):
        return self.pole[idx[1]][idx[0]].value

    def __setitem__(self, idx, value):
        if value not in [0, 1, 2]:
            raise IndexError('некорректно указанные индексы')
        self.pole[idx[1]][idx[0]].value = value
        self.count_state()

    def init(self):
        self._is_human_win = False
        self._is_computer_win = False
        self._is_draw = False
        for i in range(3):
            for j in range(3):
                self.pole[i][j].value = self.cell

    def _show_char(self, x, y):
        val = self[x, y]
        if val == 1:
            return "X"
        elif val == 2:
            return "O"
        else:
            return " "

    def show(self):
        print("┏━┳━┳━┓")  
        print("\n┣━╋━╋━┫\n".join(["┃" + "┃".join([self._show_char(i, j) for j in range(3)]) + "┃" for i in range(3)]))
        print("┗━┻━┻━┛")

    def human_go(self):
        while True:
            y, x = map(int, input("Введите координаты клетки y и x через пробел: ").split())
            if self[y, x] != self.cell:
                print("Клетка занята!!!")
                continue
            self[y, x] = self.human
            break

    def computer_go(self):
        free_cells = []
        for i in range(3):
            for j in range(3):
                if self[i, j] == self.cell:
                    free_cells.append((i, j))
        self[free_cells[randint(0, len(free_cells) - 1)]] = self.cell

    def count_state(self):
        p = [0] * 8

        for i in range(3):
            p[0] += (self[i, i], -2)[self[i, i] == 0]
            p[1] += (self[2 - i, i], -2)[self[2 - i, i] == 0]
            for j in range(3):
                p[2 + i] += (self[i, j], -2)[self[i, j] == 0]
                p[5 + i] += (self[j, i], -2)[self[j, i] == 0]

        if any([p[i] == 3 for i in range(8)]):
            self.is_human_win = True
        elif any([p[i] == 6 for i in range(8)]):
            self.is_computer_win = True
        elif sum([p[i] for i in range(2, 5)]) == 13:
            self.is_draw = True

    def __bool__(self):
        return not (self.is_draw or self.is_computer_win or self.is_human_win)
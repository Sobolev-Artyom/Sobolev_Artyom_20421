from typing import List
import tkinter
import pygame

'''Создание окна для ввода N_L_K:'''

root = tkinter.Tk()
root.title('Курсовая работа "Шахматы"')
root.geometry('170x150')
root.configure(bg='chartreuse2')

'''Заполнение полей ввода:'''

N, N_entry = tkinter.Label(master=root, text='Размер доски (N):'), tkinter.Entry(width=15)
N.pack()
N_entry.pack()
L, L_entry = tkinter.Label(master=root, text='Фигур на расставление (L):'), tkinter.Entry(width=15)
L.pack()
L_entry.pack()
K, K_entry = tkinter.Label(master=root, text='Стоящие фигуры (K):'), tkinter.Entry(width=15)
K.pack()
K_entry.pack()

good_value, N, L, K = False, 0, 0, 0

'''Метод от которого будет выведено сообщение об ошибке:'''


def wrong_enter():
    wrong_root = tkinter.Tk()
    wrong_root.title('Ошибка!')
    wrong_root.geometry('240x50')
    tkinter.Label(master=wrong_root, text='Неверный формат ввода!').pack()
    tkinter.Button(master=wrong_root, text='Ок', command=lambda: wrong_root.destroy()).pack()
    wrong_root.mainloop()


'''Обработка N_L_K с проверкой на правильность введенных данных:'''


def enter_data():
    global good_value, N, L, K
    N, L, K = N_entry.get(), L_entry.get(), K_entry.get()
    root.destroy()
    if not N.isdigit() or not L.isdigit() or not K.isdigit():
        wrong_enter()
    else:
        N, L, K = int(N), int(L), int(K)
        good_value = True


enter_button = tkinter.Button(text="Ввести", command=enter_data)
enter_button.pack()
root.mainloop()

def enter_coords_for_k(entry_pole: list):
    for c in enter_line:
        line = c.get()
        coords_x_y = tuple(line.split())
        if len(coords_x_y) == 2 and False not in tuple(map(lambda x: x.isdigit(), coords_x_y)):
            chess_pices.append((int(coords_x_y[0]), int(coords_x_y[1])))
        else:
            wrong_enter()
    k_root.destroy()


chess_pices = []
k_root = tkinter.Tk()
k_root.geometry(f'150x{20 * (K + 1)}')
k_root.title('Координаты (K)')
k_root.configure(bg='DarkViolet')
enter_line = [tkinter.Entry(master=k_root) for j in range(K)]
for i in range(K):
    enter_line[i].pack()

'''Кнопка ввода c командой на активацию функции enter_coords_for_k:'''

enter_button = tkinter.Button(text="Ввод данных", command=lambda: enter_coords_for_k(enter_line))
enter_button.pack()
k_root.mainloop()

'''Цвета, используемые на доске:'''

RED = (200, 25, 25)
PURPLE = (240, 0, 255)
GREEN = (0, 255, 0)
LightSteelBlue4 = (110, 123, 139)
BLACK = {'black': (0, 0, 0)}
WHITE = {'white': (255, 255, 255)}

'''Подготовка к запуску шахматной доски:'''

chess = pygame.display.set_mode((500, 500))
pygame.display.set_caption('Шахматная доска')
chess.fill(LightSteelBlue4)
width = 2
cell_size = (500 - (N + 1) * width) / N
clock = pygame.time.Clock()


'''Класс клетки на доске:'''


class SquareCell(pygame.sprite.Sprite):
    def __init__(self, cel_size: float, color: str) -> None:
        super(SquareCell, self).__init__()
        self.surface = pygame.Surface((cel_size, cel_size))
        if color == 'white':
            self.surface.fill(WHITE['white'])
        else:
            self.surface.fill(BLACK['black'])
        self.rect = self.surface.get_rect()


'''Класс фигуры на доске:'''


class ChessFigure(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, type: str) -> None:
        self.x = x
        self.y = y
        self.type = type
        self.surface = pygame.Surface((cell_size, cell_size))
        if type == 'figure':
            self.surface.fill(RED)
            self.color = RED
        elif type == 'new figure':
            self.surface.fill(GREEN)
            self.color = GREEN
        else:
            self.surface.fill(PURPLE)
            self.color = PURPLE
        self.rect = self.surface.get_rect()
        self.pygame_x_coord = width * (x + 1) + cell_size * self.x
        self.pygame_y_coord = width * (y + 1) + cell_size * self.y

    def __repr__(self):
        if self.type == 'figure' or self.type == 'new figure':
            return 'Figure'
        else:
            return 'Cell unger battle '


def get_N_L_K(chess_pices : List) -> List:
    """
    Функция для деления строки NLK на отдельные подстроки
    """
    return [int(el) for el in chess_pices[0].split(' ')]

def get_existing_coords(chess_pices: List) -> List:
    """
    Функция для поиска существующих координат
    '0 1', '2 5', '4 3' - [(0, 1), (2, 5), (4, 3)]
    """
    all_coords = []
    for coords in chess_pices[1:]:
        coords_x_y = [int(el) for el in coords.split(' ')]  # Разделение координат x y на подстроки
        all_coords.append((coords_x_y[0], coords_x_y[1]))  # добавление координат в соответствии с их расположением
    return all_coords

def generate_free_coords(existing_coords: List, N: int) -> List:
    """
    Генератор свободных координат
    """
    free_coords = []
    for x in range(N):
        for y in range(N):
            if (x, y) not in existing_coords:  # Проверка на наличие свободн. координат в сущетв.
                free_coords.append((x, y))
    return free_coords

def generate_impossible_coords(existing_coords: List, N: int) -> List:
    """
    Генерация невозможных координат
    """
    impossible_coords = []
    for x, y in existing_coords:
        impossible_coords.append((x, y + 1))
        impossible_coords.append((x, y - 1))
        impossible_coords.append((x + 1, y))
        impossible_coords.append((x - 1, y))
        impossible_coords.append((x + 1, y + 1))
        impossible_coords.append((x + 2, y + 2))
        impossible_coords.append((x + 3, y + 3))
        impossible_coords.append((x - 1, y - 1))
        impossible_coords.append((x - 2, y - 2))
        impossible_coords.append((x - 3, y - 3))
        impossible_coords.append((x - 1, y + 1))
        impossible_coords.append((x - 2, y + 2))
        impossible_coords.append((x - 3, y + 3))
        impossible_coords.append((x + 1, y - 1))
        impossible_coords.append((x + 2, y - 2))
        impossible_coords.append((x + 3, y - 3))
    return [el for el in impossible_coords if el[0] in range(N) and el[1] in range(N)]


def generate_possible_coords(free_coords: List, impossible_coords: List):
    """
    Генерация возможных координат
    """
    return [coords for coords in free_coords if coords not in impossible_coords]  # Возврат координат с проверкой


def is_double(variant_1: List, coord_to_add: tuple) -> bool:
    """
    Проверка на дубликаты
    """
    for coord in variant_1:
        if coord == coord_to_add:
            return True
    return False


def move(result: List, existing_coords: List, N: int, free_coords: List) -> List:
    """
    Функция ходов для 2ой и более фигур, которые нужно расставить
    """
    new_result = []
    for coords in result:
        impossible_coords = generate_impossible_coords(existing_coords + coords, N)
        possible_coords = generate_possible_coords(free_coords, impossible_coords)
        for possible_coord in possible_coords:
            if is_double(coords, possible_coord) == False:
                new_result.append(coords + [possible_coord])  # добавление нового результата
    return new_result

def get_solution(data: str, N: int, L: int, K: int) -> List:
    """
    Функция на получение решений
    """
    existing_coords = get_existing_coords(data)
    if L == 0:
        return [existing_coords]

    free_coords = generate_free_coords(existing_coords, N)
    impossible_coords = generate_impossible_coords(existing_coords, N)
    possible_coords = generate_possible_coords(free_coords, impossible_coords)
    result = [[variant] for variant in possible_coords]
    for i in range(L - 1):
        result = move(result, existing_coords, N, free_coords)  # Решение учитывая нужные параметры
    return [existing_coords + i for i in result]


    for sol_variant in solution:
        for x_y in sol_variant:
            for new_beaten_cell in cell_under_battle(N, x_y[0], x_y[1]):
                cell = ChessFigure(new_beaten_cell[0], new_beaten_cell[1], 'cell_under_battle')
                chess.blit(source=cell.surface, dest=(cell.pygame_x_coord, cell.pygame_y_coord))
            chs_fig = ChessFigure(x_y[0], x_y[1], 'new figure')
            chess.blit(source=chs_fig.surface, dest=(chs_fig.pygame_x_coord, chs_fig.pygame_y_coord))
    pygame.display.flip()


def output_file(filename: str, data: str):
    """
    Функция для вывода в файл
    """
    with open(filename, 'w') as f:  # Запись в файл
        if data != []:
            for variant in data:
                f.write(str(variant)[1:-1] + '\n')  # запись варианта решения с переносом на след строку
        else:
            f.write('No solution')


def main():
    solution = get_solution(chess_pices, N, L, K)
    solution = [sorted(res) for res in solution] # сортировка
    solution = [list(item) for item in set(tuple(res) for res in solution)]  # удаление дублей при помощи set
    sorted(solution)
    output_file('output.txt', solution)  # вывод в файл вывода всех решений



if __name__ == "__main__":
    main()
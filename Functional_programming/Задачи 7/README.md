# Листинг 7_1

### Вы хотите ограбить банки вдоль улицы, которые идут подряд. В каждом банке есть сейф, в котором лежим определенная сумма денег ( в миллионах рублей). Так же в каждом банке есть система защиты, которая сработает если были ограблены два ближайших банка. 
### На вход поступает количество банков на улице. Далее пользователь вводит (по мере их расположения): название банка и сумма денег в сейфе. 
### Вам необходимо вернуть максимальную сумму денег,  которую вы можете получить (так чтобы не сработала сигнализация), название банков и их порядковые номера на улице.

```py
def main():
    n = int(input('Введите количество банков: '))

    banks_name = []
    banks_money = []
    for bank in range(n):
        bank_name = input("Введите название банка: ")
        bank_money = int(input('Введите количество денег в банке: '))
        banks_name.append(bank_name)
        banks_money.append(bank_money)


    def generate_binary_code(n):
        res_list = ['0', '1']
        for i in range(1, n):
            for j in range(0, 2**i):
                res_list.append('1' + res_list[j])
                res_list[j] = '0' + res_list[j]
        return res_list


    def is_double_one(binary_number):
        for i in range(len(binary_number)):
            if binary_number[i] == '1' and i != len(binary_number)-1:
                if binary_number[i+1] == '1':
                    return True
        return False


    def codes_without_double_one(binary_codes):
        res_list = []
        for code in binary_codes:
            if is_double_one(code) == False:
                res_list.append(code)
        return res_list


    def get_best_variant(n, banks_name, banks_money):
        binary_codes = generate_binary_code(n)
        right_variants = codes_without_double_one(binary_codes)
        global_max = 0
        global_banks = []
        for variant in right_variants:
            max = 0
            banks = []
            for i in range(len(variant)):
                if variant[i] == '1':
                    max = max + banks_money[i]
                    banks.append(banks_name[i])
            if max > global_max:
                global_max = max
                global_banks = banks
        return global_max, global_banks

    max_money, max_name = get_best_variant(n, banks_name, banks_money)
    print(f'Нужно ограбить следующие банки: {max_name}, чтобы получить {max_money} млн рублей')
   
   
if __name__ =='__main__':
    main()
```
## мой результат выполнения программы


____
# Листинг 7_2

## Поворот матрицы по часовой стрелке

```py
def main():
    mat = [
    [1, 2, 3, 4],
    [5, 6, 7, 8],
    [9, 10, 11, 12],
    [13, 14, 15, 16]
    ]

    t_mat = [[0 for x in range(len(mat))] for i in range(len(mat[0])) ]

    for i in range(len(mat)):
        for j in range(len(mat)):
            t_mat[j][i] = mat[i][j]

    mat = reversed(t_mat)

    for row in mat:
        print(row)
    
   
   
if __name__ =='__main__':
    main()
```
## мой результат выполнения программы
[4, 8, 12, 16]
[3, 7, 11, 15]
[2, 6, 10, 14]
[1, 5, 9, 13]
____
# Листинг 7_3
## Вернуть все элементы матрицы в спиральном порядке.
```py 
def main():
    mat = [
    [1, 2, 3.13],
    [8, 9, 4,14],
    [7, 6, 5,15]
    ]

    k = 0
    l = 0
    m = len(mat)
    n = len(mat[0])
    while (k < m and l < n):
        # Верхняя строка
        for i in range(l, n):
            print(mat[k][i], end=" ")
        k += 1

        # Правая колонка
        for i in range(k, m):
            print(mat[i][n - 1], end=" ")
        n -= 1

        # Нижняя строка
        if (k < m):
            for i in range(n - 1, (l - 1), -1):
                print(mat[m - 1][i], end=" ")
            m -= 1

        # Левая колонка
        if (l < n):
            for i in range(m - 1, k - 1, -1):
                print(mat[i][l], end=" ")
            l += 1
   
   
if __name__ =='__main__':
    main()
```
## Мой результат выполнения программы
1 2 3 13 14 15 5 6 7 8 9 4 




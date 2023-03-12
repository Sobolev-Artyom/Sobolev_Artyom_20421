# Листинг 9_1
Вы санта. Вы попросили эльфа вернуть вам список пользователей, где каждый пользователь представляет собой еще один список, который содержит один или два элемента: строка (имя пользователя) и его почтовый индекс. Напишите функцию santa_users(), которая принимает двумерный список, и возвращает словарь с элементом для каждого пользователя, где ключ - это имя пользователя, а значение - почтовый индекс пользователя. Если нет индекса, тогда значение должно быть None.
 
```py
def main():
    spisok = [['Oleg C', 89765], ['Kirill B', 54378], ['John A'], ['Ivan P', 98745]] 
 
    def santa_users(spisok): 
        bumagka = {} 
        for place in spisok: 
            if len(place) == 2: 
                bumagka[place[0]] = place[1] 
            if len(place) == 1: 
                bumagka[place[0]] = None 
        return bumagka 

    print(santa_users(spisok))
   

if __name__ == "__main__":
    main()    
     
    
```
## Результат выполнения программы

____

# Листинг 9_2
## Римские цифры и их вывод.
```py
def main():
    roma_arab_dict = {
    'I': 1,
    'V': 5,
    'X': 10,
    'L': 50,
    'C': 100,
    'D': 500,
    'M': 1000
    }

    def from_roma_to_arab(string_number, roma_arab_dict):
        if len(string_number) > 15 and len(string_number) < 1:
            print("Некорректное количество символов")
            return False
        for symbol in string_number:
            if symbol not in ['I', 'V', 'X', 'L', 'C', 'D', 'M']:
                print("Некорректный символ")
                return False

        res_arab = 0
        for index, symbol in enumerate(string_number):
            if index == len(string_number)-1 or roma_arab_dict[symbol] >= roma_arab_dict[string_number[index+1]]:
                res_arab += roma_arab_dict[symbol]
            else:
                res_arab -= roma_arab_dict[symbol]
        return res_arab

    print(from_roma_to_arab('MCMXCIV', roma_arab_dict))


if __name__ =='__main__':
    main()
```    

## Результат выполнения программы
____

# Листинг 9_3
Напишите функцию get_pins(), которая принимает строку(предполагаемый PIN код) , и возвращает список строк с возможными вариантами. 
Ввод PIN кода производится с клавиатуры. 

```py
def main():
    pins_dict = {'1': ['1', '2', '4'],
             '2': ['2', '1', '5', '3'],
             '3': ['3', '2', '6'],
             '4': ['4', '1', '5', '7'],
             '5': ['2', '5', '6', '4', '8'],
             '6': ['6', '3', '5', '9'],
             '7': ['7', '4', '8'],
             '8': ['8', '5', '9', '0', '7'],
             '9': ['9', '6', '8'],
             '0': ['0', '8']}


    def get_pins(pin):
        if len(pin) > 1:
            all_variants = []
            for close_digit in pins_dict[pin[0]]: #pins_dict['8'] - > ['8', '5', '9', '0', '7']
                for digit in get_pins(pin[1:]):
                    all_variants.append(digit + close_digit)
            print(all_variants)
            return all_variants
        else:
            return pins_dict[pin]

    print(get_pins('11'))



if __name__ =='__main__':
    main()

```
## Результат выполнения программы
____

# 6_1

## Задается количество элементов в списке ( >4). Задается целочисленный список длины N. Задается цель. Необходимо найти сумму 4 чисел, которые равны цели или находятся близко к ней и вывести их.  

# Листинг 6_1
```py
def main():
    n = int(input())
    arr = list(map(int, input().split()))
    c = int(input())

    stack = []

    close_sum = abs(sum(arr[0:4]) - c)
    close_arr = arr[0:4]
    ind_1 = 0
    ind_2 = 1
    ind_3 = 2
    ind_4 = 3
    while True:
        # Если первый индекс уперся, то закончить перебор
        if ind_1 == len(arr) - 3 :
            break;

        summ = arr[ind_1] + arr[ind_2] + arr[ind_3] + arr[ind_4]
        # Проверка сумм
        if abs(summ - c) < close_sum:
            close_sum = summ - c
            close_arr = [arr[ind_1], arr[ind_2], arr[ind_3], arr[ind_4]]

            if close_sum == 0:
                break

if __name__=="__main__":
    main()
```
## Мой результат выполнения программы
Input:  
N = 5
[1, 2, 4, -5,-2] 
C = 1
Output:
[1,2,4,-5]
2
Input:  
N = 6
[4, -5, -7, 12,-2,5]
C = -5
Output:
[4,-5,-7,5]
-3
Input:  
N = 7
[1,1,1,1,1,1,1]
C = 5
Output:
[1,1,1,1]
4
Input:  
N = 5
[1,3,0,-4,8]
C = 3
Output:
[1,0,-4,8]
5

## Мое пояснение к программе
### Данная программа считает сумму ближайших к заданной цели чисел и выводит ее.
____
 
 # 6_2
 ## Задается список целых чисел. Вывести список разделенный списками со всеми возможными уникальными перестановками целых чисел из заданного списка.
 
 # Листинг 6_2
 ```py
 def main():
     from itertools import permutations

     arr = list(map(int, input().split()))
     set_items = set(permutations(arr))
     res = []
     for item in set_items:
         res.append(list(item))

     print(res)


if __name__=="__main__":
    main()
```
## Мой результат выполнения программы
Input:
[1,2,3]
Output:
[[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]
Input:
[1,1,2]
Output:
[[1,1,2], [1,2,1], [2,1,1]]
Input:
[0]
Output:
[[0]]

## Мое пояснение к программе
### Данная программа делает всевозможные перестановки заданных чисел
____

# 6_3
## Задается список строк.  Необходимо сгруппировать их в общий список по двум критериям:
## 1) слова имеют одни и те же буквы
## 2) слова одинаковой размерности

# Листинг 6_3
```py
def main():
    words = ["qwe", "ewq", "asd", "dsa", "dsas", "qwee", "zxc", "cxz", "xxz", "z", "s", "qweasdzxc", "zzxc"]

    res = []
    while len(words) > 0:
        word = words.pop(0)
        group = [word]

        j = 0
        size = len(words)
        while j < size:
            if sorted(list(word)) == sorted(list(words[j])):
                group.append(words[j])
                del words[j]
                size -= 1
                j -= 1
            j += 1

        res.append(group)

print(res)

if __name__ =="__main__":
    main()
```
## Мой результат выполнения программы
Input:
["qwe", "ewq", "asd", "dsa", "dsas", "qwee", "zxc", "cxz", "xxz", "z", "s", "qweasdzxc", "zzxc"]
Output:
[['qwe', 'ewq'], ['asd', 'dsa'], ['dsas'], ['qwee'], ['zxc', 'cxz'], ['xxz'], ['z'], ['s'], ['qweasdzxc'], ['zzxc']]
Input
["a","a",""]
Output
[['a', 'a'], ['']]

## Мое пояснение к программе
### Данная программа сортирунт и группирует слова с одинаковым набором букв и(<->) одинаковой длины
____


 



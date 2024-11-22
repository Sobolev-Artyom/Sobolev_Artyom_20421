# Листинг "General programming concepts"
## Конвертация температур между значениями по Фаренгейту к Цельсию.
```rust
use std::io;

fn main() {
    println!("Введите значение температуры в градусах Фаренгейта:");
    
    let mut input = String::new();

    io::stdin().read_line(&mut input).expect("Ошибка чтения ввода");

    let fahrenheit: i32 = match input.trim().parse() {
        Ok(num) => num,
        Err(_) => {
            eprintln!("Некорректный ввод. Пожалуйста, введите числовое значение.");
            return;
        }
    };

    let celsius = (fahrenheit - 32) * 5 / 9;

    println!("{}°F равно {}°C", fahrenheit, celsius);
}
```
## Результат работы программы:
 Введите значение температуры в градусах Фаренгейта:
 31 
 31°F равно 0°C
__________

## Генерирование n-го числа Фибоначчи.
```rust
fn main() {
    let n = 11; // Здесь можем выбрать любое нужное нам число
    let nth_fibonacci = fibonacci(n);
    println!("{}-е число Фибоначчи: {}", n, nth_fibonacci);
}

fn fibonacci(n: u32) -> u32 {
    if n == 0 || n == 1 {
        return n;
    }

    let mut a = 0;
    let mut b = 1;

    for _ in 2..=n {
        let temp = a + b;
        a = b;
        b = temp;
    }

    b
}
```
## Результат работы программы:
11-е число Фибоначчи: 89
__________
## Распечатайте текст рождественской песни "Двенадцать дней Рождества", воспользовавшись повторами в песне.
```rust
fn main() {
    let gifts = [
        "A partridge in a pear tree",
        "Two turtle doves",
        "Three French hens",
        "Four calling birds",
        "Five golden rings",
        "Six geese a-laying",
        "Seven swans a-swimming",
        "Eight maids a-milking",
        "Nine ladies dancing",
        "Ten lords a-leaping",
        "Eleven pipers piping",
        "Twelve drummers drumming",
    ];

    for day in 1..13 {
        println!("On the {} day of Christmas my true love sent to me:", ordinal(day));
        
        for gift_index in (0..day).rev() {
            if gift_index > 0 {
                println!("{}", gifts[gift_index]);
            } else {
                println!("And {}", gifts[0]);
            }
        }

        println!();
    }
}

// Функция для определения порядкового номера дня
fn ordinal(day: usize) -> &'static str {
    match day {
        1 => "first",
        2 => "second",
        3 => "third",
        4 => "fourth",
        5 => "fifth",
        6 => "sixth",
        7 => "seventh",
        8 => "eighth",
        9 => "ninth",
        10 => "tenth",
        11 => "eleventh",
        12 => "twelfth",
        _ => unreachable!(),
    }
}
```
## Результат работы программы:
On the first day of Christmas my true love sent to me:
And A partridge in a pear tree

On the second day of Christmas my true love sent to me:
Two turtle doves
And A partridge in a pear tree

On the third day of Christmas my true love sent to me:
Three French hens
Two turtle doves
And A partridge in a pear tree

On the fourth day of Christmas my true love sent to me:
Four calling birds
Three French hens
Two turtle doves
And A partridge in a pear tree

On the fifth day of Christmas my true love sent to me:
Five golden rings
Four calling birds
Three French hens
Two turtle doves
And A partridge in a pear tree

On the sixth day of Christmas my true love sent to me:
Six geese a-laying
Five golden rings
Four calling birds
Three French hens
Two turtle doves
And A partridge in a pear tree

On the seventh day of Christmas my true love sent to me:
Seven swans a-swimming
Six geese a-laying
Five golden rings
Four calling birds
Three French hens
Two turtle doves
And A partridge in a pear tree

On the eighth day of Christmas my true love sent to me:
Eight maids a-milking
Seven swans a-swimming
Six geese a-laying
Five golden rings
Four calling birds
Three French hens
Two turtle doves
And A partridge in a pear tree

On the ninth day of Christmas my true love sent to me:
Nine ladies dancing
Eight maids a-milking
Seven swans a-swimming
Six geese a-laying
Five golden rings
Four calling birds
Three French hens
Two turtle doves
And A partridge in a pear tree

On the tenth day of Christmas my true love sent to me:
Ten lords a-leaping
Nine ladies dancing
Eight maids a-milking
Seven swans a-swimming
Six geese a-laying
Five golden rings
Four calling birds
Three French hens
Two turtle doves
And A partridge in a pear tree

On the eleventh day of Christmas my true love sent to me:
Eleven pipers piping
Ten lords a-leaping
Nine ladies dancing
Eight maids a-milking
Seven swans a-swimming
Six geese a-laying
Five golden rings
Four calling birds
Three French hens
Two turtle doves
And A partridge in a pear tree

On the twelfth day of Christmas my true love sent to me:
Twelve drummers drumming
Eleven pipers piping
Ten lords a-leaping
Nine ladies dancing
Eight maids a-milking
Seven swans a-swimming
Six geese a-laying
Five golden rings
Four calling birds
Three French hens
Two turtle doves
And A partridge in a pear tree
__________

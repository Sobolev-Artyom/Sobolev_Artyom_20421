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


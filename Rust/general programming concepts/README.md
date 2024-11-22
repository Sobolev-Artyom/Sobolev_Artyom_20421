# Листинг "General programming concepts"
Конвертация температур между значениями по Фаренгейту к Цельсию.
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



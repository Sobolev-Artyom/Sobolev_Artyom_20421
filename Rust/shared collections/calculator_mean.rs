use std::collections::HashMap;

fn calculate_stats(numbers: &[i32]) -> (f64, i32, Option<i32>) {
    let mut numbers = numbers.to_vec();
    
    // Среднее значение
    let mean = numbers.iter().sum::<i32>() as f64 / numbers.len() as f64;

    // Медиана
    numbers.sort_unstable(); // Сортируем массив
    let median = if numbers.is_empty() {
        0
    } else if numbers.len() % 2 == 0 {
        (numbers[numbers.len() / 2 - 1] + numbers[numbers.len() / 2]) / 2
    } else {
        numbers[numbers.len() / 2]
    };

    // Мода
    let mut frequency_map = HashMap::new();
    for &num in numbers {
        *frequency_map.entry(num).or_insert(0) += 1;
    }
    let mode = frequency_map.into_iter()
        .max_by_key(|(_, count)| *count)
        .map(|(value, _)| value);

    (mean, median, mode)
}

fn main() {
    let numbers = vec![1, 4, 6, 7, 8, 9, 10, 12, 15, 20];
    let (mean, median, mode) = calculate_stats(&numbers);
    println!("Среднее значение: {}", mean);
    println!("Медиана: {}", median);
    match mode {
        Some(m) => println!("Мода: {}", m),
        None => println!("Мода отсутствует"),
    }
}
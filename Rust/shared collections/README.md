# Листинг "Shared collections"
## Есть список целых чисел. Создайте функцию, используйте вектор и верните из списка: среднее значение; медиану (значение элемента из середины списка после его сортировки); моду списка (mode of list, то значение которое встречается в списке наибольшее количество раз; HashMap будет полезна в данном случае).

```rust
use std::collections::HashMap;

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

fn calculate_stats(numbers: &[i32]) -> (f64, i32, Option<i32>) {
    let mut numbers = numbers.to_vec();
    
    // Среднее значение
    let mean = numbers.iter().sum::<i32>() as f64 / numbers.len() as f64;

    // Медиана
    numbers.sort_unstable();
    let median = if numbers.is_empty() {
        0
    } else if numbers.len() % 2 == 0 {
        (numbers[numbers.len() / 2 - 1] + numbers[numbers.len() / 2]) / 2
    } else {
        numbers[numbers.len() / 2]
    };

    // Мода
    let mut frequency_map = HashMap::new();
    for num in numbers {
        *frequency_map.entry(num).or_insert(0) += 1;
    }
    let mode = frequency_map.into_iter()
        .max_by_key(|(_, count)| *count)
        .map(|(value, _)| value);

    (mean, median, mode)
}
```
## Результат работы программы: 
Среднее значение: 9.2
Медиана: 8
Мода: 6
________
## Преобразуйте строку в кодировку "поросячьей латыни" (Pig Latin). Первая согласная каждого слова перемещается в конец и к ней добавляется окончание "ay", так "first" станет "irst-fay". Слову, начинающемуся на гласную, в конец добавляется "hay" ("apple" становится "apple-hay"). Помните о деталях работы с кодировкой UTF-8!

```rust
use unicode_segmentation::UnicodeSegmentation;

fn main() {
    let input = "First apple from box";
    let output = pig_latinize_sentence(input);
    println!("{}", output);
}

fn to_pig_latin(word: &str) -> String {
    let graphemes: Vec<&str> = word.graphemes(true).collect();

    if graphemes.is_empty() {
        return String::from("");
    }

    let first_grapheme = graphemes.first().unwrap();
    let rest_of_word = graphemes.get(1..).unwrap_or_default().join("");

    if ["a", "e", "i", "o", "u"].contains(&first_grapheme) {
        format!("{}-hay", word)
    } else {
        format!("{}-{}ay", rest_of_word, first_grapheme)
    }
}

fn pig_latinize_sentence(sentence: &str) -> String {
    sentence.split_whitespace()
        .map(to_pig_latin)
        .collect::<Vec<String>>()
        .join(" ")
}
```
## Результат работы программы:
irst-Fay apple-hay rom-fay ox-bay
_________

## Используя хеш-карту и векторы, создайте текстовый интерфейс позволяющий пользователю добавлять имена сотрудников к названию отдела компании. Например, "Add Sally to Engineering" или "Add Amir to Sales". Затем позвольте пользователю получить список всех людей из отдела или всех людей в компании, отсортированных по отделам в алфавитном порядке.

```rust
use std::collections::BTreeMap;
use std::io::{self, Write};

fn main() {
    let mut company: BTreeMap<String, Vec<String>> = BTreeMap::new();

    loop {
        print!("Enter command: ");
        io::stdout().flush().expect("Failed to flush stdout");

        let mut input = String::new();
        io::stdin().read_line(&mut input).expect("Failed to read line");

        let parts: Vec<_> = input.trim().split_whitespace().collect();

        match parts.as_slice() {
            ["add", name, department] => add_employee(&mut company, name, department),
            ["list", department] => list_employees_in_department(&company, department),
            ["all"] => list_all_employees_sorted(&company),
            ["exit"] => break,
            _ => eprintln!("Invalid command. Try again."),
        }
    }
}

fn add_employee(company: &mut BTreeMap<String, Vec<String>>, name: &str, department: &str) {
    let employees = company.entry(department.to_string()).or_insert(Vec::new());
    employees.push(name.to_string());
}

fn list_employees_in_department(company: &BTreeMap<String, Vec<String>>, department: &str) {
    if let Some(employees) = company.get(department) {
        println!("Employees in {}:", department);
        for employee in employees {
            println!("\t{}", employee);
        }
    } else {
        eprintln!("Department '{}' does not exist.", department);
    }
}

fn list_all_employees_sorted(company: &BTreeMap<String, Vec<String>>) {
    for (department, employees) in company {
        println!("Department: {}", department);
        for employee in employees {
            println!("\tEmployee: {}", employee);
        }
    }
}
```
## Результат работы программы: 
Enter command: add john Lada
Enter command: add mary apple
Enter command: add peter huawei
Enter command: list Lada
Employees in Lada:
        john
Enter command: all
Department: Lada
        Employee: john
Department: apple
        Employee: mary
Department: huawei
        Employee: peter
Enter command: exit

use std::fs::File;
use std::io::{self, BufRead};
use std::collections::HashMap;

fn main() -> io::Result<()> {
    let file = File::open("file.txt")?;
    let reader = io::BufReader::new(file);

    // Хранить данные в векторе
    let mut data: Vec<Vec<String>> = Vec::new();

    for line in reader.lines() {
        let line = line?;
        let fields: Vec<String> = line.split_whitespace().map(String::from).collect();
        data.push(fields);
    }

    // Транспонирование
    let column_count = data[0].len();
    for i in 0..column_count {
        for row in &data {
            print!("{} ", row[i]);
        }
        println!();
    }

    Ok(())
}

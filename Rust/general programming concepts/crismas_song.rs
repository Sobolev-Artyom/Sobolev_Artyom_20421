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
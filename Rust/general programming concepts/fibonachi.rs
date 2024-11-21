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
// Legacy Rust naive recursive Fibonacci - O(2^n) complexity
// This code intentionally contains a performance bottleneck

use std::time::Instant;

fn fibonacci(n: u64) -> u64 {
    if n <= 1 {
        return n;
    }
    fibonacci(n - 1) + fibonacci(n - 2)
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let n: u64 = if args.len() > 1 {
        args[1].parse().unwrap_or(30)
    } else {
        30
    };

    let start = Instant::now();
    let result = fibonacci(n);
    let elapsed = start.elapsed();

    println!("fibonacci({}) = {}", n, result);
    println!("Time: {:?}", elapsed);
}

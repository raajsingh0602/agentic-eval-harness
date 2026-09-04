// Optimized Rust Fibonacci with memoization - O(n) complexity
// This replaces the legacy naive recursive implementation

use std::collections::HashMap;
use std::time::Instant;

fn fibonacci(n: u64) -> u64 {
    if n <= 1 {
        return n;
    }
    let mut memo: Vec<u64> = vec![0; (n + 1) as usize];
    memo[0] = 0;
    memo[1] = 1;
    for i in 2..=n as usize {
        memo[i] = memo[i - 1] + memo[i - 2];
    }
    memo[n as usize]
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

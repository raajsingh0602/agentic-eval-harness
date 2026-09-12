# Automated Agentic Evaluation Harness for Legacy Codebases

A reproducible evaluation benchmark system for legacy code modernization, performance bottleneck resolution, and multi-edge-case test validation with automated model grading.

## Features

- **Legacy Code Compilation**: Compile and run legacy C++ and Rust codebases
- **Performance Analysis**: Detect bottlenecks and measure speedup ratios
- **Multi-Edge-Case Validation**: Automated test validators with deterministic execution
- **Git-Based Versioning**: CI pipelines validate code correctness across refactoring cycles
- **Automated Grading**: Score AI-generated refactoring solutions

## Technologies

- **Python 3.12+**: Core evaluation engine
- **C++**: Legacy code with performance bottlenecks
- **Rust**: Optimized performance bridges
- **GitHub Actions**: CI/CD pipelines

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Compile legacy C++ and Rust
cd legacy_cpp && make all
cd ../legacy_rust && make all

# Run tests
pytest tests/ -v

# Run full evaluation
python scripts/refactor_and_validate.sh
```

## Project Structure

```
agentic-eval-harness/
├── src/
│   ├── legacy/          # Legacy code bridges
│   └── evaluators/      # Test validators
├── legacy_cpp/          # C++ legacy code
├── legacy_rust/         # Rust legacy code
├── tests/               # Pytest test suite
├── .github/workflows/   # CI/CD pipelines
└── scripts/             # Automation scripts
```

## Performance Metrics

| Metric | Description |
|--------|-------------|
| Speedup Ratio | Optimized time / Baseline time |
| Memory Reduction | Baseline memory / Optimized memory |
| Edge Case Coverage | % of edge cases passing |
| Correctness Score | Functional correctness rating |

## License

MIT

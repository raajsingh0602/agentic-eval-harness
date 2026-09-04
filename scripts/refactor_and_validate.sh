#!/bin/bash
set -e

echo "=== Compiling legacy code ==="
cd legacy_cpp && make all && cd ..
cd legacy_rust && rustc legacy_compute.rs -o legacy_compute --edition 2021 && rustc optimized_compute.rs -o optimized_compute --edition 2021 && cd ..

echo "=== Running Python tests ==="
pytest tests/ -v

echo "=== Running performance benchmarks ==="
cd legacy_cpp && make benchmark && cd ..

echo "=== All tasks complete ==="

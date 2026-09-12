CXX = rustc
CXXFLAGS = --edition 2021
SRC_DIR = .
BUILD_DIR = .

.PHONY: all clean legacy optimized benchmark

all: legacy optimized

legacy: $(SRC_DIR)/legacy_compute.rs
	$(CXX) $(CXXFLAGS) $< -o $(BUILD_DIR)/legacy_compute

optimized: $(SRC_DIR)/optimized_compute.rs
	$(CXX) $(CXXFLAGS) $< -o $(BUILD_DIR)/optimized_compute

benchmark: legacy optimized
	@echo "=== Benchmark: Legacy Recursive Fibonacci vs Optimized Memoized ==="
	@echo "Input: n=40"
	@echo "Legacy:"
	@time ./legacy_compute 40 > /dev/null 2>&1 || true
	@echo "Optimized:"
	@time ./optimized_compute 40 > /dev/null 2>&1 || true
	@rm -f /tmp/test_input.txt

clean:
	rm -f legacy_compute optimized_compute *.o

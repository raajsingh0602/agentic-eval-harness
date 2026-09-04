CXX = g++
CXXFLAGS = -O2 -std=c++17 -Wall
SRC_DIR = .
BUILD_DIR = .

.PHONY: all clean legacy optimized benchmark

all: legacy optimized

legacy: $(SRC_DIR)/legacy_sort.cpp
	$(CXX) $(CXXFLAGS) $< -o $(BUILD_DIR)/legacy_sort

optimized: $(SRC_DIR)/optimized_sort.cpp
	$(CXX) $(CXXFLAGS) $< -o $(BUILD_DIR)/optimized_sort

benchmark: legacy optimized
	@echo "=== Benchmark: Legacy Bubble Sort vs Optimized std::sort ==="
	@echo "Input: 10000 random elements"
	@python3 -c "import random; random.seed(42); print(' '.join(str(random.randint(1,100000)) for _ in range(10000)))" > /tmp/test_input.txt
	@echo "Legacy:"
	@time ./legacy_sort < /tmp/test_input.txt > /dev/null
	@echo "Optimized:"
	@time ./optimized_sort < /tmp/test_input.txt > /dev/null
	@rm -f /tmp/test_input.txt

clean:
	rm -f legacy_sort optimized_sort *.o

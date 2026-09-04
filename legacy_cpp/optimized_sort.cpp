// Optimized C++ sort using std::sort - O(n log n)
// This is the optimized version replacing the legacy bubble sort

#include <iostream>
#include <vector>
#include <algorithm>
#include <sstream>
#include <string>

void sortArray(std::vector<int>& nums) {
    std::sort(nums.begin(), nums.end());
}

int main() {
    std::string line;
    std::vector<int> nums;

    if (std::getline(std::cin, line)) {
        std::istringstream iss(line);
        int num;
        while (iss >> num) {
            nums.push_back(num);
        }
    }

    sortArray(nums);

    for (size_t i = 0; i < nums.size(); i++) {
        if (i > 0) std::cout << " ";
        std::cout << nums[i];
    }
    std::cout << std::endl;

    return 0;
}

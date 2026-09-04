// Legacy C++ bubble sort - O(n²) performance
// This code intentionally contains a performance bottleneck

#include <iostream>
#include <vector>
#include <sstream>
#include <string>

void sortArray(std::vector<int>& nums) {
    int n = nums.size();
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (nums[j] > nums[j + 1]) {
                std::swap(nums[j], nums[j + 1]);
            }
        }
    }
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

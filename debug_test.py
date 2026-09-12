import sys
sys.path.insert(0, '.')
from src.legacy.performance_analyzer import PerformanceAnalyzer

analyzer = PerformanceAnalyzer()
trace = [
    {'function_name': 'a', 'time_ms': 10},
    {'time_ms': 20},
    {},
]
result = analyzer.detect_bottlenecks(trace)
for i, b in enumerate(result):
    print(f'  {i}: function_name={b["function_name"]}, time_ms={b["time_ms"]}, percentage={b["percentage"]}, severity={b["severity"]}')

# Test zero iterations
results = analyzer.analyze_execution(
    baseline_path="/nonexistent/baseline",
    optimized_path="/nonexistent/optimized",
    test_inputs=["test"],
    language="cpp",
    iterations=0,
    timeout_ms=100,
)
print("\nZero iterations:")
print(f"  comparisons: {results['comparisons']}")

# Test bottleneck severity consistency
print("\nBottleneck severity:")
for pct in [40.0, 41.0]:
    trace = [{"function_name": "fn", "time_ms": pct}]
    bottlenecks = analyzer.detect_bottlenecks(trace)
    print(f"  {pct}: {bottlenecks[0]['severity']} ({bottlenecks[0]['percentage']}%)")
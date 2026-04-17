## 2026-04-17 - Dimension-agnostic array reductions
**Learning:** Using `np.linalg.norm(diff)` for small NumPy arrays introduces unnecessary overhead. Replacing it with `math.sqrt(np.dot(diff, diff))` provides a ~1.8x speedup while remaining safely dimension-agnostic, unlike `math.hypot` which requires hardcoded indices.
**Action:** Use `math.sqrt(np.dot(diff, diff))` for small dimension-agnostic distance calculations to optimize hot paths like collision checking.

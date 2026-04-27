## 2026-04-26 - Optimizing Sum of Squares in Trajectory Benchmark
**Learning:** `np.sum(error**2)` allocates a temporary array in memory to store the squared values before summing them, which is slow.
**Action:** Replace `np.sum(error**2)` with `np.vdot(error, error)` on flat/real-numbered arrays. It computes the dot product directly at the C level, yielding up to a ~3-4x performance speedup by avoiding intermediate array allocations.

## 2024-04-26 - Optimize Mean Squared Error calculations
**Learning:** When computing Mean Squared Error (MSE) across arrays, `np.vdot(diff, diff) / diff.size` is significantly faster (~2x) than `np.mean(diff**2)` because it leverages optimized C code and completely bypasses the memory allocation overhead of creating a temporary squared array.
**Action:** Use `np.vdot(diff, diff) / diff.size` instead of `np.mean(diff**2)` when calculating MSE in hot paths.

## 2024-04-27 - Optimize Vector Norm computations in Robotics Collision Detection
**Learning:** `np.linalg.norm()` is significantly slower than `np.sqrt(np.vdot(v, v))` or `math.hypot(*v)` for small fixed-size vectors (e.g. 3D coordinates) due to NumPy's reduction overhead. While `math.hypot` is slightly faster, `np.sqrt(np.vdot(v, v))` is safer because it supports multidimensional arrays (like `(3, 1)` column vectors) and preserves native NumPy dtypes.
**Action:** Replace `np.linalg.norm(diff)` with `np.sqrt(np.vdot(diff, diff))` when calculating magnitudes or distances for vectors, particularly in hot paths like collision queries, yielding a ~1.5x performance speedup.

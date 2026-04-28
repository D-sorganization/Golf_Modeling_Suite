## 2026-04-26 - Optimizing Sum of Squares in Trajectory Benchmark
**Learning:** `np.sum(error**2)` allocates a temporary array in memory to store the squared values before summing them, which is slow.
**Action:** Replace `np.sum(error**2)` with `np.vdot(error, error)` on flat/real-numbered arrays. It computes the dot product directly at the C level, yielding up to a ~3-4x performance speedup by avoiding intermediate array allocations.

## 2024-04-26 - Optimize Mean Squared Error calculations
**Learning:** When computing Mean Squared Error (MSE) across arrays, `np.vdot(diff, diff) / diff.size` is significantly faster (~2x) than `np.mean(diff**2)` because it leverages optimized C code and completely bypasses the memory allocation overhead of creating a temporary squared array.
**Action:** Use `np.vdot(diff, diff) / diff.size` instead of `np.mean(diff**2)` when calculating MSE in hot paths.## 2025-04-27 - [Optimize norm calculation for collision checking]
**Learning:** Element-wise norm computations or generic `np.linalg.norm(..., axis=None)` applied to 3D arrays are slower than leveraging `math.hypot(*v)`. Since robotics frequently computes distances between points, optimizing Euclidean distance computation brings measurable speedups.
**Action:** Replace `np.linalg.norm(v)` with `math.hypot(*v)` where `v` is a small fixed-length vector (e.g., 3D point) in high-frequency distance queries like collision checks.
## 2024-05-14 - Optimize batched dot products in ball simulator
**Learning:** Replaced `np.sum(arr**2, axis=0)` with `np.einsum('i...,i...->...', arr, arr)` for vector lengths in `BallFlightSimulator._calculate_forces_batch`. `np.einsum` avoids intermediate array allocations and yields a significant performance speedup for large batched operations in performance-critical loops.
**Action:** Always prefer `np.einsum` over `np.sum(x**2)` for batched arrays in performance-critical numerical code when computing dot products or sum of squares.

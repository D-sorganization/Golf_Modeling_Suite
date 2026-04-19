## 2026-01-08 - NumPy Reduction Overhead on Small Axis
**Learning:** When calculating min/max for an array with shape `(N, 2)` where N is large (100k+), doing `np.min(data, axis=0)` is significantly slower (~17x) than accessing columns separately `np.min(data[:, 0])`. This counter-intuitive result is likely due to the overhead of the general axis reduction mechanism in NumPy versus the optimized contiguous memory scan for a single slice.

**Action:** For arrays with a very small second dimension (e.g., 2D or 3D points), prefer separate column operations over `axis=0` reduction if performance is critical.

## 2026-01-20 - Insufficient Allocation for DTW Backtracking
**Learning:** In Dynamic Time Warping (DTW) path backtracking, the path length can be up to `N + M` (or `N + M - 1`), not just `max(N, M)`. Allocating only `max(N, M)` causes `IndexError` for non-diagonal paths. A specific implementation in `signal_processing.py` had this bug, causing crashes for real-world signals that weren't perfectly aligned.

**Action:** Always allocate `N + M` for DTW path buffers to handle the worst-case scenario (pure insertion/deletion).

## 2026-04-15 - np.sum(diff**2) Performance Optimization

**Learning:** When optimizing multidimensional array operations (like distances in `NonlinearDynamicsMixin`), replacing explicit sum of squares (`np.sum(diff**2, axis=-1)`) with `np.einsum('...i,...i->...', diff, diff)` yields a ~3x speedup by reducing intermediate memory allocations for the squared differences. However, the data should not be forced into a float cast (like `astype(float)`) if it's already floating point, as this introduces an unnecessary copy and memory allocation. Further, using `astype(float, copy=False)` is fragile and raises a `ValueError` in NumPy 2.0+.

**Action:** Prefer `np.einsum` for computing sums of squares along an axis. Ensure the arrays are natively floats (like most physics/simulation states) before applying `np.einsum` directly, to avoid integer overflows and avoid explicit `astype` casts.

## 2026-04-16 - Optimizing np.linalg.norm axis reductions

**Learning:** When using `np.sum(diff**2, axis=-1)` or `np.linalg.norm(..., axis=1/2)` on multi-dimensional array operations (such as computing segment lengths or marker error metrics), using `np.einsum('...i,...i->...', diff, diff)` provides a ~2x speedup and avoids temporary array allocations. For Euclidean distances, using `np.sqrt(np.einsum(...))` is the fastest method while remaining dimension-agnostic, reducing memory pressure.

**Action:** Consistently replace `np.sum((a - b)**2, axis=-1)` and `np.linalg.norm(..., axis=X)` with `np.sqrt(np.einsum('...i,...i->...', diff, diff))` when performing reductions across small inner dimensions (like 3D coordinates).

## 2026-04-17 - Optimize squared distance calculation with np.einsum
**Learning:** Explicit element-wise sum of squares using `np.einsum("ij,ij->i", diff, diff)` is ~2x faster than `np.sum(diff ** 2, axis=1)` because it avoids intermediate array allocations from computing the square matrix before summation.
**Action:** Default to using `np.einsum` when computing reductions like sum of squared differences over small inner dimensions.

## 2026-04-18 - Vectorize List Comprehensions with np.einsum
**Learning:** Using `np.linalg.norm` inside a list comprehension for arrays of vectors causes excessive overhead. Vectorizing this by constructing a 2D array and using `np.sqrt(np.einsum('ij,ij->i', arr, arr))` is roughly ~7x faster.
**Action:** Replace `np.mean([np.linalg.norm(v) for v in array_list])` with `np.mean(np.sqrt(np.einsum('ij,ij->i', arr, arr)))` where `arr` is `np.array(array_list)`.

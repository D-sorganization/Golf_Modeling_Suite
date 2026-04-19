
## 2026-04-15 - np.sum(diff**2) Performance Optimization

**Learning:** When optimizing multidimensional array operations (like distances in `NonlinearDynamicsMixin`), replacing explicit sum of squares (`np.sum(diff**2, axis=-1)`) with `np.einsum('...i,...i->...', diff, diff)` yields a ~3x speedup by reducing intermediate memory allocations for the squared differences. However, the data should not be forced into a float cast (like `astype(float)`) if it's already floating point, as this introduces an unnecessary copy and memory allocation. Further, using `astype(float, copy=False)` is fragile and raises a `ValueError` in NumPy 2.0+.

**Action:** Prefer `np.einsum` for computing sums of squares along an axis. Ensure the arrays are natively floats (like most physics/simulation states) before applying `np.einsum` directly, to avoid integer overflows and avoid explicit `astype` casts.

## 2026-04-16 - Optimizing np.linalg.norm axis reductions

**Learning:** When using `np.sum(diff**2, axis=-1)` or `np.linalg.norm(..., axis=1/2)` on multi-dimensional array operations (such as computing segment lengths or marker error metrics), using `np.einsum('...i,...i->...', diff, diff)` provides a ~2x speedup and avoids temporary array allocations. For Euclidean distances, using `np.sqrt(np.einsum(...))` is the fastest method while remaining dimension-agnostic, reducing memory pressure.

**Action:** Consistently replace `np.sum((a - b)**2, axis=-1)` and `np.linalg.norm(..., axis=X)` with `np.sqrt(np.einsum('...i,...i->...', diff, diff))` when performing reductions across small inner dimensions (like 3D coordinates).

## 2026-04-20 - Optimizing math.sqrt with math.hypot

**Learning:** When calculating Euclidean distances manually in Python (e.g., `math.sqrt(x**2 + y**2 + z**2)`), the overhead from Python's power operator (`**`) and intermediate operations makes it significantly slower than using the C-optimized `math.hypot(x, y, z)`. Benchmarks demonstrate up to a ~2x performance speedup. `math.hypot` also avoids potential intermediate overflow and underflow, making the code more mathematically robust, and reduces verbosity.

**Action:** Consistently replace manual distance calculations using `math.sqrt` and `**` with `math.hypot` for both 2D and 3D Euclidean distances in Python code when not performing bulk operations via NumPy.

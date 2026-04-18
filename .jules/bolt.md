
## 2026-04-17 - Optimize squared distance calculation with np.einsum
**Learning:** Explicit element-wise sum of squares using `np.einsum("ij,ij->i", diff, diff)` is ~2x faster than `np.sum(diff ** 2, axis=1)` because it avoids intermediate array allocations from computing the square matrix before summation.
**Action:** Default to using `np.einsum` when computing reductions like sum of squared differences over small inner dimensions.
## 2026-04-18 - Vectorize List Comprehensions with np.einsum
**Learning:** Using `np.linalg.norm` inside a list comprehension for arrays of vectors causes excessive overhead. Vectorizing this by constructing a 2D array and using `np.sqrt(np.einsum('ij,ij->i', arr, arr))` is roughly ~7x faster.
**Action:** Replace `np.mean([np.linalg.norm(v) for v in array_list])` with `np.mean(np.sqrt(np.einsum('ij,ij->i', arr, arr)))` where `arr` is `np.array(array_list)`.

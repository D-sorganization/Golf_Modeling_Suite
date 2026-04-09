## 2026-04-09 - Optimize 3D vector distance calculations
**Learning:** For arrays with small inner dimensions (like 3D coordinates), `np.linalg.norm(..., axis=1)` introduces significant reduction overhead. Explicit element-wise sum of squares with `np.sqrt(np.sum(np.square(..., dtype=float), axis=-1))` is significantly faster.
**Action:** Replace `np.linalg.norm(..., axis=1)` with the explicit element-wise approach when calculating distances for 3D coordinates.

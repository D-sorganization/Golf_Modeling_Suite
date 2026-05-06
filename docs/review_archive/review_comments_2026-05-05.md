# Review Comments Archive - 2026-05-05

Generated: 2026-05-05T22:24:24.782741

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #4028: src/shared/python/motion_matching/loaders/_align.py:90

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Recompute impact index from resampled trajectory**

`impact_idx_out` is currently derived only from `opts.impact_target_t_s`, so for `time_alignment="address"`/`"none"` (or when impact gets clipped by interpolation bounds) the returned impact frame can be unrelated to the actual speed peak. This breaks the `impact_idx` contract (`max clubhead speed`) and feeds the wrong frame into downstream anchor-cost terms...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4028#discussion_r3193108542)

---

### PR #4028: src/shared/python/motion_matching/loaders/_align.py:37

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Implement the promised 5-point impact derivative**

The function states it uses a 5-point central difference, but the current derivative is a 3-point form `((x[i+1]-x[i-1]) / dt)` with copied edge values. This diverges from the MATLAB reference implementation and can shift detected impact indices on noisy/high-curvature swings, causing Python/MATLAB alignment mismatches. Use the actual 5-point stencil so impa...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4028#discussion_r3193108549)

---


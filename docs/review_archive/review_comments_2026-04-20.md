# Review Comments Archive - 2026-04-20

Generated: 2026-04-20T11:06:48.819117

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #2857: Dockerfile:39

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Fail the image build when lockfile install fails**

The builder now masks dependency installation failures with `|| true`, so a partial or failed `requirements.lock` install still produces a “successful” image. In environments with transient index issues or an invalid lock entry, this will ship a runtime missing required packages and fail later at import/startup instead of failing fast during build.

Useful? ...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2857#discussion_r3112079588)

---

### PR #2857: Dockerfile:32

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Quote pip version specifier to avoid shell redirection**

In shell-form `RUN`, `pip>=25.3` is parsed as `pip` plus output redirection (`> =25.3`), so the version constraint is not actually passed to pip. That means the intended security floor (`pip >= 25.3`) is not guaranteed, and the command behavior depends on whatever pip version the base image already has.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2857#discussion_r3112079600)

---

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #2858: src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/src/apps/golf_gui/Simscape Multibody Data Plotters/Python Version/integrated_golf_gui_r0/golf_data_core.py:752

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Preserve near-parallel vector rotation accuracy**

Using `dot_val > 0.999999` / `< -0.999999` snaps vectors within about 0.0014 rad (~0.08°) to exact identity or 180° rotation, which is much looser than the previous `np.allclose` behavior and drops legitimate small-angle rotations. In the renderer path (`y_axis` to `direction_normalized`), this causes visible orientation error for vectors that are slightly ti...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2858#discussion_r3112157739)

---

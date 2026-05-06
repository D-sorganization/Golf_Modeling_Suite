# Review Comments Archive - 2026-05-06

Generated: 2026-05-06T15:01:31.896824

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #4090: src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/motion_matching/option4_python_bridge/tests/conftest.py:21

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Handle missing matlab package when checking marker availability**

`pytest_collection_modifyitems` calls `importlib.util.find_spec("matlab.engine")`, but on Python 3.10+ this raises `ModuleNotFoundError` when the parent `matlab` package is absent instead of returning `None`. On machines without MATLAB (the common CI/dev case this hook is meant to support), collection aborts with an INTERNALERROR before any sk...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4090#discussion_r3197765779)

---

### PR #4090: src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/motion_matching/option4_python_bridge/fit_swing_python.py:104

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Validate theta0 before starting MATLAB engine**

`fit_swing_scipy` starts the MATLAB engine before checking whether `options.theta0` has the correct length. That means a simple user-input error can trigger an unnecessary (and expensive) engine startup, and on hosts without MATLAB it will raise an engine startup failure instead of the intended `ValueError` for bad `theta0`, making argument validation unusable ...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4090#discussion_r3197765789)

---


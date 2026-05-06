"""Compare per-step vs trajectory-level surrogate held-out RMSE.

Tiny synthetic dataset, fixed seed. Marked ``slow`` because it trains two
models even at small scale. The comparison is logged and asserted to be
"both finite, both finite-RMSE" rather than ranked — both architectures are
valid Option-2 instantiations and the choice is dataset-dependent (see issue
#4044 and ``option2_nn_surrogate/APPROACH.md``).
"""

from __future__ import annotations

import logging

import numpy as np
import pytest

pytestmark = [pytest.mark.slow, pytest.mark.unit]

torch = pytest.importorskip("torch")

LOGGER = logging.getLogger(__name__)


def _make_perstep_dataset(
    n: int = 256, n_state: int = 4, n_ctrl: int = 2, seed: int = 0xC0FFEE
) -> tuple[np.ndarray, np.ndarray]:
    """Synthetic ``(q, q_dot, tau) -> q_ddot`` rows under a known linear law."""
    rng = np.random.default_rng(seed)
    x = rng.standard_normal((n, n_state + n_ctrl)).astype(np.float32)
    # Known linear map plus tiny noise — both surrogates should fit easily.
    weights = rng.standard_normal((n_state + n_ctrl, n_state)).astype(np.float32)
    y = x @ weights + 0.01 * rng.standard_normal((n, n_state)).astype(np.float32)
    return x, y


def _train_perstep(
    x: np.ndarray, y: np.ndarray, epochs: int = 30, seed: int = 0
) -> float:
    """Train the per-step ``DynamicsMLP`` and return held-out RMSE."""
    from src.shared.python.motion_matching.surrogate.perstep.train import DynamicsMLP

    torch.manual_seed(seed)
    n = x.shape[0]
    cut = int(0.8 * n)
    x_tr = torch.from_numpy(x[:cut])
    y_tr = torch.from_numpy(y[:cut])
    x_te = torch.from_numpy(x[cut:])
    y_te = torch.from_numpy(y[cut:])

    model = DynamicsMLP(
        input_dim=x.shape[1], output_dim=y.shape[1], hidden_sizes=[32, 32]
    )
    opt = torch.optim.Adam(model.parameters(), lr=3e-3)
    loss_fn = torch.nn.MSELoss()
    for _ in range(epochs):
        opt.zero_grad()
        loss = loss_fn(model(x_tr), y_tr)
        loss.backward()
        opt.step()

    model.eval()
    with torch.no_grad():
        pred = model(x_te).cpu().numpy()
    return float(np.sqrt(np.mean((pred - y_te.cpu().numpy()) ** 2)))


def _train_trajectory_surrogate_proxy(
    x: np.ndarray, y: np.ndarray, epochs: int = 30, seed: int = 0
) -> float:
    """Train a tiny trajectory-style proxy (single-MLP regressor) on the same data.

    The real trajectory-level surrogate consumes ``(B, D)`` coefficients and
    emits ``(B, N, 10)`` kinematics; constructing that input at test scale would
    explode runtime. For the comparison contract — "both architectures fit a
    held-out signal under the same fixed seed" — a comparable MLP trained on the
    same row-wise data is a fair proxy. The full trajectory-level surrogate has
    its own dedicated tests in ``test_surrogate_train.py``.
    """
    torch.manual_seed(seed + 1)
    n = x.shape[0]
    cut = int(0.8 * n)
    x_tr = torch.from_numpy(x[:cut])
    y_tr = torch.from_numpy(y[:cut])
    x_te = torch.from_numpy(x[cut:])
    y_te = torch.from_numpy(y[cut:])

    model = torch.nn.Sequential(
        torch.nn.Linear(x.shape[1], 64),
        torch.nn.GELU(),
        torch.nn.Linear(64, 64),
        torch.nn.GELU(),
        torch.nn.Linear(64, y.shape[1]),
    )
    opt = torch.optim.AdamW(model.parameters(), lr=3e-3, weight_decay=1e-4)
    loss_fn = torch.nn.MSELoss()
    for _ in range(epochs):
        opt.zero_grad()
        loss = loss_fn(model(x_tr), y_tr)
        loss.backward()
        opt.step()

    model.eval()
    with torch.no_grad():
        pred = model(x_te).cpu().numpy()
    return float(np.sqrt(np.mean((pred - y_te.cpu().numpy()) ** 2)))


def test_perstep_vs_trajectory_holdout_rmse() -> None:
    """Both architectures must converge to a finite, sub-baseline held-out RMSE."""
    x, y = _make_perstep_dataset()
    baseline = float(np.sqrt(np.mean(y[int(0.8 * x.shape[0]) :] ** 2)))

    rmse_perstep = _train_perstep(x, y)
    rmse_trajectory = _train_trajectory_surrogate_proxy(x, y)

    LOGGER.info(
        "perstep_rmse=%.4f trajectory_proxy_rmse=%.4f baseline=%.4f",
        rmse_perstep,
        rmse_trajectory,
        baseline,
    )

    assert np.isfinite(rmse_perstep)
    assert np.isfinite(rmse_trajectory)
    assert rmse_perstep < baseline, (
        f"per-step did not beat trivial baseline: {rmse_perstep} >= {baseline}"
    )
    assert rmse_trajectory < baseline, (
        f"trajectory proxy did not beat trivial baseline: "
        f"{rmse_trajectory} >= {baseline}"
    )

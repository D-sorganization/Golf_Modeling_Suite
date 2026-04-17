import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

ca = MagicMock()
pin = MagicMock()
cpin = MagicMock()

_OPT_ARM_MOCKS = {
    "casadi": ca,
    "pinocchio": pin,
    "pinocchio.casadi": cpin,
}

sys.modules.pop("src.shared.python.optimization.examples.optimize_arm", None)

with patch.dict(sys.modules, _OPT_ARM_MOCKS):
    from src.shared.python.optimization.examples.optimize_arm import main  # noqa: E402

_module_patcher = patch.dict(sys.modules, _OPT_ARM_MOCKS)


def setup_module(module):
    _module_patcher.start()


def teardown_module(module):
    _module_patcher.stop()


@pytest.fixture
def mock_casadi():
    opti = MagicMock()
    mock_var = MagicMock()
    mock_var.__getitem__.return_value = MagicMock()
    mock_var.__len__.return_value = 2

    mock_var.__eq__ = MagicMock()  # type: ignore[method-assign]
    mock_var.__eq__.return_value = MagicMock()  # type: ignore[attr-defined]

    mock_slice_return = MagicMock()
    mock_slice_return.__len__.return_value = 2
    mock_slice_return.__eq__ = MagicMock()  # type: ignore[method-assign]
    mock_slice_return.__eq__.return_value = MagicMock()  # type: ignore[attr-defined]
    mock_var.__getitem__.return_value = mock_slice_return

    opti.variable.return_value = mock_var
    opti.bounded.return_value = MagicMock()
    opti.subject_to.return_value = MagicMock()
    opti.minimize.return_value = MagicMock()
    opti.solver.return_value = MagicMock()

    sol = MagicMock()
    call_count = 0

    def value_side_effect(arg):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return np.zeros((2, 41))
        if call_count == 2:
            return np.zeros((2, 41))
        if call_count == 3:
            return np.zeros((2, 40))
        return 0.1234

    sol.value.side_effect = value_side_effect
    opti.solve.return_value = sol
    ca.Opti.return_value = opti
    ca.sumsqr.return_value = MagicMock()

    return opti


@pytest.fixture
def mock_pinocchio():
    model = MagicMock()
    model.nq = 2
    model.nv = 2
    model.nu = 2
    pin.buildModelFromUrdf.return_value = model

    cmodel = MagicMock()
    cpin.Model.return_value = cmodel
    cpin.Model.createData.return_value = MagicMock()
    cpin.aba.return_value = MagicMock()

    return model


def test_main_execution(mock_casadi, mock_pinocchio):
    with (
        patch("os.path.exists", return_value=True),
        patch(
            "src.shared.python.optimization.examples.optimize_arm.np.savetxt"
        ) as mock_save,
    ):
        main()

        mock_casadi.solver.assert_called_with(
            "ipopt", {"expand": True}, {"max_iter": 1000, "print_level": 5}
        )
        mock_casadi.solve.assert_called()
        assert mock_save.call_count == 3


def test_main_missing_dependencies():
    with (
        patch(
            "src.shared.python.optimization.examples.optimize_arm.DEPENDENCIES_AVAILABLE",
            False,
        ),
        patch(
            "src.shared.python.optimization.examples.optimize_arm.MISSING_DEP_ERROR",
            "Test Error",
            create=True,
        ),
        patch(
            "src.shared.python.optimization.examples.optimize_arm.logger"
        ) as mock_logger,
    ):
        main()
        mock_logger.error.assert_any_call(
            "Skipping optimize_arm.py due to missing dependencies: Test Error"
        )


def test_urdf_not_found():
    with patch("os.path.exists", return_value=False), pytest.raises(SystemExit):
        main()


def test_optimization_failure(mock_casadi, mock_pinocchio):
    mock_casadi.solve.side_effect = RuntimeError("Infeasible")

    with patch("os.path.exists", return_value=True), pytest.raises(SystemExit):
        main()

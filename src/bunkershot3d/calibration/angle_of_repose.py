"""
Angle of repose calibration experiment.

The underlying simulation has not yet been written (see #5486 and the
follow-up #5554). To keep the calibration optimizer test suite useful
without misleading downstream consumers, the placeholder formula now
lives behind an explicit ``use_mock=True`` kwarg — calling
``run_simulation`` with the default path raises ``NotImplementedError``.
"""

from pathlib import Path  # noqa: F401  (kept for forward-compat with the real impl)


def _mock_angle_of_repose(friction: float) -> float:
    """Placeholder linear mapping used by tests and the optimizer fixture.

    This is **not** physics — it is a deliberately simple monotone
    mapping that lets the calibration optimizer's plumbing be exercised
    end-to-end without a working DEM solver. Real callers must wait
    for the implementation tracked in #5554.

    tracked: #5554
    """
    return 20.0 + (friction * 24.0)


class AngleOfReposeExperiment:
    """Simulates pouring particles from a lifted cylinder to measure final pile angle."""

    def __init__(self, backend: str = "chrono") -> None:
        """
        Initialize the experiment.
        Args:
            backend: The simulator backend to use (chrono, liggghts, mpm)
        """
        self.backend = backend
        self.target_angle = 32.0  # degrees

    def run_simulation(self, params: dict, *, use_mock: bool = False) -> float:
        """
        Run the calibration experiment for a given parameter set.

        Args:
            params: dict of DEM contact-model parameters. Must contain
                ``friction_coefficient``.
            use_mock: When ``True``, return the placeholder linear
                mapping ``_mock_angle_of_repose(friction)``. The real
                DEM experiment has not been implemented yet (see #5554),
                so the default path raises ``NotImplementedError`` to
                prevent silent misuse.

        Returns:
            The measured angle of repose in degrees.
        """
        if not use_mock:
            raise NotImplementedError(  # tracked: #5554
                "Real angle-of-repose simulation is not implemented yet; "
                "pass use_mock=True to get the placeholder formula. "
                "Tracked: #5554."
            )

        friction = params.get("friction_coefficient", 0.5)
        return _mock_angle_of_repose(friction)

    def calibrate(self) -> dict:
        """
        Run Bayesian optimization / CMA-ES to find optimal parameters.
        """
        # Mock calibration loop
        best_params = {"friction_coefficient": 0.5, "restitution_coefficient": 0.3}
        return best_params

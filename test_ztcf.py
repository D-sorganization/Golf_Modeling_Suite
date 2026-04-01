import numpy as np
from src.shared.python.biomechanics.ztcf import ZTCFResult

def test_ztcf_magnitudes():
    forces = np.array([
        [1.0, 2.0, 3.0],
        [4.0, 5.0, 6.0]
    ])
    accel = np.zeros(2)
    result = ZTCFResult(joint_forces=forces, joint_accelerations=accel, n_joints=2)

    expected_mags = np.linalg.norm(forces, axis=1)
    expected_max = float(np.max(expected_mags))

    np.testing.assert_allclose(result.magnitudes(), expected_mags)
    assert np.isclose(result.max_magnitude(), expected_max)
    print("Test passed!")

if __name__ == "__main__":
    test_ztcf_magnitudes()

import sqlite3

import h5py
import numpy as np
from src.shared.python.engine_core.interfaces import PhysicsEngine
from src.shared.python.ml.dataset_generator import DatasetGenerator


class MockEngine(PhysicsEngine):
    def __init__(self):
        self.t = 0.0
        self.q = np.array([0.0, 0.0])
        self.v = np.array([0.0, 0.0])
        self.M = np.eye(2)

    def get_full_state(self):
        return {"t": self.t, "q": self.q, "v": self.v, "M": self.M}

    def set_state(self, q, v):
        self.q = q
        self.v = v
        self.t = 0.0

    def step(self, tau, dt):
        self.v += tau * dt
        self.q += self.v * dt
        self.t += dt

    def compute_contact_forces(self):
        return np.zeros(6)

    # Add remaining abstract methods from PhysicsEngine
    def compute_bias_forces(self, *args, **kwargs):
        return np.zeros(2)

    def compute_control_acceleration(self, *args, **kwargs):
        return np.zeros(2)

    def compute_drift_acceleration(self, *args, **kwargs):
        return np.zeros(2)

    def compute_gravity_forces(self, *args, **kwargs):
        return np.zeros(2)

    def compute_inverse_dynamics(self, *args, **kwargs):
        return np.zeros(2)

    def compute_jacobian(self, *args, **kwargs):
        return np.zeros((2, 2))

    def compute_mass_matrix(self, *args, **kwargs):
        return self.M

    def compute_ztcf(self, *args, **kwargs):
        return np.zeros(2)

    def compute_zvcf(self, *args, **kwargs):
        return np.zeros(2)

    def forward(self, *args, **kwargs):
        pass

    def get_state(self, *args, **kwargs):
        return self.q, self.v

    def get_time(self, *args, **kwargs):
        return self.t

    def load_from_path(self, *args, **kwargs):
        pass

    def load_from_string(self, *args, **kwargs):
        pass

    @property
    def model_name(self, *args, **kwargs):
        return "mock"

    def reset(self, *args, **kwargs):
        pass

    def set_control(self, *args, **kwargs):
        pass


def test_dataset_generator_creates_files(tmp_path):
    engine = MockEngine()
    generator = DatasetGenerator(tmp_path, "test_data", engine)

    # Generate some data to create the h5 file
    def init_fn():
        return np.zeros(2), np.zeros(2)

    def policy_fn(t, q, v):
        return np.zeros(2)

    generator.generate_batch(1, 10, init_fn, policy_fn)

    assert generator.h5_path.exists()
    assert generator.db_path.exists()


def test_dataset_generator_generates_batch(tmp_path):
    engine = MockEngine()
    generator = DatasetGenerator(tmp_path, "test_batch", engine, seed=42)

    def init_fn():
        return np.random.rand(2), np.random.rand(2)

    def policy_fn(t, q, v):
        return -0.1 * q - 0.05 * v

    generator.generate_batch(
        num_runs=2,
        frames_per_run=10,
        initial_conditions_fn=init_fn,
        control_policy_fn=policy_fn,
    )

    # Check HDF5
    with h5py.File(generator.h5_path, "r") as h5f:
        assert "runs" in h5f
        runs = list(h5f["runs"].keys())
        assert len(runs) == 2

        run_data = h5f["runs"][runs[0]]
        assert "kinematics/q" in run_data
        assert run_data["kinematics/q"].shape == (10, 2)
        assert "kinematics/v" in run_data
        assert "kinetics/tau" in run_data

    # Check SQLite
    with sqlite3.connect(generator.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM simulations")
        count = cursor.fetchone()[0]
        assert count == 2

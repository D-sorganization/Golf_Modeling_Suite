from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

import h5py
import numpy as np
from src.shared.python.dashboard.recorder import GenericPhysicsRecorder
from src.shared.python.engine_core.interfaces import PhysicsEngine
from src.shared.python.logging_pkg.logging_config import get_logger

logger = get_logger(__name__)


class DatasetGenerator:
    """Generates ML-ready datasets from physics engine simulations.

    Compiles kinematics, kinetics, and model data into HDF5 and SQLite formats
    suitable for neural network training and validation.
    """

    def __init__(
        self,
        output_dir: str | Path,
        dataset_name: str,
        engine: PhysicsEngine,
        seed: int | None = None,
    ):
        self.output_dir = Path(output_dir)
        self.dataset_name = dataset_name
        self.engine = engine
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.h5_path = self.output_dir / f"{dataset_name}.h5"
        self.db_path = self.output_dir / f"{dataset_name}.sqlite"

        self._init_sqlite()

    def _init_sqlite(self) -> None:
        """Initialize SQLite database for metadata."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS simulations (
                    run_id TEXT PRIMARY KEY,
                    seed INTEGER,
                    num_frames INTEGER,
                    dt REAL,
                    engine_type TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def generate_batch(
        self,
        num_runs: int,
        frames_per_run: int,
        initial_conditions_fn: callable,
        control_policy_fn: callable,
        dt: float = 0.01,
    ) -> None:
        """Generate a batch of simulation runs."""
        with h5py.File(self.h5_path, "a") as h5f:
            if "runs" not in h5f:
                h5f.create_group("runs")

            for i in range(num_runs):
                run_id = str(uuid4())
                logger.info(f"Generating run {i + 1}/{num_runs} (ID: {run_id})")

                # Setup
                q0, v0 = initial_conditions_fn()
                # Assuming engine has a method to set state
                try:
                    self.engine.set_state(q0, v0)
                except AttributeError:
                    logger.warning("Engine does not support set_state. Continuing...")

                recorder = GenericPhysicsRecorder(
                    self.engine,
                    max_samples=frames_per_run,
                    initial_capacity=frames_per_run,
                )
                recorder.set_analysis_config({"track_total_control": True})
                recorder.start()

                # Run simulation
                for _step in range(frames_per_run):
                    full_state = self.engine.get_full_state()
                    tau = control_policy_fn(
                        full_state["t"], full_state["q"], full_state["v"]
                    )

                    try:
                        self.engine.step(tau, dt)
                    except AttributeError as e:
                        raise RuntimeError("Engine must support step") from e

                    recorder.record_step(tau)

                recorder.stop()

                # Save to disk
                self._save_run_h5(h5f, run_id, recorder.data, frames_per_run)
                self._save_run_sqlite(run_id, frames_per_run, dt)

    def _save_run_h5(
        self, h5f: h5py.File, run_id: str, data: dict[str, Any], num_frames: int
    ) -> None:
        """Save a single run's data to HDF5."""
        run_group = h5f["runs"].create_group(run_id)

        # Save kinematics
        kinematics = run_group.create_group("kinematics")
        if data.get("joint_positions") is not None:
            kinematics.create_dataset("q", data=data["joint_positions"][:num_frames])
        if data.get("joint_velocities") is not None:
            kinematics.create_dataset("v", data=data["joint_velocities"][:num_frames])
        if data.get("joint_accelerations") is not None:
            kinematics.create_dataset(
                "a", data=data["joint_accelerations"][:num_frames]
            )

        # Save kinetics
        kinetics = run_group.create_group("kinetics")
        if data.get("joint_torques") is not None:
            kinetics.create_dataset("tau", data=data["joint_torques"][:num_frames])
        if data.get("ground_forces") is not None:
            kinetics.create_dataset(
                "contact_forces", data=data["ground_forces"][:num_frames]
            )
        if data.get("total_energy") is not None:
            kinetics.create_dataset("energy", data=data["total_energy"][:num_frames])

        # Save times
        run_group.create_dataset("times", data=data["times"][:num_frames])

    def _save_run_sqlite(self, run_id: str, num_frames: int, dt: float) -> None:
        """Save run metadata to SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO simulations (run_id, seed, num_frames, dt, engine_type)
                VALUES (?, ?, ?, ?, ?)
            """,
                (run_id, self.seed, num_frames, dt, self.engine.__class__.__name__),
            )
            conn.commit()

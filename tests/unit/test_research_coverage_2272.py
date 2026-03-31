"""Coverage tests for research and learning modules.

Targeting zero/low-coverage modules identified in issue #2272:
- src/research/deformable/objects.py (290 stmts, 0%)
- src/research/multi_robot/coordination.py (189 stmts, 0%)
- src/research/multi_robot/system.py (185 stmts, 0%)
- src/research/differentiable/engine.py (253 stmts, 0%)
- src/research/mpc/controller.py (182 stmts, 0%)
- src/research/mpc/specialized.py (125 stmts, 0%)
- src/learning/imitation/learners.py (353 stmts, 13%)
"""

from __future__ import annotations

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# src/research/deformable/objects.py
# ---------------------------------------------------------------------------


class TestMaterialProperties:
    """Tests for deformable MaterialProperties dataclass."""

    def test_default_creation(self) -> None:
        from src.research.deformable.objects import MaterialProperties

        mat = MaterialProperties()
        assert mat.youngs_modulus > 0
        assert mat.density > 0
        assert 0 < mat.poisson_ratio < 0.5

    def test_custom_properties(self) -> None:
        from src.research.deformable.objects import MaterialProperties

        mat = MaterialProperties(
            youngs_modulus=200e9,
            poisson_ratio=0.3,
            density=7800.0,
            damping=0.02,
        )
        assert mat.youngs_modulus == pytest.approx(200e9)
        assert mat.poisson_ratio == pytest.approx(0.3)
        assert mat.density == pytest.approx(7800.0)

    def test_bending_stiffness_optional(self) -> None:
        from src.research.deformable.objects import MaterialProperties

        mat_with = MaterialProperties(bending_stiffness=500.0)
        assert mat_with.bending_stiffness == pytest.approx(500.0)

        mat_without = MaterialProperties()
        assert mat_without.bending_stiffness is None

    def test_shear_stiffness_optional(self) -> None:
        from src.research.deformable.objects import MaterialProperties

        mat = MaterialProperties(shear_stiffness=1000.0)
        assert mat.shear_stiffness == pytest.approx(1000.0)

    def test_gravity_constant(self) -> None:
        from src.research.deformable.objects import GRAVITY

        assert pytest.approx(9.81) == GRAVITY


class TestDeformableObjectCreation:
    """Tests for deformable object classes."""

    def test_cable_creation(self) -> None:
        from src.research.deformable.objects import Cable, MaterialProperties

        mesh = np.linspace([0, 0, 0], [1, 0, 0], 10)
        mat = MaterialProperties()
        cable = Cable(mesh=mesh, material=mat)
        assert cable is not None

    def test_cloth_creation(self) -> None:
        from src.research.deformable.objects import Cloth, MaterialProperties

        mesh = np.zeros((4, 3))
        mesh[0] = [0, 0, 0]
        mesh[1] = [1, 0, 0]
        mesh[2] = [0, 1, 0]
        mesh[3] = [1, 1, 0]
        mat = MaterialProperties()
        cloth = Cloth(mesh=mesh, width=2, height=2, material=mat)
        assert cloth is not None

    def test_soft_body_creation(self) -> None:
        from src.research.deformable.objects import MaterialProperties, SoftBody

        mesh = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
        tetra = np.array([[0, 1, 2, 3]], dtype=int)
        mat = MaterialProperties()
        body = SoftBody(mesh=mesh, tetrahedra=tetra, material=mat)
        assert body is not None


# ---------------------------------------------------------------------------
# src/research/multi_robot/coordination.py
# ---------------------------------------------------------------------------


class TestFormationConfig:
    """Tests for multi-robot FormationConfig."""

    def test_basic_creation(self) -> None:
        from src.research.multi_robot.coordination import FormationConfig

        positions = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float)
        config = FormationConfig(name="triangle", positions=positions)
        assert config.name == "triangle"
        assert config.reference_frame == "leader"

    def test_with_orientations(self) -> None:
        from src.research.multi_robot.coordination import FormationConfig

        positions = np.array([[0, 0, 0], [1, 0, 0]], dtype=float)
        orientations = np.array([[0, 0, 0], [0, 0, 0]], dtype=float)
        config = FormationConfig(
            name="line", positions=positions, orientations=orientations
        )
        assert config.orientations is not None

    def test_reference_frame_world(self) -> None:
        from src.research.multi_robot.coordination import FormationConfig

        positions = np.zeros((3, 3))
        config = FormationConfig(
            name="test", positions=positions, reference_frame="world"
        )
        assert config.reference_frame == "world"


class TestFormationController:
    """Tests for FormationController."""

    def test_creation(self) -> None:
        from src.research.multi_robot.coordination import (
            FormationConfig,
            FormationController,
        )

        positions = np.array([[0, 0, 0], [2, 0, 0]], dtype=float)
        config = FormationConfig(name="pair", positions=positions)
        controller = FormationController(
            robots=["robot_0", "robot_1"], formation=config
        )
        assert controller is not None

    def test_robot_list(self) -> None:
        from src.research.multi_robot.coordination import (
            FormationConfig,
            FormationController,
        )

        robots = ["r0", "r1", "r2"]
        positions = np.zeros((3, 3))
        config = FormationConfig(name="triangle", positions=positions)
        ctrl = FormationController(robots=robots, formation=config)
        assert ctrl is not None


# ---------------------------------------------------------------------------
# src/research/multi_robot/system.py
# ---------------------------------------------------------------------------


class TestTaskEnums:
    """Tests for TaskStatus and TaskType enums."""

    def test_task_status_values(self) -> None:
        from src.research.multi_robot.system import TaskStatus

        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.ASSIGNED.value == "assigned"

    def test_task_type_values(self) -> None:
        from src.research.multi_robot.system import TaskType

        assert TaskType.MOVE_TO.value == "move_to"
        assert TaskType.PICK.value == "pick"
        assert TaskType.PLACE.value == "place"
        assert TaskType.INSPECT.value == "inspect"
        assert TaskType.WAIT.value == "wait"

    def test_all_task_statuses_accessible(self) -> None:
        from src.research.multi_robot.system import TaskStatus

        statuses = list(TaskStatus)
        assert len(statuses) == 5

    def test_all_task_types_accessible(self) -> None:
        from src.research.multi_robot.system import TaskType

        types = list(TaskType)
        assert len(types) >= 5


class TestTaskDataclass:
    """Tests for Task dataclass."""

    def test_basic_task_creation(self) -> None:
        from src.research.multi_robot.system import Task, TaskStatus, TaskType

        task = Task(
            task_id="task_001",
            task_type=TaskType.MOVE_TO,
            target_position=np.array([1.0, 0.0, 0.5]),
        )
        assert task.task_id == "task_001"
        assert task.task_type == TaskType.MOVE_TO
        assert task.status == TaskStatus.PENDING

    def test_task_with_priority(self) -> None:
        from src.research.multi_robot.system import Task, TaskType

        task = Task(
            task_id="high_priority",
            task_type=TaskType.PICK,
            priority=10,
        )
        assert task.priority == 10

    def test_task_default_status_is_pending(self) -> None:
        from src.research.multi_robot.system import Task, TaskStatus, TaskType

        task = Task(task_id="t1", task_type=TaskType.WAIT)
        assert task.status == TaskStatus.PENDING

    def test_task_dependencies(self) -> None:
        from src.research.multi_robot.system import Task, TaskType

        task = Task(
            task_id="dependent_task",
            task_type=TaskType.PLACE,
            dependencies=["task_001", "task_002"],
        )
        assert len(task.dependencies) == 2


class TestTaskCoordinator:
    """Tests for TaskCoordinator."""

    def test_creation(self) -> None:
        from src.research.multi_robot.system import TaskCoordinator

        coord = TaskCoordinator()
        assert coord is not None

    def test_multi_robot_system_creation(self) -> None:
        from src.research.multi_robot.system import MultiRobotSystem

        system = MultiRobotSystem()
        assert system is not None


# ---------------------------------------------------------------------------
# src/research/mpc/controller.py
# ---------------------------------------------------------------------------


class TestMPCDataclasses:
    """Tests for MPC dataclasses."""

    def test_cost_function_creation(self) -> None:
        from src.research.mpc.controller import CostFunction

        Q = np.eye(4)
        R = np.eye(2)
        cost = CostFunction(Q=Q, R=R)
        assert cost is not None

    def test_cost_function_with_terminal(self) -> None:
        from src.research.mpc.controller import CostFunction

        n, m = 4, 2
        Q = np.eye(n)
        R = np.eye(m)
        P = 2 * np.eye(n)
        cost = CostFunction(Q=Q, R=R, P=P)
        assert cost.P is not None

    def test_cost_function_with_refs(self) -> None:
        from src.research.mpc.controller import CostFunction

        Q = np.eye(3)
        R = np.eye(2)
        x_ref = np.ones(3)
        u_ref = np.zeros(2)
        cost = CostFunction(Q=Q, R=R, x_ref=x_ref, u_ref=u_ref)
        assert cost.x_ref is not None
        np.testing.assert_array_equal(cost.u_ref, np.zeros(2))

    def test_constraint_creation_mixed(self) -> None:
        from src.research.mpc.controller import Constraint

        A = np.eye(4)
        B = np.zeros((4, 2))
        lb = -np.ones(4)
        ub = np.ones(4)
        constraint = Constraint(A=A, B=B, lb=lb, ub=ub)
        assert constraint.constraint_type == "mixed"

    def test_constraint_default_type(self) -> None:
        from src.research.mpc.controller import Constraint

        c = Constraint()
        assert c.constraint_type == "mixed"
        assert c.A is None

    def test_mpc_result_success(self) -> None:
        from src.research.mpc.controller import MPCResult

        result = MPCResult(
            success=True,
            optimal_states=np.zeros((10, 4)),
            optimal_controls=np.zeros((9, 2)),
            cost=15.3,
            solve_time=0.012,
            iterations=5,
        )
        assert result.success is True
        assert result.cost == pytest.approx(15.3)
        assert result.iterations == 5

    def test_mpc_result_failure(self) -> None:
        from src.research.mpc.controller import MPCResult

        result = MPCResult(
            success=False,
            optimal_states=None,
            optimal_controls=None,
            cost=float("inf"),
        )
        assert result.success is False
        assert result.optimal_states is None


# ---------------------------------------------------------------------------
# src/research/mpc/specialized.py
# ---------------------------------------------------------------------------


class TestCentroidalState:
    """Tests for CentroidalState dataclass."""

    def test_creation(self) -> None:
        from src.research.mpc.specialized import CentroidalState

        state = CentroidalState(
            com_position=np.array([0.0, 0.0, 0.9]),
            com_velocity=np.zeros(3),
            angular_momentum=np.zeros(3),
            contact_forces={},
        )
        assert state is not None
        np.testing.assert_array_equal(state.com_position, [0, 0, 0.9])

    def test_with_contact_forces(self) -> None:
        from src.research.mpc.specialized import CentroidalState

        state = CentroidalState(
            com_position=np.array([0, 0, 1.0]),
            com_velocity=np.array([0.1, 0, 0]),
            angular_momentum=np.zeros(3),
            contact_forces={
                "left_foot": np.array([0, 0, 400.0]),
                "right_foot": np.array([0, 0, 400.0]),
            },
        )
        assert "left_foot" in state.contact_forces
        assert len(state.contact_forces) == 2


# ---------------------------------------------------------------------------
# src/research/differentiable/engine.py
# ---------------------------------------------------------------------------


class TestOptimizationResult:
    """Tests for OptimizationResult dataclass."""

    def test_successful_result(self) -> None:
        from src.research.differentiable.engine import OptimizationResult

        result = OptimizationResult(
            success=True,
            optimal_states=np.zeros((20, 4)),
            optimal_controls=np.zeros((19, 2)),
            final_cost=0.5,
            iterations=50,
            gradient_norm=1e-6,
        )
        assert result.success is True
        assert result.final_cost == pytest.approx(0.5)
        assert result.gradient_norm < 1e-5

    def test_failed_result(self) -> None:
        from src.research.differentiable.engine import OptimizationResult

        result = OptimizationResult(
            success=False,
            optimal_states=np.array([]),
            optimal_controls=np.array([]),
            final_cost=float("inf"),
            iterations=100,
            gradient_norm=10.0,
        )
        assert result.success is False
        assert result.gradient_norm > 1.0

    def test_autodiff_backend_enum(self) -> None:
        from src.research.differentiable.engine import AutodiffBackend

        assert AutodiffBackend is not None
        backends = list(AutodiffBackend)
        assert len(backends) > 0


# ---------------------------------------------------------------------------
# src/learning/imitation/learners.py
# ---------------------------------------------------------------------------


class TestTrainingConfig:
    """Tests for TrainingConfig dataclass."""

    def test_default_config(self) -> None:
        from src.learning.imitation.learners import TrainingConfig

        config = TrainingConfig()
        assert config.epochs == 100
        assert config.batch_size == 256
        assert config.learning_rate == pytest.approx(0.001)
        assert config.dropout == 0.0

    def test_custom_config(self) -> None:
        from src.learning.imitation.learners import TrainingConfig

        config = TrainingConfig(
            epochs=50,
            batch_size=128,
            learning_rate=0.0001,
            weight_decay=1e-4,
        )
        assert config.epochs == 50
        assert config.batch_size == 128
        assert config.learning_rate == pytest.approx(0.0001)

    def test_hidden_sizes_default(self) -> None:
        from src.learning.imitation.learners import TrainingConfig

        config = TrainingConfig()
        assert isinstance(config.hidden_sizes, list)
        assert len(config.hidden_sizes) > 0

    def test_activation_default(self) -> None:
        from src.learning.imitation.learners import TrainingConfig

        config = TrainingConfig()
        assert config.activation == "relu"


class TestDemonstration:
    """Tests for Demonstration dataclass."""

    def test_basic_creation(self) -> None:
        from src.learning.imitation.learners import Demonstration

        T = 100
        n_joints = 7
        timestamps = np.linspace(0, 1, T)
        positions = np.random.default_rng(42).normal(0, 0.1, (T, n_joints))
        velocities = np.random.default_rng(42).normal(0, 0.5, (T, n_joints))

        demo = Demonstration(
            timestamps=timestamps,
            joint_positions=positions,
            joint_velocities=velocities,
        )
        assert demo is not None
        assert len(demo.timestamps) == T
        assert demo.success is True

    def test_with_actions(self) -> None:
        from src.learning.imitation.learners import Demonstration

        T = 50
        n_joints = 6
        timestamps = np.linspace(0, 0.5, T)
        positions = np.zeros((T, n_joints))
        velocities = np.zeros((T, n_joints))
        actions = np.random.default_rng(0).uniform(-1, 1, (T, n_joints))

        demo = Demonstration(
            timestamps=timestamps,
            joint_positions=positions,
            joint_velocities=velocities,
            actions=actions,
            task_id="golf_swing_001",
        )
        assert demo.task_id == "golf_swing_001"
        assert demo.actions is not None

    def test_failed_demonstration(self) -> None:
        from src.learning.imitation.learners import Demonstration

        T = 20
        demo = Demonstration(
            timestamps=np.linspace(0, 0.2, T),
            joint_positions=np.zeros((T, 3)),
            joint_velocities=np.zeros((T, 3)),
            success=False,
        )
        assert demo.success is False

    def test_metadata_field(self) -> None:
        from src.learning.imitation.learners import Demonstration

        T = 10
        demo = Demonstration(
            timestamps=np.linspace(0, 0.1, T),
            joint_positions=np.zeros((T, 3)),
            joint_velocities=np.zeros((T, 3)),
            metadata={"club": "driver", "course": "test"},
        )
        assert demo.metadata["club"] == "driver"


class TestDemonstrationDataset:
    """Tests for DemonstrationDataset."""

    def test_empty_dataset(self) -> None:
        from src.learning.imitation.learners import DemonstrationDataset

        dataset = DemonstrationDataset()
        assert dataset is not None

    def test_dataset_with_demonstrations(self) -> None:
        from src.learning.imitation.learners import Demonstration, DemonstrationDataset

        T = 30
        demo1 = Demonstration(
            timestamps=np.linspace(0, 1, T),
            joint_positions=np.zeros((T, 4)),
            joint_velocities=np.zeros((T, 4)),
        )
        demo2 = Demonstration(
            timestamps=np.linspace(0, 0.5, T),
            joint_positions=np.ones((T, 4)),
            joint_velocities=np.zeros((T, 4)),
        )
        dataset = DemonstrationDataset(demonstrations=[demo1, demo2])
        assert dataset is not None


class TestBehaviorCloningCreation:
    """Tests for BehaviorCloning learner instantiation."""

    def test_basic_creation(self) -> None:
        from src.learning.imitation.learners import BehaviorCloning

        bc = BehaviorCloning(observation_dim=10, action_dim=4)
        assert bc is not None

    def test_creation_with_config(self) -> None:
        from src.learning.imitation.learners import BehaviorCloning, TrainingConfig

        config = TrainingConfig(epochs=5, batch_size=32)
        bc = BehaviorCloning(observation_dim=12, action_dim=6, config=config)
        assert bc is not None

    def test_dagger_creation(self) -> None:
        from src.learning.imitation.learners import DAgger

        dagger = DAgger(observation_dim=8, action_dim=4)
        assert dagger is not None

    def test_gail_creation(self) -> None:
        from src.learning.imitation.learners import GAIL

        gail = GAIL(observation_dim=8, action_dim=4)
        assert gail is not None

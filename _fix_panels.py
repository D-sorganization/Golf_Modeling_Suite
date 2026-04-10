"""Fix build_triple_panel and build_golfer_panel - extract callback classes."""
import ast
from pathlib import Path

path = Path('src/shared/python/pendulum_simulator/gui/panel_builders.py')
content = path.read_text(encoding='utf-8')

# ──────────────────────────────────────────────────────────────────────────
# Part 1: build_triple_panel
# ──────────────────────────────────────────────────────────────────────────

OLD_TRIPLE = '''def build_triple_panel(main_window: Any) -> SimulationPanel:
    """Build and return the triple pendulum simulation panel.

    Parameters
    ----------
    main_window : MainWindow
        The main window instance (used to access state if needed).

    Returns
    -------
    SimulationPanel
        A fully wired simulation panel for the triple pendulum model.
    """
    controls = ControlsWidgetTriple()
    pendulum = PendulumWidget()
    matrix = TripleMatrixWidget()
    torque_history = TorqueHistoryWidget()

    def build_params(p: dict) -> TriplePendulumParams:
        tilt_rad = np.radians(p.get("tilt_deg", 0.0))
        g = GRAVITY_MSS if p.get("gravity_on", True) else 0.0
        g_eff = g * float(np.cos(tilt_rad))  # (#1113)
        pendulum.set_tilt_angle(tilt_rad)
        pendulum.set_view_azimuth(np.radians(p.get("azimuth_deg", 0.0)))  # (#1118)
        return TriplePendulumParams(
            m1=p["m1"],
            m2=p["m2"],
            m3=p["m3"],
            L1=p["L1"],
            L2=p["L2"],
            L3=p["L3"],
            g=g_eff,
            b1=p.get("b1", 0.0),
            b2=p.get("b2", 0.0),
            b3=p.get("b3", 0.0),
            mu1=p.get("mu1", 0.0),
            mu2=p.get("mu2", 0.0),
            mu3=p.get("mu3", 0.0),
            scapula_offset_rad=np.radians(p.get("scapula_deg", 0.0)),
        )

    def build_state(p: dict) -> np.ndarray:
        return np.array(
            [
                p["theta1_rad"],
                p["phi1_rad"],
                p["phi2_rad"],
                p["dtheta1"],
                p["dphi1"],
                p["dphi2"],
            ],
        )

    def build_torque(p: dict) -> object:
        return make_polynomial_torque_triple(
            p["shoulder_coeffs"],
            p["elbow_coeffs"],
            p["wrist_coeffs"],
        )

    def build_limits(p: dict) -> JointLimitsNDOF | None:
        if not p.get("enable_limits", False):
            return None
        return JointLimitsNDOF(
            angle_min=np.array(p["limit_mins_rad"]),
            angle_max=np.array(p["limit_maxs_rad"]),
            stiffness=p.get("limit_stiffness", 500.0),
        )

    def build_clamp(p: dict) -> np.ndarray | None:
        if not p.get("enable_clamp", False):
            return None
        return np.array(p["torque_limits"])

    # Optimizer (#1109)
    optimizer = OptimizationWidget(
        model_name="Triple Pendulum",
        n_torque_params=3,
    )

    def _make_triple_objective(p: dict) -> Callable:
        """Build a tip-speed objective from current controls."""
        params = build_params(p)
        initial_state = build_state(p)
        t_end = p["t_end"]
        limits = build_limits(p)
        clamp = build_clamp(p)

        def objective(coeffs: np.ndarray) -> float:
            n_third = len(coeffs) // 3
            s_c = list(coeffs[:n_third])
            e_c = list(coeffs[n_third : 2 * n_third])
            w_c = list(coeffs[2 * n_third :])
            torque_func = make_polynomial_torque_triple(s_c, e_c, w_c)
            try:
                result = run_simulation_triple(
                    params=params,
                    initial_state=initial_state,
                    t_end=t_end,
                    torque_func=torque_func,  # type: ignore[arg-type]
                    torque_limits=clamp,
                    limits=limits,
                )
                vels = result.joint_velocities_at(result.n_steps - 1)  # type: ignore[attr-defined]
                tip_v = vels.get("tip", (0, 0))
                speed = float(np.hypot(tip_v[0], tip_v[1]))
                return -speed
            except (
                RuntimeError,
                ValueError,
                ArithmeticError,
            ) as exc:  # noqa: BLE001
                logger.debug("triple objective simulation failed: %s", exc)
                return 0.0

        return objective

    panel = SimulationPanel(
        controls=controls,
        pendulum=pendulum,  # type: ignore[arg-type]
        matrix=matrix,  # type: ignore[arg-type]
        params_builder=build_params,
        torque_builder=build_torque,
        state_builder=build_state,
        run_simulation=run_simulation_triple,
        torque_history=torque_history,
        limits_builder=build_limits,
        clamp_builder=build_clamp,
        optimizer=optimizer,
        objective_builder=_make_triple_objective,
    )
    panel._settings_key = "splitter_triple"

    # Wire perturbation panel (#1284)
    perturb = PerturbationPanel()

    def _triple_simulate_fn(coeffs: list) -> object:
        p = controls.get_params()
        params = build_params(p)
        initial_state = build_state(p)
        limits = build_limits(p)
        clamp = build_clamp(p)
        torque_func = make_polynomial_torque_triple(coeffs[0], coeffs[1], coeffs[2])
        return run_simulation_triple(
            params=params,
            initial_state=initial_state,
            t_end=p["t_end"],
            torque_func=torque_func,  # type: ignore[arg-type]
            limits=limits,
            clamp=clamp,
        )

    def _triple_extract_fn(result: object) -> dict:
        res = result  # type: ignore[assignment]
        pos = res.positions_at(res.n_steps - 1)  # type: ignore[attr-defined]
        tip_xy = pos.get("tip", (0.0, 0.0))
        # Triple pendulum has no joint_velocities_at; approximate from last two frames
        if res.n_steps >= 2:  # type: ignore[attr-defined]
            dt = float(res.t[-1] - res.t[-2])  # type: ignore[attr-defined]
            pos_prev = res.positions_at(res.n_steps - 2)  # type: ignore[attr-defined]
            tip_prev = pos_prev.get("tip", (0.0, 0.0))
            vx = (tip_xy[0] - tip_prev[0]) / max(dt, 1e-9)
            vy = (tip_xy[1] - tip_prev[1]) / max(dt, 1e-9)
        else:
            vx, vy = 0.0, 0.0
        speed = float(np.hypot(vx, vy))
        return {
            "tip_speed_final": speed,
            "tip_position_final": np.array([tip_xy[0], tip_xy[1]]),
        }

    perturb.set_coeffs_source(
        lambda: [
            controls.get_params().get("shoulder_coeffs", [0.0]),
            controls.get_params().get("elbow_coeffs", [0.0]),
            controls.get_params().get("wrist_coeffs", [0.0]),
        ]
    )

    def _triple_preset_coeffs(name: str) -> list[list[float]]:
        preset = controls.PRESETS.get(name)
        if preset is None:
            return [[0.0], [0.0], [0.0]]

        def _parse(s: str) -> list[float]:
            return [float(x.strip()) for x in s.split(",") if x.strip()] or [0.0]

        # Triple PRESETS tuple: indices 6=tau_sh, 7=tau_el, 8=tau_wr
        return [_parse(str(preset[6])), _parse(str(preset[7])), _parse(str(preset[8]))]

    perturb.set_preset_source(
        lambda: list(controls.PRESETS.keys()),
        _triple_preset_coeffs,
    )
    perturb.set_simulation_callbacks(_triple_simulate_fn, _triple_extract_fn)
    panel.set_perturbation_panel(perturb)
    return panel'''

NEW_TRIPLE = '''class _TriplePanelCallbacks:
    """Callback closures for the triple-pendulum simulation panel."""

    def __init__(
        self,
        controls: "ControlsWidgetTriple",
        pendulum: "PendulumWidget",
    ) -> None:
        self._controls = controls
        self._pendulum = pendulum

    def build_params(self, p: dict) -> "TriplePendulumParams":
        tilt_rad = np.radians(p.get("tilt_deg", 0.0))
        g = GRAVITY_MSS if p.get("gravity_on", True) else 0.0
        g_eff = g * float(np.cos(tilt_rad))  # (#1113)
        self._pendulum.set_tilt_angle(tilt_rad)
        self._pendulum.set_view_azimuth(np.radians(p.get("azimuth_deg", 0.0)))  # (#1118)
        return TriplePendulumParams(
            m1=p["m1"], m2=p["m2"], m3=p["m3"],
            L1=p["L1"], L2=p["L2"], L3=p["L3"],
            g=g_eff, b1=p.get("b1", 0.0), b2=p.get("b2", 0.0), b3=p.get("b3", 0.0),
            mu1=p.get("mu1", 0.0), mu2=p.get("mu2", 0.0), mu3=p.get("mu3", 0.0),
            scapula_offset_rad=np.radians(p.get("scapula_deg", 0.0)),
        )

    def build_state(self, p: dict) -> np.ndarray:
        return np.array([
            p["theta1_rad"], p["phi1_rad"], p["phi2_rad"],
            p["dtheta1"], p["dphi1"], p["dphi2"],
        ])

    def build_torque(self, p: dict) -> object:
        return make_polynomial_torque_triple(
            p["shoulder_coeffs"], p["elbow_coeffs"], p["wrist_coeffs"],
        )

    def build_limits(self, p: dict) -> "JointLimitsNDOF | None":
        if not p.get("enable_limits", False):
            return None
        return JointLimitsNDOF(
            angle_min=np.array(p["limit_mins_rad"]),
            angle_max=np.array(p["limit_maxs_rad"]),
            stiffness=p.get("limit_stiffness", 500.0),
        )

    def build_clamp(self, p: dict) -> "np.ndarray | None":
        if not p.get("enable_clamp", False):
            return None
        return np.array(p["torque_limits"])

    def make_objective(self, p: dict) -> "Callable":
        """Build a tip-speed objective from current controls."""
        params = self.build_params(p)
        initial_state = self.build_state(p)
        t_end = p["t_end"]
        limits = self.build_limits(p)
        clamp = self.build_clamp(p)

        def objective(coeffs: np.ndarray) -> float:
            n_third = len(coeffs) // 3
            torque_func = make_polynomial_torque_triple(
                list(coeffs[:n_third]),
                list(coeffs[n_third : 2 * n_third]),
                list(coeffs[2 * n_third :]),
            )
            try:
                result = run_simulation_triple(
                    params=params, initial_state=initial_state, t_end=t_end,
                    torque_func=torque_func,  # type: ignore[arg-type]
                    torque_limits=clamp, limits=limits,
                )
                vels = result.joint_velocities_at(result.n_steps - 1)  # type: ignore[attr-defined]
                tip_v = vels.get("tip", (0, 0))
                return -float(np.hypot(tip_v[0], tip_v[1]))
            except (RuntimeError, ValueError, ArithmeticError) as exc:  # noqa: BLE001
                logger.debug("triple objective simulation failed: %s", exc)
                return 0.0

        return objective

    def simulate(self, coeffs: list) -> object:
        p = self._controls.get_params()
        torque_func = make_polynomial_torque_triple(coeffs[0], coeffs[1], coeffs[2])
        return run_simulation_triple(
            params=self.build_params(p), initial_state=self.build_state(p),
            t_end=p["t_end"], torque_func=torque_func,  # type: ignore[arg-type]
            limits=self.build_limits(p), clamp=self.build_clamp(p),
        )

    def extract_metrics(self, result: object) -> dict:
        res = result  # type: ignore[assignment]
        pos = res.positions_at(res.n_steps - 1)  # type: ignore[attr-defined]
        tip_xy = pos.get("tip", (0.0, 0.0))
        if res.n_steps >= 2:  # type: ignore[attr-defined]
            dt = float(res.t[-1] - res.t[-2])  # type: ignore[attr-defined]
            pos_prev = res.positions_at(res.n_steps - 2)  # type: ignore[attr-defined]
            tip_prev = pos_prev.get("tip", (0.0, 0.0))
            vx = (tip_xy[0] - tip_prev[0]) / max(dt, 1e-9)
            vy = (tip_xy[1] - tip_prev[1]) / max(dt, 1e-9)
        else:
            vx, vy = 0.0, 0.0
        return {
            "tip_speed_final": float(np.hypot(vx, vy)),
            "tip_position_final": np.array([tip_xy[0], tip_xy[1]]),
        }

    def get_preset_coeffs(self, name: str) -> list[list[float]]:
        preset = self._controls.PRESETS.get(name)
        if preset is None:
            return [[0.0], [0.0], [0.0]]

        def _parse(s: str) -> list[float]:
            return [float(x.strip()) for x in s.split(",") if x.strip()] or [0.0]

        return [_parse(str(preset[6])), _parse(str(preset[7])), _parse(str(preset[8]))]

    def get_current_coeffs(self) -> list[list[float]]:
        p = self._controls.get_params()
        return [
            p.get("shoulder_coeffs", [0.0]),
            p.get("elbow_coeffs", [0.0]),
            p.get("wrist_coeffs", [0.0]),
        ]


def build_triple_panel(main_window: Any) -> SimulationPanel:
    """Build and return the triple pendulum simulation panel.

    Parameters
    ----------
    main_window : MainWindow
        The main window instance (used to access state if needed).

    Returns
    -------
    SimulationPanel
        A fully wired simulation panel for the triple pendulum model.
    """
    controls = ControlsWidgetTriple()
    pendulum = PendulumWidget()
    matrix = TripleMatrixWidget()
    torque_history = TorqueHistoryWidget()
    cb = _TriplePanelCallbacks(controls, pendulum)
    optimizer = OptimizationWidget(model_name="Triple Pendulum", n_torque_params=3)
    panel = SimulationPanel(
        controls=controls,
        pendulum=pendulum,  # type: ignore[arg-type]
        matrix=matrix,  # type: ignore[arg-type]
        params_builder=cb.build_params,
        torque_builder=cb.build_torque,
        state_builder=cb.build_state,
        run_simulation=run_simulation_triple,
        torque_history=torque_history,
        limits_builder=cb.build_limits,
        clamp_builder=cb.build_clamp,
        optimizer=optimizer,
        objective_builder=cb.make_objective,
    )
    panel._settings_key = "splitter_triple"
    perturb = PerturbationPanel()
    perturb.set_coeffs_source(cb.get_current_coeffs)
    perturb.set_preset_source(lambda: list(controls.PRESETS.keys()), cb.get_preset_coeffs)
    perturb.set_simulation_callbacks(cb.simulate, cb.extract_metrics)
    panel.set_perturbation_panel(perturb)
    return panel'''

assert OLD_TRIPLE in content, "Could not find build_triple_panel text"
content = content.replace(OLD_TRIPLE, NEW_TRIPLE)

# ──────────────────────────────────────────────────────────────────────────
# Part 2: build_golfer_panel - same pattern with _GolferPanelCallbacks
# ──────────────────────────────────────────────────────────────────────────

OLD_GOLFER = '''def build_golfer_panel(main_window: Any) -> SimulationPanel:
    """Build and return the golfer upper body simulation panel.

    Parameters
    ----------
    main_window : MainWindow
        The main window instance (used to access state if needed).

    Returns
    -------
    SimulationPanel
        A fully wired simulation panel for the golfer upper body model.
    """
    controls = ControlsWidgetGolfer()
    pendulum = GolferPendulumWidget()
    matrix = GolferMatrixWidget()
    torque_history = TorqueHistoryWidget()

    def build_params(p: dict) -> GolferParams:
        tilt_rad = np.radians(p.get("tilt_deg", 0.0))
        g = GRAVITY_MSS if p.get("gravity_on", True) else 0.0
        g_eff = g * float(np.cos(tilt_rad))  # (#1113)
        pendulum.set_tilt_angle(tilt_rad)
        pendulum.set_view_azimuth(np.radians(p.get("azimuth_deg", 0.0)))  # (#1118)
        return GolferParams(
            m_hub=p["m_hub"],
            m_r_upper=p["m_r_upper"],
            m_r_fore=p["m_r_fore"],
            m_l_upper=p["m_l_upper"],
            m_l_fore=p["m_l_fore"],
            m_club=p["m_club"],
            L_hub=p["L_hub"],
            L_r_upper=p["L_r_upper"],
            L_r_fore=p["L_r_fore"],
            L_l_upper=p["L_l_upper"],
            L_l_fore=p["L_l_fore"],
            L_club=p["L_club"],
            d_rs=p["d_rs"],
            d_ls=p["d_ls"],
            grip_right=p["grip_right"],
            grip_left=p["grip_left"],
            m_clubhead=p.get("m_clubhead", 0.2),
            g=g_eff,
            b_hub=p.get("b_hub", 0.0),
            b_rs=p.get("b_rs", 0.0),
            b_re=p.get("b_re", 0.0),
            b_rh=p.get("b_rh", 0.0),
            b_ls=p.get("b_ls", 0.0),
            b_le=p.get("b_le", 0.0),
            b_lh=p.get("b_lh", 0.0),
            L_rscap=p.get("L_rscap", 0.12),
            L_lscap=p.get("L_lscap", 0.12),
            m_rscap=p.get("m_rscap", 0.5),
            m_lscap=p.get("m_lscap", 0.5),
        )

    def build_state(p: dict) -> np.ndarray:
        return np.array(
            [
                p["theta_hub_rad"],
                p["alpha_rs_rad"],
                p["alpha_re_rad"],
                p["alpha_rh_rad"],
                p["alpha_ls_rad"],
                p["alpha_le_rad"],
                p["alpha_lh_rad"],
                0.0,  # theta_club (computed by projection)
                0.0,
                0.0,
                0.0,
                0.0,  # qdot (all zero)
                0.0,
                0.0,
                0.0,
                0.0,
            ]
        )

    def build_torque(p: dict) -> object:
        return make_polynomial_torque_golfer(
            p["hub_coeffs"],
            p["rs_coeffs"],
            p["re_coeffs"],
            p["rh_coeffs"],
            p["ls_coeffs"],
            p["le_coeffs"],
            p["lh_coeffs"],
        )

    def build_limits(p: dict) -> JointLimitsNDOF | None:
        if not p.get("enable_limits", False):
            return None
        return JointLimitsNDOF(
            angle_min=np.array(p["limit_mins_rad"]),
            angle_max=np.array(p["limit_maxs_rad"]),
            stiffness=p.get("limit_stiffness", 500.0),
        )

    def build_clamp(p: dict) -> np.ndarray | None:
        if not p.get("enable_clamp", False):
            return None
        return np.array(p["torque_limits"])

    # Optimizer (#1110)
    optimizer = OptimizationWidget(
        model_name="Golfer Upper Body",
        n_torque_params=7,
    )

    def _make_golfer_objective(p: dict) -> Callable:
        """Build a clubhead-speed objective from current controls."""
        params = build_params(p)
        initial_state = build_state(p)
        t_end = p["t_end"]
        limits = build_limits(p)
        clamp = build_clamp(p)

        def objective(coeffs: np.ndarray) -> float:
            n_seventh = max(1, len(coeffs) // 7)
            slices = [
                list(coeffs[i * n_seventh : (i + 1) * n_seventh]) for i in range(7)
            ]
            torque_func = make_polynomial_torque_golfer(*slices)
            try:
                result = run_simulation_golfer(
                    params=params,
                    initial_state=initial_state,
                    t_end=t_end,
                    torque_func=torque_func,  # type: ignore[arg-type]
                    torque_limits=clamp,
                    limits=limits,
                )
                vels = result.joint_velocities_at(result.n_steps - 1)  # type: ignore[attr-defined]
                tip_v = vels.get("club_tip", (0, 0))
                speed = float(np.hypot(tip_v[0], tip_v[1]))
                return -speed
            except (
                RuntimeError,
                ValueError,
                ArithmeticError,
            ) as exc:  # noqa: BLE001
                logger.debug("golfer objective simulation failed: %s", exc)
                return 0.0

        return objective

    panel = SimulationPanel(
        controls=controls,
        pendulum=pendulum,  # type: ignore[arg-type]
        matrix=matrix,  # type: ignore[arg-type]
        params_builder=build_params,
        torque_builder=build_torque,
        state_builder=build_state,
        run_simulation=run_simulation_golfer,
        torque_history=torque_history,
        limits_builder=build_limits,
        clamp_builder=build_clamp,
        optimizer=optimizer,
        objective_builder=_make_golfer_objective,
    )
    panel._settings_key = "splitter_golfer"

    # Wire perturbation panel (#1284)
    perturb = PerturbationPanel()

    def _golfer_simulate_fn(coeffs: list) -> object:
        p = controls.get_params()
        params = build_params(p)
        initial_state = build_state(p)
        limits = build_limits(p)
        clamp = build_clamp(p)
        torque_func = make_polynomial_torque_golfer(*coeffs)  # type: ignore[arg-type]
        return run_simulation_golfer(
            params=params,
            initial_state=initial_state,
            t_end=p["t_end"],
            torque_func=torque_func,  # type: ignore[arg-type]
            limits=limits,
            clamp=clamp,
        )

    def _golfer_extract_fn(result: object) -> dict:
        res = result  # type: ignore[assignment]
        pos = res.positions_at(res.n_steps - 1)  # type: ignore[attr-defined]
        tip_xy = pos.get("club_tip", pos.get("tip", (0.0, 0.0)))
        if res.n_steps >= 2:  # type: ignore[attr-defined]
            dt = float(res.t[-1] - res.t[-2])  # type: ignore[attr-defined]
            pos_prev = res.positions_at(res.n_steps - 2)  # type: ignore[attr-defined]
            tip_prev = pos_prev.get("club_tip", pos_prev.get("tip", (0.0, 0.0)))
            vx = (tip_xy[0] - tip_prev[0]) / max(dt, 1e-9)
            vy = (tip_xy[1] - tip_prev[1]) / max(dt, 1e-9)
        else:
            vx, vy = 0.0, 0.0
        speed = float(np.hypot(vx, vy))
        return {
            "tip_speed_final": speed,
            "tip_position_final": np.array([tip_xy[0], tip_xy[1]]),
        }

    def _golfer_coeffs_fn() -> list:
        p = controls.get_params()
        joint_keys = [
            "hip_coeffs",
            "spine_coeffs",
            "r_shoulder_coeffs",
            "r_elbow_coeffs",
            "l_shoulder_coeffs",
            "l_elbow_coeffs",
            "wrist_coeffs",
        ]
        return [p.get(k, [0.0]) for k in joint_keys]

    perturb.set_coeffs_source(_golfer_coeffs_fn)

    _GOLFER_TAU_KEYS = [
        "tau_hub",
        "tau_rs",
        "tau_re",
        "tau_rh",
        "tau_ls",
        "tau_le",
        "tau_lh",
    ]

    def _golfer_preset_coeffs(name: str) -> list[list[float]]:
        preset = controls.PRESETS.get(name)
        if preset is None:
            return [[0.0]] * len(_GOLFER_TAU_KEYS)

        def _parse(s: str) -> list[float]:
            return [float(x.strip()) for x in s.split(",") if x.strip()] or [0.0]

        return [_parse(str(preset.get(k, "0"))) for k in _GOLFER_TAU_KEYS]

    perturb.set_preset_source(
        lambda: list(controls.PRESETS.keys()),
        _golfer_preset_coeffs,
    )
    perturb.set_simulation_callbacks(_golfer_simulate_fn, _golfer_extract_fn)
    panel.set_perturbation_panel(perturb)
    return panel'''

NEW_GOLFER = '''_GOLFER_TAU_KEYS = [
    "tau_hub", "tau_rs", "tau_re", "tau_rh", "tau_ls", "tau_le", "tau_lh",
]


class _GolferPanelCallbacks:
    """Callback closures for the golfer upper-body simulation panel."""

    def __init__(
        self,
        controls: "ControlsWidgetGolfer",
        pendulum: "GolferPendulumWidget",
    ) -> None:
        self._controls = controls
        self._pendulum = pendulum

    def build_params(self, p: dict) -> "GolferParams":
        tilt_rad = np.radians(p.get("tilt_deg", 0.0))
        g = GRAVITY_MSS if p.get("gravity_on", True) else 0.0
        g_eff = g * float(np.cos(tilt_rad))  # (#1113)
        self._pendulum.set_tilt_angle(tilt_rad)
        self._pendulum.set_view_azimuth(np.radians(p.get("azimuth_deg", 0.0)))  # (#1118)
        return GolferParams(
            m_hub=p["m_hub"], m_r_upper=p["m_r_upper"], m_r_fore=p["m_r_fore"],
            m_l_upper=p["m_l_upper"], m_l_fore=p["m_l_fore"], m_club=p["m_club"],
            L_hub=p["L_hub"], L_r_upper=p["L_r_upper"], L_r_fore=p["L_r_fore"],
            L_l_upper=p["L_l_upper"], L_l_fore=p["L_l_fore"], L_club=p["L_club"],
            d_rs=p["d_rs"], d_ls=p["d_ls"], grip_right=p["grip_right"],
            grip_left=p["grip_left"], m_clubhead=p.get("m_clubhead", 0.2),
            g=g_eff, b_hub=p.get("b_hub", 0.0), b_rs=p.get("b_rs", 0.0),
            b_re=p.get("b_re", 0.0), b_rh=p.get("b_rh", 0.0),
            b_ls=p.get("b_ls", 0.0), b_le=p.get("b_le", 0.0), b_lh=p.get("b_lh", 0.0),
            L_rscap=p.get("L_rscap", 0.12), L_lscap=p.get("L_lscap", 0.12),
            m_rscap=p.get("m_rscap", 0.5), m_lscap=p.get("m_lscap", 0.5),
        )

    def build_state(self, p: dict) -> np.ndarray:
        return np.array([
            p["theta_hub_rad"], p["alpha_rs_rad"], p["alpha_re_rad"], p["alpha_rh_rad"],
            p["alpha_ls_rad"], p["alpha_le_rad"], p["alpha_lh_rad"],
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,  # theta_club + qdot zeros
        ])

    def build_torque(self, p: dict) -> object:
        return make_polynomial_torque_golfer(
            p["hub_coeffs"], p["rs_coeffs"], p["re_coeffs"], p["rh_coeffs"],
            p["ls_coeffs"], p["le_coeffs"], p["lh_coeffs"],
        )

    def build_limits(self, p: dict) -> "JointLimitsNDOF | None":
        if not p.get("enable_limits", False):
            return None
        return JointLimitsNDOF(
            angle_min=np.array(p["limit_mins_rad"]),
            angle_max=np.array(p["limit_maxs_rad"]),
            stiffness=p.get("limit_stiffness", 500.0),
        )

    def build_clamp(self, p: dict) -> "np.ndarray | None":
        if not p.get("enable_clamp", False):
            return None
        return np.array(p["torque_limits"])

    def make_objective(self, p: dict) -> "Callable":
        """Build a clubhead-speed objective from current controls."""
        params = self.build_params(p)
        initial_state = self.build_state(p)
        t_end = p["t_end"]
        limits = self.build_limits(p)
        clamp = self.build_clamp(p)

        def objective(coeffs: np.ndarray) -> float:
            n_seventh = max(1, len(coeffs) // 7)
            slices = [list(coeffs[i * n_seventh:(i + 1) * n_seventh]) for i in range(7)]
            torque_func = make_polynomial_torque_golfer(*slices)
            try:
                result = run_simulation_golfer(
                    params=params, initial_state=initial_state, t_end=t_end,
                    torque_func=torque_func,  # type: ignore[arg-type]
                    torque_limits=clamp, limits=limits,
                )
                vels = result.joint_velocities_at(result.n_steps - 1)  # type: ignore[attr-defined]
                tip_v = vels.get("club_tip", (0, 0))
                return -float(np.hypot(tip_v[0], tip_v[1]))
            except (RuntimeError, ValueError, ArithmeticError) as exc:  # noqa: BLE001
                logger.debug("golfer objective simulation failed: %s", exc)
                return 0.0

        return objective

    def simulate(self, coeffs: list) -> object:
        p = self._controls.get_params()
        return run_simulation_golfer(
            params=self.build_params(p), initial_state=self.build_state(p),
            t_end=p["t_end"],
            torque_func=make_polynomial_torque_golfer(*coeffs),  # type: ignore[arg-type]
            limits=self.build_limits(p), clamp=self.build_clamp(p),
        )

    def extract_metrics(self, result: object) -> dict:
        res = result  # type: ignore[assignment]
        pos = res.positions_at(res.n_steps - 1)  # type: ignore[attr-defined]
        tip_xy = pos.get("club_tip", pos.get("tip", (0.0, 0.0)))
        if res.n_steps >= 2:  # type: ignore[attr-defined]
            dt = float(res.t[-1] - res.t[-2])  # type: ignore[attr-defined]
            pos_prev = res.positions_at(res.n_steps - 2)  # type: ignore[attr-defined]
            tip_prev = pos_prev.get("club_tip", pos_prev.get("tip", (0.0, 0.0)))
            vx = (tip_xy[0] - tip_prev[0]) / max(dt, 1e-9)
            vy = (tip_xy[1] - tip_prev[1]) / max(dt, 1e-9)
        else:
            vx, vy = 0.0, 0.0
        return {
            "tip_speed_final": float(np.hypot(vx, vy)),
            "tip_position_final": np.array([tip_xy[0], tip_xy[1]]),
        }

    def get_current_coeffs(self) -> list:
        p = self._controls.get_params()
        return [p.get(k, [0.0]) for k in [
            "hip_coeffs", "spine_coeffs", "r_shoulder_coeffs", "r_elbow_coeffs",
            "l_shoulder_coeffs", "l_elbow_coeffs", "wrist_coeffs",
        ]]

    def get_preset_coeffs(self, name: str) -> list[list[float]]:
        preset = self._controls.PRESETS.get(name)
        if preset is None:
            return [[0.0]] * len(_GOLFER_TAU_KEYS)

        def _parse(s: str) -> list[float]:
            return [float(x.strip()) for x in s.split(",") if x.strip()] or [0.0]

        return [_parse(str(preset.get(k, "0"))) for k in _GOLFER_TAU_KEYS]


def build_golfer_panel(main_window: Any) -> SimulationPanel:
    """Build and return the golfer upper body simulation panel.

    Parameters
    ----------
    main_window : MainWindow
        The main window instance (used to access state if needed).

    Returns
    -------
    SimulationPanel
        A fully wired simulation panel for the golfer upper body model.
    """
    controls = ControlsWidgetGolfer()
    pendulum = GolferPendulumWidget()
    matrix = GolferMatrixWidget()
    torque_history = TorqueHistoryWidget()
    cb = _GolferPanelCallbacks(controls, pendulum)
    optimizer = OptimizationWidget(model_name="Golfer Upper Body", n_torque_params=7)
    panel = SimulationPanel(
        controls=controls,
        pendulum=pendulum,  # type: ignore[arg-type]
        matrix=matrix,  # type: ignore[arg-type]
        params_builder=cb.build_params,
        torque_builder=cb.build_torque,
        state_builder=cb.build_state,
        run_simulation=run_simulation_golfer,
        torque_history=torque_history,
        limits_builder=cb.build_limits,
        clamp_builder=cb.build_clamp,
        optimizer=optimizer,
        objective_builder=cb.make_objective,
    )
    panel._settings_key = "splitter_golfer"
    perturb = PerturbationPanel()
    perturb.set_coeffs_source(cb.get_current_coeffs)
    perturb.set_preset_source(lambda: list(controls.PRESETS.keys()), cb.get_preset_coeffs)
    perturb.set_simulation_callbacks(cb.simulate, cb.extract_metrics)
    panel.set_perturbation_panel(perturb)
    return panel'''

assert OLD_GOLFER in content, "Could not find build_golfer_panel text"
content = content.replace(OLD_GOLFER, NEW_GOLFER)

path.write_text(content, encoding='utf-8')
print(f"Fixed {path}")

# Verify
tree2 = ast.parse(path.read_text(encoding='utf-8'))
for node in ast.walk(tree2):
    if isinstance(node, ast.FunctionDef) and node.name in ('build_triple_panel', 'build_golfer_panel'):
        print(f"  {node.name}: {node.end_lineno - node.lineno} LOC")

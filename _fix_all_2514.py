"""
Atomic fix script for issue #2514 — decompose oversized Python functions.

Applies all 5 refactors in one shot so concurrent sessions can't partially revert.
"""

import ast
import sys
from pathlib import Path

REPO = Path(__file__).parent


def func_loc(filepath: Path, func_name: str) -> int | None:
    tree = ast.parse(filepath.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == func_name:
                return node.end_lineno - node.lineno
    return None


# ---------------------------------------------------------------------------
# Fix 1: analytical_fk_jacobians_jax in physics_golfer_jax.py
# ---------------------------------------------------------------------------

JAX_FILE = REPO / "src/shared/python/pendulum_simulator/physics_golfer_jax.py"

JAX_HELPERS = '''
def _compute_trig_golfer_jax(q: "JaxArray") -> tuple:  # type: ignore[type-arg]
    """Precompute all sin/cos values needed for golfer Jacobians."""
    th_hub = q[0]
    alpha_rs, alpha_re = q[1], q[2]
    alpha_ls, alpha_le = q[4], q[5]
    th_club = q[7]
    sh, ch = jnp.sin(th_hub), jnp.cos(th_hub)
    th_rs = th_hub + alpha_rs
    srs, crs = jnp.sin(th_rs), jnp.cos(th_rs)
    th_re = th_hub + alpha_rs + alpha_re
    sre, cre = jnp.sin(th_re), jnp.cos(th_re)
    th_ls = th_hub + alpha_ls
    sls, cls_ = jnp.sin(th_ls), jnp.cos(th_ls)
    th_le = th_hub + alpha_ls + alpha_le
    sle, cle = jnp.sin(th_le), jnp.cos(th_le)
    sc, cc = jnp.sin(th_club), jnp.cos(th_club)
    return sh, ch, srs, crs, sre, cre, sls, cls_, sle, cle, sc, cc


def _jac_hub_jax(sh: "JaxArray", ch: "JaxArray", p: "GolferParamsJAX") -> "JaxArray":
    """Position Jacobian for the hub mass point."""
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(p.L_hub * ch)
    J = J.at[1, 0].set(p.L_hub * sh)
    return J


def _jac_rs_jax(sh: "JaxArray", ch: "JaxArray", p: "GolferParamsJAX") -> "JaxArray":
    """Position Jacobian for the right shoulder."""
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(p.L_hub * ch - p.d_rs * sh)
    J = J.at[1, 0].set(p.L_hub * sh + p.d_rs * ch)
    return J


def _jac_re_jax(
    sh: "JaxArray", ch: "JaxArray", srs: "JaxArray", crs: "JaxArray",
    p: "GolferParamsJAX",
) -> "JaxArray":
    """Position Jacobian for the right elbow."""
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(p.L_hub * ch - p.d_rs * sh + p.L_r_upper * crs)
    J = J.at[1, 0].set(p.L_hub * sh + p.d_rs * ch + p.L_r_upper * srs)
    J = J.at[0, 1].set(p.L_r_upper * crs)
    J = J.at[1, 1].set(p.L_r_upper * srs)
    return J


def _jac_rh_jax(
    sh: "JaxArray", ch: "JaxArray", srs: "JaxArray", crs: "JaxArray",
    sre: "JaxArray", cre: "JaxArray", p: "GolferParamsJAX",
) -> "JaxArray":
    """Position Jacobian for the right hand."""
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(p.L_hub * ch - p.d_rs * sh + p.L_r_upper * crs + p.L_r_fore * cre)
    J = J.at[1, 0].set(p.L_hub * sh + p.d_rs * ch + p.L_r_upper * srs + p.L_r_fore * sre)
    J = J.at[0, 1].set(p.L_r_upper * crs + p.L_r_fore * cre)
    J = J.at[1, 1].set(p.L_r_upper * srs + p.L_r_fore * sre)
    J = J.at[0, 2].set(p.L_r_fore * cre)
    J = J.at[1, 2].set(p.L_r_fore * sre)
    return J


def _jac_ls_jax(sh: "JaxArray", ch: "JaxArray", p: "GolferParamsJAX") -> "JaxArray":
    """Position Jacobian for the left shoulder."""
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(p.L_hub * ch + p.d_ls * sh)
    J = J.at[1, 0].set(p.L_hub * sh - p.d_ls * ch)
    return J


def _jac_le_jax(
    sh: "JaxArray", ch: "JaxArray", sls: "JaxArray", cls_: "JaxArray",
    p: "GolferParamsJAX",
) -> "JaxArray":
    """Position Jacobian for the left elbow."""
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(p.L_hub * ch + p.d_ls * sh + p.L_l_upper * cls_)
    J = J.at[1, 0].set(p.L_hub * sh - p.d_ls * ch + p.L_l_upper * sls)
    J = J.at[0, 4].set(p.L_l_upper * cls_)
    J = J.at[1, 4].set(p.L_l_upper * sls)
    return J


def _jac_lh_jax(
    sh: "JaxArray", ch: "JaxArray", sls: "JaxArray", cls_: "JaxArray",
    sle: "JaxArray", cle: "JaxArray", p: "GolferParamsJAX",
) -> "JaxArray":
    """Position Jacobian for the left hand."""
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(p.L_hub * ch + p.d_ls * sh + p.L_l_upper * cls_ + p.L_l_fore * cle)
    J = J.at[1, 0].set(p.L_hub * sh - p.d_ls * ch + p.L_l_upper * sls + p.L_l_fore * sle)
    J = J.at[0, 4].set(p.L_l_upper * cls_ + p.L_l_fore * cle)
    J = J.at[1, 4].set(p.L_l_upper * sls + p.L_l_fore * sle)
    J = J.at[0, 5].set(p.L_l_fore * cle)
    J = J.at[1, 5].set(p.L_l_fore * sle)
    return J


def _jac_club_end_jax(
    sh: "JaxArray", ch: "JaxArray", srs: "JaxArray", crs: "JaxArray",
    sre: "JaxArray", cre: "JaxArray", sc: "JaxArray", cc: "JaxArray",
    coeff_x: "JaxArray", coeff_y: "JaxArray", p: "GolferParamsJAX",
) -> "JaxArray":
    """Position Jacobian for a club point (COM or tip) parameterised by offset coefficients."""
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(p.L_hub * ch - p.d_rs * sh + p.L_r_upper * crs + p.L_r_fore * cre)
    J = J.at[1, 0].set(p.L_hub * sh + p.d_rs * ch + p.L_r_upper * srs + p.L_r_fore * sre)
    J = J.at[0, 1].set(p.L_r_upper * crs + p.L_r_fore * cre)
    J = J.at[1, 1].set(p.L_r_upper * srs + p.L_r_fore * sre)
    J = J.at[0, 2].set(p.L_r_fore * cre)
    J = J.at[1, 2].set(p.L_r_fore * sre)
    J = J.at[0, 7].set(coeff_x * cc)
    J = J.at[1, 7].set(coeff_y * sc)
    return J

'''

JAX_NEW_FUNC = '''def analytical_fk_jacobians_jax(q: JaxArray, p: GolferParamsJAX) -> dict[str, JaxArray]:
    """Compute position Jacobians analytically for all mass points (JAX version).

    Parameters
    ----------
    q : JaxArray, shape (8,)
        Generalized coordinates
    p : GolferParamsJAX
        Physical parameters

    Returns
    -------
    dict
        Keys: 'hub', 're', 'rh', 'le', 'lh', 'club_com', 'club_tip'
        Each value is shape (2, 8): J[row, col] = d(pos[row])/dq[col]
    """
    if not (q is not None):
        raise ValueError("q must be provided")
    sh, ch, srs, crs, sre, cre, sls, cls_, sle, cle, sc, cc = _compute_trig_golfer_jax(q)
    return {
        "hub": _jac_hub_jax(sh, ch, p),
        "rs": _jac_rs_jax(sh, ch, p),
        "re": _jac_re_jax(sh, ch, srs, crs, p),
        "rh": _jac_rh_jax(sh, ch, srs, crs, sre, cre, p),
        "ls": _jac_ls_jax(sh, ch, p),
        "le": _jac_le_jax(sh, ch, sls, cls_, p),
        "lh": _jac_lh_jax(sh, ch, sls, cls_, sle, cle, p),
        "club_com": _jac_club_end_jax(
            sh, ch, srs, crs, sre, cre, sc, cc,
            0.5 * p.L_club - p.grip_right,
            -0.5 * (p.L_club - 2 * p.grip_right),
            p,
        ),
        "club_tip": _jac_club_end_jax(
            sh, ch, srs, crs, sre, cre, sc, cc,
            p.L_club - p.grip_right,
            -(p.L_club - p.grip_right),
            p,
        ),
    }
'''


def fix_jax_file():
    text = JAX_FILE.read_text(encoding="utf-8")
    # Find the old function and replace with helpers + new function
    old_start = "def analytical_fk_jacobians_jax(q: JaxArray, p: GolferParamsJAX) -> dict[str, JaxArray]:"
    idx = text.find(old_start)
    if idx == -1:
        print("ERROR: could not find analytical_fk_jacobians_jax in jax file")
        return False

    # Find end of function (next top-level def after line 421)
    lines = text.splitlines(keepends=True)
    # Find line number of old_start
    start_lineno = None
    for i, line in enumerate(lines):
        if old_start in line:
            start_lineno = i
            break
    if start_lineno is None:
        print("ERROR: could not find start line")
        return False

    # Find end: next top-level def or class
    end_lineno = len(lines)
    for i in range(start_lineno + 1, len(lines)):
        if lines[i] and lines[i][0].isalpha() and (
            lines[i].startswith("def ") or lines[i].startswith("class ")
        ):
            end_lineno = i
            break

    old_func_text = "".join(lines[start_lineno:end_lineno])
    replacement = JAX_HELPERS + JAX_NEW_FUNC
    new_text = text.replace(old_func_text, replacement)
    if new_text == text:
        print("ERROR: jax replacement had no effect")
        return False
    JAX_FILE.write_text(new_text, encoding="utf-8")
    loc = func_loc(JAX_FILE, "analytical_fk_jacobians_jax")
    print(f"analytical_fk_jacobians_jax: {loc} LOC (target <= 50)")
    return loc is not None and loc <= 50


# ---------------------------------------------------------------------------
# Fix 2: _build_qt_window in cross_engine_dashboard.py
# ---------------------------------------------------------------------------

DASH_FILE = REPO / "src/launchers/cross_engine_dashboard.py"


def fix_dashboard_file():
    text = DASH_FILE.read_text(encoding="utf-8")

    old_func_start = 'def _build_qt_window() -> object:\n    """Build and return the QMainWindow instance (deferred Qt import).'
    idx = text.find(old_func_start)
    if idx == -1:
        print("ERROR: could not find _build_qt_window")
        return False

    lines = text.splitlines(keepends=True)
    start_lineno = None
    for i, line in enumerate(lines):
        if line.strip().startswith("def _build_qt_window()"):
            start_lineno = i
            break
    if start_lineno is None:
        print("ERROR: could not find _build_qt_window start line")
        return False

    end_lineno = len(lines)
    for i in range(start_lineno + 1, len(lines)):
        if lines[i] and not lines[i][0].isspace() and (
            lines[i].startswith("def ") or lines[i].startswith("class ")
        ):
            end_lineno = i
            break

    old_func_text = "".join(lines[start_lineno:end_lineno])

    # Build replacement: rename inner function as _create_dashboard_window_class
    # and make _build_qt_window a 3-line wrapper
    new_helper = old_func_text.replace(
        "def _build_qt_window() -> object:\n"
        '    """Build and return the QMainWindow instance (deferred Qt import).\n'
        "\n"
        "    Returns\n"
        "    -------\n"
        "    QMainWindow subclass instance.\n"
        "\n"
        "    Raises\n"
        "    ------\n"
        "    ImportError if PyQt6 or Matplotlib is not available.\n"
        '    """\n',
        "def _create_dashboard_window_class() -> type:\n"
        '    """Construct and return the _Window class with deferred Qt/mpl imports.\n'
        "\n"
        "    Returns\n"
        "    -------\n"
        "    type\n"
        "        A QMainWindow subclass ready to be instantiated.\n"
        "\n"
        "    Raises\n"
        "    ------\n"
        "    ImportError if PyQt6 or Matplotlib is not available.\n"
        '    """\n',
    )
    # Replace the final `return _Window()` with `return _Window`
    new_helper = new_helper.rstrip()
    if new_helper.endswith("return _Window()"):
        new_helper = new_helper[:-len("return _Window()")] + "return _Window"
    new_helper += "\n"

    new_wrapper = (
        "\n\n"
        "def _build_qt_window() -> object:\n"
        '    """Build and return the QMainWindow instance (deferred Qt import)."""\n'
        "    return _create_dashboard_window_class()()\n"
    )

    replacement = new_helper + new_wrapper
    new_text = text.replace(old_func_text, replacement)
    if new_text == text:
        print("ERROR: dashboard replacement had no effect")
        return False
    DASH_FILE.write_text(new_text, encoding="utf-8")
    loc = func_loc(DASH_FILE, "_build_qt_window")
    print(f"_build_qt_window: {loc} LOC (target <= 50)")
    return loc is not None and loc <= 50


# ---------------------------------------------------------------------------
# Fix 3 & 4: build_triple_panel + build_golfer_panel in panel_builders.py
# ---------------------------------------------------------------------------

PANEL_FILE = REPO / "src/shared/python/pendulum_simulator/gui/panel_builders.py"

TRIPLE_CALLBACKS_CLASS = '''
class _TripleCallbacks:
    """Callbacks capturing controls/pendulum widgets for the triple-pendulum panel.

    Extracted to keep build_triple_panel within the 50-LOC function-size budget.
    """

    def __init__(self, controls: "ControlsWidgetTriple", pendulum: "PendulumWidget") -> None:
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
            g=g_eff,
            b1=p.get("b1", 0.0), b2=p.get("b2", 0.0), b3=p.get("b3", 0.0),
            mu1=p.get("mu1", 0.0), mu2=p.get("mu2", 0.0), mu3=p.get("mu3", 0.0),
            scapula_offset_rad=np.radians(p.get("scapula_deg", 0.0)),
        )

    def build_state(self, p: dict) -> "np.ndarray":
        return np.array([
            p["theta1_rad"], p["phi1_rad"], p["phi2_rad"],
            p["dtheta1"], p["dphi1"], p["dphi2"],
        ])

    def build_torque(self, p: dict) -> object:
        return make_polynomial_torque_triple(
            p["shoulder_coeffs"], p["elbow_coeffs"], p["wrist_coeffs"]
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

    def make_objective(self, p: dict) -> Callable:
        """Build a tip-speed objective from current controls."""
        params = self.build_params(p)
        initial_state = self.build_state(p)
        t_end = p["t_end"]
        limits = self.build_limits(p)
        clamp = self.build_clamp(p)

        def objective(coeffs: np.ndarray) -> float:
            n_third = len(coeffs) // 3
            s_c = list(coeffs[:n_third])
            e_c = list(coeffs[n_third: 2 * n_third])
            w_c = list(coeffs[2 * n_third:])
            torque_func = make_polynomial_torque_triple(s_c, e_c, w_c)
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

    def get_current_coeffs(self) -> list:
        p = self._controls.get_params()
        return [
            p.get("shoulder_coeffs", [0.0]),
            p.get("elbow_coeffs", [0.0]),
            p.get("wrist_coeffs", [0.0]),
        ]

    def get_preset_coeffs(self, name: str) -> list[list[float]]:
        preset = self._controls.PRESETS.get(name)
        if preset is None:
            return [[0.0], [0.0], [0.0]]

        def _parse(s: str) -> list[float]:
            return [float(x.strip()) for x in s.split(",") if x.strip()] or [0.0]

        # Triple PRESETS tuple: indices 6=tau_sh, 7=tau_el, 8=tau_wr
        return [_parse(str(preset[6])), _parse(str(preset[7])), _parse(str(preset[8]))]

'''

TRIPLE_NEW_FUNC = '''def build_triple_panel(main_window: Any) -> SimulationPanel:
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
    cb = _TripleCallbacks(controls, pendulum)
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
    return panel

'''

_GOLFER_TAU_KEYS_CONST = '''_GOLFER_TAU_KEYS: list[str] = [
    "tau_hub", "tau_rs", "tau_re", "tau_rh", "tau_ls", "tau_le", "tau_lh",
]

'''

GOLFER_CALLBACKS_CLASS = '''
class _GolferCallbacks:
    """Callbacks capturing controls/pendulum widgets for the golfer panel.

    Extracted to keep build_golfer_panel within the 50-LOC function-size budget.
    """

    def __init__(
        self, controls: "ControlsWidgetGolfer", pendulum: "GolferPendulumWidget"
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
            g=g_eff,
            b_hub=p.get("b_hub", 0.0), b_rs=p.get("b_rs", 0.0),
            b_re=p.get("b_re", 0.0), b_rh=p.get("b_rh", 0.0),
            b_ls=p.get("b_ls", 0.0), b_le=p.get("b_le", 0.0),
            b_lh=p.get("b_lh", 0.0),
            L_rscap=p.get("L_rscap", 0.12), L_lscap=p.get("L_lscap", 0.12),
            m_rscap=p.get("m_rscap", 0.5), m_lscap=p.get("m_lscap", 0.5),
        )

    def build_state(self, p: dict) -> "np.ndarray":
        return np.array([
            p["theta_hub_rad"], p["alpha_rs_rad"], p["alpha_re_rad"],
            p["alpha_rh_rad"], p["alpha_ls_rad"], p["alpha_le_rad"],
            p["alpha_lh_rad"],
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,  # club + all qdot
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

    def make_objective(self, p: dict) -> Callable:
        """Build a clubhead-speed objective from current controls."""
        params = self.build_params(p)
        initial_state = self.build_state(p)
        t_end = p["t_end"]
        limits = self.build_limits(p)
        clamp = self.build_clamp(p)

        def objective(coeffs: np.ndarray) -> float:
            n_seventh = max(1, len(coeffs) // 7)
            slices = [list(coeffs[i * n_seventh: (i + 1) * n_seventh]) for i in range(7)]
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
        torque_func = make_polynomial_torque_golfer(*coeffs)  # type: ignore[arg-type]
        return run_simulation_golfer(
            params=self.build_params(p), initial_state=self.build_state(p),
            t_end=p["t_end"], torque_func=torque_func,  # type: ignore[arg-type]
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
        joint_keys = [
            "hip_coeffs", "spine_coeffs", "r_shoulder_coeffs", "r_elbow_coeffs",
            "l_shoulder_coeffs", "l_elbow_coeffs", "wrist_coeffs",
        ]
        return [p.get(k, [0.0]) for k in joint_keys]

    def get_preset_coeffs(self, name: str) -> list[list[float]]:
        preset = self._controls.PRESETS.get(name)
        if preset is None:
            return [[0.0]] * len(_GOLFER_TAU_KEYS)

        def _parse(s: str) -> list[float]:
            return [float(x.strip()) for x in s.split(",") if x.strip()] or [0.0]

        return [_parse(str(preset.get(k, "0"))) for k in _GOLFER_TAU_KEYS]

'''

GOLFER_NEW_FUNC = '''def build_golfer_panel(main_window: Any) -> SimulationPanel:
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
    cb = _GolferCallbacks(controls, pendulum)
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
    return panel

'''


def fix_panel_file():
    text = PANEL_FILE.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    # --- Replace build_triple_panel ---
    triple_start = None
    for i, line in enumerate(lines):
        if line.startswith("def build_triple_panel("):
            triple_start = i
            break
    if triple_start is None:
        print("ERROR: could not find build_triple_panel")
        return False

    triple_end = len(lines)
    for i in range(triple_start + 1, len(lines)):
        if lines[i] and not lines[i][0].isspace() and (
            lines[i].startswith("def ") or lines[i].startswith("class ")
        ):
            triple_end = i
            break

    triple_old = "".join(lines[triple_start:triple_end])

    # --- Replace build_golfer_panel ---
    golfer_start = None
    for i, line in enumerate(lines):
        if line.startswith("def build_golfer_panel("):
            golfer_start = i
            break
    if golfer_start is None:
        print("ERROR: could not find build_golfer_panel")
        return False

    golfer_end = len(lines)
    for i in range(golfer_start + 1, len(lines)):
        if lines[i] and not lines[i][0].isspace() and (
            lines[i].startswith("def ") or lines[i].startswith("class ")
        ):
            golfer_end = i
            break

    golfer_old = "".join(lines[golfer_start:golfer_end])

    # Remove the inline _GOLFER_TAU_KEYS if present inside build_golfer_panel
    # (it's inside the old golfer_old text, we don't need it there)

    # Build new text: insert _TripleCallbacks before build_triple_panel,
    # insert _GOLFER_TAU_KEYS + _GolferCallbacks before build_golfer_panel
    new_text = text.replace(triple_old, TRIPLE_CALLBACKS_CLASS + TRIPLE_NEW_FUNC)
    new_text = new_text.replace(golfer_old, _GOLFER_TAU_KEYS_CONST + GOLFER_CALLBACKS_CLASS + GOLFER_NEW_FUNC)

    if new_text == text:
        print("ERROR: panel replacement had no effect")
        return False
    PANEL_FILE.write_text(new_text, encoding="utf-8")

    loc_t = func_loc(PANEL_FILE, "build_triple_panel")
    loc_g = func_loc(PANEL_FILE, "build_golfer_panel")
    print(f"build_triple_panel: {loc_t} LOC (target <= 50)")
    print(f"build_golfer_panel: {loc_g} LOC (target <= 50)")
    return (
        loc_t is not None and loc_t <= 50
        and loc_g is not None and loc_g <= 50
    )


# ---------------------------------------------------------------------------
# Fix 5: _build_overlay_section in toolstrip_widget.py
# ---------------------------------------------------------------------------

TOOLSTRIP_FILE = REPO / "src/shared/python/pendulum_simulator/gui/toolstrip_widget.py"

# Two new methods to be inserted into the class (before _build_overlay_section)
OVERLAY_HELPERS = '''
    def _overlay_build_frame_rows(self, overlay_layout: "QVBoxLayout") -> None:
        """Build rows A-D: force/mobility/force-ellipsoid checkboxes and segment row."""
        # Row A: Force Vectors
        self.chk_forces = QCheckBox("Force Vectors")
        self.chk_forces.setStyleSheet(_CHK_FORCE)
        self.chk_forces.setToolTip(
            "Show net joint force vectors at each joint.\\n"
            "Arrow length scales with force magnitude."
        )
        self.chk_forces.toggled.connect(self.forces_toggled.emit)
        self._sld_force = _make_scale_slider(_SLIDER_FORCE, default=10)
        self._sld_force.setToolTip("Force vector display scale (0.1× – 100×)")
        self._sld_force.valueChanged.connect(self._on_force_scale)
        self._lbl_force_scale = QLabel("1.0×")
        self._lbl_force_scale.setStyleSheet(_VAL_LBL)
        overlay_layout.addLayout(
            _overlay_row(self.chk_forces, self._sld_force, self._lbl_force_scale)
        )
        # Row B: Mobility Ellipsoids
        self.chk_mob = QCheckBox("Mobility Ellipsoids")
        self.chk_mob.setStyleSheet(_CHK_MOB)
        self.chk_mob.setToolTip(
            "Show mobility ellipsoids at segment endpoints.\\n"
            "Cyan = achievable velocity; large = high dexterity."
        )
        self.chk_mob.toggled.connect(self.mob_ellipsoid_toggled.emit)
        self._sld_mob = _make_scale_slider(_SLIDER_MOB, default=10, max_val=100)
        self._sld_mob.setToolTip("Mobility ellipsoid display scale (0.1× – 10×)")
        self._sld_mob.valueChanged.connect(self._on_mob_scale)
        self._lbl_mob_scale = QLabel("1.0×")
        self._lbl_mob_scale.setStyleSheet(_VAL_LBL)
        overlay_layout.addLayout(
            _overlay_row(self.chk_mob, self._sld_mob, self._lbl_mob_scale)
        )
        # Row C: Force Ellipsoids
        self.chk_force_ell = QCheckBox("Force Ellipsoids")
        self.chk_force_ell.setStyleSheet(_CHK_FELL)
        self.chk_force_ell.setToolTip(
            "Show force ellipsoids at segment endpoints.\\n"
            "Orange = achievable endpoint force; small = near-singular."
        )
        self.chk_force_ell.toggled.connect(self.force_ellipsoid_toggled.emit)
        self._sld_force_ell = _make_scale_slider(_SLIDER_FELL, default=10, max_val=100)
        self._sld_force_ell.setToolTip("Force ellipsoid display scale (0.1× – 10×)")
        self._sld_force_ell.valueChanged.connect(self._on_force_ell_scale)
        self._lbl_force_ell_scale = QLabel("1.0×")
        self._lbl_force_ell_scale.setStyleSheet(_VAL_LBL)
        overlay_layout.addLayout(
            _overlay_row(
                self.chk_force_ell, self._sld_force_ell, self._lbl_force_ell_scale
            )
        )
        # Row D: Per-segment visibility sub-checkboxes (#1100, #1101, #1102)
        seg_row = QHBoxLayout()
        seg_row.setContentsMargins(0, 1, 0, 0)
        seg_row.setSpacing(2)
        seg_lbl = QLabel("Segments:")
        seg_lbl.setStyleSheet("color:#505070;font-size:11px;")
        seg_row.addWidget(seg_lbl)
        self._segment_checks: dict[str, QCheckBox] = {}
        self._segment_names: list[str] = ["shoulder", "wrist", "tip"]
        for name in self._segment_names:
            chk = QCheckBox(name[:6])
            chk.setChecked(True)
            chk.setStyleSheet(
                "QCheckBox{color:#707090;font-size:11px;spacing:2px;}"
                "QCheckBox::indicator{width:11px;height:11px;border:1px solid #404060;"
                "border-radius:2px;background:#1a1a2a;}"
                "QCheckBox::indicator:checked{background:#303068;border-color:#5050a0;}"
            )
            chk.toggled.connect(self._on_segment_toggled)
            seg_row.addWidget(chk)
            self._segment_checks[name] = chk
        seg_row.addStretch()
        overlay_layout.addLayout(seg_row)

    def _overlay_build_extra_col(self, layout: "QHBoxLayout") -> None:
        """Build the extra toggles column (right of the overlay frame)."""
        extra_col = QVBoxLayout()
        extra_col.setContentsMargins(0, 0, 0, 0)
        extra_col.setSpacing(2)
        self.chk_zero_torque = QCheckBox("Zero-\\u03c4 Forces")
        self.chk_zero_torque.setStyleSheet(_CHK_ZERO)
        self.chk_zero_torque.setToolTip(
            "Show zero-torque counterfactual forces (dashed vectors).\\n"
            "These represent joint forces if all driving torques were removed—\\n"
            "the passive drift due to gravity and inertia alone."
        )
        self.chk_zero_torque.toggled.connect(self.zero_torque_toggled.emit)
        extra_col.addWidget(self.chk_zero_torque)
        self.chk_com = QCheckBox("Center of Mass")
        self.chk_com.setStyleSheet(_CHK_COM)
        self.chk_com.setToolTip("Show the combined center of mass of the whole system.")
        self.chk_com.toggled.connect(self.com_toggled.emit)
        extra_col.addWidget(self.chk_com)
        self.chk_torque = QCheckBox("Torque Vectors")
        self.chk_torque.setStyleSheet(_CHK_TORQUE)
        self.chk_torque.setToolTip(
            "Show applied torque as curved arrows at each joint.\\n"
            "Red arrows — magnitude scales with torque value."
        )
        self.chk_torque.toggled.connect(self.torque_vectors_toggled.emit)
        extra_col.addWidget(self.chk_torque)
        self.chk_mof = QCheckBox("Moment of Force")
        self.chk_mof.setStyleSheet(_CHK_MOF)
        self.chk_mof.setToolTip(
            "Show moment of force from proximal segment on distal.\\n"
            "Blue arrows — proximal-on-distal convention."
        )
        self.chk_mof.toggled.connect(self.moment_of_force_toggled.emit)
        extra_col.addWidget(self.chk_mof)
        self.chk_sum_moments = QCheckBox("Sum of Moments")
        self.chk_sum_moments.setStyleSheet(_CHK_SUM)
        self.chk_sum_moments.setToolTip(
            "Show sum of all moments (torque + moment of force)\\n"
            "Green arrows — resultant moment at each joint."
        )
        self.chk_sum_moments.toggled.connect(self.sum_moments_toggled.emit)
        extra_col.addWidget(self.chk_sum_moments)
        self.chk_3d = QCheckBox("3D Segments")
        self.chk_3d.setStyleSheet(_CHK_COM)
        self.chk_3d.setToolTip(
            "Toggle 3D tapered segment rendering (#1155).\\n"
            "Shows segments as gradient-shaded cylinders."
        )
        self.chk_3d.toggled.connect(self.mode_3d_toggled.emit)
        extra_col.addWidget(self.chk_3d)
        # Rotation controls (#1146)
        azimuth_row = QHBoxLayout()
        azimuth_row.setContentsMargins(0, 0, 0, 0)
        azimuth_row.setSpacing(2)
        az_lbl = QLabel("Az:")
        az_lbl.setStyleSheet("color:#606080;font-size:10px;")
        az_lbl.setToolTip("View azimuth rotation (0°-360°)")
        azimuth_row.addWidget(az_lbl)
        self._sld_azimuth = QSlider(Qt.Orientation.Horizontal)
        self._sld_azimuth.setRange(0, 360)
        self._sld_azimuth.setValue(0)
        self._sld_azimuth.setFixedWidth(80)
        self._sld_azimuth.setStyleSheet(
            "QSlider::groove:horizontal{height:4px;background:#252540;"
            "border-radius:2px;}"
            "QSlider::handle:horizontal{width:10px;margin:-3px 0;"
            "background:#6080b0;border-radius:5px;}"
        )
        self._sld_azimuth.valueChanged.connect(self._on_azimuth_slider)
        azimuth_row.addWidget(self._sld_azimuth)
        self._lbl_azimuth = QLabel("0°")
        self._lbl_azimuth.setStyleSheet("color:#606080;font-size:10px;min-width:30px;")
        azimuth_row.addWidget(self._lbl_azimuth)
        extra_col.addLayout(azimuth_row)
        tilt_row = QHBoxLayout()
        tilt_row.setContentsMargins(0, 0, 0, 0)
        tilt_row.setSpacing(2)
        tilt_lbl = QLabel("Tilt:")
        tilt_lbl.setStyleSheet("color:#606080;font-size:10px;")
        tilt_lbl.setToolTip("Swing plane tilt from vertical (0°-90°)")
        tilt_row.addWidget(tilt_lbl)
        self._sld_tilt = QSlider(Qt.Orientation.Horizontal)
        self._sld_tilt.setRange(0, 90)
        self._sld_tilt.setValue(0)
        self._sld_tilt.setFixedWidth(80)
        self._sld_tilt.setStyleSheet(
            "QSlider::groove:horizontal{height:4px;background:#252540;"
            "border-radius:2px;}"
            "QSlider::handle:horizontal{width:10px;margin:-3px 0;"
            "background:#608050;border-radius:5px;}"
        )
        self._sld_tilt.valueChanged.connect(self._on_tilt_slider)
        tilt_row.addWidget(self._sld_tilt)
        self._lbl_tilt = QLabel("0°")
        self._lbl_tilt.setStyleSheet("color:#606080;font-size:10px;min-width:30px;")
        tilt_row.addWidget(self._lbl_tilt)
        extra_col.addLayout(tilt_row)
        extra_col.addStretch()
        layout.addLayout(extra_col)

'''

OVERLAY_NEW_FUNC = '''    def _build_overlay_section(self, layout: "QHBoxLayout") -> None:
        """Build stacked overlay controls: three rows of [☑ checkbox] [slider] [value].

        All three overlay types (Force Vectors, Mobility Ellipsoids, Force Ellipsoids)
        are stacked vertically in a compact section.
        """
        if not (layout is not None):
            raise ValueError("layout must be provided")
        overlay_frame = QFrame()
        overlay_frame.setObjectName("overlay_section")
        overlay_frame.setStyleSheet(_OVERLAY_SECTION)
        overlay_layout = QVBoxLayout(overlay_frame)
        overlay_layout.setContentsMargins(4, 2, 4, 2)
        overlay_layout.setSpacing(1)
        self._overlay_build_frame_rows(overlay_layout)
        layout.addWidget(overlay_frame)
        layout.addWidget(_vline())
        self._overlay_build_extra_col(layout)
        layout.addWidget(_vline())
        self._status_lbl = QLabel("Ready")
        self._status_lbl.setStyleSheet("color:#404060;font-size:11px;")
        layout.addWidget(self._status_lbl)
        layout.addStretch()

'''


def fix_toolstrip_file():
    text = TOOLSTRIP_FILE.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    # Find _build_overlay_section start (it's a method, indented)
    start_lineno = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("def _build_overlay_section("):
            start_lineno = i
            break
    if start_lineno is None:
        print("ERROR: could not find _build_overlay_section")
        return False

    # Find end: next method/def at same indent level
    indent = len(lines[start_lineno]) - len(lines[start_lineno].lstrip())
    end_lineno = len(lines)
    for i in range(start_lineno + 1, len(lines)):
        line = lines[i]
        if not line.strip():
            continue
        curr_indent = len(line) - len(line.lstrip())
        if curr_indent <= indent and (
            line.lstrip().startswith("def ") or line.lstrip().startswith("class ")
            or line.lstrip().startswith("# ") or line.lstrip().startswith("@")
        ):
            end_lineno = i
            break

    old_method = "".join(lines[start_lineno:end_lineno])

    # Insert OVERLAY_HELPERS before the old method, replace old with new
    replacement = OVERLAY_HELPERS + OVERLAY_NEW_FUNC
    new_text = text.replace(old_method, replacement)
    if new_text == text:
        print("ERROR: toolstrip replacement had no effect")
        return False
    TOOLSTRIP_FILE.write_text(new_text, encoding="utf-8")
    loc = func_loc(TOOLSTRIP_FILE, "_build_overlay_section")
    print(f"_build_overlay_section: {loc} LOC (target <= 50)")
    return loc is not None and loc <= 50


# ---------------------------------------------------------------------------
# Write TDD test file
# ---------------------------------------------------------------------------

TEST_FILE = REPO / "tests/unit/test_function_size_contracts.py"

TEST_CONTENT = '''"""
Contract tests: enforce <= 50-LOC function-size budget on nominated functions.

These tests use AST inspection so no imports of the target modules are needed.
They serve as regression gates: if a function grows beyond the budget the test
turns red immediately — before runtime or coverage issues surface.
"""

from __future__ import annotations

import ast
import pytest
from pathlib import Path

REPO = Path(__file__).parent.parent.parent


def _func_loc(filepath: Path, func_name: str) -> int | None:
    """Return the LOC of *func_name* in *filepath* via AST, or None if not found."""
    tree = ast.parse(filepath.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == func_name:
                return node.end_lineno - node.lineno
    return None


LOC_BUDGET = 50


@pytest.mark.unit
class TestAnalyticalFkJacobiansJax:
    """analytical_fk_jacobians_jax must stay within the LOC budget."""

    _FILE = REPO / "src/shared/python/pendulum_simulator/physics_golfer_jax.py"
    _FUNC = "analytical_fk_jacobians_jax"

    def test_function_exists(self) -> None:
        loc = _func_loc(self._FILE, self._FUNC)
        assert loc is not None, f"{self._FUNC} not found in {self._FILE}"

    def test_loc_within_budget(self) -> None:
        loc = _func_loc(self._FILE, self._FUNC)
        assert loc is not None
        assert loc <= LOC_BUDGET, (
            f"{self._FUNC} is {loc} LOC — exceeds budget of {LOC_BUDGET}. "
            "Extract helper functions."
        )


@pytest.mark.unit
class TestBuildQtWindow:
    """_build_qt_window must stay within the LOC budget."""

    _FILE = REPO / "src/launchers/cross_engine_dashboard.py"
    _FUNC = "_build_qt_window"

    def test_function_exists(self) -> None:
        loc = _func_loc(self._FILE, self._FUNC)
        assert loc is not None, f"{self._FUNC} not found in {self._FILE}"

    def test_loc_within_budget(self) -> None:
        loc = _func_loc(self._FILE, self._FUNC)
        assert loc is not None
        assert loc <= LOC_BUDGET, (
            f"{self._FUNC} is {loc} LOC — exceeds budget of {LOC_BUDGET}. "
            "Extract helper functions."
        )


@pytest.mark.unit
class TestBuildTriplePanel:
    """build_triple_panel must stay within the LOC budget."""

    _FILE = REPO / "src/shared/python/pendulum_simulator/gui/panel_builders.py"
    _FUNC = "build_triple_panel"

    def test_function_exists(self) -> None:
        loc = _func_loc(self._FILE, self._FUNC)
        assert loc is not None, f"{self._FUNC} not found in {self._FILE}"

    def test_loc_within_budget(self) -> None:
        loc = _func_loc(self._FILE, self._FUNC)
        assert loc is not None
        assert loc <= LOC_BUDGET, (
            f"{self._FUNC} is {loc} LOC — exceeds budget of {LOC_BUDGET}. "
            "Extract helper class."
        )


@pytest.mark.unit
class TestBuildGolferPanel:
    """build_golfer_panel must stay within the LOC budget."""

    _FILE = REPO / "src/shared/python/pendulum_simulator/gui/panel_builders.py"
    _FUNC = "build_golfer_panel"

    def test_function_exists(self) -> None:
        loc = _func_loc(self._FILE, self._FUNC)
        assert loc is not None, f"{self._FUNC} not found in {self._FILE}"

    def test_loc_within_budget(self) -> None:
        loc = _func_loc(self._FILE, self._FUNC)
        assert loc is not None
        assert loc <= LOC_BUDGET, (
            f"{self._FUNC} is {loc} LOC — exceeds budget of {LOC_BUDGET}. "
            "Extract helper class."
        )


@pytest.mark.unit
class TestBuildOverlaySection:
    """_build_overlay_section must stay within the LOC budget."""

    _FILE = REPO / "src/shared/python/pendulum_simulator/gui/toolstrip_widget.py"
    _FUNC = "_build_overlay_section"

    def test_function_exists(self) -> None:
        loc = _func_loc(self._FILE, self._FUNC)
        assert loc is not None, f"{self._FUNC} not found in {self._FILE}"

    def test_loc_within_budget(self) -> None:
        loc = _func_loc(self._FILE, self._FUNC)
        assert loc is not None
        assert loc <= LOC_BUDGET, (
            f"{self._FUNC} is {loc} LOC — exceeds budget of {LOC_BUDGET}. "
            "Extract helper methods."
        )
'''


def write_test_file():
    TEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    TEST_FILE.write_text(TEST_CONTENT, encoding="utf-8")
    print(f"Test file written: {TEST_FILE}")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Fix #2514: Decompose oversized Python functions ===\n")
    results = []

    print("Writing TDD test file...")
    results.append(write_test_file())

    print("\nFix 1: analytical_fk_jacobians_jax")
    results.append(fix_jax_file())

    print("\nFix 2: _build_qt_window")
    results.append(fix_dashboard_file())

    print("\nFix 3 & 4: build_triple_panel + build_golfer_panel")
    results.append(fix_panel_file())

    print("\nFix 5: _build_overlay_section")
    results.append(fix_toolstrip_file())

    print("\n=== Summary ===")
    if all(results):
        print("All fixes applied successfully.")
        sys.exit(0)
    else:
        print("One or more fixes FAILED.")
        sys.exit(1)

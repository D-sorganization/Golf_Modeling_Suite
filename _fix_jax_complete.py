"""
Complete atomic replacement of analytical_fk_jacobians_jax section.

Replaces the entire 181-LOC function with all necessary helpers extracted
plus the short orchestrator (17 LOC after ruff format). Works whether the
file is in original state or partially-fixed state.
"""
import ast
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent
JAX_FILE = REPO / "src/shared/python/pendulum_simulator/physics_golfer_jax.py"

FULL_REPLACEMENT = '''
def _compute_trig_golfer_jax(q: JaxArray) -> tuple:
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


def _jac_hub_jax(sh: JaxArray, ch: JaxArray, p: GolferParamsJAX) -> JaxArray:
    """Position Jacobian for the hub mass point."""
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(p.L_hub * ch)
    J = J.at[1, 0].set(p.L_hub * sh)
    return J


def _jac_rs_jax(sh: JaxArray, ch: JaxArray, p: GolferParamsJAX) -> JaxArray:
    """Position Jacobian for the right shoulder."""
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(p.L_hub * ch - p.d_rs * sh)
    J = J.at[1, 0].set(p.L_hub * sh + p.d_rs * ch)
    return J


def _jac_re_jax(
    sh: JaxArray,
    ch: JaxArray,
    srs: JaxArray,
    crs: JaxArray,
    p: GolferParamsJAX,
) -> JaxArray:
    """Position Jacobian for the right elbow."""
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(p.L_hub * ch - p.d_rs * sh + p.L_r_upper * crs)
    J = J.at[1, 0].set(p.L_hub * sh + p.d_rs * ch + p.L_r_upper * srs)
    J = J.at[0, 1].set(p.L_r_upper * crs)
    J = J.at[1, 1].set(p.L_r_upper * srs)
    return J


def _jac_rh_jax(
    sh: JaxArray,
    ch: JaxArray,
    srs: JaxArray,
    crs: JaxArray,
    sre: JaxArray,
    cre: JaxArray,
    p: GolferParamsJAX,
) -> JaxArray:
    """Position Jacobian for the right hand."""
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(
        p.L_hub * ch - p.d_rs * sh + p.L_r_upper * crs + p.L_r_fore * cre
    )
    J = J.at[1, 0].set(
        p.L_hub * sh + p.d_rs * ch + p.L_r_upper * srs + p.L_r_fore * sre
    )
    J = J.at[0, 1].set(p.L_r_upper * crs + p.L_r_fore * cre)
    J = J.at[1, 1].set(p.L_r_upper * srs + p.L_r_fore * sre)
    J = J.at[0, 2].set(p.L_r_fore * cre)
    J = J.at[1, 2].set(p.L_r_fore * sre)
    return J


def _jac_ls_jax(sh: JaxArray, ch: JaxArray, p: GolferParamsJAX) -> JaxArray:
    """Position Jacobian for the left shoulder."""
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(p.L_hub * ch + p.d_ls * sh)
    J = J.at[1, 0].set(p.L_hub * sh - p.d_ls * ch)
    return J


def _jac_le_jax(
    sh: JaxArray,
    ch: JaxArray,
    sls: JaxArray,
    cls_: JaxArray,
    p: GolferParamsJAX,
) -> JaxArray:
    """Position Jacobian for the left elbow."""
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(p.L_hub * ch + p.d_ls * sh + p.L_l_upper * cls_)
    J = J.at[1, 0].set(p.L_hub * sh - p.d_ls * ch + p.L_l_upper * sls)
    J = J.at[0, 4].set(p.L_l_upper * cls_)
    J = J.at[1, 4].set(p.L_l_upper * sls)
    return J


def _jac_lh_jax(
    sh: JaxArray,
    ch: JaxArray,
    sls: JaxArray,
    cls_: JaxArray,
    sle: JaxArray,
    cle: JaxArray,
    p: GolferParamsJAX,
) -> JaxArray:
    """Position Jacobian for the left hand."""
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(
        p.L_hub * ch + p.d_ls * sh + p.L_l_upper * cls_ + p.L_l_fore * cle
    )
    J = J.at[1, 0].set(
        p.L_hub * sh - p.d_ls * ch + p.L_l_upper * sls + p.L_l_fore * sle
    )
    J = J.at[0, 4].set(p.L_l_upper * cls_ + p.L_l_fore * cle)
    J = J.at[1, 4].set(p.L_l_upper * sls + p.L_l_fore * sle)
    J = J.at[0, 5].set(p.L_l_fore * cle)
    J = J.at[1, 5].set(p.L_l_fore * sle)
    return J


def _jac_club_end_jax(
    sh: JaxArray,
    ch: JaxArray,
    srs: JaxArray,
    crs: JaxArray,
    sre: JaxArray,
    cre: JaxArray,
    sc: JaxArray,
    cc: JaxArray,
    coeff_x: JaxArray,
    coeff_y: JaxArray,
    p: GolferParamsJAX,
) -> JaxArray:
    """Position Jacobian for a club point parameterised by offset coefficients."""
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(
        p.L_hub * ch - p.d_rs * sh + p.L_r_upper * crs + p.L_r_fore * cre
    )
    J = J.at[1, 0].set(
        p.L_hub * sh + p.d_rs * ch + p.L_r_upper * srs + p.L_r_fore * sre
    )
    J = J.at[0, 1].set(p.L_r_upper * crs + p.L_r_fore * cre)
    J = J.at[1, 1].set(p.L_r_upper * srs + p.L_r_fore * sre)
    J = J.at[0, 2].set(p.L_r_fore * cre)
    J = J.at[1, 2].set(p.L_r_fore * sre)
    J = J.at[0, 7].set(coeff_x * cc)
    J = J.at[1, 7].set(coeff_y * sc)
    return J


def _jac_club_com_jax(
    sh: JaxArray,
    ch: JaxArray,
    srs: JaxArray,
    crs: JaxArray,
    sre: JaxArray,
    cre: JaxArray,
    sc: JaxArray,
    cc: JaxArray,
    p: GolferParamsJAX,
) -> JaxArray:
    """Position Jacobian for the club center of mass."""
    coeff_x = 0.5 * p.L_club - p.grip_right
    coeff_y = -0.5 * (p.L_club - 2 * p.grip_right)
    return _jac_club_end_jax(sh, ch, srs, crs, sre, cre, sc, cc, coeff_x, coeff_y, p)


def _jac_club_tip_jax(
    sh: JaxArray,
    ch: JaxArray,
    srs: JaxArray,
    crs: JaxArray,
    sre: JaxArray,
    cre: JaxArray,
    sc: JaxArray,
    cc: JaxArray,
    p: GolferParamsJAX,
) -> JaxArray:
    """Position Jacobian for the club tip."""
    coeff_x = p.L_club - p.grip_right
    coeff_y = -(p.L_club - p.grip_right)
    return _jac_club_end_jax(sh, ch, srs, crs, sre, cre, sc, cc, coeff_x, coeff_y, p)


def analytical_fk_jacobians_jax(q: JaxArray, p: GolferParamsJAX) -> dict[str, JaxArray]:
    """Compute position Jacobians analytically for all mass points (JAX version)."""
    if not (q is not None):
        raise ValueError("q must be provided")
    sh, ch, srs, crs, sre, cre, sls, cls_, sle, cle, sc, cc = (
        _compute_trig_golfer_jax(q)
    )
    return {
        "hub": _jac_hub_jax(sh, ch, p),
        "rs": _jac_rs_jax(sh, ch, p),
        "re": _jac_re_jax(sh, ch, srs, crs, p),
        "rh": _jac_rh_jax(sh, ch, srs, crs, sre, cre, p),
        "ls": _jac_ls_jax(sh, ch, p),
        "le": _jac_le_jax(sh, ch, sls, cls_, p),
        "lh": _jac_lh_jax(sh, ch, sls, cls_, sle, cle, p),
        "club_com": _jac_club_com_jax(sh, ch, srs, crs, sre, cre, sc, cc, p),
        "club_tip": _jac_club_tip_jax(sh, ch, srs, crs, sre, cre, sc, cc, p),
    }
'''


def func_loc(filepath: Path, func_name: str) -> int | None:
    tree = ast.parse(filepath.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == func_name:
                return node.end_lineno - node.lineno
    return None


def main() -> int:
    text = JAX_FILE.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    # Find analytical_fk_jacobians_jax (could be at various positions)
    # Also look for _compute_trig_golfer_jax in case previous fix was partial
    section_start = None
    for i, line in enumerate(lines):
        if line.startswith("def _compute_trig_golfer_jax(") or line.startswith(
            "def analytical_fk_jacobians_jax("
        ):
            # Start of the section we want to replace
            if section_start is None or i < section_start:
                section_start = i
            break

    if section_start is None:
        # Try just finding analytical_fk_jacobians_jax
        for i, line in enumerate(lines):
            if line.startswith("def analytical_fk_jacobians_jax("):
                section_start = i
                break

    if section_start is None:
        print("ERROR: could not find target functions")
        return 1

    # Find end: next top-level def that is NOT one of our helpers
    our_helpers = {
        "_compute_trig_golfer_jax",
        "_jac_hub_jax",
        "_jac_rs_jax",
        "_jac_re_jax",
        "_jac_rh_jax",
        "_jac_ls_jax",
        "_jac_le_jax",
        "_jac_lh_jax",
        "_jac_club_end_jax",
        "_jac_club_com_jax",
        "_jac_club_tip_jax",
        "analytical_fk_jacobians_jax",
    }

    end_lineno = len(lines)
    for i in range(section_start + 1, len(lines)):
        line = lines[i]
        if not line.startswith("def ") and not line.startswith("class "):
            continue
        # Check if this is one of our helpers
        is_ours = False
        for name in our_helpers:
            if line.startswith(f"def {name}("):
                is_ours = True
                break
        if not is_ours:
            end_lineno = i
            break

    old_section = "".join(lines[section_start:end_lineno])
    replacement = FULL_REPLACEMENT + "\n\n"
    new_text = text.replace(old_section, replacement)
    if new_text == text:
        print("WARNING: no change made (possibly already correct)")
        # Still run ruff

    JAX_FILE.write_text(new_text if new_text != text else text, encoding="utf-8")

    # Run ruff check --fix (auto-fix only, ignore remaining errors for now)
    subprocess.run(
        ["python3", "-m", "ruff", "check", "--fix", str(JAX_FILE)],
        cwd=REPO, capture_output=True
    )
    # Run ruff format
    subprocess.run(
        ["python3", "-m", "ruff", "format", str(JAX_FILE)],
        cwd=REPO, capture_output=True
    )

    loc = func_loc(JAX_FILE, "analytical_fk_jacobians_jax")
    print(f"analytical_fk_jacobians_jax: {loc} LOC")

    # Check ruff
    result = subprocess.run(
        ["python3", "-m", "ruff", "check", str(JAX_FILE)],
        cwd=REPO, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"ruff errors:\n{result.stdout}")
        return 1

    if loc is None or loc > 50:
        print("FAIL: over 50 LOC budget")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

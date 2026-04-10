"""
Fix analytical_fk_jacobians_jax to stay <= 50 LOC after ruff format.

The current version (39 LOC pre-format) expands to 55 LOC post-format because
ruff expands the 11-arg _jac_club_end_jax calls. Solution: add thin wrappers
_jac_club_com_jax and _jac_club_tip_jax (9 args each, fits in 88 chars).
Also apply ruff UP037 fixes (remove string quotes from type annotations).
"""
import ast
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent
JAX_FILE = REPO / "src/shared/python/pendulum_simulator/physics_golfer_jax.py"

# New helpers to insert BEFORE analytical_fk_jacobians_jax
NEW_HELPERS = '''
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

'''

# Replacement for analytical_fk_jacobians_jax (short docstring to stay under budget)
NEW_FUNC = '''def analytical_fk_jacobians_jax(q: JaxArray, p: GolferParamsJAX) -> dict[str, JaxArray]:
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

    # Find analytical_fk_jacobians_jax
    start_lineno = None
    for i, line in enumerate(lines):
        if line.startswith("def analytical_fk_jacobians_jax("):
            start_lineno = i
            break
    if start_lineno is None:
        print("ERROR: could not find analytical_fk_jacobians_jax")
        return 1

    # Find end: next top-level def or class
    end_lineno = len(lines)
    for i in range(start_lineno + 1, len(lines)):
        if lines[i] and lines[i][0].isalpha() and (
            lines[i].startswith("def ") or lines[i].startswith("class ")
        ):
            end_lineno = i
            break

    old_func = "".join(lines[start_lineno:end_lineno])
    replacement = NEW_HELPERS + NEW_FUNC + "\n\n"
    new_text = text.replace(old_func, replacement)
    if new_text == text:
        print("ERROR: replacement had no effect")
        return 1

    JAX_FILE.write_text(new_text, encoding="utf-8")

    # Run ruff check --fix and format
    subprocess.run(
        ["python3", "-m", "ruff", "check", "--fix", str(JAX_FILE)],
        cwd=REPO,
        check=False,
    )
    subprocess.run(
        ["python3", "-m", "ruff", "format", str(JAX_FILE)],
        cwd=REPO,
        check=False,
    )

    loc = func_loc(JAX_FILE, "analytical_fk_jacobians_jax")
    print(f"analytical_fk_jacobians_jax: {loc} LOC (target <= 50)")
    if loc is None or loc > 50:
        print("FAIL: still over budget")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

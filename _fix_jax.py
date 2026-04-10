"""Fix analytical_fk_jacobians_jax - extract per-body Jacobian helpers."""
from pathlib import Path

path = Path('src/shared/python/pendulum_simulator/physics_golfer_jax.py')
content = path.read_text(encoding='utf-8')

# Find the function and replace it with extracted helpers + thin orchestrator
# The function spans lines 240-421

HELPERS = '''def _compute_trig_golfer_jax(
    q: JaxArray,
) -> tuple[JaxArray, ...]:
    """Precompute sin/cos values for all golfer joint angles from q."""
    th_hub = q[0]
    alpha_rs, alpha_re = q[1], q[2]
    alpha_ls, alpha_le = q[4], q[5]
    th_club = q[7]
    th_rs_abs = th_hub + alpha_rs
    th_re_abs = th_hub + alpha_rs + alpha_re
    th_ls_abs = th_hub + alpha_ls
    th_le_abs = th_hub + alpha_ls + alpha_le
    return (
        jnp.sin(th_hub), jnp.cos(th_hub),
        jnp.sin(th_rs_abs), jnp.cos(th_rs_abs),
        jnp.sin(th_re_abs), jnp.cos(th_re_abs),
        jnp.sin(th_ls_abs), jnp.cos(th_ls_abs),
        jnp.sin(th_le_abs), jnp.cos(th_le_abs),
        jnp.sin(th_club), jnp.cos(th_club),
    )


def _jac_hub_jax(sh: JaxArray, ch: JaxArray, p: GolferParamsJAX) -> JaxArray:
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(p.L_hub * ch)
    J = J.at[1, 0].set(p.L_hub * sh)
    return J


def _jac_rs_jax(sh: JaxArray, ch: JaxArray, p: GolferParamsJAX) -> JaxArray:
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(p.L_hub * ch - p.d_rs * sh)
    J = J.at[1, 0].set(p.L_hub * sh + p.d_rs * ch)
    return J


def _jac_re_jax(
    sh: JaxArray, ch: JaxArray,
    srs: JaxArray, crs: JaxArray,
    p: GolferParamsJAX,
) -> JaxArray:
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(p.L_hub * ch - p.d_rs * sh + p.L_r_upper * crs)
    J = J.at[1, 0].set(p.L_hub * sh + p.d_rs * ch + p.L_r_upper * srs)
    J = J.at[0, 1].set(p.L_r_upper * crs)
    J = J.at[1, 1].set(p.L_r_upper * srs)
    return J


def _jac_rh_jax(
    sh: JaxArray, ch: JaxArray,
    srs: JaxArray, crs: JaxArray,
    sre: JaxArray, cre: JaxArray,
    p: GolferParamsJAX,
) -> JaxArray:
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
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(p.L_hub * ch + p.d_ls * sh)
    J = J.at[1, 0].set(p.L_hub * sh - p.d_ls * ch)
    return J


def _jac_le_jax(
    sh: JaxArray, ch: JaxArray,
    sls: JaxArray, cls_: JaxArray,
    p: GolferParamsJAX,
) -> JaxArray:
    J = jnp.zeros((2, N_DOF))
    J = J.at[0, 0].set(p.L_hub * ch + p.d_ls * sh + p.L_l_upper * cls_)
    J = J.at[1, 0].set(p.L_hub * sh - p.d_ls * ch + p.L_l_upper * sls)
    J = J.at[0, 4].set(p.L_l_upper * cls_)
    J = J.at[1, 4].set(p.L_l_upper * sls)
    return J


def _jac_lh_jax(
    sh: JaxArray, ch: JaxArray,
    sls: JaxArray, cls_: JaxArray,
    sle: JaxArray, cle: JaxArray,
    p: GolferParamsJAX,
) -> JaxArray:
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
    """Shared Jacobian structure for club_com and club_tip."""
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

'''

MAIN_FUNC = '''def analytical_fk_jacobians_jax(q: JaxArray, p: GolferParamsJAX) -> dict[str, JaxArray]:
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
        Keys: 'hub', 'rs', 're', 'rh', 'ls', 'le', 'lh', 'club_com', 'club_tip'
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
    }'''

# Find the function start marker in the file
marker = 'def analytical_fk_jacobians_jax(q: JaxArray, p: GolferParamsJAX) -> dict[str, JaxArray]:'
assert marker in content, f"Function marker not found in {path}"

# Find where the function starts and ends using ast
import ast
tree = ast.parse(content)
func_node = None
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'analytical_fk_jacobians_jax':
        func_node = node
        break
assert func_node is not None

lines = content.splitlines(keepends=True)
func_text = ''.join(lines[func_node.lineno - 1:func_node.end_lineno])

# Replace the function with helpers + new main function
content = content.replace(func_text, HELPERS + MAIN_FUNC)
path.write_text(content, encoding='utf-8')
print(f"Fixed {path}")

# Verify
tree2 = ast.parse(path.read_text(encoding='utf-8'))
for node in ast.walk(tree2):
    if isinstance(node, ast.FunctionDef) and node.name == 'analytical_fk_jacobians_jax':
        print(f"  analytical_fk_jacobians_jax: {node.end_lineno - node.lineno} LOC")

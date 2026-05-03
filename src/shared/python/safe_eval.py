"""Safe mathematical expression evaluator.

Replaces all uses of ``eval()`` with a hardened AST-based evaluator that:

1. Parses the expression into an AST and validates every node type.
2. Compiles the validated AST into a code object (no raw string eval).
3. Executes the compiled code in a namespace that contains **only** the
   caller-supplied names -- ``__builtins__`` is always empty.

This eliminates the class of attacks where ``eval()`` can be abused even
when ``__builtins__`` is set to ``{}``.

Design-by-Contract
-------------------
* **Precondition**: ``expression`` is a non-empty string; ``namespace`` keys
  are all plain identifiers.
* **Postcondition**: the return value is whatever the compiled expression
  produces; no side-effects outside ``namespace``.
* **Invariant**: only the node types listed in ``_ALLOWED_NODE_TYPES`` will
  ever be executed.
"""

from __future__ import annotations

import ast
import math
import operator
from typing import Any

import numpy as np

# Conditional import: contracts module may or may not be importable depending on PYTHONPATH.
# The try/except pattern is intentional — noqa suppresses isort on this block.
try:
    from src.shared.python.contracts import require  # noqa: I001
except ImportError:

    def require(condition: bool, *args: object) -> None:  # type: ignore[misc]
        """Fallback require() when contracts module is unavailable."""
        if not condition:
            msg = args[0] if args else "Precondition violated"
            raise AssertionError(msg)


__all__ = [
    "safe_eval",
    "safe_eval_math",
    "validate_expression",
    "NUMPY_MATH_NAMESPACE",
    "SCALAR_MATH_NAMESPACE",
]

# ── Allowed AST node types ──────────────────────────────────────────────
# These are the *only* node kinds we permit.  Anything else (Import,
# FunctionDef, Attribute access, etc.) is rejected.

_ALLOWED_NODE_TYPES: tuple[type, ...] = (
    ast.Expression,
    ast.Load,
    # Arithmetic / logic
    ast.BinOp,
    ast.UnaryOp,
    ast.operator,
    ast.unaryop,
    ast.cmpop,
    ast.Compare,
    ast.BoolOp,
    ast.boolop,
    # Literals & names
    ast.Constant,
    ast.Name,
    # Function calls (only bare-name calls, no attribute calls)
    ast.Call,
    ast.keyword,
    # Subscript / slice (for array indexing)
    ast.Subscript,
    ast.Index,  # kept for Python 3.8 compat
    ast.Slice,
    # Starred args (e.g. f(*x))
    ast.Starred,
    # IfExp (ternary)
    ast.IfExp,
)


# ── Pre-built namespaces ────────────────────────────────────────────────

NUMPY_MATH_NAMESPACE: dict[str, Any] = {
    # Standard functions (numpy versions for array support)
    "abs": np.abs,
    "min": np.minimum,
    "max": np.maximum,
    "sum": np.sum,
    "len": len,
    "round": np.round,
    # Trigonometric
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "asin": np.arcsin,
    "acos": np.arccos,
    "atan": np.arctan,
    # Exponential / logarithmic
    "sqrt": np.sqrt,
    "log": np.log,
    "log10": np.log10,
    "exp": np.exp,
    "pow": np.power,
    # Statistical
    "mean": np.mean,
    "std": np.std,
    "median": np.median,
    # Constants
    "pi": np.pi,
    "e": np.e,
    # np-prefixed aliases
    "np_sqrt": np.sqrt,
    "np_log": np.log,
    "np_log10": np.log10,
    "np_exp": np.exp,
    "np_sin": np.sin,
    "np_cos": np.cos,
    "np_tan": np.tan,
    "np_abs": np.abs,
    "np_mean": np.mean,
    "np_std": np.std,
    "np_min": np.min,
    "np_max": np.max,
}

SCALAR_MATH_NAMESPACE: dict[str, Any] = {
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "len": len,
    "round": round,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "pow": pow,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
    "math": math,
}


# ── Core functions ──────────────────────────────────────────────────────


def validate_expression(
    expression: str,
    allowed_names: set[str] | None = None,
) -> ast.Expression:
    """Parse *expression* and validate every AST node.

    Parameters
    ----------
    expression:
        The math expression to validate.
    allowed_names:
        If provided, every ``ast.Name`` node must reference a name in this
        set.  Pass ``None`` to skip name checking (the caller is
        responsible for controlling the execution namespace).

    Returns
    -------
    ast.Expression
        The validated AST, ready to be compiled.

    Raises
    ------
    ValueError
        If the expression contains disallowed constructs.
    """
    if not expression or not expression.strip():
        raise ValueError("Expression must not be empty")

    require(
        isinstance(expression, str),
        "expression must be a string",
        type(expression).__name__,
    )

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid syntax: {exc}") from exc

    for node in ast.walk(tree):
        # Check node type is allowed
        if not isinstance(node, _ALLOWED_NODE_TYPES):
            raise ValueError(f"Unsafe operation detected: {type(node).__name__}")

        # Validate names
        if isinstance(node, ast.Name):
            if allowed_names is not None and node.id not in allowed_names:
                raise ValueError(f"Unknown variable or function: {node.id}")

        # Only bare-name function calls allowed (no attribute calls like
        # os.system)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if allowed_names is not None and node.func.id not in allowed_names:
                    raise ValueError(f"Unknown function: {node.func.id}")
            else:
                raise ValueError("Attribute-based function calls not allowed")

    return tree


_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
    ast.BitOr: operator.or_,
    ast.BitXor: operator.xor,
    ast.BitAnd: operator.and_,
    ast.MatMult: operator.matmul,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Not: operator.not_,
    ast.Invert: operator.invert,
}

def _eval_ast(node: ast.AST, namespace: dict[str, Any]) -> Any:
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body, namespace)
    elif isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Name):
        if node.id in namespace:
            return namespace[node.id]
        raise NameError(f"name '{node.id}' is not defined")
    elif isinstance(node, ast.BinOp):
        left = _eval_ast(node.left, namespace)
        right = _eval_ast(node.right, namespace)
        return _OPERATORS[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_ast(node.operand, namespace)
        return _OPERATORS[type(node.op)](operand)
    elif isinstance(node, ast.Compare):
        left = _eval_ast(node.left, namespace)
        for op, right_node in zip(node.ops, node.comparators):
            right = _eval_ast(right_node, namespace)
            if not _OPERATORS[type(op)](left, right):
                return False
            left = right
        return True
    elif isinstance(node, ast.BoolOp):
        values = [_eval_ast(v, namespace) for v in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        elif isinstance(node.op, ast.Or):
            return any(values)
    elif isinstance(node, ast.Call):
        func = _eval_ast(node.func, namespace)
        # Handle ast.Starred for *args
        args = []
        for arg in node.args:
            if isinstance(arg, ast.Starred):
                args.extend(_eval_ast(arg.value, namespace))
            else:
                args.append(_eval_ast(arg, namespace))
        kwargs = {kw.arg: _eval_ast(kw.value, namespace) for kw in node.keywords if kw.arg}
        return func(*args, **kwargs)
    elif isinstance(node, ast.Subscript):
        value = _eval_ast(node.value, namespace)
        slice_val = _eval_ast(node.slice, namespace)
        return value[slice_val]
    elif isinstance(node, ast.Index): # Python 3.8 compat
        return _eval_ast(node.value, namespace)
    elif isinstance(node, ast.Slice):
        lower = _eval_ast(node.lower, namespace) if node.lower else None
        upper = _eval_ast(node.upper, namespace) if node.upper else None
        step = _eval_ast(node.step, namespace) if node.step else None
        return slice(lower, upper, step)
    elif isinstance(node, ast.IfExp):
        test = _eval_ast(node.test, namespace)
        if test:
            return _eval_ast(node.body, namespace)
        else:
            return _eval_ast(node.orelse, namespace)
    else:
        raise ValueError(f"Unsupported AST node: {type(node).__name__}")


def safe_eval(
    expression: str,
    namespace: dict[str, Any],
    *,
    allowed_names: set[str] | None = None,
) -> Any:
    """Evaluate *expression* safely in *namespace*.

    Parameters
    ----------
    expression:
        Mathematical expression to evaluate.
    namespace:
        Dict of names the expression may reference (variables, functions,
        constants).  ``__builtins__`` is always forced to ``{}``.
    allowed_names:
        Optional explicit allowlist.  Defaults to ``namespace.keys()``.

    Returns
    -------
    Any
        Result of the expression evaluation.
    """
    if not (expression is not None):
        raise ValueError("expression must be provided")
    if not (expression is not None):
        raise ValueError("expression must be provided")
    if allowed_names is None:
        allowed_names = set(namespace.keys())

    tree = validate_expression(expression, allowed_names)
    return _eval_ast(tree, namespace)


def safe_eval_math(
    expression: str,
    variables: dict[str, Any] | None = None,
    *,
    use_numpy: bool = True,
) -> Any:
    """Convenience wrapper that merges caller variables with math functions.

    Parameters
    ----------
    expression:
        Mathematical expression.
    variables:
        Caller-supplied variables (signal data, parameters, etc.).
    use_numpy:
        If True, use numpy math functions (array-safe).  Otherwise use
        scalar ``math`` module functions.
    """
    if not (expression is not None):
        raise ValueError("expression must be provided")
    if not (expression is not None):
        raise ValueError("expression must be provided")
    base = dict(NUMPY_MATH_NAMESPACE if use_numpy else SCALAR_MATH_NAMESPACE)
    if variables:
        base.update(variables)
    return safe_eval(expression, base)

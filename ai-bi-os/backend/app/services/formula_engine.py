"""Safe evaluator for user-supplied derived-column expressions.

Deliberately does not use eval()/exec()/pandas.eval() (engine='python' is a
thin wrapper over eval, and even the numexpr engine has had sandbox-escape
CVEs) — user formulas run server-side against real data, so this walks the
parsed AST itself and only ever executes a fixed, explicit whitelist of
operators and functions.
"""
import ast
import operator

import numpy as np
import pandas as pd


class FormulaError(ValueError):
    pass


_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARYOPS = {ast.USub: operator.neg, ast.UAdd: operator.pos}
_COMPARE_OPS = {
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}
_FUNCS = {
    "abs": np.abs,
    "round": np.round,
    "sqrt": np.sqrt,
    "log": np.log,
    "log10": np.log10,
    "exp": np.exp,
    "min": np.minimum,
    "max": np.maximum,
}

MAX_EXPRESSION_LENGTH = 500


def _eval(node: ast.AST, columns: dict):
    if isinstance(node, ast.Expression):
        return _eval(node.body, columns)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise FormulaError("Only numeric literals are allowed")
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in columns:
            raise FormulaError(f"Unknown column: {node.id}")
        return columns[node.id]
    if isinstance(node, ast.BinOp):
        op = _BINOPS.get(type(node.op))
        if op is None:
            raise FormulaError(f"Operator not allowed: {type(node.op).__name__}")
        return op(_eval(node.left, columns), _eval(node.right, columns))
    if isinstance(node, ast.UnaryOp):
        op = _UNARYOPS.get(type(node.op))
        if op is None:
            raise FormulaError(f"Operator not allowed: {type(node.op).__name__}")
        return op(_eval(node.operand, columns))
    if isinstance(node, ast.Compare):
        if len(node.ops) != 1:
            raise FormulaError("Chained comparisons are not supported")
        op = _COMPARE_OPS.get(type(node.ops[0]))
        if op is None:
            raise FormulaError(f"Comparison not allowed: {type(node.ops[0]).__name__}")
        return op(_eval(node.left, columns), _eval(node.comparators[0], columns))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCS:
            raise FormulaError("Only abs, round, sqrt, log, log10, exp, min, max are allowed")
        if node.keywords:
            raise FormulaError("Keyword arguments are not supported")
        args = [_eval(a, columns) for a in node.args]
        return _FUNCS[node.func.id](*args)
    raise FormulaError(f"Unsupported expression syntax: {type(node).__name__}")


def evaluate_formula(df: pd.DataFrame, expression: str) -> pd.Series:
    """Evaluates `expression` against df's columns and returns the result as a
    Series aligned to df's index. Raises FormulaError on anything unsafe,
    unknown, or malformed rather than ever calling eval()."""
    if not expression or not expression.strip():
        raise FormulaError("Expression is empty")
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise FormulaError(f"Expression is too long (max {MAX_EXPRESSION_LENGTH} characters)")

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise FormulaError(f"Invalid syntax: {e.msg}")

    columns = {col: df[col] for col in df.columns}
    result = _eval(tree, columns)

    if not isinstance(result, pd.Series):
        # A formula of pure literals (e.g. "2 + 2") is valid but scalar —
        # broadcast it to a constant column matching the dataset's length.
        result = pd.Series([result] * len(df), index=df.index)

    return result

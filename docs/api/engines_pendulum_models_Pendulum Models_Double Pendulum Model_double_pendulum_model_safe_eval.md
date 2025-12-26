# engines.pendulum_models.Pendulum Models.Double Pendulum Model.double_pendulum_model.safe_eval

Safe evaluation of user-provided mathematical expressions.

## Classes

### SafeEvaluator

Safe evaluation of user-provided expressions using AST whitelisting.

#### Methods

##### validate
```python
def validate(self: Any, expression: str) -> ast.AST
```

Parses and validates the expression against the allowlist.

##### compile
```python
def compile(self: Any, expression: str) -> CodeType
```

Validates and compiles the expression.

##### evaluate_code
```python
def evaluate_code(self: Any, code: CodeType, context: Any) -> float
```

Evaluates compiled code with the given context.

##### evaluate
```python
def evaluate(self: Any, expression: str, context: Any) -> float
```

Evaluates the expression with the given context.

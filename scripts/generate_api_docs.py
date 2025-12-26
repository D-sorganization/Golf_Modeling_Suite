#!/usr/bin/env python3
"""
API Documentation Generator

This script generates comprehensive API documentation for the Golf Modeling Suite,
including module references, class hierarchies, and usage examples.
"""

import ast
import sys
from pathlib import Path
from typing import Any

from shared.python.core import setup_logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = setup_logging(__name__)


class APIDocGenerator:
    """Generates API documentation from Python source code."""

    def __init__(self, output_dir: Path):
        """Initialize the API documentation generator."""
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.modules_info: dict[str, Any] = {}

    def analyze_module(self, module_path: Path) -> dict[str, Any]:
        """Analyze a Python module and extract API information."""
        module_info: dict[str, Any] = {
            "path": str(module_path),
            "classes": [],
            "functions": [],
            "constants": [],
            "imports": [],
            "docstring": "",
        }

        try:
            # Read and parse the module
            with open(module_path, encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            # Extract module docstring
            docstring = ast.get_docstring(tree)
            if docstring:
                module_info["docstring"] = docstring

            # Analyze AST nodes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = self._analyze_class(node)
                    module_info["classes"].append(class_info)

                elif isinstance(node, ast.FunctionDef):
                    # Only top-level functions (not methods)
                    if isinstance(
                        node.parent if hasattr(node, "parent") else None, ast.Module
                    ):
                        func_info = self._analyze_function(node)
                        module_info["functions"].append(func_info)

                elif isinstance(node, ast.Assign):
                    # Constants (uppercase variables)
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            const_info = {
                                "name": target.id,
                                "line": node.lineno,
                            }
                            module_info["constants"].append(const_info)

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        module_info["imports"].append(
                            {
                                "module": alias.name,
                                "alias": alias.asname,
                                "type": "import",
                            }
                        )

                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        module_info["imports"].append(
                            {
                                "module": node.module,
                                "name": alias.name,
                                "alias": alias.asname,
                                "type": "from_import",
                            }
                        )

        except Exception as e:
            logger.error(f"Failed to analyze module {module_path}: {e}")

        return module_info

    def _analyze_class(self, node: ast.ClassDef) -> dict[str, Any]:
        """Analyze a class definition."""
        class_info: dict[str, Any] = {
            "name": node.name,
            "line": node.lineno,
            "docstring": ast.get_docstring(node) or "",
            "methods": [],
            "properties": [],
            "bases": [],
        }

        # Extract base classes
        for base in node.bases:
            if isinstance(base, ast.Name):
                class_info["bases"].append(base.id)
            elif isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name):
                class_info["bases"].append(f"{base.value.id}.{base.attr}")

        # Analyze class members
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self._analyze_function(item)
                method_info["is_method"] = True

                # Classify method type
                if item.name.startswith("__") and item.name.endswith("__"):
                    method_info["method_type"] = "magic"
                elif item.name.startswith("_"):
                    method_info["method_type"] = "private"
                else:
                    method_info["method_type"] = "public"

                class_info["methods"].append(method_info)

            elif isinstance(item, ast.AsyncFunctionDef):
                method_info = self._analyze_function(item)
                method_info["is_method"] = True
                method_info["is_async"] = True
                class_info["methods"].append(method_info)

        return class_info

    def _analyze_function(self, node) -> dict[str, Any]:
        """Analyze a function definition."""
        func_info = {
            "name": node.name,
            "line": node.lineno,
            "docstring": ast.get_docstring(node) or "",
            "args": [],
            "returns": None,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
        }

        # Analyze arguments
        for arg in node.args.args:
            arg_info = {"name": arg.arg}

            # Type annotation
            if arg.annotation:
                arg_info["type"] = self._get_annotation_string(arg.annotation)

            func_info["args"].append(arg_info)

        # Return type annotation
        if node.returns:
            func_info["returns"] = self._get_annotation_string(node.returns)

        return func_info

    def _get_annotation_string(self, annotation) -> str:
        """Convert AST annotation to string."""
        try:
            if isinstance(annotation, ast.Name):
                return annotation.id
            elif isinstance(annotation, ast.Attribute) and isinstance(
                annotation.value, ast.Name
            ):
                return f"{annotation.value.id}.{annotation.attr}"
            elif isinstance(annotation, ast.Subscript):
                # Handle generic types like List[str]
                value = self._get_annotation_string(annotation.value)
                slice_val = self._get_annotation_string(annotation.slice)
                return f"{value}[{slice_val}]"
            elif isinstance(annotation, ast.Constant):
                return str(annotation.value)
            else:
                return "Any"
        except Exception:
            return "Any"

    def scan_project(self, project_root: Path) -> dict[str, Any]:
        """Scan the entire project for Python modules."""
        project_info: dict[str, Any] = {
            "modules": {},
            "packages": [],
        }

        # Find all Python files
        python_files = list(project_root.rglob("*.py"))

        # Filter out test files and __pycache__
        python_files = [
            f
            for f in python_files
            if "__pycache__" not in str(f)
            and "test_" not in f.name
            and not f.name.endswith("_test.py")
        ]

        logger.info(f"Found {len(python_files)} Python files to analyze")

        for py_file in python_files:
            try:
                # Get relative path from project root
                rel_path = py_file.relative_to(project_root)
                module_name = (
                    str(rel_path)
                    .replace("/", ".")
                    .replace("\\", ".")
                    .replace(".py", "")
                )

                # Skip if it's a script in scripts/ directory
                if module_name.startswith("scripts."):
                    continue

                module_info = self.analyze_module(py_file)
                project_info["modules"][module_name] = module_info

            except Exception as e:
                logger.warning(f"Skipped {py_file}: {e}")

        return project_info

    def generate_module_doc(self, module_name: str, module_info: dict[str, Any]) -> str:
        """Generate documentation for a single module."""
        doc = []

        # Module header
        doc.append(f"# {module_name}")
        doc.append("")

        # Module docstring
        if module_info["docstring"]:
            doc.append(module_info["docstring"])
            doc.append("")

        # Classes
        if module_info["classes"]:
            doc.append("## Classes")
            doc.append("")

            for class_info in module_info["classes"]:
                doc.append(f"### {class_info['name']}")
                doc.append("")

                if class_info["docstring"]:
                    doc.append(class_info["docstring"])
                    doc.append("")

                # Base classes
                if class_info["bases"]:
                    doc.append(f"**Inherits from:** {', '.join(class_info['bases'])}")
                    doc.append("")

                # Methods
                if class_info["methods"]:
                    doc.append("#### Methods")
                    doc.append("")

                    for method in class_info["methods"]:
                        if (
                            method["method_type"] == "public"
                        ):  # Only document public methods
                            doc.append(f"##### {method['name']}")

                            # Method signature
                            args_str = ", ".join(
                                [
                                    f"{arg['name']}: {arg.get('type', 'Any')}"
                                    for arg in method["args"]
                                ]
                            )
                            return_str = (
                                f" -> {method['returns']}" if method["returns"] else ""
                            )

                            doc.append("```python")
                            async_prefix = "async " if method.get("is_async") else ""
                            doc.append(
                                f"{async_prefix}def {method['name']}({args_str}){return_str}"
                            )
                            doc.append("```")
                            doc.append("")

                            if method["docstring"]:
                                doc.append(method["docstring"])
                                doc.append("")

        # Functions
        if module_info["functions"]:
            doc.append("## Functions")
            doc.append("")

            for func_info in module_info["functions"]:
                if not func_info["name"].startswith("_"):  # Only public functions
                    doc.append(f"### {func_info['name']}")

                    # Function signature
                    args_str = ", ".join(
                        [
                            f"{arg['name']}: {arg.get('type', 'Any')}"
                            for arg in func_info["args"]
                        ]
                    )
                    return_str = (
                        f" -> {func_info['returns']}" if func_info["returns"] else ""
                    )

                    doc.append("```python")
                    async_prefix = "async " if func_info.get("is_async") else ""
                    doc.append(
                        f"{async_prefix}def {func_info['name']}({args_str}){return_str}"
                    )
                    doc.append("```")
                    doc.append("")

                    if func_info["docstring"]:
                        doc.append(func_info["docstring"])
                        doc.append("")

        # Constants
        if module_info["constants"]:
            doc.append("## Constants")
            doc.append("")

            for const in module_info["constants"]:
                doc.append(f"- `{const['name']}`")
            doc.append("")

        return "\n".join(doc)

    def generate_index(self, project_info: dict[str, Any]) -> str:
        """Generate the main API index."""
        doc = []

        doc.append("# Golf Modeling Suite API Reference")
        doc.append("")
        doc.append("This is the complete API reference for the Golf Modeling Suite.")
        doc.append("")

        # Group modules by package
        packages: dict[str, list[str]] = {}
        for module_name in project_info["modules"]:
            parts = module_name.split(".")
            package = parts[0] if len(parts) > 1 else "root"

            if package not in packages:
                packages[package] = []
            packages[package].append(module_name)

        # Generate package sections
        for package_name, modules in sorted(packages.items()):
            doc.append(f"## {package_name.title()} Package")
            doc.append("")

            for module_name in sorted(modules):
                module_info = project_info["modules"][module_name]

                # Module link and description
                doc_file = module_name.replace(".", "_") + ".md"
                doc.append(f"- [{module_name}]({doc_file})")

                if module_info["docstring"]:
                    # First line of docstring as description
                    first_line = module_info["docstring"].split("\n")[0]
                    doc.append(f"  - {first_line}")

                # List classes and functions
                if module_info["classes"]:
                    class_names = [c["name"] for c in module_info["classes"]]
                    doc.append(f"  - Classes: {', '.join(class_names)}")

                if module_info["functions"]:
                    func_names = [
                        f["name"]
                        for f in module_info["functions"]
                        if not f["name"].startswith("_")
                    ]
                    if func_names:
                        doc.append(f"  - Functions: {', '.join(func_names)}")

                doc.append("")

        return "\n".join(doc)

    def generate_docs(self, project_root: Path):
        """Generate complete API documentation."""
        logger.info("Scanning project for modules...")
        project_info = self.scan_project(project_root)

        logger.info(
            f"Generating documentation for {len(project_info['modules'])} modules..."
        )

        # Generate index
        index_content = self.generate_index(project_info)
        with open(self.output_dir / "index.md", "w", encoding="utf-8") as f:
            f.write(index_content)

        # Generate individual module docs
        for module_name, module_info in project_info["modules"].items():
            doc_content = self.generate_module_doc(module_name, module_info)
            doc_filename = module_name.replace(".", "_") + ".md"

            with open(self.output_dir / doc_filename, "w", encoding="utf-8") as f:
                f.write(doc_content)

        logger.info(f"API documentation generated in {self.output_dir}")


def main():
    """Generate API documentation."""
    print("📚 API Documentation Generator")
    print("=" * 50)

    # Setup output directory
    output_dir = Path("docs/api")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate documentation
    generator = APIDocGenerator(output_dir)
    generator.generate_docs(project_root)

    print(f"✅ API documentation generated in {output_dir}")


if __name__ == "__main__":
    main()

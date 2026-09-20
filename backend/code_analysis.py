"""Python source metrics and local import dependency analysis."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import tokenize
from typing import Any, Iterable

from .scanner import ScanResult, ScannedFile


@dataclass(slots=True)
class _PythonModule:
    file: ScannedFile
    module_name: str
    is_package: bool
    tree: ast.Module | None = None
    parse_error: str | None = None


class _ComplexityVisitor(ast.NodeVisitor):
    """Calculate a compact McCabe-style cyclomatic complexity score."""

    def __init__(self) -> None:
        self.value = 1

    def visit_If(self, node: ast.If) -> None:
        self.value += 1
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self.value += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.value += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.value += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.value += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self.value += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self.value += max(0, len(node.values) - 1)
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        self.value += 1 + len(node.ifs)
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> None:  # Python 3.10+
        self.value += max(0, len(node.cases) - 1)
        self.generic_visit(node)

    def visit_match_case(self, node: ast.match_case) -> None:
        if node.guard is not None:
            self.value += 1
        self.generic_visit(node)

    # A nested callable has its own score and must not inflate its parent.
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        return

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        return


def _function_complexity(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    visitor = _ComplexityVisitor()
    for statement in node.body:
        visitor.visit(statement)
    return visitor.value


class _DefinitionCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.scope: list[str] = []
        self.functions: list[dict[str, Any]] = []
        self.classes: list[dict[str, Any]] = []

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qualified_name = ".".join((*self.scope, node.name))
        self.functions.append(
            {
                "name": node.name,
                "qualified_name": qualified_name,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "complexity": _function_complexity(node),
                "async": isinstance(node, ast.AsyncFunctionDef),
            }
        )
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qualified_name = ".".join((*self.scope, node.name))
        self.classes.append(
            {
                "name": node.name,
                "qualified_name": qualified_name,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
            }
        )
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()


def _module_identity(relative_path: Path) -> tuple[str, bool]:
    without_suffix = relative_path.with_suffix("")
    parts = list(without_suffix.parts)
    is_package = bool(parts and parts[-1] == "__init__")
    if is_package:
        parts.pop()
    return ".".join(parts), is_package


def _read_python_ast(path: Path) -> ast.Module:
    # tokenize.open honors Python encoding cookies as well as UTF-8 source.
    with tokenize.open(path) as handle:
        return ast.parse(handle.read(), filename=str(path))


def _import_names(tree: ast.Module, module: _PythonModule) -> set[str]:
    names: set[str] = set()
    package_parts = module.module_name.split(".") if module.module_name else []
    if not module.is_package and package_parts:
        package_parts.pop()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
            continue
        if not isinstance(node, ast.ImportFrom):
            continue

        if node.level:
            keep = max(0, len(package_parts) - node.level + 1)
            base_parts = package_parts[:keep]
        else:
            base_parts = []
        if node.module:
            base_parts.extend(node.module.split("."))
        base = ".".join(base_parts)
        for alias in node.names:
            if alias.name == "*":
                if base:
                    names.add(base)
                continue
            candidate = ".".join((*base_parts, alias.name))
            if candidate:
                names.add(candidate)
    return names


def _resolve_local_imports(imports: Iterable[str], modules: dict[str, _PythonModule]) -> set[str]:
    resolved: set[str] = set()
    for imported in imports:
        candidate = imported
        while candidate:
            if candidate in modules:
                resolved.add(modules[candidate].module_name)
                break
            candidate = candidate.rpartition(".")[0]
    return resolved


def _strongly_connected_components(graph: dict[str, set[str]]) -> list[list[str]]:
    index = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[list[str]] = []

    def connect(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for neighbor in sorted(graph[node]):
            if neighbor not in indices:
                connect(neighbor)
                lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
            elif neighbor in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[neighbor])

        if lowlinks[node] != indices[node]:
            return
        component: list[str] = []
        while stack:
            member = stack.pop()
            on_stack.remove(member)
            component.append(member)
            if member == node:
                break
        components.append(sorted(component))

    for node in sorted(graph):
        if node not in indices:
            connect(node)
    return components


def _representative_cycle(component: list[str], graph: dict[str, set[str]]) -> list[str]:
    allowed = set(component)
    if len(component) == 1:
        return [component[0], component[0]]

    def search(start: str, node: str, path: list[str], visiting: set[str]) -> list[str] | None:
        for neighbor in sorted(graph[node] & allowed):
            if neighbor == start:
                return [*path, start]
            if neighbor in visiting:
                continue
            result = search(start, neighbor, [*path, neighbor], {*visiting, neighbor})
            if result:
                return result
        return None

    for start in component:
        result = search(start, start, [start], {start})
        if result:
            return result
    return [*component, component[0]]


def analyze_python_code(scan: ScanResult) -> dict[str, Any]:
    """Return JSON-serializable code metrics and local dependencies for Python."""
    python_modules: list[_PythonModule] = []
    for file in scan.files:
        if file.language != "Python":
            continue
        module_name, is_package = _module_identity(file.relative_path)
        python_modules.append(_PythonModule(file, module_name, is_package))

    # Empty root __init__.py has no importable dotted name, but still gets metrics.
    modules_by_name = {module.module_name: module for module in python_modules if module.module_name}
    # Projects using a conventional ``src/`` or ``lib/`` layout import packages
    # without that source-root prefix (``package.mod``, not ``src.package.mod``).
    for module in python_modules:
        parts = module.module_name.split(".")
        if len(parts) > 1 and parts[0] in {"src", "lib"}:
            modules_by_name.setdefault(".".join(parts[1:]), module)
    path_by_module = {
        module.module_name: module.file.relative_path.as_posix()
        for module in python_modules
        if module.module_name
    }
    graph: dict[str, set[str]] = {name: set() for name in modules_by_name}
    file_results: list[dict[str, Any]] = []
    all_functions: list[dict[str, Any]] = []
    total_classes = 0
    parse_errors: list[dict[str, str]] = []

    for module in python_modules:
        path = module.file.relative_path.as_posix()
        try:
            module.tree = _read_python_ast(module.file.absolute_path)
        except (OSError, SyntaxError, UnicodeError) as exc:
            if isinstance(exc, SyntaxError):
                location = f"line {exc.lineno}" if exc.lineno else "unknown line"
                module.parse_error = f"{exc.msg} ({location})"
            else:
                module.parse_error = str(exc)
            parse_errors.append({"path": path, "error": module.parse_error})
            file_results.append(
                {
                    "path": path,
                    "module": module.module_name,
                    "functions": 0,
                    "classes": 0,
                    "average_complexity": 0.0,
                    "most_complex_function": None,
                    "dependencies": [],
                    "parse_error": module.parse_error,
                }
            )
            continue

        collector = _DefinitionCollector()
        collector.visit(module.tree)
        total_classes += len(collector.classes)
        complexities = [item["complexity"] for item in collector.functions]
        most_complex = max(collector.functions, key=lambda item: item["complexity"], default=None)
        for function in collector.functions:
            all_functions.append({"path": path, **function})

        dependencies = _resolve_local_imports(_import_names(module.tree, module), modules_by_name)
        dependencies.discard(module.module_name)
        if module.module_name:
            graph[module.module_name] = dependencies
        file_results.append(
            {
                "path": path,
                "module": module.module_name,
                "functions": len(collector.functions),
                "classes": len(collector.classes),
                "average_complexity": round(sum(complexities) / len(complexities), 2) if complexities else 0.0,
                "most_complex_function": most_complex,
                "dependencies": sorted(path_by_module[name] for name in dependencies),
                "parse_error": None,
            }
        )

    cyclic_components = [
        component
        for component in _strongly_connected_components(graph)
        if len(component) > 1 or (component and component[0] in graph[component[0]])
    ]
    cycles = []
    for component in cyclic_components:
        cycle_modules = _representative_cycle(component, graph)
        cycles.append(
            {
                "files": [path_by_module[name] for name in component],
                "cycle": [path_by_module[name] for name in cycle_modules],
            }
        )

    edges = [
        {"source": path_by_module[source], "target": path_by_module[target]}
        for source in sorted(graph)
        for target in sorted(graph[source])
    ]
    all_complexities = [function["complexity"] for function in all_functions]
    most_complex_function = max(all_functions, key=lambda item: item["complexity"], default=None)
    file_results.sort(key=lambda item: item["path"].lower())

    return {
        "language": "Python",
        "summary": {
            "files": len(python_modules),
            "parsed_files": len(python_modules) - len(parse_errors),
            "files_with_errors": len(parse_errors),
            "functions": len(all_functions),
            "classes": total_classes,
            "average_complexity": round(sum(all_complexities) / len(all_complexities), 2) if all_complexities else 0.0,
            "most_complex_function": most_complex_function,
        },
        "files": file_results,
        "dependencies": {
            "edges": edges,
            "cycles": cycles,
            "circular_dependencies": len(cycles),
        },
        "parse_errors": parse_errors,
    }

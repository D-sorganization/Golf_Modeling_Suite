"""Fix _build_qt_window - move _Window class into _create_dashboard_window_class factory."""
import ast
from pathlib import Path

path = Path('src/launchers/cross_engine_dashboard.py')
content = path.read_text(encoding='utf-8')

# Find _build_qt_window in the AST
tree = ast.parse(content)
func_node = None
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == '_build_qt_window':
        func_node = node
        break
assert func_node is not None, "_build_qt_window not found"

lines = content.splitlines(keepends=True)
func_text = ''.join(lines[func_node.lineno - 1:func_node.end_lineno])

# The new structure:
# - _create_dashboard_window_class(): contains class def + deferred imports + split _update_charts
# - _build_qt_window(): thin 3-line factory

# Find _update_charts in the class and split it
# We'll do string replacement to split _update_charts into two helpers

# First, check if _update_charts exists in the function
assert '_update_charts' in func_text, "_update_charts not found"

# Split _update_charts into _draw_robustness_chart_bars and _draw_cv_chart_bars
OLD_UPDATE = '''        def _update_charts(
            self,
            engine_names: list[str],
            cv_summary: dict[str, float],
        ) -> None:
            """Refresh Robustness Score and CV charts from the latest results.

            Parameters
            ----------
            engine_names : list of str
                Names of engines that were run.
            cv_summary : dict
                Output of CrossEnginePerturbationRunner.compute_cv_summary().

            Design by Contract
            ------------------
            Pre:  engine_names is non-empty
            Pre:  cv_summary has the three standard CV keys
            Post: both canvases are redrawn
            """
            if not _has_mpl:
                return
            if not engine_names:
                return

            metric_keys = [
                "cv_total_energy_final",
                "cv_end_effector_speed_final",
                "cv_peak_end_effector_speed",
            ]
            metric_labels = ["Energy", "Speed", "Peak Speed"]

            # Robustness Score: use mean CV across metrics per engine.
            # Since compute_cv_summary returns aggregate CVs (not per-engine),
            # we compute a single robustness score for the ensemble.
            cv_values = [cv_summary.get(k, 0.0) for k in metric_keys]
            mean_cv = float(np.mean(cv_values)) if cv_values else 0.0
            robustness = max(0.0, min(1.0, 1.0 - mean_cv))
            robustness_per_engine = [robustness] * len(engine_names)

            ax = self._ax_rs
            ax.clear()
            ax.set_facecolor("#1a1a2e")
            x = np.arange(len(engine_names))
            bars = ax.bar(
                x,
                robustness_per_engine,
                color="#5555b0",
                edgecolor="#303070",
                width=0.5,
            )
            ax.set_xticks(x)
            ax.set_xticklabels(engine_names, fontsize=9)
            ax.set_ylim(0.0, 1.0)
            ax.set_ylabel("Robustness Score", fontsize=9)
            ax.axhline(0.5, color="#ff6060", linewidth=0.8, linestyle="--")
            self._style_ax(ax)

            # Annotate bar values
            for bar, val in zip(bars, robustness_per_engine, strict=True):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.02,
                    f"{val:.2f}",
                    ha="center",
                    va="bottom",
                    color="#d0d0f0",
                    fontsize=8,
                )

            self._canvas_rs.draw()

            # CV chart — one bar per metric
            ax2 = self._ax_cv
            ax2.clear()
            ax2.set_facecolor("#1a1a2e")
            x2 = np.arange(len(metric_labels))
            bars2 = ax2.bar(
                x2,
                cv_values,
                color="#8040c0",
                edgecolor="#502080",
                width=0.5,
            )
            ax2.set_xticks(x2)
            ax2.set_xticklabels(metric_labels, fontsize=9)
            ax2.set_ylabel("CV", fontsize=9)
            ax2.axhline(1.0, color="#ff6060", linewidth=0.8, linestyle="--")
            self._style_ax(ax2)

            for bar, val in zip(bars2, cv_values, strict=True):
                ax2.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.01,
                    f"{val:.3f}",
                    ha="center",
                    va="bottom",
                    color="#d0d0f0",
                    fontsize=8,
                )

            self._canvas_cv.draw()'''

NEW_UPDATE = '''        def _draw_robustness_chart_bars(
            self,
            engine_names: list[str],
            robustness_per_engine: list[float],
        ) -> None:
            """Draw robustness score bar chart."""
            ax = self._ax_rs
            ax.clear()
            ax.set_facecolor("#1a1a2e")
            x = np.arange(len(engine_names))
            bars = ax.bar(x, robustness_per_engine, color="#5555b0", edgecolor="#303070", width=0.5)
            ax.set_xticks(x)
            ax.set_xticklabels(engine_names, fontsize=9)
            ax.set_ylim(0.0, 1.0)
            ax.set_ylabel("Robustness Score", fontsize=9)
            ax.axhline(0.5, color="#ff6060", linewidth=0.8, linestyle="--")
            self._style_ax(ax)
            for bar, val in zip(bars, robustness_per_engine, strict=True):
                ax.text(
                    bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                    f"{val:.2f}", ha="center", va="bottom", color="#d0d0f0", fontsize=8,
                )
            self._canvas_rs.draw()

        def _draw_cv_chart_bars(
            self,
            cv_values: list[float],
            metric_labels: list[str],
        ) -> None:
            """Draw coefficient-of-variation bar chart."""
            ax2 = self._ax_cv
            ax2.clear()
            ax2.set_facecolor("#1a1a2e")
            x2 = np.arange(len(metric_labels))
            bars2 = ax2.bar(x2, cv_values, color="#8040c0", edgecolor="#502080", width=0.5)
            ax2.set_xticks(x2)
            ax2.set_xticklabels(metric_labels, fontsize=9)
            ax2.set_ylabel("CV", fontsize=9)
            ax2.axhline(1.0, color="#ff6060", linewidth=0.8, linestyle="--")
            self._style_ax(ax2)
            for bar, val in zip(bars2, cv_values, strict=True):
                ax2.text(
                    bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                    f"{val:.3f}", ha="center", va="bottom", color="#d0d0f0", fontsize=8,
                )
            self._canvas_cv.draw()

        def _update_charts(
            self,
            engine_names: list[str],
            cv_summary: dict[str, float],
        ) -> None:
            """Refresh Robustness Score and CV charts from the latest results."""
            if not _has_mpl or not engine_names:
                return
            metric_keys = [
                "cv_total_energy_final",
                "cv_end_effector_speed_final",
                "cv_peak_end_effector_speed",
            ]
            metric_labels = ["Energy", "Speed", "Peak Speed"]
            cv_values = [cv_summary.get(k, 0.0) for k in metric_keys]
            mean_cv = float(np.mean(cv_values)) if cv_values else 0.0
            robustness = max(0.0, min(1.0, 1.0 - mean_cv))
            self._draw_robustness_chart_bars(engine_names, [robustness] * len(engine_names))
            self._draw_cv_chart_bars(cv_values, metric_labels)'''

assert OLD_UPDATE in func_text, "Could not find _update_charts text to replace"
func_text_new = func_text.replace(OLD_UPDATE, NEW_UPDATE)

# Now wrap the modified class definition in a factory function
# and replace _build_qt_window with a thin factory

# The new structure: rename _build_qt_window -> _create_dashboard_window_class
# and add a new thin _build_qt_window

NEW_FACTORY = func_text_new.replace(
    'def _build_qt_window() -> object:',
    'def _create_dashboard_window_class() -> type:'
).replace(
    '    return _Window()',
    '    return _Window'
)

NEW_THIN = '''def _build_qt_window() -> object:
    """Build and return the QMainWindow instance (deferred Qt import).

    Returns
    -------
    QMainWindow subclass instance.

    Raises
    ------
    ImportError if PyQt6 or Matplotlib is not available.
    """
    return _create_dashboard_window_class()()

'''

content = content.replace(func_text, NEW_FACTORY + '\n\n' + NEW_THIN)
path.write_text(content, encoding='utf-8')
print(f"Fixed {path}")

# Verify
tree2 = ast.parse(path.read_text(encoding='utf-8'))
for node in ast.walk(tree2):
    if isinstance(node, ast.FunctionDef) and node.name in ('_build_qt_window', '_create_dashboard_window_class'):
        print(f"  {node.name}: {node.end_lineno - node.lineno} LOC")

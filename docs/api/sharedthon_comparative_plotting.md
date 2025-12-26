# sharedthon.comparative_plotting

Plotting module for comparative swing analysis.

Visualizes the differences between two swings using overlays and difference plots.

## Classes

### ComparativePlotter

Generates comparison plots for two swings.

#### Methods

##### plot_comparison
```python
def plot_comparison(self: Any, fig: Any, field_name: str, joint_idx: Any, title: Any, ylabel: str) -> None
```

Plot overlay of two signals and their difference.

Args:
    fig: Matplotlib figure
    field_name: Data field to compare
    joint_idx: Joint index (optional)
    title: Plot title
    ylabel: Y-axis label

##### plot_phase_comparison
```python
def plot_phase_comparison(self: Any, fig: Any, joint_idx: int, joint_name: str, ax: Any) -> None
```

Overlay phase diagrams (Angle vs Velocity).

Args:
    fig: Matplotlib figure (optional if ax provided)
    joint_idx: Joint index
    joint_name: Name of joint for labels
    ax: Matplotlib Axes to plot on (optional)

##### plot_dashboard
```python
def plot_dashboard(self: Any, fig: Figure) -> None
```

Create a summary dashboard for the comparison.

Args:
    fig: Matplotlib figure

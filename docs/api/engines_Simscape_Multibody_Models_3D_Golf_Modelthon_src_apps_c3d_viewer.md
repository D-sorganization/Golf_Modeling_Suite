# engines.Simscape_Multibody_Models.3D_Golf_Modelthon.src.apps.c3d_viewer

C3D Motion Analysis GUI

Features:
- Load C3D files (via ezc3d)
- Inspect metadata, markers, analog channels
- 2D plots of marker/analog time-series
- 3D marker trajectory viewer
- Basic kinematic analysis: speed, path length, extrema

Dependencies:
    See python/requirements.txt for required packages.

## Classes

### MarkerData

### AnalogData

### C3DDataModel

#### Methods

##### marker_names
```python
def marker_names(self: Any) -> list[str]
```

Return list of marker names.

##### analog_names
```python
def analog_names(self: Any) -> list[str]
```

Return list of analog channel names.

### MplCanvas

Matplotlib canvas widget for embedding plots in Qt.

**Inherits from:** FigureCanvas

#### Methods

##### clear_axes
```python
def clear_axes(self: Any) -> None
```

Clear all axes from the figure.

##### add_subplot
```python
def add_subplot(self: Any) -> Axes
```

Add a subplot to the figure and return the axes.

### C3DViewerMainWindow

Main window for the C3D motion analysis viewer application.

**Inherits from:** QtWidgets.QMainWindow

#### Methods

##### open_c3d_file
```python
def open_c3d_file(self: Any) -> None
```

Open a file dialog to load a C3D file.

##### update_marker_plot
```python
def update_marker_plot(self: Any) -> None
```

Update the marker plot based on selected marker and component.

##### update_analog_plot
```python
def update_analog_plot(self: Any) -> None
```

Update the analog plot based on selected channel.

##### update_3d_view
```python
def update_3d_view(self: Any) -> None
```

Update the 3D view based on selected markers and frame.

##### update_analysis_panel
```python
def update_analysis_panel(self: Any) -> None
```

Update the analysis panel with statistics for the selected marker.

##### show_about_dialog
```python
def show_about_dialog(self: Any) -> None
```

Display the about dialog with application information.

# engines.physics_engines.mujocothon.mujoco_humanoid_golf.advanced_gui

Advanced professional GUI for golf swing analysis.

This module provides a comprehensive interface with:
- Simulation controls and visualization
- Real-time biomechanical analysis
- Advanced plotting and data export
- Force/torque vector visualization
- Camera controls

## Classes

### AdvancedGolfAnalysisWindow

Professional golf swing analysis application with comprehensive features.

**Inherits from:** QtWidgets.QMainWindow, AdvancedGuiMethodsMixin

#### Methods

##### keyPressEvent
```python
def keyPressEvent(self: Any, event: Any) -> None
```

Handle keyboard shortcuts.

##### load_current_model
```python
def load_current_model(self: Any) -> None
```

Load selected model and recreate actuator controls.

##### open_actuator_detail_dialog
```python
def open_actuator_detail_dialog(self: Any, actuator_index: int, actuator_name: str, slider: Any) -> None
```

Open a dialog with comprehensive controls for an actuator.

##### on_open_poly_generator
```python
def on_open_poly_generator(self: Any, actuator_index: int, actuator_name: str) -> None
```

Open the visual polynomial generator for the specified actuator.

##### on_actuator_filter_changed
```python
def on_actuator_filter_changed(self: Any, text: str) -> None
```

Filter actuator groups by substring match.

##### on_model_changed
```python
def on_model_changed(self: Any, index: int) -> None
```

Handle model selection change.

##### on_play_pause_toggled
```python
def on_play_pause_toggled(self: Any, checked: bool) -> None
```

Handle play/pause button toggle.

##### on_reset_clicked
```python
def on_reset_clicked(self: Any) -> None
```

Reset simulation to initial state.

##### on_record_toggled
```python
def on_record_toggled(self: Any, checked: bool) -> None
```

Handle recording toggle.

##### on_take_screenshot
```python
def on_take_screenshot(self: Any) -> None
```

Capture and save the current simulation view.

##### on_actuator_changed
```python
def on_actuator_changed(self: Any) -> None
```

Update actuator torques when any slider changes.

##### on_actuator_slider_changed
```python
def on_actuator_slider_changed(self: Any, actuator_index: int, value: int) -> None
```

Handle slider change - update constant value and label.

##### on_constant_value_changed
```python
def on_constant_value_changed(self: Any, actuator_index: int, value: float) -> None
```

Handle constant value input change.

##### on_control_type_changed
```python
def on_control_type_changed(self: Any, actuator_index: int, type_index: int) -> None
```

Handle control type selection change.

##### on_polynomial_coeff_changed
```python
def on_polynomial_coeff_changed(self: Any, actuator_index: int, coeff_index: int, value: float) -> None
```

Handle polynomial coefficient change.

##### on_damping_changed
```python
def on_damping_changed(self: Any, actuator_index: int, damping: float) -> None
```

Handle damping value change.

##### on_camera_changed
```python
def on_camera_changed(self: Any, camera_name: str) -> None
```

Handle camera view change.

##### on_azimuth_changed
```python
def on_azimuth_changed(self: Any, value: int) -> None
```

Handle azimuth slider change.

##### on_elevation_changed
```python
def on_elevation_changed(self: Any, value: int) -> None
```

Handle elevation slider change.

##### on_distance_changed
```python
def on_distance_changed(self: Any, value: int) -> None
```

Handle distance slider change.

##### on_lookat_changed
```python
def on_lookat_changed(self: Any) -> None
```

Handle lookat position change.

##### on_reset_camera
```python
def on_reset_camera(self: Any) -> None
```

Reset camera to default position.

##### on_sky_color_clicked
```python
def on_sky_color_clicked(self: Any) -> None
```

Handle sky color button click - open color picker.

##### on_ground_color_clicked
```python
def on_ground_color_clicked(self: Any) -> None
```

Handle ground color button click - open color picker.

##### on_reset_background
```python
def on_reset_background(self: Any) -> None
```

Reset background colors to defaults.

##### on_show_torques_changed
```python
def on_show_torques_changed(self: Any, state: int) -> None
```

Handle torque visualization toggle.

##### on_torque_scale_changed
```python
def on_torque_scale_changed(self: Any, value: int) -> None
```

Handle torque scale slider change.

##### on_show_forces_changed
```python
def on_show_forces_changed(self: Any, state: int) -> None
```

Handle force visualization toggle.

##### on_force_scale_changed
```python
def on_force_scale_changed(self: Any, value: int) -> None
```

Handle force scale slider change.

##### on_show_contacts_changed
```python
def on_show_contacts_changed(self: Any, state: int) -> None
```

Handle contact force visualization toggle.

##### on_plot_type_changed
```python
def on_plot_type_changed(self: Any, plot_type: str) -> None
```

Handle plot type selection change.

##### on_generate_plot
```python
def on_generate_plot(self: Any) -> None
```

Generate the selected plot.

##### update_metrics
```python
def update_metrics(self: Any) -> None
```

Update real-time metrics display.

##### on_export_csv
```python
def on_export_csv(self: Any) -> None
```

Export recorded data to CSV.

##### on_export_data
```python
def on_export_data(self: Any) -> None
```

Export simulation data to CSV and JSON.

##### on_export_json
```python
def on_export_json(self: Any) -> None
```

Export recorded data to JSON.

##### update_body_lists
```python
def update_body_lists(self: Any) -> None
```

Update body selection combo boxes.

##### on_manip_body_selected
```python
def on_manip_body_selected(self: Any, index: int) -> None
```

Handle body selection from combo box.

##### on_change_body_color
```python
def on_change_body_color(self: Any) -> None
```

Open color picker for selected body.

##### on_reset_body_color
```python
def on_reset_body_color(self: Any) -> None
```

Reset selected body color to default.

##### on_manual_transform
```python
def on_manual_transform(self: Any, type_: str, axis: int, value: float) -> None
```

Handle manual transform changes.

##### update_manual_transform_values
```python
def update_manual_transform_values(self: Any) -> None
```

Update sliders from current selection.

##### on_drag_enabled_changed
```python
def on_drag_enabled_changed(self: Any, state: int) -> None
```

Handle drag mode enable/disable.

##### on_maintain_orientation_changed
```python
def on_maintain_orientation_changed(self: Any, state: int) -> None
```

Handle maintain orientation setting.

##### on_nullspace_posture_changed
```python
def on_nullspace_posture_changed(self: Any, state: int) -> None
```

Handle nullspace posture optimization setting.

##### on_add_constraint
```python
def on_add_constraint(self: Any) -> None
```

Add a constraint to the selected body.

##### on_remove_constraint
```python
def on_remove_constraint(self: Any) -> None
```

Remove constraint from selected body.

##### on_clear_constraints
```python
def on_clear_constraints(self: Any) -> None
```

Clear all constraints.

##### update_constraints_list
```python
def update_constraints_list(self: Any) -> None
```

Update the list of active constraints.

##### on_save_pose
```python
def on_save_pose(self: Any) -> None
```

Save current pose to library.

##### on_load_pose
```python
def on_load_pose(self: Any) -> None
```

Load selected pose from library.

##### on_delete_pose
```python
def on_delete_pose(self: Any) -> None
```

Delete selected pose from library.

##### on_export_poses
```python
def on_export_poses(self: Any) -> None
```

Export pose library to file.

##### on_import_poses
```python
def on_import_poses(self: Any) -> None
```

Import pose library from file.

##### update_pose_list
```python
def update_pose_list(self: Any) -> None
```

Update the pose library list.

##### on_interpolate_poses
```python
def on_interpolate_poses(self: Any, value: int) -> None
```

Interpolate between two selected poses.

##### on_ik_damping_changed
```python
def on_ik_damping_changed(self: Any, value: int) -> None
```

Handle IK damping slider change.

##### on_ik_step_changed
```python
def on_ik_step_changed(self: Any, value: int) -> None
```

Handle IK step size slider change.

##### on_open_meshcat
```python
def on_open_meshcat(self: Any) -> None
```

Open the Meshcat visualizer in the default browser.

### ActuatorDetailDialog

On-demand editor for actuator control parameters.

**Inherits from:** QtWidgets.QDialog

#### Methods

## Constants

- `CONTROL_TYPE_LABELS`

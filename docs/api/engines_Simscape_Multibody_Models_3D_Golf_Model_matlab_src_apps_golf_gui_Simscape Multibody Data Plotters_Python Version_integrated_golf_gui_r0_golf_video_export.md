# engines.Simscape_Multibody_Models.3D_Golf_Model.matlab.src.apps.golf_gui.Simscape Multibody Data Plotters.Python Version.integrated_golf_gui_r0.golf_video_export

Video Export Module for Golf Visualizer
Export 3D golf swing animations to high-quality video

Features:
- 60/120 FPS high-quality MP4 export
- Multiple resolution options (720p, 1080p, 4K)
- Progress tracking
- Background rendering (non-blocking UI)

## Classes

### VideoExportConfig

Configuration for video export

### VideoExporter

Export 3D golf swing animations to video

Usage:
    exporter = VideoExporter(renderer, frame_processor)
    exporter.export_video(config)

**Inherits from:** QObject

#### Methods

##### export_video
```python
def export_video(self: Any, config: VideoExportConfig)
```

Export animation to video file

Args:
    config: Video export configuration

### VideoExportThread

Video export in background thread (doesn't freeze UI)

Usage:
    thread = VideoExportThread(renderer, frame_processor, config)
    thread.progress.connect(lambda c, t: print(f"{c}/{t}"))
    thread.finished.connect(lambda p: print(f"Done: {p}"))
    thread.start()

**Inherits from:** QThread

#### Methods

##### run
```python
def run(self: Any)
```

Run export in background thread

### VideoExportDialog

User-friendly video export dialog

Integration into golf_gui_application.py:
Simply create and show this dialog when user wants to export

**Inherits from:** QDialog

#### Methods

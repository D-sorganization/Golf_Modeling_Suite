# sharedthon.pose_estimation.interface

Interface for pose estimation modules.

## Classes

### PoseEstimationResult

Standardized result from a pose estimator.

### PoseEstimator

Abstract base class for pose estimators.

**Inherits from:** ABC

#### Methods

##### load_model
```python
def load_model(self: Any, model_path: Any) -> None
```

Load the estimation model/weights.

Args:
    model_path: Path to model weights, or None for default.

##### estimate_from_image
```python
def estimate_from_image(self: Any, image: np.ndarray) -> PoseEstimationResult
```

Estimate pose from a single image frame.

Args:
    image: Input image (H, W, C) usually BGR or RGB.

Returns:
    PoseEstimationResult containing joint angles.

##### estimate_from_video
```python
def estimate_from_video(self: Any, video_path: Path) -> list[PoseEstimationResult]
```

Process an entire video file.

Args:
    video_path: Path to video file.

Returns:
    List of results for each frame.

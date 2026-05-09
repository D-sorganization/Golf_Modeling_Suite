"""Body-part shape fitters.

Public fitters added in #4756:

- :class:`BetweenTwoMarkersFitter` — for BETWEEN_TWO bindings.
- :class:`ClusterKabschFitter` — rigid Kabsch over a marker cluster.
- :class:`ProcrustesAnisotropicFitter` — Kabsch + anisotropic scale.
"""

from __future__ import annotations

from src.shared.python.body_part_viz.fitters.between_two import (
    BetweenTwoMarkersFitter,
)
from src.shared.python.body_part_viz.fitters.cluster_kabsch import (
    ClusterKabschFitter,
)
from src.shared.python.body_part_viz.fitters.procrustes_anisotropic import (
    ProcrustesAnisotropicFitter,
)

__all__ = [
    "BetweenTwoMarkersFitter",
    "ClusterKabschFitter",
    "ProcrustesAnisotropicFitter",
]

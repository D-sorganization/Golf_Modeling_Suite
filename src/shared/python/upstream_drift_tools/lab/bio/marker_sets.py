"""Deterministic marker-set detection for C3D files.

This module replaces the historical 6-name substring match for clubhead /
grip markers used by ``motion_matching.loaders.c3d``. CGM2.4, 41-marker
Plug-in-Gait, IOR, and other conventions silently produced NaN-filled club
poses because the 6-name match did not consider the wider marker context.

The :func:`detect_marker_set` function inspects a list of marker labels and
returns the first :class:`MarkerSet` whose **minimum required subset** is
present in the file. Detection is deterministic via a fixed priority order;
the chosen set and its match score are logged at INFO level so that pipeline
operators can reproduce decisions from logs alone.

The detector is intentionally pure: no I/O, no global state, no external
dependencies. C3D loaders pass ``metadata.marker_labels`` directly.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from enum import Enum

logger = logging.getLogger(__name__)


class MarkerSet(Enum):
    """Enumeration of recognised mocap marker conventions.

    Members:
        CGM2_4:           Conventional Gait Model v2.4 (Leardini variant).
        PLUG_IN_GAIT_41:  Vicon full-body Plug-in-Gait, 41-marker variant.
        PLUG_IN_GAIT_28:  Vicon Plug-in-Gait reduced 28-marker subset
                          (the canonical default in this repository).
        IOR:              Istituto Ortopedico Rizzoli lower-limb protocol.
        GOLF_CLUSTER:     Custom golf-cluster set with rigid 3-marker
                          clubhead and grip clusters (``Marker_2:2:*`` and
                          ``Marker_3:3:*``).
        UNKNOWN:          No known set matched the input labels.
    """

    CGM2_4 = "cgm2_4"
    PLUG_IN_GAIT_41 = "plug_in_gait_41"
    PLUG_IN_GAIT_28 = "plug_in_gait_28"
    IOR = "ior"
    GOLF_CLUSTER = "golf_cluster"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Canonical label registries
# ---------------------------------------------------------------------------

# Plug-in-Gait full 41-marker set (Vicon canonical labels).
_PIG_41_LABELS: frozenset[str] = frozenset(
    {
        "LFHD",
        "RFHD",
        "LBHD",
        "RBHD",
        "C7",
        "T10",
        "CLAV",
        "STRN",
        "RBAK",
        "LSHO",
        "LUPA",
        "LELB",
        "LFRM",
        "LWRA",
        "LWRB",
        "LFIN",
        "RSHO",
        "RUPA",
        "RELB",
        "RFRM",
        "RWRA",
        "RWRB",
        "RFIN",
        "LASI",
        "RASI",
        "LPSI",
        "RPSI",
        "LTHI",
        "LKNE",
        "LTIB",
        "LANK",
        "LHEE",
        "LTOE",
        "RTHI",
        "RKNE",
        "RTIB",
        "RANK",
        "RHEE",
        "RTOE",
        "LFEM",
        "RFEM",
    }
)
# Required core: must be present for a confident PiG-41 detection.
_PIG_41_REQUIRED: frozenset[str] = frozenset(
    {
        "LFHD",
        "RFHD",
        "LBHD",
        "RBHD",
        "C7",
        "T10",
        "CLAV",
        "STRN",
        "LSHO",
        "LELB",
        "LWRA",
        "LWRB",
        "RSHO",
        "RELB",
        "RWRA",
        "RWRB",
        "LASI",
        "RASI",
        "LPSI",
        "RPSI",
        "LKNE",
        "LANK",
        "LHEE",
        "LTOE",
        "RKNE",
        "RANK",
        "RHEE",
        "RTOE",
    }
)

# CGM 2.4 adds skin-mounted thigh / shank cluster markers (THI1..THI4 etc).
_CGM2_4_LABELS: frozenset[str] = frozenset(
    {
        "LFHD",
        "RFHD",
        "LBHD",
        "RBHD",
        "C7",
        "T10",
        "CLAV",
        "STRN",
        "RBAK",
        "LSHO",
        "LELB",
        "LWRA",
        "LWRB",
        "LFIN",
        "RSHO",
        "RELB",
        "RWRA",
        "RWRB",
        "RFIN",
        "LASI",
        "RASI",
        "LPSI",
        "RPSI",
        "LTHI1",
        "LTHI2",
        "LTHI3",
        "LTHI4",
        "LTIB1",
        "LTIB2",
        "LTIB3",
        "LTIB4",
        "RTHI1",
        "RTHI2",
        "RTHI3",
        "RTHI4",
        "RTIB1",
        "RTIB2",
        "RTIB3",
        "RTIB4",
        "LKNE",
        "LANK",
        "LHEE",
        "LTOE",
        "RKNE",
        "RANK",
        "RHEE",
        "RTOE",
        "LMED",
        "RMED",
        "LMMA",
        "RMMA",
    }
)
# CGM2.4 fingerprint: presence of the 4-marker thigh / shank clusters.
_CGM2_4_REQUIRED: frozenset[str] = frozenset(
    {
        "LTHI1",
        "LTHI2",
        "LTHI3",
        "LTHI4",
        "RTHI1",
        "RTHI2",
        "RTHI3",
        "RTHI4",
        "LTIB1",
        "LTIB2",
        "LTIB3",
        "LTIB4",
        "RTIB1",
        "RTIB2",
        "RTIB3",
        "RTIB4",
    }
)

# IOR (Rizzoli) lower-limb protocol distinguishing labels.
_IOR_LABELS: frozenset[str] = frozenset(
    {
        "RIAS",
        "LIAS",
        "RIPS",
        "LIPS",
        "RGT",
        "LGT",
        "RLE",
        "RME",
        "LLE",
        "LME",
        "RHF",
        "LHF",
        "RTT",
        "LTT",
        "RLM",
        "RMM",
        "LLM",
        "LMM",
        "RCA",
        "LCA",
        "RFM",
        "LFM",
        "RVM",
        "LVM",
        "RSM",
        "LSM",
    }
)
_IOR_REQUIRED: frozenset[str] = frozenset(
    {
        "RIAS",
        "LIAS",
        "RIPS",
        "LIPS",
        "RLE",
        "LLE",
        "RLM",
        "LLM",
    }
)

# Plug-in-Gait reduced 28-marker subset used as the default anatomical set
# in this repository (matches ``c3d_body._DEFAULT_ANATOMICAL_MARKERS``).
_PIG_28_LABELS: frozenset[str] = frozenset(
    {
        "WaistLeft",
        "WaistRight",
        "WaistLBack",
        "WaistRBack",
        "BackTop",
        "BackLeft",
        "BackRight",
        "HeadTop",
        "HeadFront",
        "HeadSide",
        "LShoulderTop",
        "LShoulderBack",
        "LElbowOut",
        "LUArmHigh",
        "LWristTop",
        "RShoulderBack",
        "RShoulderTop",
        "RElbowOut",
        "RUArmHigh",
        "RWristTop",
        "LKneeOut",
        "LToeIn",
        "LToeOut",
        "LAnkleOut",
        "RKneeOut",
        "RToeIn",
        "RToeOut",
        "RAnkleOut",
    }
)
_PIG_28_REQUIRED: frozenset[str] = frozenset(
    {
        "WaistLeft",
        "WaistRight",
        "BackTop",
        "HeadTop",
        "LShoulderTop",
        "LElbowOut",
        "LWristTop",
        "RShoulderBack",
        "RElbowOut",
        "RWristTop",
        "LKneeOut",
        "LAnkleOut",
        "RKneeOut",
        "RAnkleOut",
    }
)

# Golf cluster (validated set from issue #013).
_GOLF_CLUSTER_LABELS: frozenset[str] = frozenset(
    {
        "Marker_2:2:1",
        "Marker_2:2:2",
        "Marker_2:2:3",
        "Marker_3:3:1",
        "Marker_3:3:2",
        "Marker_3:3:3",
    }
)
_GOLF_CLUSTER_REQUIRED: frozenset[str] = _GOLF_CLUSTER_LABELS  # all six required


# Public per-set canonical / required mappings, keyed by enum member.
CANONICAL_LABELS: dict[MarkerSet, frozenset[str]] = {
    MarkerSet.CGM2_4: _CGM2_4_LABELS,
    MarkerSet.PLUG_IN_GAIT_41: _PIG_41_LABELS,
    MarkerSet.PLUG_IN_GAIT_28: _PIG_28_LABELS,
    MarkerSet.IOR: _IOR_LABELS,
    MarkerSet.GOLF_CLUSTER: _GOLF_CLUSTER_LABELS,
}

REQUIRED_LABELS: dict[MarkerSet, frozenset[str]] = {
    MarkerSet.CGM2_4: _CGM2_4_REQUIRED,
    MarkerSet.PLUG_IN_GAIT_41: _PIG_41_REQUIRED,
    MarkerSet.PLUG_IN_GAIT_28: _PIG_28_REQUIRED,
    MarkerSet.IOR: _IOR_REQUIRED,
    MarkerSet.GOLF_CLUSTER: _GOLF_CLUSTER_REQUIRED,
}

# Deterministic priority: more specific / more diagnostic sets first. The
# golf cluster is the most specific (its labels are unique to this repo's
# convention). CGM2.4 has unique LTHI1..4 / RTIB1..4 markers that PiG-41
# does not, so it is checked before PiG-41. PiG-28 (the in-house anatomical
# subset) is checked before PiG-41 because its labels are mutually exclusive
# with the Vicon canonical Plug-in-Gait short codes. IOR is last because
# its labels (RIAS/LIAS/RIPS/LIPS) overlap subtly with no other set.
DETECTION_PRIORITY: tuple[MarkerSet, ...] = (
    MarkerSet.GOLF_CLUSTER,
    MarkerSet.CGM2_4,
    MarkerSet.PLUG_IN_GAIT_28,
    MarkerSet.PLUG_IN_GAIT_41,
    MarkerSet.IOR,
)


def detect_marker_set(marker_names: Sequence[str]) -> MarkerSet:
    """Return the marker set whose required subset is fully present.

    Detection walks :data:`DETECTION_PRIORITY` in order and returns the first
    set whose :data:`REQUIRED_LABELS` entry is a subset of ``marker_names``.
    The chosen set and its match score (fraction of canonical labels present)
    are logged at INFO level. When no required subset matches,
    :attr:`MarkerSet.UNKNOWN` is returned and a debug-level diagnostic
    listing per-set match scores is emitted.

    Args:
        marker_names: Marker labels exactly as they appear in the C3D file's
                      ``POINT:LABELS`` parameter. The comparison is
                      case-sensitive — Vicon canonical labels are upper-case.

    Returns:
        Detected :class:`MarkerSet` member, or :attr:`MarkerSet.UNKNOWN`.
    """
    name_set = set(marker_names)
    if not name_set:
        logger.info("detect_marker_set: empty marker list -> UNKNOWN")
        return MarkerSet.UNKNOWN

    for member in DETECTION_PRIORITY:
        required = REQUIRED_LABELS[member]
        canonical = CANONICAL_LABELS[member]
        if required.issubset(name_set):
            score = len(canonical & name_set) / len(canonical)
            logger.info(
                "detect_marker_set: matched %s (required=%d/%d, canonical_score=%.2f)",
                member.name,
                len(required),
                len(required),
                score,
            )
            return member

    # No match: emit a per-set diagnostic at DEBUG level so operators can
    # see which set was closest without flooding INFO.
    if logger.isEnabledFor(logging.DEBUG):
        for member in DETECTION_PRIORITY:
            canonical = CANONICAL_LABELS[member]
            score = len(canonical & name_set) / len(canonical)
            logger.debug(
                "detect_marker_set: no match for %s (canonical_score=%.2f)",
                member.name,
                score,
            )
    logger.info(
        "detect_marker_set: no known set matched (n_labels=%d) -> UNKNOWN",
        len(name_set),
    )
    return MarkerSet.UNKNOWN


def missing_required(marker_set: MarkerSet, marker_names: Sequence[str]) -> list[str]:
    """Return the sorted list of required labels missing for ``marker_set``.

    Useful for building loader error messages when a known marker set was
    indicated (e.g. via override) but the file is incomplete.
    """
    if marker_set is MarkerSet.UNKNOWN:
        return []
    required = REQUIRED_LABELS.get(marker_set, frozenset())
    return sorted(required - set(marker_names))


__all__ = [
    "CANONICAL_LABELS",
    "DETECTION_PRIORITY",
    "MarkerSet",
    "REQUIRED_LABELS",
    "detect_marker_set",
    "missing_required",
]

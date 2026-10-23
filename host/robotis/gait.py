"""P3-001: offline-only, deterministic, periodic 10-DOF pose prototype.

No Webots, motor, servo, network, or safety-state integration. The pose offsets
are UNVERIFIED research waveforms, NOT a claim of COM shift, foot lift or gait.
All angles are radians. Runtime actuation is forbidden until the P2 gate passes.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping


JOINT_NAMES = tuple(
    f"{side}_{joint}"
    for side in ("left", "right")
    for joint in ("hip_roll", "hip_pitch", "knee_pitch", "ankle_pitch", "ankle_roll")
)
PHASE_SEQUENCE = (
    "DOUBLE_SUPPORT_A", "SHIFT_LEFT", "SWING_RIGHT",
    "DOUBLE_SUPPORT_B", "SHIFT_RIGHT", "SWING_LEFT",
)


@dataclass(frozen=True)
class GaitFrame:
    phase: str
    angles_rad: dict[str, float]


@dataclass(frozen=True)
class _JointLimits:
    neutral: float
    minimum: float
    maximum: float
    rate_limit: float


@dataclass(frozen=True)
class _Segment:
    phase: str
    duration_s: float
    start: dict[str, float]
    end: dict[str, float]


def _finite_number(value: object, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field}: boolean is not a number")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field}: expected finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field}: non-finite number")
    return number


def _smoothstep(u: float) -> float:
    """C1 easing with zero velocity at each keyframe."""
    return u * u * (3.0 - 2.0 * u)


class OfflineGait:
    """Sample a closed neutral-to-neutral test waveform; never command joints.

    Each SWING phase has two C1 subsegments (apex then neutral). A phase name is
    only a proposed schedule label; no real contact/COM/foot geometry is modeled.
    Preflight rejects any keyframe that would exceed joint or rate constraints.
    """

    def __init__(
        self,
        robot_config: Mapping[str, object],
        *,
        shift_rad: float = 0.03,
        hip_swing_rad: float = 0.06,
        knee_lift_rad: float = 0.10,
        ankle_swing_rad: float = 0.05,
        double_support_s: float = 0.4,
        shift_s: float = 0.8,
        swing_s: float = 1.2,
    ) -> None:
        if not isinstance(robot_config, Mapping) or robot_config.get("units") != "radian":
            raise ValueError("expected robot config with units=radian")
        raw_joints = robot_config.get("joints")
        if not isinstance(raw_joints, Mapping) or set(raw_joints) != set(JOINT_NAMES):
            raise ValueError("expected exactly ten canonical leg joints")
        self._limits = {}
        for name in JOINT_NAMES:
            raw = raw_joints[name]
            if (not isinstance(raw, Mapping) or type(raw.get("direction")) is not int
                    or raw["direction"] not in (-1, 1)):
                raise ValueError(f"{name}: invalid joint configuration/direction")
            spec = _JointLimits(*(
                _finite_number(raw.get(field), f"{name}.{field}")
                for field in ("neutral", "min", "max", "rate_limit")
            ))
            if not (spec.minimum <= spec.neutral <= spec.maximum and spec.rate_limit > 0):
                raise ValueError(f"{name}: invalid neutral/bounds/rate")
            self._limits[name] = spec

        amplitudes = {
            "shift_rad": shift_rad,
            "hip_swing_rad": hip_swing_rad,
            "knee_lift_rad": knee_lift_rad,
            "ankle_swing_rad": ankle_swing_rad,
        }
        durations = {
            "double_support_s": double_support_s,
            "shift_s": shift_s,
            "swing_s": swing_s,
        }
        for name, value in amplitudes.items():
            amplitudes[name] = _finite_number(value, name)
            if amplitudes[name] < 0:
                raise ValueError(f"{name}: expected nonnegative amplitude")
        for name, value in durations.items():
            durations[name] = _finite_number(value, name)
            if durations[name] <= 0:
                raise ValueError(f"{name}: expected positive duration")

        neutral = {name: spec.neutral for name, spec in self._limits.items()}
        left_shift = neutral.copy()
        right_shift = neutral.copy()
        shift = amplitudes["shift_rad"]
        for target, sign in ((left_shift, 1), (right_shift, -1)):
            target["left_hip_roll"] += sign * shift
            target["right_hip_roll"] -= sign * shift
            target["left_ankle_roll"] -= sign * shift
            target["right_ankle_roll"] += sign * shift

        def apex(shifted: dict[str, float], swing_side: str) -> dict[str, float]:
            pose = shifted.copy()
            pose[f"{swing_side}_hip_pitch"] -= amplitudes["hip_swing_rad"]
            pose[f"{swing_side}_knee_pitch"] += amplitudes["knee_lift_rad"]
            pose[f"{swing_side}_ankle_pitch"] -= amplitudes["ankle_swing_rad"]
            return pose

        right_apex = apex(left_shift, "right")
        left_apex = apex(right_shift, "left")
        ds, ws, half_swing = (durations["double_support_s"],
                              durations["shift_s"], durations["swing_s"] / 2.0)
        endpoints = (
            (PHASE_SEQUENCE[0], ds, neutral),
            (PHASE_SEQUENCE[1], ws, left_shift),
            (PHASE_SEQUENCE[2], half_swing, right_apex),
            (PHASE_SEQUENCE[2], half_swing, neutral),
            (PHASE_SEQUENCE[3], ds, neutral),
            (PHASE_SEQUENCE[4], ws, right_shift),
            (PHASE_SEQUENCE[5], half_swing, left_apex),
            (PHASE_SEQUENCE[5], half_swing, neutral),
        )
        segments = []
        prior = neutral
        for phase, duration, end in endpoints:
            for name, limits in self._limits.items():
                value = end[name]
                if not limits.minimum <= value <= limits.maximum:
                    raise ValueError(f"{phase}: {name} exceeds joint limits")
                # smoothstep's maximum slope is 1.5 per normalized segment.
                max_speed = 1.5 * abs(value - prior[name]) / duration
                if max_speed > limits.rate_limit + 1e-12:
                    raise ValueError(f"{phase}: {name} exceeds rate limit")
            segments.append(_Segment(phase, duration, prior.copy(), end.copy()))
            prior = end
        self._segments = tuple(segments)
        self.cycle_duration_s = sum(s.duration_s for s in segments)
        if not math.isfinite(self.cycle_duration_s):
            raise ValueError("non-finite gait cycle duration")

    def frame_at(self, time_s: float) -> GaitFrame:
        """Return a detached sample; supports any finite, nonnegative timestamp."""
        t = _finite_number(time_s, "time_s")
        if t < 0:
            raise ValueError("time_s cannot be negative")
        local_t = t % self.cycle_duration_s
        for segment in self._segments:
            if local_t < segment.duration_s:
                factor = _smoothstep(local_t / segment.duration_s)
                return GaitFrame(segment.phase, {
                    name: segment.start[name] + (segment.end[name] - segment.start[name]) * factor
                    for name in JOINT_NAMES
                })
            local_t -= segment.duration_s
        # Floating-point edge at the end of a cycle is always neutral.
        return GaitFrame(PHASE_SEQUENCE[0], {
            name: spec.neutral for name, spec in self._limits.items()
        })

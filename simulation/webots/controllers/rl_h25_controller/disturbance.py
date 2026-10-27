"""Explicit opt-in, simulation-only bounded force experiment (Webots Supervisor).

Forces are applied at a torso-side offset for a few 16 ms physics steps.
There is NO physical-hardware control path and NO AI commands here.
"""
from __future__ import annotations
from dataclasses import dataclass
import ctypes
import math
from typing import Mapping

CALIBRATION_MAX_FORCE_N = 4.0


@dataclass(frozen=True)
class DisturbanceSpec:
    axis: str
    direction: int
    force_n: float
    pulse_s: float
    onset_s: float
    offset_m: float
    calibration_mode: bool = False

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "DisturbanceSpec | None":
        flag = env.get("RL_H25_DISTURBANCE", "0")
        if flag not in ("0", "1", ""):
            raise ValueError("RL_H25_DISTURBANCE must be 0 or 1")
        if flag != "1":
            return None
        axis = env.get("RL_H25_DIST_AXIS", "pitch")
        if axis not in ("pitch", "roll"):
            raise ValueError("disturbance axis must be pitch or roll")
        direction = int(env.get("RL_H25_DIST_DIRECTION", "1"))
        if direction not in (-1, 1):
            raise ValueError("disturbance direction must be -1 or +1")
        force = float(env.get("RL_H25_DIST_FORCE_N", "0.10"))
        pulse = float(env.get("RL_H25_DIST_PULSE_S", "0.112"))
        onset = float(env.get("RL_H25_DIST_ONSET_S", "4.0"))
        offset = float(env.get("RL_H25_DIST_OFFSET_M", "0.04"))
        calibration = env.get("RL_H25_DIST_CALIBRATION", "0")
        if calibration not in ("0", "1", ""):
            raise ValueError("RL_H25_DIST_CALIBRATION must be 0 or 1")
        if not all(map(math.isfinite, (force, pulse, onset, offset))):
            raise ValueError("nonfinite disturbance parameter")
        calibration_mode = calibration == "1"
        max_force = CALIBRATION_MAX_FORCE_N if calibration_mode else 0.50
        # The calibration envelope is simulation-only and must be explicitly opted in.
        if not (0.01 <= force <= max_force and 0.016 <= pulse <= 0.20 and
                2.0 <= onset <= 15.0 and 0 <= offset <= 0.06):
            raise ValueError("disturbance outside safe experiment bounds")
        return cls(axis, direction, force, pulse, onset, offset, calibration_mode)

    def force_vector(self) -> list[float]:
        # NUE: Y-up, +Z creates pitch about X with a +Y offset;
        # +X creates roll about Z (force is WORLD coordinates).
        f = self.direction * self.force_n
        return [f, 0.0, 0.0] if self.axis == "roll" else [0.0, 0.0, f]

    def metadata(self) -> dict:
        return dict(axis=self.axis, direction=self.direction,
                    force_n=self.force_n, pulse_s=self.pulse_s,
                    onset_s=self.onset_s, offset_m=self.offset_m,
                    calibration_mode=self.calibration_mode,
                    world_force_n=self.force_vector())



class ForceWithOffsetAPI:
    """R2025a compatibility adapter: call the *correct* Webots C symbol.

    ABI sources (Cyberbotics R2025a):
    - include/controller/c/webots/supervisor.h:
      void wb_supervisor_node_add_force_with_offset(
        WbNodeRef, const double[3], const double[3], bool);
    - lib/controller/python/controller/node.py: Node._ref is c_void_p;
      its addForceWithOffset mistakenly dispatches wb_supervisor_node_add_force.

    Native *physics* still needs independent confirmation in force_api_probe.
    Never fall back to the known broken Python wrapper.
    """

    mode = "r2025a_ctypes_force_with_offset"

    def __init__(self, solid: object, *, library: object | None = None) -> None:
        ref = getattr(solid, "_ref", None)
        if not isinstance(ref, ctypes.c_void_p) or not ref.value:
            raise RuntimeError("Supervisor Node._ref must be a non-null c_void_p")
        if library is None:
            from controller.wb import wb  # loaded Webots libController, not a guessed dylib
            library = wb
        try:
            method = library.wb_supervisor_node_add_force_with_offset
        except AttributeError as exc:
            raise RuntimeError("Webots C force-with-offset symbol unavailable") from exc
        # WbNodeRef=void*, force/offset=pointer to three doubles, bool=bool (C).
        method.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_double),
                           ctypes.POINTER(ctypes.c_double), ctypes.c_bool]
        method.restype = None
        self._ref, self._apply = ref, method

    def add(self, force: list[float], offset: list[float], relative: bool) -> None:
        if (len(force) != 3 or len(offset) != 3 or
                not all(math.isfinite(float(v)) for v in (*force, *offset))):
            raise ValueError("force and offset must be finite 3-vectors")
        vector = (ctypes.c_double * 3)(*force)
        point = (ctypes.c_double * 3)(*offset)
        self._apply(self._ref, vector, point, bool(relative))


class DisturbanceInjector:
    def __init__(self, spec: DisturbanceSpec, solid: object, *,
                 force_api: ForceWithOffsetAPI | None = None) -> None:
        if solid is None:
            raise RuntimeError("Webots Supervisor.getSelf() returned None")
        self.spec = spec
        self.force_api = force_api if force_api is not None else ForceWithOffsetAPI(solid)
        self.applied_steps = 0
        self.first_s: float | None = None
        self.last_s: float | None = None

    def step(self, now: float, *, can_apply: bool) -> None:
        """Call after each robot.step(). Webots applies force in upcoming physics step."""
        if (not can_apply or not math.isfinite(now) or
                now < self.spec.onset_s - 1e-8 or
                now >= self.spec.onset_s + self.spec.pulse_s - 1e-8):
            return
        self.force_api.add(self.spec.force_vector(),
                           [0.0, self.spec.offset_m, 0.0], False)
        self.applied_steps += 1
        if self.first_s is None:
            self.first_s = now
        self.last_s = now

    def metadata(self) -> dict:
        return {**self.spec.metadata(), "applied_steps": self.applied_steps,
                "force_api_mode": self.force_api.mode,
                "first_application_s": self.first_s,
                "last_application_s": self.last_s}

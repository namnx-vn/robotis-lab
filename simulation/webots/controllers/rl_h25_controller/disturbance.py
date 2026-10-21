"""Explicit opt-in, simulation-only bounded force experiment (Webots Supervisor).

Forces are applied at a torso-side offset for a few 16 ms physics steps.
There is NO physical-hardware control path and NO AI commands here.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Mapping


@dataclass(frozen=True)
class DisturbanceSpec:
    axis: str
    direction: int
    force_n: float
    pulse_s: float
    onset_s: float
    offset_m: float

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
        if not all(map(math.isfinite, (force, pulse, onset, offset))):
            raise ValueError("nonfinite disturbance parameter")
        # Research simulation limits. Re-evaluate before trying larger excitations.
        if not (0.01 <= force <= 0.35 and 0.016 <= pulse <= 0.20 and
                2.0 <= onset <= 15.0 and 0 <= offset <= 0.06):
            raise ValueError("disturbance outside safe experiment bounds")
        return cls(axis, direction, force, pulse, onset, offset)

    def force_vector(self) -> list[float]:
        # NUE: Y-up, +Z creates pitch about X with a +Y offset;
        # +X creates roll about Z (force is WORLD coordinates).
        f = self.direction * self.force_n
        return [f, 0.0, 0.0] if self.axis == "roll" else [0.0, 0.0, f]

    def metadata(self) -> dict:
        return dict(axis=self.axis, direction=self.direction,
                    force_n=self.force_n, pulse_s=self.pulse_s,
                    onset_s=self.onset_s, offset_m=self.offset_m,
                    world_force_n=self.force_vector())


class DisturbanceInjector:
    def __init__(self, spec: DisturbanceSpec, solid: object) -> None:
        if solid is None:
            raise RuntimeError("Webots Supervisor.getSelf() returned None")
        self.spec = spec
        self.solid = solid
        self.applied_steps = 0
        self.first_s: float | None = None
        self.last_s: float | None = None

    def step(self, now: float, *, can_apply: bool) -> None:
        """Call after each robot.step(). Webots applies force in upcoming physics step."""
        if (not can_apply or not math.isfinite(now) or
                now < self.spec.onset_s - 1e-8 or
                now >= self.spec.onset_s + self.spec.pulse_s - 1e-8):
            return
        self.solid.addForceWithOffset(self.spec.force_vector(),
                                      [0.0, self.spec.offset_m, 0.0], False)
        self.applied_steps += 1
        if self.first_s is None:
            self.first_s = now
        self.last_s = now

    def metadata(self) -> dict:
        return {**self.spec.metadata(), "applied_steps": self.applied_steps,
                "first_application_s": self.first_s,
                "last_application_s": self.last_s}

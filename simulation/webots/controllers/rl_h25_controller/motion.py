"""Pure deterministic motion + safety layer, importable without Webots.

All joint inputs/outputs are radians. No LLM or network path is present.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class JointConfig:
    neutral: float
    minimum: float
    maximum: float
    direction: int
    rate_limit: float

    @classmethod
    def from_dict(cls, raw: dict) -> "JointConfig":
        obj = cls(float(raw["neutral"]), float(raw["min"]), float(raw["max"]),
                  int(raw["direction"]), float(raw["rate_limit"]))
        if not all(math.isfinite(v) for v in
                   (obj.neutral, obj.minimum, obj.maximum, obj.rate_limit)):
            raise ValueError("non-finite joint config")
        if (obj.minimum > obj.neutral or obj.neutral > obj.maximum or
                obj.rate_limit <= 0 or obj.direction not in (-1, 1)):
            raise ValueError("invalid joint bounds, direction or rate")
        return obj


def clamp(value: float, low: float, high: float) -> float:
    if not math.isfinite(value):
        raise ValueError("non-finite motion command")
    return min(high, max(low, value))


def advance(current: float, target: float, config: JointConfig, dt: float) -> float:
    """Slew-limit an actuator target; delta never exceeds rate*dt."""
    if not math.isfinite(current) or not math.isfinite(dt) or dt <= 0:
        raise ValueError("invalid current position or dt")
    safe = clamp(target, config.minimum, config.maximum)
    step = config.rate_limit * dt
    return clamp(current + clamp(safe - current, -step, step),
                 config.minimum, config.maximum)


@dataclass(frozen=True)
class Observation:
    roll_rad: float
    pitch_rad: float
    root_height_m: float
    obstacle_m: float


class SafetySupervisor:
    """Latching safety supervisor; FAULT/E_STOP require explicit reset.

    STOP from obstacle is latched in this Sprint. Hardware E-STOP remains
    a separate physical circuit, not replaced by this simulation class.
    """
    def __init__(self, tilt_fault_rad: float, min_root_height_m: float,
                 obstacle_stop_m: float) -> None:
        self.tilt_fault_rad = tilt_fault_rad
        self.min_root_height_m = min_root_height_m
        self.obstacle_stop_m = obstacle_stop_m
        self.state = "STAND"
        self.reason = ""

    def observe(self, obs: Observation, *, emergency_stop: bool = False) -> str:
        if emergency_stop:
            self.state, self.reason = "E_STOP", "operator_estop"
            return self.state
        if self.state in ("FAULT", "E_STOP", "STOP"):
            return self.state
        values = (obs.roll_rad, obs.pitch_rad, obs.root_height_m, obs.obstacle_m)
        if not all(math.isfinite(v) for v in values) or obs.obstacle_m < 0:
            self.state, self.reason = "FAULT", "invalid_sensor_value"
        elif abs(obs.roll_rad) > self.tilt_fault_rad or abs(obs.pitch_rad) > self.tilt_fault_rad:
            self.state, self.reason = "FAULT", "excessive_tilt"
        elif obs.root_height_m < self.min_root_height_m:
            self.state, self.reason = "FAULT", "root_too_low"
        elif obs.obstacle_m < self.obstacle_stop_m:
            self.state, self.reason = "STOP", "obstacle_nearby"
        return self.state

    def reset_with_operator_approval(self, approved: bool, safe_observation: Observation) -> bool:
        """Only a local operator path should call this; unused by Sprint 01 auto-loop."""
        if not approved:
            return False
        probe = SafetySupervisor(self.tilt_fault_rad, self.min_root_height_m,
                                 self.obstacle_stop_m)
        if probe.observe(safe_observation) != "STAND":
            return False
        self.state, self.reason = "STAND", ""
        return True


class StandController:
    """Open-loop neutral-position holding only. NOT a balance controller."""
    def __init__(self, joints: Mapping[str, JointConfig]) -> None:
        self.joints = dict(joints)
        self.targets = {name: spec.neutral for name, spec in joints.items()}

    def update(self, measured: Mapping[str, float], dt: float, enabled: bool) -> dict[str, float]:
        if set(measured) != set(self.joints):
            raise ValueError("missing or extra joint sensor")
        for name, cfg in self.joints.items():
            if not math.isfinite(measured[name]):
                raise ValueError(f"non-finite joint sensor: {name}")
            desired = cfg.neutral if enabled else self.targets[name]
            self.targets[name] = advance(self.targets[name], desired, cfg, dt)
        return self.targets.copy()

@dataclass(frozen=True)
class PIDConfig:
    kp: float
    ki: float
    kd: float
    integral_limit: float
    output_limit_rad: float
    derivative_filter_s: float

    @classmethod
    def from_dict(cls, raw: dict) -> "PIDConfig":
        c = cls(*(float(raw[k]) for k in (
            "kp", "ki", "kd", "integral_limit", "output_limit_rad", "derivative_filter_s")))
        if (not all(math.isfinite(v) for v in vars(c).values()) or
                any(v < 0 for v in (c.kp, c.ki, c.kd, c.derivative_filter_s)) or
                c.integral_limit <= 0 or c.output_limit_rad <= 0):
            raise ValueError("invalid PID configuration")
        return c


class AnglePID:
    """Bounded angle feedback with derivative on measurement and anti-windup.

    setpoint = zero (upright), error = -measured; D filtering avoids IMU noise
    amplification. Output has units radians (joint pose correction).
    Sign orientation depends on the actuator mapping; tune ONLY in simulation.
    """
    def __init__(self, cfg: PIDConfig) -> None:
        self.cfg = cfg
        self.integral = 0.0
        self.last_measurement: float | None = None
        self.filtered_rate = 0.0
        self.output = 0.0

    def reset(self) -> None:
        self.integral = 0.0
        self.last_measurement = None
        self.filtered_rate = 0.0
        self.output = 0.0

    def update(self, angle_rad: float, dt: float) -> float:
        if not math.isfinite(angle_rad) or not math.isfinite(dt) or dt <= 0:
            raise ValueError("invalid PID input")
        error = -angle_rad
        measured_rate = 0.0 if self.last_measurement is None else (
            angle_rad - self.last_measurement) / dt
        self.last_measurement = angle_rad
        alpha = dt / (self.cfg.derivative_filter_s + dt)
        self.filtered_rate += alpha * (measured_rate - self.filtered_rate)
        # Saturation-aware conditional integration. Do not grow integral in the
        # direction that pushes the output further beyond its permitted range.
        proposed_integral = clamp(self.integral + error * dt,
                                  -self.cfg.integral_limit, self.cfg.integral_limit)
        candidate = (self.cfg.kp * error + self.cfg.ki * proposed_integral -
                     self.cfg.kd * self.filtered_rate)
        if (abs(candidate) <= self.cfg.output_limit_rad or
                (candidate > self.cfg.output_limit_rad and error < 0) or
                (candidate < -self.cfg.output_limit_rad and error > 0)):
            self.integral = proposed_integral
        raw_output = (self.cfg.kp * error + self.cfg.ki * self.integral -
                      self.cfg.kd * self.filtered_rate)
        self.output = clamp(raw_output,
                            -self.cfg.output_limit_rad, self.cfg.output_limit_rad)
        return self.output


class BalanceController:
    """Outer IMU pose controller, not a proof of whole-body dynamic balance.

    The inner Webots motor position servo is separate. All target angles pass
    through joint min/max and rate limits. Disabled/latched faults freeze the
    previously accepted pose. Mode=baseline does NOT evaluate PID or integral.
    """
    def __init__(self, joints: Mapping[str, JointConfig], balance_raw: dict) -> None:
        self.joints = dict(joints)
        self.targets = {n: j.neutral for n, j in self.joints.items()}
        self.roll_pid = AnglePID(PIDConfig.from_dict(balance_raw["roll"]))
        self.pitch_pid = AnglePID(PIDConfig.from_dict(balance_raw["pitch"]))
        self.signs = {k: int(balance_raw["axis_sign"][k]) for k in ("pitch", "roll")}
        if any(s not in (-1, 1) for s in self.signs.values()):
            raise ValueError("axis_sign must be +1 or -1")
        self.mix: dict[str, tuple[str, float]] = {}
        for name, raw in balance_raw["joint_mix"].items():
            axis, gain = raw["axis"], float(raw["gain"])
            if name not in joints or axis not in ("roll", "pitch") or not math.isfinite(gain):
                raise ValueError("unknown joint / axis / gain in balance mix")
            self.mix[name] = (axis, gain)
        self.max_dt = float(balance_raw["max_dt_s"])
        if not 0 < self.max_dt <= 1.0:
            raise ValueError("invalid max_dt_s")
        self.corrections = {"roll": 0.0, "pitch": 0.0}

    def reset_pid(self) -> None:
        self.roll_pid.reset()
        self.pitch_pid.reset()
        self.corrections = {"roll": 0.0, "pitch": 0.0}

    def update(self, measured: Mapping[str, float], roll: float, pitch: float,
               dt: float, *, enabled: bool, mode: str) -> dict[str, float]:
        if mode not in ("baseline", "balance"):
            raise ValueError("invalid control mode")
        if set(measured) != set(self.joints) or not all(math.isfinite(v) for v in measured.values()):
            raise ValueError("missing/invalid joint position sensor")
        if not all(math.isfinite(v) for v in (roll, pitch, dt)) or dt <= 0:
            raise ValueError("non-finite IMU or invalid timestep")
        if not enabled:
            self.reset_pid()
            return self.targets.copy()  # FAULT/STOP/E_STOP do not issue new pose commands
        if dt > self.max_dt:
            self.reset_pid()  # avoid derivative and integral spikes on a big time gap
            raise ValueError("balance control loop timestep exceeded")
        if mode == "baseline":
            self.reset_pid()
        else:
            self.corrections["roll"] = self.roll_pid.update(self.signs["roll"] * roll, dt)
            self.corrections["pitch"] = self.pitch_pid.update(self.signs["pitch"] * pitch, dt)
        for name, spec in self.joints.items():
            offset = 0.0
            if mode == "balance" and name in self.mix:
                axis, gain = self.mix[name]
                offset = gain * self.corrections[axis]
            # Important: this assumes config joint commands & Webots motor axes
            # are already aligned in the simulation. Hardware direction is adapter-only.
            target = spec.neutral + offset
            self.targets[name] = advance(self.targets[name], target, spec, dt)
        return self.targets.copy()

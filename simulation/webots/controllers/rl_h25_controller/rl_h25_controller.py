"""Robotis Lab RL-H25 v0.2, Webots R2025a controller (Python 3).

Baseline neutral hold or bounded IMU pitch/roll outer-loop PID. No walking claims.
Safety latches STOP/FAULT/E_STOP. Hardware control is NOT supported.
Webots injects the `controller` Python module only inside its simulator runtime.
"""
from __future__ import annotations
import csv
import hashlib
import re
import json
import math
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from motion import JointConfig, Observation, SafetySupervisor, BalanceController
from disturbance import DisturbanceSpec, DisturbanceInjector
from contact_evidence import ContactEvidence

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CONFIG_PATH = PROJECT_ROOT / "configs" / "robot.json"


def load_config() -> dict:
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if data["units"] != "radian" or len(data["joints"]) != 10:
        raise ValueError("expected exactly ten joints expressed in radians")
    return data


def main() -> None:
    from controller import Robot  # Webots runtime only
    cfg = load_config()
    disturbance_spec = DisturbanceSpec.from_env(os.environ)
    contact_raw = os.getenv("RL_H25_CONTACT_EVIDENCE", "0")
    if contact_raw not in ("0", "1"):
        raise ValueError("RL_H25_CONTACT_EVIDENCE must be 0 or 1")
    contact_enabled = contact_raw == "1"
    if disturbance_spec is not None or contact_enabled:
        from controller import Supervisor  # only for opt-in experiment/evidence modes
    # RLH25.proto declares supervisor TRUE. Normal control still uses Robot only.
    robot = Supervisor() if disturbance_spec is not None or contact_enabled else Robot()
    robot_node = robot.getSelf() if disturbance_spec is not None or contact_enabled else None
    disturbance = (DisturbanceInjector(disturbance_spec, robot.getSelf())
                   if disturbance_spec is not None else None)
    step_ms = int(round(robot.getBasicTimeStep()))
    if step_ms <= 0:
        raise RuntimeError("invalid Webots time step")
    contact_evidence = ContactEvidence() if contact_enabled else None
    contact_names: dict[int, str] = {}
    if contact_evidence is not None:
        for def_name, solid_name in (
            ("LEFT_FOOT", "left_ankle_roll_link"),
            ("RIGHT_FOOT", "right_ankle_roll_link"),
        ):
            foot = robot_node.getFromProtoDef(def_name)
            if foot is None:
                raise RuntimeError(f"missing contact evidence node {def_name}")
            contact_names[foot.getId()] = solid_name
        robot_node.enableContactPointsTracking(step_ms, True)

    def contact_node_name(node_id: int) -> str:
        try:
            return contact_names[node_id]
        except KeyError as error:
            raise RuntimeError(f"unexpected contact solid node {node_id}") from error
    sensors: dict[str, object] = {}
    motors: dict[str, object] = {}
    joints = {name: JointConfig.from_dict(raw) for name, raw in cfg["joints"].items()}

    for name, spec in joints.items():
        motor = robot.getDevice(name)
        sensor = robot.getDevice(name + "_sensor")
        if motor is None or sensor is None:
            raise RuntimeError("missing motor or joint sensor: " + name)
        motor.setVelocity(float(cfg["joints"][name]["max_velocity"]))
        motor.setPosition(spec.neutral)  # 0 rad for initial vertical stance
        sensor.enable(step_ms)
        sensors[name], motors[name] = sensor, motor

    imu = robot.getDevice("imu")
    distance = robot.getDevice("front_distance")
    gps = robot.getDevice("root_gps")
    camera = robot.getDevice("head_camera")
    gyro = robot.getDevice("gyro")
    acc = robot.getDevice("accelerometer")
    for sensor in (imu, distance, gps, camera, gyro, acc):
        if sensor is None:
            raise RuntimeError("missing required sensor in RLH25.proto")
        sensor.enable(step_ms)

    control = cfg["control"]
    safety = SafetySupervisor(control["tilt_fault_rad"],
                              control["minimum_root_height_m"],
                              control["obstacle_stop_m"])
    stand = BalanceController(joints, cfg["balance"])
    mode = os.getenv("RL_H25_MODE", cfg["balance"]["default_mode"]).lower()
    if mode not in ("baseline", "balance"):
        raise ValueError("RL_H25_MODE must be baseline or balance")
    run_id = os.getenv("RL_H25_RUN_ID") or ("sim-" + uuid.uuid4().hex[:12])
    if re.fullmatch(r"[A-Za-z0-9_-]{1,80}", run_id) is None:
        raise ValueError("RL_H25_RUN_ID must contain only letters, digits, '-' or '_'")
    try:
        duration = float(os.getenv("RL_H25_DURATION_S", "0"))
    except ValueError:
        raise ValueError("RL_H25_DURATION_S must be numeric")
    if duration < 0 or not math.isfinite(duration):
        raise ValueError("RL_H25_DURATION_S must be nonnegative and finite")
    fault_injection = os.getenv("RL_H25_FORCE_FAULT", "").strip().lower()
    if fault_injection not in ("", "nan_imu", "obstacle", "estop"):
        raise ValueError("invalid RL_H25_FORCE_FAULT")
    logs_dir = Path(os.getenv("RL_H25_LOG_DIR", str(PROJECT_ROOT / "experiments" / "logs")))
    logs_dir.mkdir(parents=True, exist_ok=True)
    csv_path = logs_dir / (run_id + ".csv")
    meta_path = logs_dir / (run_id + ".json")
    meta = {
        "run_id": run_id,
        "robot": cfg["robot"],
        "software_version": "rlh25-v0.2",
        "config_sha256": hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest(),
        "build_commit": os.environ.get("RL_H25_BUILD_COMMIT", "unverified"),
        "source_commit_sha": os.environ.get("RL_H25_SOURCE_COMMIT_SHA", "unverified"),
        "test_merge_sha": os.environ.get("RL_H25_TEST_MERGE_SHA", "unverified"),
        "world_sha256": hashlib.sha256(
            (PROJECT_ROOT / "simulation/webots/worlds/rl_h25_lab.wbt").read_bytes()).hexdigest(),
        "simulation_timestep_s": step_ms / 1000.0,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "world": "rl_h25_lab.wbt",
        "controller": "v0.2 baseline hold / IMU outer-loop PID",
        "mode": mode,
        "webots_version": os.environ.get("RL_H25_WEBOTS_VERSION", "unverified"),
        "config": str(CONFIG_PATH.relative_to(PROJECT_ROOT)),
        "fault_injection": fault_injection or None,
        "disturbance": disturbance.metadata() if disturbance else None,
        "contact_evidence": contact_evidence.summary() if contact_evidence else None,
        "result": "incomplete"
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    fieldnames = ["run_id", "t_s", "dt_s", "mode", "state", "reason",
                  "roll_rad", "pitch_rad", "yaw_rad", "root_x_m", "root_y_m",
                  "root_z_m", "root_height_m", "obstacle_m", "gyro_x_rad_s",
                  "gyro_y_rad_s", "gyro_z_rad_s", "pitch_correction_rad",
                  "roll_correction_rad", "pitch_imu_rate_rad_s", "roll_imu_rate_rad_s",
                  "root_velocity_x_m_s", "root_velocity_y_m_s", "root_velocity_z_m_s",
                  "requested_force_x_n", "requested_force_y_n", "requested_force_z_n",
                  "applied_force_steps", "pulse_onset_s", "pulse_duration_s", "force_api_mode"]
    fieldnames += [name + "_target_rad" for name in joints]
    fieldnames += [name + "_measured_rad" for name in joints]
    total_steps = 0
    state = "BOOT"
    reason = ""
    log_next = 0.0
    log_period = float(os.getenv("RL_H25_LOG_PERIOD_S", str(control["log_period_s"])))
    if not math.isfinite(log_period) or not 0.016 <= log_period <= 0.20:
        raise ValueError("RL_H25_LOG_PERIOD_S must be in [0.016, 0.20]")
    meta["log_period_s"] = log_period
    last_reported_state = None
    completed = False
    last_time = robot.getTime()
    try:
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            while robot.step(step_ms) != -1:
                total_steps += 1
                now = robot.getTime()
                dt = max(0.00001, now - last_time)
                last_time = now
                if total_steps <= control["sensor_warmup_steps"]:
                    state = "SELF_TEST"
                    continue
                measured = {name: float(sensor.getValue()) for name, sensor in sensors.items()}
                roll, pitch, yaw = (float(x) for x in imu.getRollPitchYaw())
                x, height, z = (float(v) for v in gps.getValues())  # WorldInfo NUE: y is up
                gx, gy, gz = (float(v) for v in gyro.getValues())
                obstacle = float(distance.getValue())  # lookupTable maps to meters
                if fault_injection == "nan_imu":
                    roll = float("nan")
                elif fault_injection == "obstacle":
                    obstacle = 0.05
                obs = Observation(roll, pitch, height, obstacle)
                state = safety.observe(obs, emergency_stop=fault_injection == "estop")
                # The GPS position/gyro are monitored too; fail closed on invalid telemetry.
                if state not in ("E_STOP", "FAULT") and not all(
                        math.isfinite(v) for v in (x, z, yaw, gx, gy, gz)):
                    safety.state, safety.reason = "FAULT", "invalid_pose_sensor"
                    state = safety.state
                reason = safety.reason
                # Faults are latched: never replace the original stop reason with
                # an error caused by attempting PID after an invalid IMU sample.
                if state == "STAND":
                    try:
                        targets = stand.update(measured, roll, pitch, dt,
                                               enabled=True, mode=mode)
                    except ValueError as err:
                        safety.state, safety.reason = "FAULT", (
                            "control_timestep_invalid" if "timestep" in str(err)
                            else "joint_sensor_invalid")
                        state, reason = safety.state, safety.reason
                        stand.reset_pid()
                        targets = stand.targets.copy()
                        print("[RL-H25] FAULT:", err, file=sys.stderr, flush=True)
                else:
                    stand.reset_pid()
                    targets = stand.targets.copy()
                if state == "E_STOP":
                    # In simulation only. Real hardware E-STOP MUST cut its separate servo rail.
                    for motor in motors.values():
                        motor.setAvailableTorque(0.0)
                else:
                    # STOP/FAULT hold last accepted targets, no new gait/pose transition.
                    for name, motor in motors.items():
                        motor.setPosition(targets[name])
                # Apply only when STAND and healthy; a latched FAULT/STOP cancels the pulse.
                if disturbance is not None:
                    disturbance.step(now, can_apply=state == "STAND")
                if now >= log_next:
                    if contact_evidence is not None:
                        contact_evidence.observe(
                            robot_node.getContactPoints(True), contact_node_name
                        )
                    root_velocity = (robot.getSelf().getVelocity()[:3]
                                     if disturbance is not None else ("", "", ""))
                    req_force = (disturbance_spec.force_vector()
                                 if disturbance_spec is not None else ("", "", ""))
                    record = dict(run_id=run_id, t_s=f"{now:.4f}", dt_s=dt,
                                  mode=mode, state=state, reason=reason, roll_rad=roll,
                                  pitch_rad=pitch, yaw_rad=yaw, root_x_m=x,
                                  root_y_m=height, root_z_m=z, root_height_m=height,
                                  obstacle_m=obstacle, gyro_x_rad_s=gx,
                                  gyro_y_rad_s=gy, gyro_z_rad_s=gz,
                                  pitch_correction_rad=stand.corrections["pitch"],
                                  roll_correction_rad=stand.corrections["roll"],
                                  pitch_imu_rate_rad_s=stand.pitch_pid.filtered_rate,
                                  roll_imu_rate_rad_s=stand.roll_pid.filtered_rate,
                                  root_velocity_x_m_s=root_velocity[0],
                                  root_velocity_y_m_s=root_velocity[1],
                                  root_velocity_z_m_s=root_velocity[2],
                                  requested_force_x_n=req_force[0],
                                  requested_force_y_n=req_force[1],
                                  requested_force_z_n=req_force[2],
                                  applied_force_steps=(disturbance.applied_steps if disturbance else 0),
                                  pulse_onset_s=(disturbance_spec.onset_s if disturbance_spec else ""),
                                  pulse_duration_s=(disturbance_spec.pulse_s if disturbance_spec else ""),
                                  force_api_mode=(disturbance.force_api.mode if disturbance else ""))
                    record.update({name + "_target_rad": target for name, target in targets.items()})
                    record.update({name + "_measured_rad": value for name, value in measured.items()})
                    writer.writerow(record)
                    f.flush()
                    log_next = now + log_period
                if state != last_reported_state:
                    last_reported_state = state
                    print(f"[RL-H25] t={now:.2f}s state={state} reason={reason or '-'} "
                          f"height={height:.3f}m roll={roll:.3f} pitch={pitch:.3f} mode={mode}", flush=True)
                if duration > 0 and now >= duration:
                    break
            completed = True
    finally:
        meta["result"] = "controller_exited" if completed else "error"
        if disturbance is not None:
            meta["disturbance"] = disturbance.metadata()
        if contact_evidence is not None:
            meta["contact_evidence"] = contact_evidence.summary()
        meta["final_state"] = state
        meta["stop_reason"] = reason
        meta["sim_time_s"] = last_time
        meta["steps"] = total_steps
        meta["log_csv"] = str(csv_path)
        meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        print(f"[RL-H25] run={run_id} final={state} reason={reason} log={csv_path}", flush=True)


if __name__ == "__main__":
    main()

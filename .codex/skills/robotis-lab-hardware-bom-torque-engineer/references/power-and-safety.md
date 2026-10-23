# Servo power design and safety review

## Mandatory separation

Conceptual layout (not a validated wiring diagram):

```
 PC host -- USB serial --> Arduino Uno (logic powered via USB / safe regulated supply)
                                    |  I²C SDA/SCL + common signal ground
                                    v
                             PCA9685 VCC logic
                                  PCA9685 PWM outputs ---> individual servo signal wires

 Rated independent servo DC supply --> main switch --> appropriately selected fuse
    --> physical E-STOP actuator-power disable --> servo V+ rail --> individual servo +V
 Common reference ground with robust actuator return path ------------------------> servo GND
```

- **PCA9685 generates PWM control signals, not servo supply current.** Its logic VCC and high-current servo V+ are distinct. Confirm board-specific current ratings and connector trace limits. Some breakout boards cannot safely distribute aggregate stall current to 10 servos; use an appropriately rated distribution bus if needed.
- Powering multiple servos from the **Uno 5V pin or host USB is prohibited**.
- Servo voltage depends on exact model/rating, not assumed 5–6 V. Confirm logic-level/I²C compatibility, board pullups, VCC and Uno/host voltage domains from actual manuals.
- Grounds must share a reference for PWM signaling; wire actuator currents directly through suitable supply return conductors rather than fragile logic traces. Avoid loops/high dI/dt near IMU and USB serial.
- Correct fuse, switch, E-STOP and wire sizing is **blocked until** actual supply, servo current and cable/connector spec are known. Consider protective enclosure, strain relief, polarity, short-circuit protection and measured voltage at farthest servo.

## Power calculation protocol

1. Record rated input voltage range for each model, typical idle/no-load/loaded current, transient startup and stall current at the **same voltage**. If the datasheet omits data, require measured bench values and conservative upper bounds. Do not extrapolate startup or stall to continuous duty without time/temperature data.
2. For homogeneous servos, the conservative worst-case algebraic upper bound is `I_sum_peak = N × I_each_peak`; for mixed actuators use `Σ I_i_peak`. If simultaneity is reduced based on scheduling, justify from control traces and define a safe fallback for unexpected synchronized stall; a guessed diversity factor is not evidence.
3. Separate `I_continuous_est = Σ I_i_avg_under_duty`, `I_event_peak`, driver/logic consumption and future sensor current. Power `P ≈ V_load × I`; voltage-drop `ΔV ≈ I × R_total_path`, with resistance from real wire lengths, connector contacts and thermal conditions. Voltage at servo equals setpoint minus total distribution drop.
4. Compare PSU continuous and surge envelopes, actuator rail connectors, fuse time-current curve, switch/E-STOP DC rating and accessible wire gauge. Count ground return and bank-by-bank distribution. Do not choose amperage solely by summing guessed servo catalog figures.
5. Check controller brownout/reset, EMI, jitter, thermal ramp and stop/rearm response; the system may need interlocks/soft-start and software heartbeat loss behavior, but hardware E-STOP remains a separate physical path.
6. Store measured telemetry from an operator-approved bench: supply setpoint and at load, supply current, transient current capture, peak temperature over time, servo angle commanded vs observed, Uno reset/serial errors, E-STOP cut time/behavior, cable/contact heating and test duration.

## Failure modes to evaluate

| Failure | Required review / measured outcome |
|---|---|
| Simultaneous stall/startup | Rail sag, PSU current limit, fuse/switch, connector heating; stop criteria |
| Motor short/connector reversed | Current limiting, fuse behavior, insulation, polarities |
| Broken/weak common ground | PWM corruption, reboot, unsafe motion; protective connector design |
| Controller loses serial / PC | Local watchdog; no uncontrolled motion or automatic rearm |
| AI/network timeout | Motion controller and E-STOP independent of cloud |
| Emergency power cut while loaded | Robot may fall; begin with jig/tether, clear protective zone |
| Supply over/undervoltage | Stop/disable defined at component datasheet limits |
| Excessive servo heat/odor | Immediate supervised stop and operator inspection |
| Stale sensor or invalid command | Fail-closed actuator interface, no raw AI PWM |

## Never infer these without proof

A protective design is **NOT** validated by a neat diagram, an unpowered simulator, nominal current arithmetic or a green Webots CI. A physical wiring plan must be reviewed against purchased components, supply ratings and test data before use. No unprotected self-built lithium battery packs or unapproved physical actuation.

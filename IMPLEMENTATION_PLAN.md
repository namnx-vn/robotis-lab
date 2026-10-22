# ROBOTIS LAB — IMPLEMENTATION PLAN & MILESTONES

**Ngày lập:** 2026-10-19  
**Đích:** RL-H25, robot hai chân ~25 cm; đứng/đi tránh vật cản; từng bước lên autonomous exploration.  
**Dự kiến:** 24 tuần cho nền tảng từ mô phỏng đến thử robot thật có hỗ trợ; thời gian là kế hoạch có điều kiện, không phải cam kết kết quả.

## 0. Phạm vi sản phẩm tối thiểu (MVP)

**MVP-Simulation (M1):** Webots hiển thị robot hình người 25 cm có 10 DOF ở hai chân, head/arms passive, contact geometry và physics, IMU/DistanceSensor/Camera, pose đứng, chuỗi nhấc/chuyển trọng tâm, tập thử tránh vật cản đơn giản.

**MVP-Physical (M2):** Arduino Uno + servo driver + bộ servo đủ tải trên khung có giá bảo vệ, hiệu chuẩn khớp, stand, step hỗ trợ, phản ứng dừng và telemetry serial.

**MVP-Autonomy (M3):** vòng hành vi IDLE/EXPLORE/AVOID/STOP, mục tiêu cục bộ, sensor hợp nhất, dừng trước vật cản; AI chỉ cấp nhiệm vụ, không điều khiển khớp.

**Ngoài phạm vi 24 tuần:** điều khiển giống người hoàn chỉnh, chạy/leo cầu thang, tay gắp vật nặng, 3D SLAM tốc độ cao trên Uno, hỗ trợ gia đình không giám sát, mạng AI có quyền can thiệp safety.

## 1. Điều kiện và tài nguyên cần có

### 1.1 Kiến thức học theo nhu cầu

- Kỹ thuật: cơ bản điện áp/dòng/đấu mạch, Newton/mô-men/quán tính, PID, kinematics, ma trận tọa độ, sensor noise, kiểm thử.
- Công cụ: Python 3, Git, Webots (ưu tiên bản stable), Arduino IDE/CLI, công cụ serial monitor, CAD (FreeCAD/Fusion 360 hoặc tương đương), đồng hồ đo điện.
- AI: structured outputs và JSON schema, prompt safety, latency/timeout, privacy, API credential management.

### 1.2 Khởi tạo repository Git

```bash
mkdir robotis-lab && cd robotis-lab
git init
mkdir -p docs/decisions simulation/webots/worlds simulation/webots/protos \
  simulation/webots/controllers/rl_h25_controller firmware/uno_motion_controller \
  host/robotis configs tests/{unit,integration,simulation,hardware} experiments tasks
```

Thiết lập README và `.gitignore` cho `__pycache__`, build outputs, logs/video lớn, `.env`, credentials. Không commit dữ liệu ảnh camera của người khác nếu không được phép.

## 2. Lộ trình 24 tuần

| Giai đoạn | Tuần | Deliverable chính | Gate qua giai đoạn |
|---|---|---|---|
| P0 — Foundation | 1–2 | Requirements, inventory, repo, CAD thô, reference Webots | Ký duyệt cấu trúc/constraints |
| P1 — Simulation Body | 3–5 | Mô hình 25 cm, 10 joint, khối lượng/collision | Khớp quay đúng trục, không xuyên vật |
| P2 — Stand & Balance | 6–8 | Pose transition, sensor logging, stand | Đứng 30 s/5 lần thử trong sim |
| P3 — Walking Gait | 9–12 | Dịch trọng tâm, nhấc/chạm chân, đi | ≥5 bước liên tiếp, ghi độ ngã |
| P4 — Obstacle & Behaviors | 13–15 | Distance sensor, STOP/AVOID, state machine | Dừng trước vật cản và không đi xuyên |
| P5 — Hardware Bench | 16–19 | Servo calibration, Uno, driver, frame | 1 khớp → 1 chân → 2 chân trên giá |
| P6 — Supported Physical Walk | 20–22 | Stand/step trên giá an toàn, đo điện | Bước được với hỗ trợ và không quá nhiệt |
| P7 — Autonomy Bridge | 23–24 | Host planner, simple mapping, AI adapter stub | Không có lệnh AI vượt safety limits |

> Nếu robot vật lý không đủ tiền/servo torque, P5–P7 tiếp tục dùng mô phỏng và bench jig, **không ép vượt gate**.

## 3. Backlog từng tuần

### Tuần 1 — Define & Audit

- [ ] Viết `docs/architecture/requirements.md`: mục tiêu, giới hạn 25 cm, 3 triệu, điều kiện dùng PC, sàn phẳng.
- [ ] Kiểm kê linh kiện thực tế: Uno, servo, module, dây, nguồn, cảm biến, tool. Ghi part number, điện áp và tình trạng.
- [ ] Chốt danh sách 10 joint và tên chuẩn (`left_hip_roll`, `left_hip_pitch`, ...).
- [ ] Viết risk register: rơi robot, servo quá nhiệt, nguồn sụt, đứt dây, sensor sai, AI timeout.
- [ ] Tạo Git repo và commit `Initial research requirements`.

**DoD:** có bản mô tả rõ cái gì đã có/chưa có, assumption list và scope M1.

### Tuần 2 — Geometry & Mechanics

- [ ] Phác CAD toàn thân 250 mm với 10 DOF hai chân, đầu/tay passive.
- [ ] Xác định trục local, chiều dương/âm, home pose, joint limits dự kiến.
- [ ] Ước tính center of mass, khối lượng từng link và phân bố tải.
- [ ] Lập bảng torque sơ bộ theo 2–3 tư thế gối/hông bất lợi.
- [ ] Chốt môi trường lab 2 m × 2 m, nền phẳng và một vật cản đơn.

**DoD:** CAD/geometry đầu tiên + bảng joint and mass assumptions.

### Tuần 3 — Webots Skeleton

- [ ] Cài Webots stable; ghi phiên bản và đường dẫn tải.
- [ ] Tạo `rl_h25_lab.wbt` có `WorldInfo`, floor, camera quan sát bên ngoài.
- [ ] Tạo `RLH25.proto` gồm Robot, torso, head, arm pieces, hip links.
- [ ] Model có `boundingObject` và `Physics` phù hợp, kiểm tra trọng lực.

**DoD:** khởi động mô phỏng không lỗi parser, robot thả vào môi trường có trọng lực.

### Tuần 4 — Joints & Actuators

- [ ] Thêm 10 HingeJoint/RotationalMotor và PositionSensor.
- [ ] Unit radians; tên joint thống nhất; giới hạn min/max và maxVelocity.
- [ ] Tạo controller `stand_neutral`: đưa tất cả motor về home pose có ramp.
- [ ] Test từng joint một không tạo torque phi thực tế hoặc collision.

**DoD:** từng khớp hoạt động đúng trục, pose định trước lặp lại được.

### Tuần 5 — Physics & Sensors

- [ ] Chốt khối lượng link, collision feet, friction/contact.
- [ ] Thêm InertialUnit, Gyro/Accelerometer (nếu cần), DistanceSensor front, Camera.
- [ ] Tạo logger CSV cho roll/pitch, motor targets/positions, khoảng cách.
- [ ] Tạo test reset reproducible để 5 lần chạy cùng điều kiện.

**DoD:** sensor có dữ liệu hợp lý, robot không bốc bay/trôi xuyên sàn.

### Tuần 6 — Stand Pose

- [ ] Thiết kế stand sequence: crouch → neutral/stand.
- [ ] Chuyển pose bằng interpolation có giới hạn tốc độ.
- [ ] Dùng góc tilt để phân loại STABLE/UNSTABLE/FALL.
- [ ] Ghi log 5 trial × 30 s.

**DoD:** đạt ít nhất 4/5 trial đứng 30 s (không tác động bên ngoài) hoặc có báo cáo root cause.

### Tuần 7 — Weight Shift

- [ ] Điều khiển hip roll và ankle roll để chuyển trọng tâm về chân trụ.
- [ ] Nâng thử một chân nhỏ trên giá trong sim mà không gây ngã.
- [ ] Xác minh vị trí COM và support polygon (phân tích xấp xỉ).

**DoD:** nâng chân có kiểm soát trong thời gian ngắn, log trọng tâm/tilt.

### Tuần 8 — Balance Revision

- [ ] Thử 3 điều kiện: neutral, lệch tư thế nhẹ, sensor noise có giới hạn.
- [ ] Tuning feedback/PID theo dữ liệu, phân tích overshoot.
- [ ] Safety stop khi vượt góc tilt; không tự viết gait trước khi stand đạt gate.

**DoD:** báo cáo baseline và các điều kiện thất bại, khóa thông số v0.1.

### Tuần 9 — Gait Phase Machine

- [ ] Định nghĩa 6 phase: double support, shift left, swing right, double support, shift right, swing left.
- [ ] Tạo offline joint trajectories không đột ngột; plot góc/tốc độ.
- [ ] Chuyển mô phỏng bằng vận tốc rất thấp và hỗ trợ khi cần.

**DoD:** gait đi qua 6 phase không vượt joint limits.

### Tuần 10 — One-step Test

- [ ] Thử 1 bước thực trong mô phỏng, đo tiến độ cm và nghiêng.
- [ ] Ghi collision/contacts trái-phải, nhận biết chân nào chịu tải.
- [ ] Điều chỉnh thân và góc mắt cá phù hợp.

**DoD:** 1 bước có dịch chuyển thân thực, không chỉ tay chân múa tại chỗ.

### Tuần 11 — Repeated Steps

- [ ] Mở rộng 3–5 bước liên tiếp, giới hạn vận tốc.
- [ ] Dùng state transition chứ không dùng sleep chặn controller.
- [ ] Ghi success rate trên ≥10 thử nghiệm.

**DoD:** 5 bước liên tục trong trường hợp ổn định; nếu thất bại, phân tích nguyên nhân và lặp lại tuần.

### Tuần 12 — Walk Benchmark

- [ ] Benchmark step length, gait cycle time, fall rate, root causes.
- [ ] Test thay đổi nhẹ ma sát/trọng lượng/độ trễ để ước lượng sim-to-real.
- [ ] Freeze gait v0.1 và video minh chứng.

**DoD:** báo cáo kết quả và giới hạn ở điều kiện nào gait thành công.

### Tuần 13 — Obstacle Stop

- [ ] Tạo obstacle tại các khoảng cách 20, 30, 50 cm.
- [ ] `DistanceSensor` với threshold dừng bảo thủ, thêm hysteresis/filter.
- [ ] Test STOP ưu tiên mọi WALK/AI command.

**DoD:** không chạm vật cản trong set kịch bản được định nghĩa, kể cả khi lệnh WALK tiếp tục gửi.

### Tuần 14 — Avoidance

- [ ] Điều kiện rẽ khi biped hiện tại chưa có hip yaw: quay bằng các bước đổi hướng nhỏ **nếu gait support**; nếu không hỗ trợ, chỉ STOP và yêu cầu kế hoạch mới.
- [ ] Tạo state machine WALK / OBSTACLE / WAIT / TURN / RESUME.
- [ ] Bỏ qua lệnh không hợp lệ, timeout state.

**DoD:** avoidance không tự giả định robot có thể xoay tại chỗ một cách an toàn.

### Tuần 15 — Behavior Tests

- [ ] Các scenario: lối trống, vật cản đột ngột, sensor mất dữ liệu, ngã, E-STOP.
- [ ] Lập bảng transition priorities và regression tests.
- [ ] Video demo M1 kèm dữ liệu định lượng.

**DoD:** simulation MVP review thành công.

### Tuần 16 — Physical Procurement Gate

- [ ] Rà danh sách mua sau khi tính torque; thử một servo đích.
- [ ] Chọn nguồn 5–6V với current budget, bảo vệ và E-STOP.
- [ ] Thiết kế jig/gia đỡ chân; hoàn thiện schematic và wiring checklist.

**DoD:** có BOM cuối, danh sách chưa đủ tiền và phương án thu gọn scope.

### Tuần 17 — Arduino Servo Driver

- [ ] Uno + PCA9685 kiểm thử trên bàn, cấp điện cho servo từ nguồn ngoài.
- [ ] Lệnh serial có checksum, sequence number, bounds, timeout.
- [ ] Firmware watchdog và test disconnection.

**DoD:** một servo chạy các góc cho phép liên tục, không reset MCU, stop hoạt động.

### Tuần 18 — Calibrate Multi-joint

- [ ] Calibrate từng servo, đo min/max/neutral; tránh kẹt cơ khí.
- [ ] Nối nhiều servo tăng dần, kiểm tra dòng đỉnh và nhiệt.
- [ ] Lưu calibration theo serial/ID thực tế nếu có.

**DoD:** không va chạm cơ khí và không brownout ở bài kiểm thử đã xác định.

### Tuần 19 — Assemble Supported Frame

- [ ] Lắp khung trong giá đỡ/treo có bảo hộ, không để robot rơi.
- [ ] Benchmark joint target vs observed motion, servo backlash và latency.
- [ ] Điều chỉnh giới hạn vận tốc theo phần cứng.

**DoD:** stand pose trên giá đỡ, nguồn an toàn, có người giám sát.

### Tuần 20 — Supported Standing

- [ ] Cố gắng đứng có hỗ trợ từng phần, đo điểm mất cân bằng.
- [ ] So sánh mô phỏng với thực tế: COM, độ cứng khung, servo torque.
- [ ] Tuning nếu cần; chưa tháo giá khi stand không ổn định.

**DoD:** trạng thái/giới hạn rõ ràng, không tuyên bố tự đứng khi còn dựa hoàn toàn vào giá đỡ.

### Tuần 21 — Supported Stepping

- [ ] Thử chuyển trọng lượng và một bước với dây bảo hộ.
- [ ] Kiểm tra độ nóng, sụt nguồn và stop behavior.
- [ ] Lặp lại nhiều trial cùng kịch bản.

**DoD:** có số liệu số bước thành công và thất bại; E-STOP thử thật.

### Tuần 22 — Sim-to-Real Reconciliation

- [ ] Calibrate lại mô hình Webots theo cân nặng/cấu trúc thực tế.
- [ ] Điều chỉnh gait và rate limits, tạo báo cáo delta.
- [ ] Nếu không đủ khả năng đi, ghi thay đổi cần thiết về cơ khí/servo.

**DoD:** có mục `sim_to_real_report.md` và roadmap sửa bản H25.1.

### Tuần 23 — Local Autonomy

- [ ] Host Python đọc serial+sensor, cập nhật local state.
- [ ] Điều khiển bounded exploration trong Webots: vùng cho phép, waypoint đơn giản, local obstacle stop.
- [ ] AI adapter trước tiên là mock deterministic.

**DoD:** exploration chạy không cần API cloud; mất mạng không gây chuyển động không kiểm soát.

### Tuần 24 — AI Integration & Release Review

- [ ] AI API chỉ trả structured high-level intent; parser validate và permission gate.
- [ ] Test AI timeout, câu trả lời sai schema, `STOP`, không có camera, mất Internet.
- [ ] Release checklist M1/M2/M3; phân biệt test chạy sim và thật.
- [ ] Chốt next release: head camera, arm manipulation, improved navigation, LiDAR/ToF, computer on board.

**DoD:** không lệnh AI nào làm bypass physical safety. Báo cáo sản phẩm và những hạn chế được ghi rõ.

## 4. Thước đo và tiêu chí nghiệm thu

| Nhóm | KPI thử nghiệm đầu tiên | Cách đo |
|---|---|---|
| Physics | 10 joint có giới hạn và collision | motor logs + visual inspection |
| Standing | ≥4/5 lần đứng 30 s trên nền chuẩn | 5 trials độc lập |
| Walking | ≥5 bước liên tục trong sim | COM displacement, chân tiếp xúc |
| Fall recovery | Phát hiện và STOP an toàn | fault injection |
| Obstacle stop | Trước vật cản trong test setup | min distance trên logs |
| Watchdog | mất heartbeat -> safe state | ngắt serial giả lập / thật |
| AI boundary | 100% bad intent bị reject trong unit tests | valid/invalid payload suite |
| Physical electrical | không brownout/quá nhiệt ở test load | multimeter, nhiệt + log |
| Reproducibility | script, version, config, seed được lưu | run_id + artifacts |

Các KPI này là **mục tiêu đặt ra**, không phải kết quả đã đạt.

## 5. Dự toán phần cứng ban đầu (VNĐ, chưa phải báo giá)

| Hạng mục | Khoảng dự trù | Ghi chú |
|---|---:|---|
| Servo x 10 | 900.000–2.000.000+ | Phụ thuộc torque/độ bền, servo tốt có thể đắt hơn nhiều |
| PCA9685 | 60.000–140.000 | Kiểm tra hàng và mức logic |
| IMU MPU6050 hoặc tương đương | 40.000–100.000 | Dùng nếu chưa có |
| Cảm biến khoảng cách | 30.000–180.000 | Ultrasonic rẻ, ToF ổn định hơn trong vài trường hợp |
| Khung + gá + ốc vít | 300.000–700.000 | Giá in 3D ngoài có thể chênh lệch |
| Nguồn, dây, cầu chì, công tắc, phụ kiện | 250.000–550.000 | Chọn theo dòng tổng, không tiết kiệm ở an toàn |
| Dự phòng hỏng/thay | 200.000–400.000 | Nên có |
| **Tổng khả dĩ** | **1.780.000–4.070.000+** | Chưa gồm camera, board AI onboard và công cụ |

**Cách giữ mục tiêu 3 triệu:** không mua PC nhúng; dùng PC đang có, dùng Uno hiện có, tận dụng sensor có sẵn, khung nhẹ, làm testbench từ 2–4 servo trước. Không hy sinh torque, nguồn và E-STOP chỉ để đủ số servo.

## 6. Dependency và quyết định mua

```text
Inventory -> CAD -> mass estimate -> joint torque estimate
                     |
                     v
                Servo bench test
                     |
                     v
                Servo selection
                     |
                     v
        Power sizing + E-STOP design
                     |
                     v
             Complete physical BOM
                     |
                     v
             Assembly and calibration
```

Không đổi thứ tự để tránh trường hợp mua 10 servo rồi không đủ mô-men tại hông/gối. Khi mỗi servo có stall/current draw khác nhau, lựa chọn rail nguồn phải dựa vào peak load estimate cộng đo test.

## 7. Risk Register

| Rủi ro | Xác suất/ảnh hưởng | Giảm thiểu |
|---|---|---|
| Servo không đủ torque | Cao/Cao | torque budget, test 1 joint, giảm khối lượng |
| Nguồn sụt reset Arduino | Cao/Cao | nguồn servo riêng, chung GND, đo dòng đỉnh |
| Robot ngã vỡ khung | Cao/Trung bình | harness/rig, thử supported trước |
| Gait trong sim không chạy thật | Cao/Cao | sim-to-real tests, friction/backlash/latency |
| Ultrasonic không đủ mapping | Cao/Trung bình | thừa nhận giới hạn; nâng cấp perception đúng giai đoạn |
| Cloud API chậm hoặc lỗi | Trung bình/Cao | offline fallback, bounded intents, timeout |
| Dữ liệu camera riêng tư | Trung bình/Cao | consent, minimal retention, redaction |
| Budget vượt 3 triệu | Cao/Trung bình | staged purchases, gate rõ ràng |

## 8. Nhật ký thí nghiệm

Mỗi thử nghiệm có:

```yaml
run_id: sim-stand-0001
build_commit: <git-sha>
software_versions:
  webots: R2025a # ví dụ: thay bằng bản đã cài
robot: RL-H25-v0.1
scenario: stand_30s
floor: flat
mass_model: <link>
config_file: configs/robot.yaml
start_pose: crouch
expected: stand for 30 seconds
result: pass_or_fail
metrics:
  duration_s: null
  max_abs_roll_deg: null
  max_abs_pitch_deg: null
  fall_events: null
notes: <facts only>
```

## 9. Checklist ra quyết định trước mỗi release

- [ ] Có thể tái chạy tất cả test trong cùng môi trường?
- [ ] Các mô hình chân và servo thực tế khớp config?
- [ ] Safety priority được kiểm tra với AI/network offline?
- [ ] Nguồn và E-STOP được thử dưới tải?
- [ ] Các giới hạn và kịch bản thất bại đã ghi rõ?
- [ ] Có log, video/trích số liệu cho mọi tuyên bố khả năng?
- [ ] Budget còn đủ cho rủi ro tiếp theo?
- [ ] Người vận hành duyệt trước khi mở chế độ vật lý rủi ro hơn?

## 10. Bắt đầu ngay hôm nay: Session 01

**Mục tiêu 90–120 phút:** hoàn thành foundation, chưa mua gì.

1. Tạo repository `robotis-lab` và cấu trúc thư mục.
2. Cài bản Webots ổn định (theo trang releases chính thức), Python 3 và Git.
3. Viết danh sách linh kiện thực có: tên, số lượng, điện áp, chân, tình trạng.
4. Tạo `docs/architecture/requirements.md` với định nghĩa RL-H25, hai chân, 10 DOF, sàn 2 m × 2 m, 3 triệu, PC-host.
5. Tạo `tasks/backlog.md` từ lịch 24 tuần, gắn nhãn P0/P1/P2, dependencies.
6. Ghi quyết định `ADR-0001`: Simulation-first; AI is not in real-time control loop.
7. Chạy Webots example robot có sẵn trước khi tự tạo PROTO; chụp log vận hành.

**Output của Session 01:** `requirements.md`, `inventory.md`, `ADR-0001.md`, project tree và danh sách blocker.

## 11. Các câu hỏi cần quyết định trong phase P0

- Máy tính đang dùng chạy hệ điều hành nào và cấu hình phần cứng ra sao?
- Có máy in 3D, được thuê in, hay cần làm gá bằng vật liệu khác?
- Chính xác có bao nhiêu servo, chủng loại, nguồn, module và cảm biến trong hộp linh kiện?
- Robot cần tự đi không giá đỡ ngay phiên bản 1 hay chấp nhận đi có giá đỡ để học và kiểm chứng?
- Dự toán 3 triệu là mức trần tổng chi hay ngân sách cho prototype đầu tiên (có thể nâng sau)?

Các câu hỏi này quan trọng cho mua hàng, **không cản trở** triển khai giai đoạn mô phỏng.

## 12. Đường dẫn tham khảo kỹ thuật

- Webots official release: https://github.com/cyberbotics/webots/releases
- Webots controller programming: https://github.com/cyberbotics/webots/blob/master/docs/guide/controller-programming.md
- Webots sensors: https://github.com/cyberbotics/webots/blob/master/docs/guide/sensors.md
- Adafruit PCA9685 servo power: https://learn.adafruit.com/16-channel-pwm-servo-driver/hooking-it-up
- OpenAI vision guide: https://developers.openai.com/api/docs/guides/images-vision

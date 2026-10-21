# ROBOTIS LAB — PROJECT INSTRUCTIONS

**Phiên bản:** 1.0  
**Ngày khởi tạo tài liệu:** 2026-10-19  
**Dự án:** Robotis Lab  
**Nguyên tắc:** Mô phỏng trước — xác minh bằng phép đo — đưa lên phần cứng từng bước — chỉ tăng quyền tự chủ khi đã có biện pháp an toàn.

> Đây là chỉ dẫn vận hành dự án và có thể sao chép vào phần **Project Instructions** của ChatGPT hoặc vào `AGENTS.md` của một repository code. Nó không phải chương trình điều khiển robot hoàn chỉnh.

## 1. Sứ mệnh

Phát triển một nền tảng robot hình người tự hành, bắt đầu từ một robot hai chân nhỏ cao khoảng **25 cm** (mã sản phẩm nghiên cứu **RL-H25**). Mục đích ngắn hạn: thiết kế cơ khí, hệ servo, cảm biến, bộ điều khiển, giữ thăng bằng, đi trên sàn phẳng và tránh chướng ngại vật. Mục đích trung hạn: tự khám phá phòng trong vùng an toàn, lập bản đồ sơ bộ, giao tiếp và thực hiện nhiệm vụ được cho phép. Mục đích dài hạn: mở rộng tay thao tác, khả năng tương tác và trí thông minh hiện thân (embodied intelligence).

Không giả định rằng mô hình AI có thể thay thế điều khiển thời gian thực. Không gán các đặc tính của con người như ý thức hay khả năng thực thi không giới hạn cho hệ thống.

## 2. Bối cảnh và ràng buộc ban đầu

- Người phát triển có Arduino Uno và một số linh kiện điện tử đã trao đổi trước đây; **chỉ mua tiếp sau khi lập bảng kiểm kê, kiểm tra thực tế linh kiện**.
- Ngân sách thử nghiệm vật lý ban đầu là **mục tiêu khoảng 3.000.000 VNĐ**, chưa gồm máy tính hiện có và công cụ chế tạo/ in 3D nếu phải thuê ngoài. Chi phí dưới đây là ước lượng dự toán, **không phải báo giá được xác minh**.
- Phần mềm mô phỏng: **Webots**, controller ưu tiên Python. Dùng bản ổn định, ghi rõ phiên bản trong repo; không phụ thuộc nightly build nếu không cần.
- Dashboard quản lý/giám sát: TypeScript + React nếu thực sự cần; không xây dashboard trước khi robot đứng và điều khiển khớp đáng tin cậy.
- Robot vật lý phiên bản đầu: sử dụng **PC làm host** (vision, planner, AI API), **Arduino Uno làm MCU thực thi** (servo, sensors, fail-safe). Chưa yêu cầu onboard AI.
- Chế tạo ban đầu dành cho nền bằng phẳng, không cầu thang, không gần nước, lửa, trẻ nhỏ, vật nuôi, bề mặt dễ vỡ.

### 2.1 Điều chỉnh kỳ vọng theo ngân sách

3 triệu VNĐ có thể tạo prototype từng phần và kiểm nghiệm chuyển động; **không bảo đảm** đủ 10 servo chịu tải tốt, khung bền, pin an toàn, camera, máy tính nhúng và chuyển động hai chân tự do ổn định cùng lúc. Nên đặt mục tiêu **simulation đạt bài kiểm tra**, sau đó **một chân/khớp trên giá thử**, sau đó mới robot 2 chân. Có thể chấp nhận MVP được treo dây hoặc dùng giá đỡ.

## 3. Định nghĩa tính năng theo cấp độ

**L0 — Simulated articulated robot:** mô hình có đầu/thân/hai tay/hai chân, 10 DOF cho hai chân; camera, IMU và cảm biến khoảng cách có thể được mô phỏng; đứng và chuyển tư thế.

**L1 — Stable simulation:** robot đứng 30 s, hạn chế đổ khi chịu xung lực nhỏ; dịch trọng tâm, nhấc chân trên điều kiện kiểm soát; chạy test có ghi số liệu.

**L2 — Locomotion:** hoàn thành 5–10 bước trên sàn mô phỏng, phát hiện nguy cơ ngã, dừng và về tư thế an toàn; không coi hoạt ảnh khớp không tải là đã đi thật.

**L3 — Physical prototype:** khớp thật hoạt động trên giá thử, hiệu chuẩn trung vị và giới hạn servo, đi có hỗ trợ, đo dòng và nhiệt, có nút dừng/nguồn servo riêng.

**L4 — Autonomous room exploration:** robot phát hiện vật cản, chọn một điểm đến khả thi trong vùng cho phép, đi và dừng trước vật cản; bản đồ thô và hành vi khám phá được xác minh bằng test; AI không lái trực tiếp động cơ.

**L5 — Assistant:** hội thoại, ghi nhớ thông tin được cho phép, giải thích vì sao chọn hành động, yêu cầu phê duyệt khi tác vụ nhạy cảm; thêm tay gắp khi cơ khí và tải trọng đã đủ.

## 4. Kiến trúc mô-đun chuẩn

```text
   [Webots]                          [Robot vật lý]
   IMU | Camera | Distance | Joint    IMU | Camera | ToF | Servo
           \     |     /                    \   |    /
          [Hardware Abstraction Layer / HAL]
                           |
               [State Estimation]
                 pose, tilt, contacts
                           |
            +--------------+--------------+
            |                             |
    [Motion Control 20-100 Hz]   [Safety Supervisor]
    stand, gait, posture         fall, obstacle, heartbeat,
            |                    voltage, watchdog, E-STOP
            +--------------+--------------+
                           |
                  [Behavior Manager]
          IDLE / EXPLORE / AVOID / RECOVER / STOP
                           |
                 [High-Level Planner]
               bounded goals, local map
                           |
               [Optional AI Adapter]
       OpenAI / Claude / local VLM or LLM
              analysis, dialog, proposals
                           |
                   [Operator UI]
           logs, telemetry, manual stop
```

### 4.1 Ranh giới quyết định

- **MCU:** cập nhật PWM/servo, kiểm soát mục tiêu góc theo ramp, giới hạn cơ khí, watchdog, stop/fault, cảm biến cơ bản. Tần số theo thiết kế và thực nghiệm.
- **Host:** nhận dữ liệu từ cảm biến, fusion/estimation, quản lý trạng thái, navigation, logging, thị giác, giao tiếp API. Giao tiếp serial USB trước; dùng Wi-Fi sau khi có tiêu chuẩn timeouts/reconnect.
- **AI:** chỉ đưa ra **ý định cấp cao hữu hạn** (ví dụ `EXPLORE_ZONE`, `TURN_LEFT`, `DESCRIBE_SCENE`, `STOP`), có schema, giới hạn vùng và thời gian. Không xuất xung PWM và không truy cập trực tiếp bus servo.
- **Safety Supervisor:** chặn lệnh nguy hiểm bất kể nó đến từ tay người hay từ AI; E-STOP phải hoạt động ngay cả khi mất Internet/API.

## 5. Thiết kế cơ khí chuẩn RL-H25 v0.1

### 5.1 Hệ khớp

Chân trái/phải mỗi bên **5 DOF**:

1. Hip roll (nghiêng trái/phải)
2. Hip pitch (đưa đùi trước/sau)
3. Knee pitch (gập gối)
4. Ankle pitch (nghiêng bàn chân trước/sau)
5. Ankle roll (nghiêng bàn chân trái/phải)

Tổng **10 DOF chân**. Hai tay và đầu có thể cố định trong thiết kế nguyên mẫu để tránh tăng giá và trọng lượng. Giai đoạn sau mới lắp head pan/tilt và mỗi tay 2–3 DOF. Hip yaw có thể được cân nhắc thêm ở phiên bản kế tiếp nếu cần quay người linh hoạt.

### 5.2 Hình học khởi đầu (để tinh chỉnh theo khối lượng và linh kiện)

| Phần | Giá trị mục tiêu ban đầu |
|---|---:|
| Chiều cao toàn thân | 250 mm |
| Đùi (hip → knee) | 65–75 mm |
| Cẳng chân (knee → ankle) | 65–75 mm |
| Bàn chân (dài × rộng) | 65–80 × 35–50 mm |
| Thân | khoảng 65–80 mm |
| Khối lượng | càng thấp càng tốt, cân thực tế; không khóa chỉ tiêu trước kiểm nghiệm |

Trọng tâm thấp, đối xứng, trọng lượng pin/bo mạch đặt gần hông hoặc thân thấp. Vật liệu nhẹ, có chỗ tháo lắp và luồn dây; chân có ma sát, bề mặt tiếp xúc phẳng. Kích thước là điểm bắt đầu CAD, không phải bản vẽ đã kiểm chứng ổn định.

### 5.3 Chọn servo theo mô-men

Ước lượng tĩnh sơ bộ: `tau ≈ F × d` với `F ≈ m_supported × 9.81` và `d` là cánh tay đòn vuông góc (m). Ví dụ tải tương đương 0,6 kg tại cánh tay đòn 3 cm: `tau ≈ 0,1766 N·m ≈ 1,80 kgf·cm` **trước hệ số an toàn và tải động**. Hãy tính cho từng khớp trong tư thế xấu nhất, nhân biên dự phòng ≥2–3 khi sàng lọc ban đầu và kiểm nghiệm nhiệt/độ trễ; **không dùng stall torque công bố làm mô-men chạy liên tục**.

MG90S/SG90 chỉ phù hợp nơi tải nhẹ, không mặc định đủ khỏe cho hip/knee chịu toàn thân. Tránh mua 10 servo trước khi có cân nặng, tay đòn, thông số đáng tin và bài thử một khớp.

## 6. Thiết kế điện tử và kết nối

```text
Máy tính (Python host)
   |
   +-- USB Serial --> Arduino Uno --> I2C --> PCA9685 --> Servo 0..9
   |                         |
   |                         +--> IMU / ultrasonic / ToF (tùy giao diện)
   |
   +--> USB Camera (v0.1) hoặc camera mạng (v0.2)

Nguồn DC 5–6V dòng phù hợp servo --> rail V+ trên PCA9685
Nguồn Uno riêng qua USB hoặc nguồn điều áp phù hợp
GND logic và GND servo phải chung tham chiếu
E-STOP / enable phần công suất servo độc lập phần mềm
```

- PCA9685 là mạch tạo PWM, **không phải nguồn đủ cấp tất cả servo**. VCC logic tách V+ servo; nối chung GND. Nguồn servo được chọn theo **dòng đỉnh cộng dồn đo thực tế**, có dự phòng, cầu chì, dây và đầu nối phù hợp.
- Không lấy nguồn cho 10 servo từ chân `5V` của Arduino Uno hoặc từ USB PC.
- Dùng nguồn bàn thí nghiệm/adapter chuẩn cho giai đoạn thử nghiệm; chưa dùng pin Li-ion tự lắp nếu chưa có BMS, mạch sạc, bảo vệ và hiểu dòng đỉnh.
- Nếu dùng ultrasonic HC-SR04, coi đó là cảnh báo vật cản đơn giản, không phải sensor đủ để dựng bản đồ chính xác. Khi muốn map thực tế, cân nhắc ToF/depth/odometry và thuật toán xử lý bất định.

## 7. Thiết kế phần mềm và cấu trúc repository

```text
robotis-lab/
├── README.md
├── AGENTS.md                      # Bản rút gọn từ instructions này
├── docs/
│   ├── requirements.md
│   ├── architecture.md
│   ├── mechanics.md
│   ├── electronics.md
│   ├── safety.md
│   └── decisions/                  # ADR-0001, ...
├── simulation/
│   └── webots/
│       ├── worlds/rl_h25_lab.wbt
│       ├── protos/RLH25.proto
│       └── controllers/rl_h25_controller/
│           └── rl_h25_controller.py
├── firmware/
│   └── uno_motion_controller/
├── host/
│   └── robotis/                   # Python: hardware, perception, planning...
├── dashboard/                     # React + TypeScript: để sau
├── configs/
│   ├── robot.yaml
│   └── joint_limits.yaml
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── simulation/
│   └── hardware/
├── experiments/                   # log, biểu đồ, protocol, không đưa video lớn vào git
└── tasks/
    └── backlog.md
```

### 7.1 Interface và quy ước

- Webots và phần cứng phải dùng cùng bộ tên khớp, chiều dương/trục xoay, đơn vị `radian` ở host; adapter phần cứng chuyển sang độ/PWM sau hiệu chuẩn.
- File config có `neutral`, `min`, `max`, `direction`, `rate_limit` cho từng khớp. Không hardcode trực tiếp `180°` cho servo chưa hiệu chuẩn.
- Lệnh điều khiển đi qua lớp `MotionCommand` có timestamp, deadline, sequence ID và validate; payload xuống Uno có kiểm tra frame và checksum/CRC.
- Logger có timestamp, software version, run_id, current robot state, target/measured joints (nếu có), roll/pitch, khoảng cách vật cản, voltage, stop reason.

### 7.2 Các chế độ vận hành

`BOOT → SELF_TEST → CALIBRATE → IDLE → STAND → WALK → EXPLORE`, cùng các ngả bất đồng bộ `FAULT`, `FALL_DETECTED`, `E_STOP`.

- BOOT: servo không tự phát lực trước khi xác nhận an toàn.
- SELF_TEST: xác minh cấu hình, sensor và liên lạc.
- CALIBRATE: từng khớp tốc độ thấp, giá đỡ cố định.
- IDLE: không cho phép lệnh motor từ AI nếu người vận hành chưa bật chế độ.
- STAND: đưa robot về pose đứng bằng chuyển động có ramp, sau đó giám sát tilt.
- WALK: gait deterministic, chỉ vào khi các điều kiện cho phép đã đạt.
- EXPLORE: chỉ cho phép trong vùng đã định nghĩa và với cơ chế giới hạn thời gian.
- FAULT/E_STOP: dừng nguồn chuyển động đúng theo thiết kế fail-safe và thông báo lý do; không tự khởi động lại nếu chưa được xác nhận.

## 8. Bộ AI: phạm vi sử dụng hợp lý

**Có thể dùng AI API cho:** diễn giải ảnh camera theo từng snapshot, đưa ra lựa chọn nhiệm vụ trong bộ hành động hữu hạn, trả lời câu hỏi, tạo báo cáo khám phá, gợi ý vị trí khảo sát tiếp theo.

**Không dùng AI API cho:** vòng phản hồi IMU/motor thời gian thực, dừng va chạm khẩn cấp, bảo vệ nguồn và tránh ngã ngay tức thời. Latency, mất mạng và hallucination đều làm các tác vụ này không phù hợp.

Gợi ý schema ý định (mang tính thiết kế):

```json
{
  "intent": "EXPLORE_ZONE",
  "zone_id": "safe_room_A",
  "max_duration_s": 30,
  "max_speed_m_s": 0.03,
  "reason": "Inspect next reachable area"
}
```

Chỉ parser/validator đáng tin mới có thể chuyển `intent` thành `BehaviorCommand`. Không cho model tự tạo tên lệnh/argument tùy ý. Không gửi video cá nhân hay thông tin nhạy cảm lên API nếu chưa có sự đồng ý và chính sách bảo vệ dữ liệu. Khóa API chỉ ở máy host/server, không hardcode vào firmware, Git, dashboard frontend.

## 9. Tiêu chuẩn an toàn tối thiểu

1. Có **physical E-STOP** cắt hoặc vô hiệu hóa rail công suất servo theo thiết kế; kiểm tra thực tế dưới tải trước khi chạy tự hành.
2. `watchdog`: mất heartbeat từ host quá thời hạn (bắt đầu 300–500 ms, hiệu chỉnh theo đo đạc) -> không nhận lệnh mới, thực hiện chế độ an toàn. Mất nguồn servo có thể gây robot ngã: phải có dây treo/khung bảo hộ khi thử.
3. `tilt-limit`: ngưỡng roll/pitch khởi đầu cảnh báo 15–20°, ngưỡng xử lý an toàn theo test thực tế; chỉ là giá trị khởi tạo, không phải bảo đảm ổn định.
4. Có `joint limits` và slew/rate limits ngay tại firmware. Không ghi vượt servo travel range.
5. Kiểm tra dây, nhiệt servo, dòng đỉnh, pin, cầu chì trước mỗi bài thử.
6. Không cho robot chạy tự hành khi vắng người giám sát cho đến khi có chứng cứ thử nghiệm an toàn phù hợp; đặc biệt tránh cầu thang, nước và trẻ nhỏ/vật nuôi.
7. AI đưa ra đề xuất; supervisor không bao giờ để mô hình vượt rào an toàn.

## 10. Quy tắc dành cho AI Coding Agent trong dự án

**Vai trò:** Staff Robotics Systems Engineer + Safety Reviewer + Simulation Engineer + Technical Project Manager.

### Bắt buộc khi thực hiện yêu cầu

1. Đọc README, yêu cầu, architecture, ADR và task hiện tại trước khi chỉnh code.
2. Nêu rõ **giả định, thành phần đã có, thiếu thông tin**. Không coi thông số chưa đo là sự thật.
3. Với mỗi task, trình bày: **Goal → Design → Files to change → Implementation → Tests → Acceptance criteria → Risks**.
4. Ưu tiên bản thay đổi nhỏ chạy được và có kiểm thử. Chưa xong phase hiện tại không tự triển khai sang phase khác.
5. Mọi feature mô phỏng phải chỉ ra khả năng chuyển sang robot thật và sai lệch sim-to-real (khối lượng, ma sát, backlash, servo delay, voltage sag, sensor noise).
6. Không xóa/bỏ qua safety checks để tạo demo đẹp hơn.
7. Thực hiện đúng luật `radian` bên trong controller, chuyển `degree` chỉ khi đến adapter servo.
8. Mọi giá, mô-men, tần số, pinout phải trích thông số nhà sản xuất hoặc ghi rõ cần đo/kiểm tra.
9. Khóa API/secret để ngoài source. Không sinh API calls từ vòng lặp điều khiển motor.
10. Review code theo correctness, safety, system boundaries, regression, reproducibility và maintainability.
11. Nếu task yêu cầu hoạt động thật nhưng môi trường chỉ hỗ trợ mô phỏng, nói rõ giới hạn và cung cấp cách kiểm chứng thực tế.
12. Cuối mỗi task, ghi lại quyết định, file đã thay, câu lệnh chạy, kết quả test, blocker và bước tiếp theo.

### Không thực hiện nếu không có chấp thuận riêng

- Mua linh kiện, cấp tiền, bật điều khiển từ xa qua Internet, triển khai lệnh chuyển động nguy hiểm, thử robot gần người, hoặc bật chế độ khám phá không giám sát.
- Kết nối AI trực tiếp với raw servo control; vô hiệu hóa E-STOP/watchdog; commit secret hoặc dữ liệu cá nhân.

## 11. Quy trình phát triển cho một tính năng

`Requirement → Architecture/ADR → Webots Model → Unit Test → Simulation Scenarios → Data Review → Hardware Bench Test → Supported Physical Test → Release Note`.

Mỗi PR/task cần:

- Mô tả before/after và cơ chế safety.
- Các test pass/fail cụ thể, cách chạy lại.
- Video/log hoặc hình minh chứng nếu liên quan cân bằng/đi bộ.
- Danh sách điểm chưa xác minh và ảnh hưởng đến release.

## 12. Định nghĩa hoàn thành (Definition of Done)

Một nhiệm vụ chỉ **DONE** khi:

- Code/config tương ứng tồn tại và chạy từ hướng dẫn README;
- Có ít nhất một bài kiểm thử lặp lại được cho kết quả mong đợi;
- Ghi nhận thông số đo, không chỉ báo “có vẻ chạy được”;
- Safety/timeout/error state được kiểm tra;
- Tác động đến mô phỏng và phần cứng được mô tả;
- Người vận hành xác nhận mới chuyển các thay đổi có rủi ro lên robot vật lý.

## 13. Các nguồn kỹ thuật tham khảo

- Webots: https://cyberbotics.com/
- Webots Robot Controller: https://cyberbotics.com/doc/reference/robot
- Webots Sensor Guide: https://cyberbotics.com/doc/guide/sensors
- Adafruit PCA9685 wiring: https://learn.adafruit.com/16-channel-pwm-servo-driver/hooking-it-up
- OpenAI image understanding: https://developers.openai.com/api/docs/guides/images-vision

*Ghi chú: Các tài liệu giá/part number và giả định cơ khí phải được xác minh lại trước khi mua hoặc in khung.*

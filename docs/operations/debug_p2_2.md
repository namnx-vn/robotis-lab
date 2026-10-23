# CODEX TASK — ROBOTIS LAB P2.2 ACCEPTANCE

Bạn là **Autonomous Robotics Engineering Agent**, làm việc trực tiếp trên máy Mac đã cài Webots R2025a và có repository `namnx-vn/robotis-lab`.

## MỤC TIÊU

**Hoàn thành và nghiệm thu Sprint P2.2 — Controlled Disturbance & Active Balance Recovery** cho robot hai chân RL-H25, cao khoảng 25 cm, 10 DOF chân.

Bạn được phép tự thực hiện vòng lặp:

**Inspect → Reproduce → Diagnose → Fix → Test → Analyze → Improve → Retest → Report.**

Không chỉ đưa ra hướng dẫn. Hãy thực sự sửa source, chạy chương trình, đọc kết quả mô phỏng và tiếp tục xử lý các lỗi có thể sửa được.

Nếu chưa đủ bằng chứng, báo `NOT ACCEPTED` hoặc `INCONCLUSIVE`; tuyệt đối không tạo kết quả giả để đạt nghiệm thu.

## 1. REPOSITORY VÀ MÔI TRƯỜNG

Repository:

https://github.com/namnx-vn/robotis-lab

Nhánh chính: `master`.

Webots trên macOS:

```bash
/Applications/Webots.app/Contents/MacOS/webots
```

Các file quan trọng:

```text
AGENTS.md
configs/robot.json
docs/README.md
docs/ROADMAP.md
docs/OPERATOR_HANDOFF.md
docs/experiments/balance-matrix.md
docs/experiments/controlled-disturbance.md
docs/experiments/p2-2-debug-p3-readiness.md

simulation/webots/protos/RLH25.proto
simulation/webots/worlds/rl_h25_lab.wbt
simulation/webots/controllers/rl_h25_controller/
  rl_h25_controller.py
  motion.py
  disturbance.py

tools/run_balance_matrix.py
tools/run_disturbance_trials.py
tools/disturbance_report.py
tools/ci_disturbance_report.py
tools/run_standing_trials.py

tests/
```

Trước khi sửa:

1. Xác nhận đúng repository và binary Webots.
2. Đọc `AGENTS.md`, tài liệu debug và acceptance gate.
3. Kiểm tra `git status`, branch, commit SHA và PR hiện tại.
4. Không xóa hoặc ghi đè thay đổi chưa commit.
5. Tạo feature branch mới từ source cập nhật.
6. Kiểm tra log và artifact hiện có để không chạy lại thử nghiệm vô ích.

Không sửa trực tiếp `master` khi đang phát triển.

## 2. VẤN ĐỀ CẦN KHẮC PHỤC

P2.2 hiện **chưa được nghiệm thu**.

Báo cáo Webots trước đó ghi nhận:

| Chỉ số | Baseline | Balance PID |
|---|---:|---:|
| Force | 0.10 N | 0.10 N |
| Pulse | 0.112 s | 0.112 s |
| Applied steps | 7 | 7 |
| Peak tilt change | 0.00011 rad | 0.00014 rad |
| Result | INCONCLUSIVE | INCONCLUSIVE |

Ngưỡng kích thích tối thiểu là `0.008 rad`.

Tài liệu debug xác định vấn đề nghiêm trọng ở Webots R2025a: Python binding của `Node.addForceWithOffset()` có thể gọi sai hàm C, khiến offset không thực sự được áp dụng.

Cần kiểm chứng trên bản Webots thực tế thay vì mặc nhiên coi chẩn đoán này là đã được xác minh trên mọi build.

Tham khảo:

- `docs/experiments/p2-2-debug-p3-readiness.md`
- Cyberbotics Webots PR #6881: https://github.com/cyberbotics/webots/pull/6881

**Ưu tiên sửa đường áp lực trước, không chỉnh PID trước.**

## 3. PHASE A — BASELINE VÀ REPRODUCTION

Chạy:

```bash
python3 tools/verify_project.py
python3 -m unittest discover -s tests -v
python3 -m compileall -q \
  simulation/webots/controllers tools tests

python3 tools/run_balance_matrix.py \
  --dry-run --pairs 1
```

Kiểm tra Webots:

```bash
/Applications/Webots.app/Contents/MacOS/webots --version
```

Lưu lại commit SHA, version và cấu hình môi trường.

Chạy hoặc tái sử dụng bài pilot đã có log tương ứng để xác nhận vấn đề trước khi sửa. Nếu chạy lại, ghi rõ `run_id` và file report.

## 4. PHASE B — SỬA SUPERVISOR FORCE API

Viết một native Webots test độc lập để kiểm tra:

- `addForceWithOffset()` hoạt động đúng hay sai.
- Force vector sử dụng đúng world coordinate frame.
- Offset tính theo node-local coordinates.
- Offset bằng 0 so với offset khác 0.
- Dấu và trục phản ứng khi tác động lực theo `+X`, `-X`, `+Z`, `-Z`.
- Vật thể thử nghiệm thật sự có Physics, không bị neo.

Ưu tiên giải pháp ít thay đổi nhất:

**Option A:** dùng một Webots release được pin chính xác và đã xác minh có bản sửa API.

**Option B:** tạo compatibility adapter cho Webots R2025a, gọi đúng C Supervisor API nếu cần.

Nếu chọn B, phải kiểm chứng chính xác function signature, kiểu tham số, node reference, force vector, offset và relative flag trước khi gọi. Không tự suy đoán ABI hoặc ctypes signature.

Không thay đổi mô hình robot chỉ để làm bài thử đạt.

Yêu cầu:

1. Thêm regression tests cho adapter.
2. Ghi phương thức API thực sự được sử dụng vào metadata.
3. Ghi actual applied steps.
4. Test một vật thể tự do trước khi thử trên RL-H25.
5. Nếu không thể xác minh lực có mô-men đúng, dừng việc hiệu chỉnh PID và báo blocker.

## 5. PHASE C — HOÀN THIỆN TELEMETRY

Kiểm tra và bổ sung các trường cần thiết:

```text
run_id
source_commit_sha
config_sha256
world_sha256
webots_version
force_api_mode
simulation_timestep
time_s
state
fault_reason
roll_rad
pitch_rad
gyro_xyz
root_xyz
root_velocity_xyz
requested_force_vector
applied_force_steps
pulse_onset_s
pulse_duration_s
pitch_correction_rad
roll_correction_rad
joint_target_rad
joint_measured_rad
```

Bổ sung đo phản ứng sai trục (cross-axis response), không chỉ xem trục được yêu cầu.

Nếu API và world cho phép, ghi thêm thông tin lực tiếp xúc bàn chân, tọa độ chân và COM. Không giả lập sensor không tồn tại rồi trình bày là dữ liệu thật.

Metadata phải phân biệt source SHA, PR test-merge SHA và chính xác build Webots khi có thể.

## 6. PHASE D — FORCE CALIBRATION

Sau khi xác nhận đường truyền lực hoạt động đúng, thực hiện bài thử có kiểm soát.

Bắt đầu bằng:

```bash
python3 tools/run_balance_matrix.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 1 \
  --force 0.10 \
  --pulse 0.112 \
  --duration 14
```

Thử đủ bốn trường hợp:

```text
pitch +1
pitch -1
roll  +1
roll  -1
```

Phải kiểm tra lực có tác dụng thực tế, đúng chiều và tạo được kích thích đo được.

Chỉ xem xét tăng lực lên `0.15 N`, rồi `0.20 N` nếu bài trước an toàn, đường áp lực đã được xác minh, và không đủ kích thích. Không tự động tăng lực qua nhiều mức khi có FAULT, trượt chân hoặc dữ liệu không đáng tin.

Không tăng lực vượt giới hạn cấu hình hoặc sửa các ngưỡng an toàn để ép PASS.

Nếu một hướng bị FAULT hoặc sai trục, ưu tiên phân tích lỗi đó trước khi thử hướng tiếp theo.

## 7. PHASE E — PID DIAGNOSIS VÀ TUNING

Sau khi có phản ứng nghiêng thực tế:

1. Đọc dữ liệu roll/pitch trước, trong và sau xung lực.
2. Kiểm tra dấu điều khiển pitch/roll và joint mixing.
3. Xác định lệnh PID có chống lại góc nghiêng hay làm nghiêng tăng.
4. Đối chiếu motor target và measured position.
5. Kiểm tra saturation, rate limit, integral windup và dao động.
6. Chỉ sửa một nhóm tham số hợp lý mỗi lần.
7. Chạy lại cùng bài thử với cùng lực và cấu hình khác không đổi.
8. Ghi kết quả trước/sau mỗi lần chỉnh.

Không thay đổi `tilt_fault_rad = 0.45` để đạt PASS.

Không bỏ E-STOP, FAULT, STOP, giới hạn khớp hoặc tốc độ khớp.

Nếu chưa có dữ liệu đủ mạnh để xác định PID sai chiều, không đảo dấu một cách ngẫu nhiên.

## 8. PHASE F — FULL ACCEPTANCE MATRIX

Khi pilot hợp lệ và an toàn, chạy đầy đủ:

```bash
python3 tools/run_balance_matrix.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 5 \
  --force 0.10 \
  --pulse 0.112 \
  --duration 14
```

Thay giá trị force chỉ khi envelope đã được hiệu chuẩn, an toàn và ghi rõ trong report.

Tiêu chí nghiệm thu bắt buộc:

- Đủ bốn hướng: pitch ±, roll ±.
- Ít nhất 3 cặp baseline/balance hợp lệ mỗi hướng, ưu tiên 5.
- Peak tilt change ≥ `0.008 rad` cho thử nghiệm hợp lệ.
- Góc nghiêng ban đầu của trục thử nhỏ hơn `0.08 rad`.
- Không có FAULT, ngã, mất chiều cao hoặc drift vượt giới hạn.
- Phục hồi về sai lệch ≤ `0.025 rad`, duy trì tối thiểu `0.8 s` trong cửa sổ phục hồi `5 s`.
- PID giảm trung bình peak tilt ít nhất `10%` so với baseline trên **từng hướng**.
- Mọi cặp có run IDs độc lập, force schedule khớp nhau và metadata so sánh được.
- Kiểm tra tiếp xúc chân và xác minh robot không bị xuyên sàn, neo cứng hoặc trượt không giải thích được.

Nếu chưa thể tự xác minh foot contact bằng công cụ/mô phỏng, đánh dấu `PENDING_OPERATOR_VISUAL_CHECK`. Khi đó không được tuyên bố nghiệm thu hoàn chỉnh.

**Không giảm ngưỡng nghiệm thu hoặc lọc bỏ run lỗi để làm đẹp tỷ lệ thành công.**

## 9. PHASE G — TEST FAILURE VÀ REGRESSION

Sau mỗi thay đổi quan trọng, chạy lại:

```bash
python3 tools/verify_project.py
python3 -m unittest discover -s tests -v
python3 tools/check_docs_links.py
python3 -m compileall -q \
  simulation/webots/controllers tools tests
```

Đảm bảo còn hoạt động đúng:

- NORMAL / STAND
- Fault do sensor invalid hoặc NaN
- Excessive tilt
- Low body height
- Obstacle STOP
- E_STOP
- Joint position/rate limits
- Force injection bị hủy khi robot không ở trạng thái an toàn
- Incomplete hoặc corrupt report bị từ chối

Sau khi tạo PR, kiểm tra GitHub Actions và đọc artifact của **chính commit được kiểm thử**. Nếu CI lỗi, đọc console/JSON/CSV và sửa trong branch, không bỏ qua lỗi.

## 10. REPORT BẮT BUỘC

Tạo hoặc cập nhật:

```text
docs/experiments/p2-2-acceptance-report.md
docs/OPERATOR_HANDOFF.md
```

Lưu raw CSV, JSON và log trong thư mục thí nghiệm được Git ignore, hoặc GitHub Actions artifacts. Không commit dữ liệu lớn, bí mật, thông tin cá nhân.

Báo cáo phải có:

- Goal và phạm vi thay đổi.
- Branch, commit SHA, Webots version.
- Danh sách file thay đổi.
- Lỗi đã phát hiện và nguyên nhân.
- Cách sửa đã chọn, lý do và rủi ro.
- Test commands thực sự đã chạy.
- Kết quả unit/integration/native Webots.
- Metrics baseline và balance cho cả bốn hướng.
- Số cặp hợp lệ và số cặp thất bại.
- Các trường hợp FAULT và thời điểm lỗi đầu tiên.
- Kết quả acceptance gate.
- Những phần chưa được xác minh.
- GitHub Actions run URLs, PR URL.
- Next action và những việc cần người vận hành.

Sử dụng một trong ba kết luận:

```text
ACCEPTED
NOT_ACCEPTED
INCONCLUSIVE
```

Chỉ dùng `ACCEPTED` khi tất cả tiêu chí bắt buộc có bằng chứng thực tế.

## 11. QUYỀN HẠN VÀ GIỚI HẠN

Bạn được phép tự sửa mã mô phỏng, test, analyzer, metadata, tài liệu và CI; chạy Webots, debug và lặp lại kiểm thử trong phạm vi P2.2.

Được tạo branch, commit và PR trên GitHub nếu quyền truy cập cho phép. Không tự merge các thay đổi làm yếu an toàn hoặc chưa qua các test bắt buộc.

Không triển khai hoặc thử nghiệm robot vật lý, firmware Arduino, cấp nguồn servo, mua linh kiện hay điều khiển PWM.

Không mở P3 Walking khi P2.2 chưa được nghiệm thu.

Không che giấu lỗi, sửa CSV thủ công hoặc tạo số liệu mô phỏng giả.

## 12. DEFINITION OF DONE

Công việc được coi là hoàn tất khi:

1. Đường áp lực có offset được kiểm chứng trên Webots native.
2. Bốn hướng lực có dữ liệu hợp lệ, đo được.
3. Full baseline/balance matrix đạt acceptance gate.
4. Các bài regression và CI đều đạt.
5. Tiếp xúc bàn chân được xác minh.
6. Báo cáo nghiệm thu và file bàn giao đầy đủ.
7. Source và thay đổi được lưu vào Git, có PR/commit truy xuất được.

Nếu không đạt, dừng ở một blocker cụ thể có bằng chứng, không tuyên bố hoàn thành.

**BẮT ĐẦU NGAY. Không dừng lại ở bước lập kế hoạch. Hãy kiểm tra repo, sửa lỗi đầu tiên, thực thi test, phân tích report rồi tiếp tục trong phạm vi được phép.**
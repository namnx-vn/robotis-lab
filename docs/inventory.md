# Robotis Lab — Hardware Inventory (ảnh người dùng)

- **Dự án:** RL-H25 / Robotis Lab
- **Ngày lập:** 2026-10-25
- **Nguồn kiểm kê:** 10 ảnh người dùng gửi trong cuộc trò chuyện, gồm ảnh riêng từng linh kiện và ảnh tổng hợp. Các linh kiện xuất hiện lặp lại trong nhiều ảnh **không** được tính thêm.
- **Phạm vi xác minh:** nhận dạng bằng mắt qua ảnh, **chưa kiểm tra điện, chưa chạy chương trình, chưa đo thông số, chưa xác minh phụ kiện trong túi**.
- **Quy ước số lượng:** `>=1` nghĩa là nhìn thấy ít nhất một món; chưa phải số lượng tồn kho vật lý đã đếm.
- **Trạng thái chung:** `PHOTO_IDENTIFIED / UNTESTED`.

## 1. Những linh kiện đã thấy

| ID | Linh kiện | Mã/kiểu đọc được hoặc nhận dạng | Số lượng thấy | Vai trò tiềm năng với RL-H25 | Tình trạng/xác minh |
|---|---|---|---:|---|---|
| HW-001 | Bo vi điều khiển Arduino Uno tương thích | UNO, dạng Uno R3 | >=1 | MCU điều khiển cấp thấp, giao tiếp USB Serial | Thấy mặt trước; chưa nạp chương trình |
| HW-002 | Mạch driver transistor/động cơ bước | ULN2003 / ULN2003AN (theo nhận dạng trong cuộc trò chuyện) | >=1 | Chỉ phù hợp tải/động cơ tương thích, **không thay PCA9685 để điều khiển servo vị trí** | Chưa kiểm chân/chạy tải |
| HW-003 | Mạch đồng hồ thời gian thực | DS1302, có pin cúc áo CR2032 nhìn thấy | >=1 | Thời gian cho log hoặc tính năng phụ | Chưa xác minh dung lượng pin/chạy giờ |
| HW-004 | Màn hình ký tự | LCD 1602A, 16 chân, `1602A Ver5.5` | >=1 | Hiển thị trạng thái, lỗi, pin | Nhìn thấy pad 16 chân, chưa thấy header hàn hoàn chỉnh; chưa test |
| HW-005 | Đầu đọc RFID | `RFID-RC522` (MFRC522-type) | >=1 | Nhận thẻ/lệnh người dùng; không cần cho chức năng đi | Chưa xác minh hoạt động; dùng logic 3.3 V và chuyển mức tín hiệu khi cần |
| HW-006 | Relay module 1 kênh | `JQC-3FF-S-Z`, cuộn hút 5 VDC ghi trên relay | >=1 | Thí nghiệm đóng/cắt tải DC áp thấp; **không mặc định dùng làm E-STOP servo** | Chưa test; không thao tác điện lưới trong giai đoạn học |
| HW-007 | LED 7 đoạn 4 chữ số | `5461AS-1` nhìn thấy trên thân | >=1 | Hiển thị số đơn giản | Loại anode/cathode, điện trở và pinout chưa xác minh |
| HW-008 | Ma trận LED | 8×8 điểm sáng | >=1 | Hiển thị biểu tượng/trạng thái | Chưa rõ part number/pinout/driver; ảnh cho thấy phần LED rời |
| HW-009 | LED 7 đoạn 1 chữ số | Loại rời (chưa đọc được mã) | >=1 | Hiển thị trạng thái đơn giản | Chưa xác minh common-anode/cathode và chân |
| HW-010 | Điều khiển từ xa | Remote dạng IR, ~21 phím | >=1 | Gửi lệnh nếu bổ sung mắt nhận IR tương thích | Chỉ thấy remote, **chưa xác nhận có module nhận IR** |
| HW-011 | Joystick analog có nút nhấn | Board `HW-504`, kiểu KY-023 | >=1 | Điều khiển thử nghiệm thủ công / hiệu chuẩn | Chưa đo VRx/VRy/switch |
| HW-012 | Module cảm biến âm thanh | Micro điện dung + LM393-type board (nhận dạng theo hình dạng, chip chưa đọc rõ) | >=1 | Phát hiện ngưỡng âm thanh; không tự hiểu lời nói | Chưa thử; không coi là micro để nhận dạng tiếng nói |
| HW-013 | Cảm biến nhiệt độ/độ ẩm | DHT11 (vỏ xanh trên PCB 3 chân) | >=1 | Quan sát môi trường, tính năng phụ | Chưa xác minh đầu chân cụ thể của board |
| HW-014 | Cảm biến nước | PCB in chữ `Water Sensor` trong túi | >=1 | Thử phát hiện nước; **không cần cho RL-H25 ban đầu** | Chưa rõ có đi kèm board giao tiếp hay không |
| HW-015 | Bảng nút nhấn nhiều phím | PCB xanh gồm nhiều nút tactile, trong túi | >=1 | Nhập lệnh thủ công/chọn chế độ | Không đủ ảnh để xác nhận ma trận phím, số nút, mạch quét/pinout |

**Phụ kiện nhìn thấy nhưng chưa xác nhận:** tấm thẻ màu trắng trong túi RC522 **có thể** là thẻ RFID; chưa xác nhận loại, số lượng hoặc khả năng đọc. Pin CR2032 nằm trong module DS1302, không tính như nguồn cấp robot.

## 2. Những thứ chưa được xác nhận sở hữu qua ảnh

- **Thiết bị truyền động:** servo điều khiển góc, động cơ bước 28BYJ-48, động cơ giảm tốc; bánh răng/trục/cơ cấu chân.
- **Mạch servo:** PCA9685 hoặc bộ điều khiển servo khác.
- **Cảm biến cân bằng/định vị:** MPU6050/IMU, cảm biến tiếp xúc bàn chân, cảm biến ToF/ultrasonic, camera.
- **Điện và an toàn:** rail nguồn servo 5–6 V đủ dòng, bộ hạ áp, pin/BMS, cầu chì, E-STOP vật lý.
- **Lắp ráp/đo đạc:** breadboard, dây jumper, cáp USB Type-B, bộ điện trở, biến trở LCD, mỏ hàn, đồng hồ vạn năng, khung in 3D, gá servo, ốc vít.
- **AI/host:** máy tính xách tay xuất hiện trong ảnh, nhưng **chưa xác nhận cấu hình, khả năng chạy Webots, cổng USB hoặc là máy chuyên dùng làm host**.

> “Chưa xác nhận” **không có nghĩa là chắc chắn chưa có**. Cần hỏi/kiểm kê thực tế trước khi mua.

## 3. Khả năng tái sử dụng trong RL-H25

**Dùng ngay ở giai đoạn điều khiển thử nghiệm (sau kiểm tra):** Arduino Uno (HW-001), joystick (HW-011), LCD1602 (HW-004).

**Tính năng phụ/không ưu tiên cho robot biết đi:** RTC (HW-003), RFID (HW-005), relay (HW-006), hiển thị LED (HW-007/008/009), remote (HW-010), cảm biến âm thanh (HW-012), DHT11 (HW-013), cảm biến nước (HW-014), bảng nút nhấn (HW-015), ULN2003 (HW-002).

**Khoảng thiếu quan trọng nhất để đi bằng hai chân:** servo phù hợp tải; cơ khí; nguồn và E-STOP; PCA9685/driver; IMU. Danh sách mua chỉ nên chốt sau mô hình khối lượng, mô-men xoắn và bench-test 1 servo.

## 4. Kiểm tra trước khi chuyển `PHOTO_IDENTIFIED` → `TESTED`

1. Chụp rõ **hai mặt, số chân và nhãn** từng module; kiểm đếm thực tế và cập nhật `actual_qty`.
2. Xác minh Arduino kết nối được máy tính, nhận COM/tty, nạp Blink và ghi phiên bản board.
3. Kiểm tra board LCD có hàng chân hàn chưa, pinout và mức tương phản; ghi lại mã chính xác của LED 7 đoạn.
4. Kiểm tra RC522 và các module 3.3 V theo datasheet trước khi nối với mức logic 5 V của Uno.
5. Kiểm kê dây, breadboard, cáp, công cụ và nguồn **trước khi quyết định mua**.
6. Không thử đóng cắt điện lưới; không cấp nguồn nhiều servo qua chân 5 V của Arduino.

## 5. Tích hợp với kế hoạch dự án

- **Phase:** P0 — Inventory audit; hiện mới hoàn thành kiểm kê qua ảnh, **chưa hoàn thành kiểm kê vật lý**.
- **Tiếp theo:** xác minh số lượng, điện áp, pinout và tình trạng; tạo mô hình Webots RL-H25 10 DOF; tính torque/power estimate trước khi mua.
- **Không tuyên bố:** đã có robot thật, servo, camera, phần cứng AI, khung hoặc khả năng đứng/đi.
- **Liên hệ:** `PROJECT_INSTRUCTIONS.md`, `IMPLEMENTATION_PLAN.md`.

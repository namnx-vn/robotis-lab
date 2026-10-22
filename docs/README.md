# Robotis Lab · Tài liệu

Tài liệu được nhóm theo **mục đích**, thay vì đặt tất cả vào một thư mục. Mã nguồn Webots, controller và các lệnh chạy vẫn nằm ở thư mục project chính.

## Bắt đầu tại đây

| Bạn muốn tìm | Tài liệu |
|---|---|
| Tiến độ và điều kiện qua phase | [Roadmap](ROADMAP.md) · [Backlog](../tasks/backlog.md) |
| Việc cần chủ dự án kiểm tra | [Operator handoff](OPERATOR_HANDOFF.md) |
| Bắt đầu chạy Webots | [Root README](../README.md) |

## Architecture — Yêu cầu và thiết kế

- [Requirements](architecture/requirements.md) — mục tiêu, ràng buộc và nghiệm thu Sprint 01
- [ADR-0001](architecture/adr-0001.md) — quyết định simulation-first
- [Mechanics](architecture/mechanics.md) — hình học, khối lượng, hệ tọa độ và khớp
- [Balance design](architecture/balance-design.md) — PID, joint mixing và giới hạn
- [Safety](architecture/safety.md) — trạng thái lỗi và nguyên tắc an toàn

## Experiments — Quy trình mô phỏng

- [Standing baseline](experiments/standing-baseline.md) — 5 lần đứng tĩnh
- [Controlled disturbance](experiments/controlled-disturbance.md) — thử xung lực chuẩn hóa
- [Balance matrix](experiments/balance-matrix.md) — pitch/roll theo hai chiều và acceptance gate

## Operations — CI và quy trình làm việc

- [CI report feedback loop](operations/ci-report-feedback-loop.md) — commit → Webots → CSV/JSON → review
- [Operator handoff](OPERATOR_HANDOFF.md) — file bàn giao **giữ đường dẫn ổn định** cho các lượt tự động
- [Roadmap](ROADMAP.md) — file roadmap **giữ đường dẫn ổn định** để không phá agent contract

## Archive — Lịch sử, không phải kết quả nghiệm thu hiện tại

- [Source migration](archive/source-import.md) — hướng dẫn import đã hoàn thành
- Báo cáo offline trước đây: [Sprint 01](archive/reports/sprint-01.md), [v0.2](archive/reports/v0.2.md), [Sprint 02.1](archive/reports/sprint-02.1.md)

Các báo cáo trong archive chỉ thể hiện **phạm vi kiểm thử được ghi trong chính tài liệu**, không mặc nhiên xác nhận Webots đã cân bằng chủ động. Report CI mới nhất và telemetry thật nằm trong GitHub Actions artifacts, không commit vào `docs/`.

## Quy ước

- Tài liệu mới: đặt theo nhóm `architecture/`, `experiments/`, `operations/`, hoặc `archive/`; tên file `lowercase-kebab-case.md`.
- `ROADMAP.md` và `OPERATOR_HANDOFF.md` giữ tên/đường dẫn cũ vì được tham chiếu trực tiếp từ các công cụ.
- Sửa đường dẫn Markdown khi đổi vị trí. Chạy `python3 tools/check_docs_links.py` và `python3 -m unittest discover -s tests -v`.
- Không đưa secrets, video riêng tư, hoặc raw telemetry chứa dữ liệu nhạy cảm vào Git.

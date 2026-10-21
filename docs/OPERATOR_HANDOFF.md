# ROBOTIS LAB — Ghi chú bàn giao cho người vận hành

**Cập nhật:** 22/10/2026, giờ Việt Nam.  
**Mốc kiểm tra dự kiến:** 07:00 ngày 23/10/2026 (Asia/Ho_Chi_Minh).  
**Repo:** https://github.com/namnx-vn/robotis-lab  
**Phạm vi ủy quyền:** tự phát triển, thử Webots trên GitHub CI, phân tích report, sửa và chạy lại trong thời gian đã định; không điều khiển phần cứng, nới an toàn hay tuyên bố nghiệm thu khi chưa đủ dữ liệu.

## Những việc đã hoàn thành

1. **PR #3** — https://github.com/namnx-vn/robotis-lab/pull/3 — đã merge, commit `8c6e105d0a8eec18c410c3dba35cc388d52a0407`. Sửa README cũ, bổ sung quy trình CI report → thay đổi code → CI report, cập nhật AGENTS.md.
2. **Master CI sau PR #3**: https://github.com/namnx-vn/robotis-lab/actions/runs/39648409470 đã PASS native Webots. Trước đó baseline ở commit `ef7e287724bfca351d666b0030a137f09c06c01d` (run https://github.com/namnx-vn/robotis-lab/actions/runs/39645977052) cho **5/5 standing 31,92 giây**, static only, không có ngoại lực.
3. **PR #4** — https://github.com/namnx-vn/robotis-lab/pull/4 — triển khai CI thử lực mới bằng Webots thật, lưu CSV/JSON/Markdown và phân biệt integrity PASS với scientific recovery. Các workflow Python CI, Webots smoke và disturbance pilot của PR #4 đều hoàn tất thành công: https://github.com/namnx-vn/robotis-lab/actions/runs/39648900940.

## Kết quả thử lực thực tế gần nhất: INCONCLUSIVE

Artifact từ run `39648900940`, commit `e0ba9c1e453c6927fe73e213b1faa57839b906cf` (đây là test merge SHA, không phải SHA head nhánh):

| Mục đo | Baseline | Balance PID |
|---|---:|---:|
| Trục/hướng | pitch +1 | pitch +1 |
| Lực xung | 0,10 N | 0,10 N |
| Thời gian xung | 0,112 s | 0,112 s |
| Bước thực sự áp lực | 7 | 7 |
| Peak tilt change | **0,00011 rad** | **0,00014 rad** |
| FAULT | Không | Không |
| Verdict | INCONCLUSIVE | INCONCLUSIVE |

- Script ngắt đúng sau cặp đầu vì cả hai phản ứng thấp hơn ngưỡng kích thích đo được **0,008 rad**; chưa chạy pitch -1 / roll ±. `ci_evidence_ok=true` chỉ nghĩa là tạo đủ bằng chứng đúng định dạng, **không** chứng minh PID tốt hơn.
- Không tăng lực vô hạn, không bỏ giới hạn nghiêng 0,45 rad. **Việc cần nghiên cứu tiếp:** kiểm tra hệ trục và ứng dụng lực/torsion, khối lượng/mô-men, tính thích hợp của ngưỡng 0,008 rad; sau đó thử pulse nhỏ được định lượng trên nhánh mô phỏng, có report riêng và giới hạn rõ ràng.
- Vẫn cần kiểm tra trực quan bàn chân với sàn, không xuyên sàn/neo cứng; CI headless CSV chưa thay thế kiểm tra tiếp xúc.

## Trạng thái sprint

| Sprint | Trạng thái |
|---|---|
| P1 mô hình 10 DOF Webots | Source + native smoke có thật |
| P2 đứng tĩnh | Automated baseline PASS 5/5 |
| P2.2 cân bằng khi chịu lực | **INCONCLUSIVE / chưa nghiệm thu** |
| P3 Weight Shift/Walking | **BLOCKED** đến khi P2 có bằng chứng đủ |
| P4 Avoidance/Safety | Chưa kiểm thử đầy đủ trong bài thí nghiệm hiện hành |
| P5–P7 phần cứng/tự hành | Chưa được phép thực hiện vì thiếu inventory/torque/power và phê duyệt riêng |

## Việc cần người vận hành sáng mai

- Mở [GitHub Pull Requests](https://github.com/namnx-vn/robotis-lab/pulls), [GitHub Actions](https://github.com/namnx-vn/robotis-lab/actions) và file này để xem các commit/PR/CI run bổ sung qua đêm.
- Nếu P2 vẫn còn `INCONCLUSIVE`, không kết luận robot tự cân bằng và chưa bắt đầu thử bước đi.
- Khi có thể, mở Webots R2025a trên Mac và kiểm tra hai bàn chân có tiếp xúc đúng với sàn, không bị neo/chìm/trượt. Chụp màn hình contact/bounding objects hoặc gửi logs cho phiên chat tiếp theo.
- Quyết định mua linh kiện, chạy servo thật, firmware hoặc tự di chuyển phần cứng vẫn phải được xác nhận riêng.

## Tự động hóa ban đêm

Đã thiết lập tác vụ phát triển **mỗi giờ** tới 07:00 ngày 23/10/2026 giờ Việt Nam; mỗi lượt sẽ đọc lại code + CI, làm các thay đổi mô phỏng nhỏ có tests, cập nhật file này và đăng PR/merge thay đổi đủ an toàn. **Không thể bảo đảm tất cả sprint hoàn thành qua một đêm**; mỗi milestone phải dựa trên kết quả thật, không phải số giờ đã chạy.

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
- Phân tích source + artifact xác định lỗi chính: Python binding của Webots R2025a gọi `addForce` thay cho `addForceWithOffset`; offset 0,04 m bị mất và tham số hệ tọa độ không còn đáng tin cậy. Lỗi upstream này được sửa sau R2025a trong Cyberbotics PR [#6881](https://github.com/cyberbotics/webots/pull/6881). Cần bài test API native tối thiểu để xác nhận đúng build trong CI.
- Không tăng lực, đổi PID hoặc bỏ giới hạn nghiêng 0,45 rad trước khi sửa/xác minh đường áp lực. Báo cáo debug và kế hoạch P3 chi tiết nằm tại [P2.2 Debug Findings and P3 Implementation Readiness](experiments/p2-2-debug-p3-readiness.md).
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

Đã thiết lập tác vụ phát triển **mỗi giờ** tới 07:00 ngày 23/10/2026 giờ Việt Nam; mỗi lượt có thể đọc lại code + CI, chạy kiểm tra và chuẩn bị/cập nhật PR nhỏ để người vận hành review. Tác vụ **không được tự merge**, tự tuning PID, bắt đầu gait, điều khiển phần cứng hoặc nới safety gate. **Không thể bảo đảm tất cả sprint hoàn thành qua một đêm**; mỗi milestone phải dựa trên kết quả thật và phê duyệt phù hợp, không phải số giờ đã chạy.

## Cập nhật triển khai P2.2 ngày 22/10/2026 — PR #8

- **Draft PR:** https://github.com/namnx-vn/robotis-lab/pull/8; nhánh `fix/p22-supervisor-force-abi`, nền `02fc43a`. Không merge tự động.
- **Sửa code:** thay Webots R2025a Python wrapper lỗi bằng lời gọi C ABI `wb_supervisor_node_add_force_with_offset` chính xác, `Node._ref` và `ctypes` bốn tham số. Không fallback về Python binding lỗi.
- **Thử nghiệm mới:** `tools/run_force_api_probe.py` với một vật thể Physics tự do; kiểm tra trọng lực, zero-offset vs nonzero, pitch/roll ±, world-frame force và local-frame offset. CI chặn thử RL-H25 nếu probe không đạt.
- **Telemetries:** source/test-merge SHA, config/world hash, Webots version khi xác minh được, actual API call count, lực, vận tốc, cross-axis peak, thời điểm FAULT. Analyzer từ chối provenance không xác minh.
- **Không đổi** PID gains/sign, hình học, ngưỡng tilt 0.45 rad, E-STOP, servo/firmware hoặc P3 gait.
- **Acceptance:** `NOT_ACCEPTED` cho tới khi kiểm chứng native probe, pilot bốn hướng, >=3 cặp/hướng có thể so sánh, cải thiện peak >=10% trên từng hướng, hồi phục đủ thời gian và foot contact được kiểm tra.
- **Báo cáo:** [P2.2 Acceptance Report](experiments/p2-2-acceptance-report.md); raw logs/JSON/CSV trong GitHub Actions PR #8, không sửa CSV tay.
- **Việc cần người vận hành:** review draft PR và xem chân tiếp xúc mặt đất trong Webots Mac; không chạy phần cứng hay bước đi.

### Bằng chứng CI native mới — PR #8, 22/10/2026

- Webots force API độc lập: **PASS 8/8**, đã kiểm tra Physics/gravity, lực ±X/±Z, offset 0/0,04 m, hướng frame; lực tạo mô-men đúng ở vật thể tự do.
- [Native disturbance CI run 39713137894](https://github.com/namnx-vn/robotis-lab/actions/runs/39713137894): workflow SUCCESS về thu thập bằng chứng, **scientific status INCONCLUSIVE**. Source head `43ec56dd3f7d89edbaa870056c085b9f45af1d5a`, test-merge `ed57598daa33eaea6dc61a953a52592313cf7c70`, binary ghi `Webots R2025a`.
- Pilot pitch +: baseline 0,00012 rad, balance 0,00016 rad, cùng 0,10 N / 0,112 s / 7 steps, không FAULT; nhỏ hơn ngưỡng 0,008 rad. Chưa có pitch -/roll ± và chưa được chỉnh PID.
- [Offline tests](https://github.com/namnx-vn/robotis-lab/actions/runs/39713137893): 99/99 PASS. [Webots smoke](https://github.com/namnx-vn/robotis-lab/actions/runs/39713137953): SUCCESS.
- [Báo cáo đầy đủ trên branch](experiments/p2-2-acceptance-report.md): **NOT_ACCEPTED**. Blocker tiếp theo là kích thích nghiêng quá nhỏ dù đường lực trên vật thể tự do đã xác minh. Chỉ tăng thăm dò lực theo thứ tự được cho phép và kiểm tra dữ liệu an toàn mỗi bước; chưa chạy matrix full, chưa mở P3, chưa thay phần cứng.

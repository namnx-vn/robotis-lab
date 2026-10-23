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

## Cập nhật P2.2 ngày 22/10/2026 — PR #8 và kiểm thử native local

- PR [#8](https://github.com/namnx-vn/robotis-lab/pull/8) đã merge vào `master`, merge SHA `576473200b818c881373067bd3081d22379d92e4`. Workflow disturbance cuối cùng trên head `43ec56dd3f7d89edbaa870056c085b9f45af1d5a` đã hoàn tất: https://github.com/namnx-vn/robotis-lab/actions/runs/39713137894.
- Follow-up runner/report là [PR #10](https://github.com/namnx-vn/robotis-lab/pull/10), head `a1730375957699d0694f52919f0cea04f888e628`; ba workflow Python, Webots simulation và disturbance pilot đều success. CI probe đạt 8/8; pilot pitch+ là `INCONCLUSIVE` (`SCIENTIFIC CERTIFICATION: NO`). Artifact raw `12411381955` đã upload nhưng endpoint trả HTTP 403 khi review nên CSV/JSON CI chưa được kiểm tra độc lập.
- Webots trên Mac được xác nhận là `R2025a`, bundle version `R2025a38`. Free-body native force probe đạt **8/8** ca, gồm lực ±X/±Z, zero/nonzero offset, body xoay, world-frame force, local-frame offset và gravity. C API adapter đang gọi `wb_supervisor_node_add_force_with_offset` với ABI 4 tham số.
- Pilot RL-H25 local ở `0.10 N`, `0.112 s`, offset `0.04 m`, đủ pitch ± và roll ±: tất cả 8 trial kết thúc `STAND`, 7 applied steps, không fault; peak tilt `0.00012–0.00016 rad`, dưới ngưỡng `0.008 rad`. Drift tối đa `0.00003 m`; height tối thiểu `0.18296 m`.
- Thang lực pitch+ được thử riêng sau khi các trial 0.10 N an toàn: `0.15 N` peak baseline/PID `0.00018/0.00024 rad`; `0.20 N` `0.00024/0.00032 rad`. Không fault, drift tối đa `0.00006 m`, nhưng cả hai đều `INCONCLUSIVE`; đã dừng ở `0.20 N`.
- Trong lần chạy đầu, local runner ghi `webots_version: unverified`; bổ sung phát hiện `Contents/Resources/version.txt` và test. Một lần timeout probe cũng để Webots child giữ output pipe; cập nhật runner để kill/reap cả process group và thêm regression test. Sau thay đổi: verifier, 103 unit tests, compileall, docs links và matrix dry-run đều PASS.
- **Kết luận P2.2: INCONCLUSIVE / chưa nghiệm thu.** API và dấu lực được kiểm chứng trên vật thể tự do; phản ứng RL-H25 vẫn thấp ít nhất 25 lần so với ngưỡng kích thích, nên không thể kết luận PID phục hồi hoặc sai dấu. Chưa chạy full 3–5 cặp/hướng. P3 gait vẫn **BLOCKED**.
- **Bằng chứng raw:** ignored `experiments/logs/` có CSV/JSON cho matrix `balance-matrix-20261022T070333Z.json` và calibration `disturbance-pitch-20261022T070429Z.json`, `disturbance-pitch-20261022T070447Z.json`; free-body JSON/log tại `/private/tmp/p22-native-probe/`. Xem [P2.2 Acceptance Report](experiments/p2-2-acceptance-report.md).
- **Việc cần người vận hành:** kiểm tra trực quan foot contact/slip trong GUI Webots và quyết định liệu force envelope/pulse hoặc mô hình cần hiệu chuẩn lại qua thay đổi được review. Không tuning PID, không gait, không phần cứng khi kích thích chưa đạt gate.

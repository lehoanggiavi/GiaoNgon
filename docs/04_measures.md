# Công thức chỉ số Pilot2 — Phase 4

Kỹ thuật xong, trình Human Gate 4. Chưa phân tích 4B, chưa dashboard.

Model: `GiaoNongPilot2` (Desktop riêng, đã nạp). Thêm đúng một bảng **Measure** hiện
(cột Value ẩn), 25 công thức mới, 5 display folders. Không quan hệ mới, không sửa fact/dim.

## Cách đọc đơn giản

Ví dụ: “tỷ lệ trễ chia số đơn trễ cho các đơn có đủ thông tin, không chia cho mọi đơn hủy”.
Mỗi chỉ số chỉ đúng trong lựa chọn đang bấm (tháng/khu vực/khung giờ...); chỗ không có dữ
liệu thì đếm/tổng hiện 0, còn tỷ lệ/trung bình hiện trống (BLANK) chứ không bịa số 0.
Tiền là số ghi nhận gốc, chưa gọi là doanh thu thực thu hay lợi nhuận kế toán, không đặt VND.

## 25 measures (registry đầy đủ ở `reports/phase4/registry.json`)

| Nhóm | Công thức |
|---|---|
| Orders | Total Orders; Completed Orders; Cancelled Orders; Cancellation Rate |
| Service | Late Eligible Orders; Late Orders; Late Rate; Late Coverage |
| Time | Avg Prep/Wait/Travel/Delivery Minutes; Median Delivery Minutes; Delivery Eligible Orders |
| Finance | Recorded Order Value/Revenue/Profit; Recorded Profit Margin; Loss Orders; Loss Rate |
| Customers | Active Customers; Repeat Customers; Repeat Customer Rate; Orders per Customer; Avg Rating |

Quy tắc chính: Total=đếm dòng (order_id duy nhất); Completed/Hủy theo cờ nguồn;
Late chỉ trên đơn cờ 0/1 (eligible), Rate=hủy/(hoàn thành+hủy);
mean/median mỗi cột có n riêng, đơn hủy 0, giá trị >=0;
Margin=tổng/tổng (có chi phí đơn hủy trong tử); Repeat=khách ≥2 đơn trong lựa chọn
(không cộng distinct giữa tháng, không gọi retention); Rating trên đơn hủy 0 có điểm.
Mọi điều kiện cohort dùng KEEPFILTERS để giao với filter đang chọn (đã bắt lỗi thực:
điều kiện thường bị filter cùng cột thay thế làm mất lọc — ví dụ eligible vọt 5.725
và coverage 763% khi lọc trễ=1); không ALL/REMOVEFILTERS.

## Đã kiểm (native thật, `reports/phase4/native_results.json` + `Log/phase4/validation.json`)

- Tổng hiện tại: 6.073 đơn (5.725 hoàn thành, 348 hủy); trễ 750/5.725; thu nhập
  203.341.200, chênh lệch 50.859.200; 2.098 khách (1.261 lặp lại); điểm trung bình 4,59.
- Context: tháng 03 (920/32/53), tháng 08 (1.144/147/250); Quận 1 (963, trễ 114);
  Trưa (2.087, thu nhập 71.137.300); nhóm xa nhất (463, trễ 250); mưa (2.189, trễ 469, hủy 188);
  combo ngày+khu vực 5 đơn; khách lặp lại tháng 03 là 150/611.
- Edge: ngày không đơn → đếm/tổng 0, tỷ lệ/trung bình BLANK; lọc hủy=1 thì Late=0;
  lọc trễ=0 thì Late=0; nhóm khách một đơn → tổng 1, lặp lại 0, tỷ lệ 0 thật (mẫu số 1).
- Đối chiếu độc lập CSV curated: 107/107 PASS, actual parse trực tiếp từ raw response
  (đếm/tiền exact, tỷ lệ/trung bình |lệch|≤1e-8). Reproducer trước sửa đã capture:
  eligible 5.725/rate 0,131/coverage 763% khi lọc trễ=1; loss 1.320 khi lọc profit≥0;
  trung bình grand khi lọc delivery≤20 — sau sửa về đúng 750/1/1, 0/0, 17,50/575.
- Registry native: bảng Measure hiện, Value ẩn, đủ 25 tên/folder/format/mô tả;
  6 bảng/5 quan hệ cũ nguyên; Month sort giữ; snapshot trước/sau chỉ khác Measure.tmdl
  + ref trong model.tmdl. Definition đã export lưu revision; nạp lại ở connection kiểm
  riêng thấy đủ 7 bảng/25 measures. Desktop của pilot vẫn mở.

## Còn thiếu / pending

- Tiền tệ, phạm vi kế toán, SLA trễ, nguồn cờ mưa, ranh giờ, thang điểm: chỉ diễn giải
  theo nguồn, chưa xác nhận. Không YTD/MoM/RFM/ML/target/ROI.
- Refresh offline qua MCP lỗi hệ thống (lịch sử); nạp + refresh Full qua Desktop msmdsrv tốt.

## Chốt Gate 4 (finalize, không chạy lại 107)

- Cột marker `Measure.Value` đã ẩn native (Get isHidden=true, bảng Measure hiện);
  definition đã export lưu revision cuối (`reports/phase4/finalize.json`).
- Sau nạp bản cuối: Total 6.073; Late Eligible khi lọc trễ=1 là 750; Late Rate=1;
  Loss khi lọc lãi≥0 là 0; Avg Delivery khi lọc ≤20 phút là 17,50 — khớp nguồn.
- Đóng thường cửa sổ Pilot2 để mở lại bị vướng (khả năng có dialog Save, không bấm
  được, không ép đóng — Desktop vẫn mở). Persistence qua export + nạp definition ở
  connection kiểm riêng (đủ 7 bảng/25 measures, Value ẩn) và query live nêu trên.
- Desktop tự chuyển shell report tay viết thành `report.json` trống (sections rỗng) +
  `.platform`; 5 đường shell P3 đổi/mất đã ghi đúng paths/hashes, byPath vẫn đúng model.
  Shell vẫn trắng, model không ảnh hưởng.

Tái chạy: \python -X utf8 scripts/phase4.py --run\ (đối chiếu outputs đã capture với expected tính mới từ curated; không chạy query/model).

107 là số comparisons (gồm cả reproducer trước sửa), không phải 107 query calls.

# Thiết kế report Pilot2 — Phase 5B (để duyệt, chưa vẽ)

Tài liệu này để người dùng duyệt nhìn: bố cục 4 trang, màu/font, vị trí từng số/biểu
đồ/lọc. Chưa tọa độ PBIR cuối, chưa theme JSON, chưa vẽ dashboard (Phase 5C).
Mọi số/binding/giới hạn lấy từ Pilot2 và chốt 5A; ảnh mẫu chỉ cho mượn logic bố cục.

## 1. Ảnh mẫu đã xem (chỉ bố cục, không lấy nội dung gốc)

4 screenshot lịch sử ngày 04/10/2026 của mẫu GiaoNongOps (không phải ảnh Pilot2):

| Ảnh | Path | SHA-256 | Ngày file |
|---|---|---|---|
| Tổng quan | `E:/Practice_DSEA/DA/OpenSrcDA/GiaoNgon/reports/reference/dashboard/Tổng quan.png` | `61d31180…af9f` | 2026-10-04 |
| Vận hành | `.../Vận hành.png` | `ff03c2c7…9959ac` | 2026-10-04 |
| Tài chính | `.../Tài chính.png` | `65cd1a33…f4e31668` | 2026-10-04 |
| Khách hàng | `.../Khách hàng.png` | `93141563…6e64b` | 2026-10-04 |

Đã mở xem cả 4 bằng công cụ ảnh (1416×733 mỗi ảnh). Giữ lại logic: nền sáng ấm, điểm
nhấn cam, thanh trái chứa điều hướng + bộ lọc, cụm KPI trên cùng, biểu đồ thẳng hàng.
Đổi toàn bộ cho Pilot2: số/bindings/đơn vị/giới hạn theo 5A; KHÔNG kế thừa chữ VND,
định nghĩa doanh thu/lợi nhuận, charts theo tuần/top quán/P90/lợi nhuận theo món/tuổi
quan hệ, snapshot ML, theme JSON, PBIR/TMDL/DAX hay QA cũ.

## 2. Khung chung (canvas 1280×720)

- Nền trang #FDF6EE (kem sáng sampled từ ảnh mẫu); sidebar #FFFDF9; thẻ trắng #FFFFFF;
  nhấn cam #E8826A (sampled); chuỗi phụ xám ấm #A8A29E; chữ chính #292524; chữ phụ #78716C.
- Font Segoe UI (sẵn trên Windows, đủ dấu tiếng Việt). Số KPI 28–32pt đậm; tên trang
  20pt; tiêu đề biểu đồ 12pt + dòng phụ xám 9pt (ghi mẫu số/phạm vi).
- Quy ước tọa độ: x/y tính từ góc trái TRÊN, y tăng xuống, canvas 1280×720.
  Sidebar x0–180: logo + tên Pilot2 y8–40; 4 nút trang h40 (Tổng quan y76–116,
  Vận hành y128–168, Tài chính y180–220, Khách hàng y232–272; đang xem nền cam chữ
  trắng); slicer dùng chung Kỳ DateRange `Dim_Date[Date]` (nhãn y318–332, hộp
  y332–362, mặc định 01/03–31/08/2026) và Khu vực `Dim_Zone[zone]` (nhãn y374–386,
  hộp y388–418, “Tất cả”); nút “Xóa lọc” y430–464; dòng “Reset về kỳ nguồn” y474–482.
- Header x192–1272: tên trang 19pt (y14) + dòng phạm vi/kỳ 9pt (y44) + “Cập nhật:
  31/08/2026” (ngày dữ liệu) góc phải.
- Hàng filter riêng trong nội dung (chỉ trang Vận hành/Tài chính): nền #F5EFE6 cao 48px
  (Vận hành y72–120: Khung giờ `Dim_TimeSlot[time_slot]` x206–438, Mưa `Fact_Orders[is_rain]`
  x476–708, Nhóm km `Dim_DistanceBand[distance_band_normalized]` x746–978;
  Tài chính y72–120: Trạng thái `Fact_Orders[is_cancelled]` x206–438), kèm chữ
  “chỉ lọc trong trang”. Cờ mưa: 0 = cờ không mưa, 1 = cờ mưa theo nguồn (pending cách đo).
  Cờ trạng thái: 0 = xong theo quy tắc dự án, 1 = hủy.
- Thẻ KPI: vạch cam trên; số 16pt đậm, nhãn 8pt, dòng mẫu số 7pt — ba vùng tách nhau,
  không chồng chữ (đã kiểm ở 100%). Card tỷ lệ có thêm dòng “Mẫu số: … (n=…)” thấy ngay
  bình thường (không chỉ tooltip) theo chốt 5A.
- Tiền ghi “đơn vị theo nguồn”, phút ghi “phút (tên trường)”, % ghi kèm mẫu số.
  Không màu đỏ/xanh đạt/không đạt (chưa có SLA/target).

## 3. Bố cục từng trang (x/y/w/h pixel trên canvas)

### Trang Tổng quan (không hàng filter riêng; chỉ lọc chung sidebar)

| ID | Visual | x/y/w/h | Nhãn + bindings + ghi chú |
|---|---|---|---|
| P1-C1 | cardVisual | 192/88/212/96 | Tổng số đơn — `Measure[Total Orders]`; tooltip `Measure[Completed Orders]`, `Measure[Cancelled Orders]` |
| P1-C2 | cardVisual | 412/88/212/96 | Tỷ lệ hủy — `Measure[Cancellation Rate]`; tooltip `Measure[Cancelled Orders]`, `Measure[Completed Orders]`, `Measure[Total Orders]` |
| P1-C3 | cardVisual 2 giá trị | 632/88/212/96 | Tỷ lệ trễ — `Measure[Late Rate]` + dòng mẫu số `Measure[Late Eligible Orders]` thấy thường trực (vùng chữ riêng, không đè nhãn) |
| P1-C4 | cardVisual | 852/88/212/96 | Chênh lệch ghi nhận — `Measure[Recorded Profit]`; tooltip `Measure[Recorded Revenue]`, `Measure[Recorded Profit Margin]` |
| P1-C5 | lineChart 1 series + legend | 192/192/620/300 | Đơn theo tháng — `Measure[Total Orders]` theo `Dim_Date[YearMonth]` (sort thời gian); tooltip `Measure[Cancelled Orders]`, `Measure[Late Orders]` |
| P1-C6 | clusteredColumnChart 2 series + legend | 824/192/448/300 | Đơn hủy (xám) và đơn trễ (cam) theo tháng — `Measure[Cancelled Orders]`, `Measure[Late Orders]` theo `Dim_Date[YearMonth]`; hai cột cạnh nhau từng tháng |

### Trang Vận hành (hàng filter y72–120, xem §2)

| ID | Visual | x/y/w/h | Nhãn + bindings + ghi chú |
|---|---|---|---|
| P2-C1 | cardVisual | 192/128/262/80 | Số đơn trễ — `Measure[Late Orders]` |
| P2-C2 | cardVisual 2 giá trị | 462/128/262/80 | Tỷ lệ trễ — `Measure[Late Rate]` + mẫu số `Measure[Late Eligible Orders]` (vùng riêng) |
| P2-C3 | cardVisual | 732/128/262/80 | Độ phủ dữ liệu trễ — `Measure[Late Coverage]` |
| P2-C4 | cardVisual 2 giá trị | 1002/128/262/80 | Giao trung vị — `Measure[Median Delivery Minutes]` + n `Measure[Delivery Eligible Orders]` |
| P2-C8 | 4 cardVisual | 192/462/732/1002 → y216 h80 w262 mỗi card | Chuẩn bị / Chờ xe / Di chuyển / Giao trung bình — `Measure[Avg Prep Minutes]`, `Measure[Avg Rider Wait Minutes]`, `Measure[Avg Travel Minutes]`, `Measure[Avg Delivery Minutes]`; KHÔNG ghi count giao làm n riêng từng bước |
| P2-C5 | barChart | 192/304/530/220 | Tỷ lệ trễ theo khung giờ — `Measure[Late Rate]` theo `Dim_TimeSlot[time_slot]`; tooltip `Measure[Late Orders]`, `Measure[Late Eligible Orders]`; click lọc chéo trong trang |
| P2-C6 | barChart | 734/304/538/220 | Tỷ lệ trễ theo nhóm km (giảm dần) — `Measure[Late Rate]` theo `Dim_DistanceBand[distance_band_normalized]`; sort GIẢM theo Late Rate (fallback đã chốt, nhãn km đầy đủ, title ghi rõ cách xếp — không hứa thứ tự tự nhiên vì model chưa có cột sort) |
| P2-C7 | tableEx | 192/524/1080/172 | Hủy/trễ theo khu vực — dòng `Dim_Zone[zone]`, các `Measure[Cancelled Orders]`, `Measure[Late Orders]`, `Measure[Late Rate]`; header + 5 dòng đầu, cuộn xem tiếp |

Hàng filter y72–120 (xem §2): Khung giờ `Dim_TimeSlot[time_slot]`, Mưa `Fact_Orders[is_rain]`, Nhóm km `Dim_DistanceBand[distance_band_normalized]` — chỉ trang này.

### Trang Tài chính

| ID | Visual | x/y/w/h | Nhãn + bindings + ghi chú |
|---|---|---|---|
| P3-C1..C3 | 3 cardVisual | 192/556/920 → y128 h96 w352 mỗi card | Giá trị đơn / Thu nhập / Chênh lệch ghi nhận — `Measure[Recorded Order Value]`, `Measure[Recorded Revenue]`, `Measure[Recorded Profit]` (đơn vị theo nguồn, không VND) |
| P3-C4..C6 | 3 cardVisual | y232 h96 w352 mỗi card | Biên chênh lệch — `Measure[Recorded Profit Margin]` (+tooltip `Measure[Recorded Profit]`/`Measure[Recorded Revenue]`); Số đơn âm (`Measure[Loss Orders]`); Tỷ lệ đơn âm (`Measure[Loss Rate]`) |
| P3-C7 | lineChart 1 series | 192/336/620/292 | Thu nhập theo tháng (triệu, số gốc) — `Measure[Recorded Revenue]` theo `Dim_Date[YearMonth]` |
| P3-C8 | tableEx | 824/336/448/292 | Thu nhập/chênh lệch/đơn âm theo khu vực — dòng `Dim_Zone[zone]`, các `Measure[Recorded Revenue]`, `Measure[Recorded Profit]`, `Measure[Loss Orders]`; header + 5 dòng đầu, cuộn xem tiếp; KHÔNG format tiền tệ |

Hàng filter y72–120 (xem §2, chip “Trạng thái: 0/1: Tất cả”): Trạng thái `Fact_Orders[is_cancelled]` (0 = xong theo quy tắc dự án, 1 = hủy) — chỉ trang này.

### Trang Khách hàng

| ID | Visual | x/y/w/h | Nhãn + bindings + ghi chú |
|---|---|---|---|
| P4-C1..C5 | 5 cardVisual | 192/408/624/840/1056 → y88 h104 w206 mỗi card | Khách có đơn (`Measure[Active Customers]`); Khách ≥2 lần (`Measure[Repeat Customers]`); Tỷ lệ lặp lại (`Measure[Repeat Customer Rate]`, tooltip `Measure[Repeat Customers]`/`Measure[Active Customers]`); Đơn bình quân (`Measure[Orders per Customer]`); Điểm trung bình (`Measure[Avg Rating]`, tooltip `Measure[Completed Orders]` = “số đơn hoàn tất trong nhóm”) |
| P4-C6 | columnChart | 192/216/530/332 | Số đơn theo nhãn khách — `Measure[Total Orders]` theo `Fact_Orders[customer_type]` (theo đơn, không phải chân dung khách) |
| P4-C7 | columnChart | 734/216/538/332 | Điểm theo đúng giờ/trễ — `Measure[Avg Rating]` theo `Fact_Orders[is_late]` (nhãn 0 = đúng giờ, 1 = trễ theo nguồn); visual filter `is_cancelled=0`; TẮT tương tác từ biểu đồ này sang các card khách (tránh biến so sánh điểm thành selection khách); tooltip Completed Orders |

Không slicer trễ riêng trang Khách (P4-C7 đã so hai nhóm). Không bảng mã khách/từng đơn.

## 4. Lọc, điều hướng, rỗng (khóa trước khi vẽ)

- Lọc chung đồng bộ 4 trang: khoảng ngày `Dim_Date[Date]` + `Dim_Zone[zone]` (sidebar).
  Riêng trang: slot/rain/band (Vận hành), is_cancelled (Tài chính). Cờ trễ KHÔNG sync
  sang trang khác. Chuyển trang giữ global + lựa chọn cục bộ.
- Nút “Xóa lọc” reset cả global và cục bộ về kỳ nguồn 01/03–31/08/2026 (KHÔNG “clear”
  thành cả 365 ngày lịch rồi gọi là mặc định).
- Click cột chỉ lọc visuals cùng trang có chủ đích; card tỷ lệ luôn kèm mẫu số nên cú
  click hẹp không tạo số gây hiểu nhầm.
- Rỗng: counts/sums = 0; rate/mean/median = trống (BLANK) — không đổi thành 0, không
  màu tốt/xấu, không target/SLA.
- Không cộng distinct khách giữa nhóm; Repeat tính lại trong selection.

## 5. Khả năng authoring đã tra (chỉ đọc) và phần chưa kiểm

- Đã tra read-only trong lượt sửa (không author/validate/reload): `powerbi-report-author`
  0.4.0 catalog cho `cardVisual` (role Data nhận nhiều measures + role Tooltips +
  objects referenceLabel* — đủ cho card 2 giá trị và mẫu số thấy thường trực),
  `slicer` (role Values + formatting dateRange — đủ cho slicer DateRange
  `Dim_Date[Date]`), `actionButton` tồn tại (nút Xóa lọc gắn bookmark khi authoring),
  catalog list đủ `clusteredColumnChart/barChart/columnChart/lineChart/tableEx/slicer/
  textbox/shape`; schema trang MS có `visualInteractions/NoFilter` (tắt tương tác
  từng visual). Sync slicer xuyên trang và bookmark reset là cấu hình khi authoring.
- Sort YearMonth theo field thời gian qua sortDefinition trong query (ghi theo skill).
  Sort tự nhiên nhóm km CHƯA có capability không sửa model — giữ fallback bar giảm theo
  Late Rate đã ghi trong P2-C6.
- Chưa kiểm: TẤT CẢ runtime (render, tương tác, sync, reset, tương phản thực,
  persistence) — toàn bộ là Phase 5C. Preview là phác tĩnh matplotlib, không phải render.

## 6. Phác tĩnh để duyệt (`reports/phase5b/`, ghi rõ MOCKUP)

4 ảnh wireframe 1280×720: khung xám + nhãn + số baseline Pilot2 (hoặc chữ “minh họa”).
Không phải screenshot native/render/test.

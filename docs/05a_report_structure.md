# Cấu trúc report Pilot2 — Phase 5A (chốt để duyệt, chưa vẽ)

Tài liệu này để người dùng duyệt: mỗi trang trả lời việc gì, xem số/biểu đồ nào, lọc
thế nào và quyết định gì. Chưa tọa độ/font/màu/theme (Phase 5B), chưa vẽ (Phase 5C).
Mọi binding đều có thật trong model đã nghiệm thu; kiểm ở cuối file.

Nguồn số baseline: `reports/phase4b/tables.json` (kỳ 01/03–31/08/2026, 6.073 đơn).
Đơn vị tiền là số ghi nhận gốc (không VND); nhãn trễ theo nguồn (không phải vi phạm SLA).

## Trang 1 — Tổng quan: có đáng xem sâu không?

Câu hỏi: lượng đơn, hủy/trễ và kết quả ghi nhận thay đổi thế nào; nên xem sâu phần nào?

| ID | Kiểu | Nhãn | Binding chính | Trục/nhóm | Đơn vị, mẫu số, sort, filter |
|---|---|---|---|---|---|
| P1-C1 | card | Tổng số đơn | `Measure[Total Orders]` | — | đơn; tooltip `Measure[Completed Orders]`, `Measure[Cancelled Orders]` |
| P1-C2 | card | Tỷ lệ hủy | `Measure[Cancellation Rate]` | — | % = hủy/(xong+hủy); tooltip tử/mẫu |
| P1-C3 | card | Tỷ lệ trễ | `Measure[Late Rate]` | — | % = trễ/đủ điều kiện; tooltip tử/mẫu (bắt buộc để không hiểu nhầm) |
| P1-C4 | card | Chênh lệch ghi nhận | `Measure[Recorded Profit]` | — | số gốc; tooltip Revenue/Margin |
| P1-C5 | line | Đơn theo tháng | `Measure[Total Orders]` | `Dim_Date[YearMonth]`, sort theo thời gian | đơn/tháng; tooltip thêm Cancelled/Late Orders |
| P1-C6 | column | Đơn hủy và đơn trễ theo tháng | `Measure[Cancelled Orders]`, `Measure[Late Orders]` | `Dim_Date[YearMonth]` | đơn; hai cột cạnh nhau, không stacked tỷ lệ |

Quyết định sau trang: tháng nào bất thường (tháng 8) thì sang Vận hành/Tài chính xem nhóm.

## Trang 2 — Vận hành: kiểm nhóm nào trước?

Câu hỏi: ca/khu vực/mưa/khoảng cách nào cần kiểm trước; bước thời gian nào đáng xem?

| ID | Kiểu | Nhãn | Binding chính | Trục/nhóm | Đơn vị, mẫu số, sort, filter |
|---|---|---|---|---|---|
| P2-C1 | card | Số đơn trễ | `Measure[Late Orders]` | — | đơn |
| P2-C2 | card | Tỷ lệ trễ (+mẫu số) | `Measure[Late Rate]` + tooltip `Measure[Late Eligible Orders]` | — | % + mẫu số luôn hiển thị |
| P2-C3 | card | Độ phủ dữ liệu trễ | `Measure[Late Coverage]` | — | % |
| P2-C4 | card | Thời gian giao trung vị | `Measure[Median Delivery Minutes]` + tooltip `Measure[Delivery Eligible Orders]` | — | phút (tên trường) + n |
| P2-C5 | bar | Tỷ lệ trễ theo khung giờ | `Measure[Late Rate]` | `Dim_TimeSlot[time_slot]` | %; tooltip Late/Late Eligible; click lọc chéo các card/table cùng trang |
| P2-C6 | bar | Tỷ lệ trễ theo nhóm km | `Measure[Late Rate]` | `Dim_DistanceBand[distance_band_normalized]`, sort theo thứ tự khoảng cách | %; tooltip Late/Late Eligible |
| P2-C7 | table | Hủy/trễ theo khu vực | `Measure[Cancelled Orders]`, `Measure[Late Orders]`, `Measure[Late Rate]` | dòng `Dim_Zone[zone]` | đơn + %; click dòng lọc chéo |
| P2-C8 | card ×4 | Chuẩn bị / Di chuyển / Chờ xe / Giao trung bình | `Measure[Avg Prep Minutes]`, `Measure[Avg Travel Minutes]`, `Measure[Avg Rider Wait Minutes]`, `Measure[Avg Delivery Minutes]` | — | phút + tooltip n (Delivery Eligible Orders); KHÔNG stacked cộng các bước (chưa rõ chồng lấn) |

Slicer trang: `Dim_TimeSlot[time_slot]`, `Fact_Orders[is_rain]` (nhãn 0/1 giải thích:
0 = cờ không mưa, 1 = cờ mưa theo nguồn), `Dim_DistanceBand[distance_band_normalized]`.
Lưu ý đã duyệt: bấm riêng nhóm trễ (is_late=1) làm Late Rate = 100% là đúng toán nhưng
vô nghĩa quyết định — card P2-C2 luôn kèm mẫu số để không ai đọc nhầm.

## Trang 3 — Tài chính: tiền ghi nhận ra sao, đơn âm ở đâu?

Câu hỏi: giá trị đơn, thu nhập, chênh lệch ghi nhận ra sao; đơn âm ở đâu?

| ID | Kiểu | Nhãn | Binding chính | Trục/nhóm | Đơn vị, mẫu số, sort, filter |
|---|---|---|---|---|---|
| P3-C1 | card | Giá trị đơn ghi nhận | `Measure[Recorded Order Value]` | — | số gốc (không gọi GMV/doanh thu thực thu) |
| P3-C2 | card | Thu nhập ghi nhận | `Measure[Recorded Revenue]` | — | số gốc (phạm vi kế toán pending) |
| P3-C3 | card | Chênh lệch ghi nhận | `Measure[Recorded Profit]` | — | số gốc (chưa phải lãi kế toán) |
| P3-C4 | card | Biên chênh lệch | `Measure[Recorded Profit Margin]` | — | % = tổng/tổng; tooltip tử/mẫu |
| P3-C5 | card | Số đơn âm | `Measure[Loss Orders]` | — | đơn (giữ lại, không phải lỗi xóa) |
| P3-C6 | card | Tỷ lệ đơn âm | `Measure[Loss Rate]` | — | % = âm/đơn có profit |
| P3-C7 | line | Thu nhập theo tháng | `Measure[Recorded Revenue]` | `Dim_Date[YearMonth]` | số gốc |
| P3-C8 | table | Thu nhập/chênh lệch/đơn âm theo khu vực | `Measure[Recorded Revenue]`, `Measure[Recorded Profit]`, `Measure[Loss Orders]` | dòng `Dim_Zone[zone]` | số gốc + đơn; KHÔNG cột VND/format tiền tệ |

Quyết định sau trang: khu vực/tháng nào chênh lệch thấp thì đối chiếu vận hành (trang 2).

## Trang 4 — Khách hàng: ai mua, mấy lần, điểm thế nào?

Câu hỏi: bao nhiêu khách có đơn, bao nhiêu đặt ≥2 lần trong lựa chọn; điểm đánh giá
liên quan nhóm nào?

| ID | Kiểu | Nhãn | Binding chính | Trục/nhóm | Đơn vị, mẫu số, sort, filter |
|---|---|---|---|---|---|
| P4-C1 | card | Số khách có đơn | `Measure[Active Customers]` | — | khách distinct trong lựa chọn (KHÔNG cộng distinct giữa nhóm) |
| P4-C2 | card | Số khách đặt ≥2 lần | `Measure[Repeat Customers]` | — | khách; tính lại trong selection |
| P4-C3 | card | Tỷ lệ khách lặp lại | `Measure[Repeat Customer Rate]` | — | %; tooltip tử/mẫu; không gọi retention/churn |
| P4-C4 | card | Đơn bình quân một khách | `Measure[Orders per Customer]` | — | đơn/khách |
| P4-C5 | card | Điểm trung bình (+n) | `Measure[Avg Rating]` | — | điểm nguồn + tooltip n (thang chưa xác nhận độc lập) |
| P4-C6 | column | Số đơn theo nhãn khách (theo đơn) | `Measure[Total Orders]` | `Fact_Orders[customer_type]` | đơn; nhãn theo đơn, không phải chân dung khách |
| P4-C7 | card | Điểm nhóm trễ vs đúng giờ (tham khảo) | `Measure[Avg Rating]` + slicer `Fact_Orders[is_late]` | — | chỉ đi cùng nhau, không kết luận nguyên nhân |

Cấm: bảng liệt kê mã khách/từng đơn; biểu đồ cộng distinct khách giữa các nhóm
(vì một khách có đơn ở nhiều nhóm sẽ bị đếm trùng).

## Hành vi lọc và điều hướng (chốt trước khi vẽ)

- Mặc định: kỳ nguồn 01/03–31/08/2026, toàn khu vực, mọi trạng thái. Lọc dùng chung
  đồng bộ xuyên trang: `Dim_Date[Date]` (khoảng ngày) và `Dim_Zone[zone]`.
- Riêng từng trang: slot/rain/band (trang 2), trạng thái hủy — `Fact_Orders[is_cancelled]`
  (0 = xong theo quy tắc dự án, 1 = hủy), cờ trễ/mưa 0/1 theo nguồn.
- Nút “Xóa lọc” trở về mặc định trên. Chuyển trang giữ nguyên context đang lọc.
- Biểu đồ click để lọc chéo chỉ trong trang chứa nó; card tỷ lệ luôn kèm mẫu số trong
  tooltip để cú click hẹp không tạo số 100%/0% gây hiểu nhầm.
- Rỗng (không có dòng): counts/sums hiện 0; rate/mean/median hiện trống (BLANK) —
  không đổi thành 0, không tô màu tốt/xấu, không đưa target/SLA chưa xác nhận vào màu.
- Sort: tháng theo `Dim_Date[MonthNumber]` (đã đặt trong model); YearMonth theo thời gian;
  nhóm km theo thứ tự khoảng cách (sort tay trong visual, không sửa model).

## Mapping câu hỏi Phase 0 → claims C1–C7 → trang

| Câu hỏi Phase 0 | Claims | Trang |
|---|---|---|
| Lượng đơn theo thời gian | C1 | Tổng quan (P1-C5, P1-C6) |
| Hủy/trễ ở đâu | C1–C4 | Vận hành (P2-C5, P2-C6, P2-C7) |
| Bước thời gian nào | C6 | Vận hành (P2-C4, P2-C8) |
| Tiền ghi nhận thế nào | C5 | Tài chính (P3-C1..C8) |
| Theo nhóm nào | C2–C4 | Vận hành (P2-C5..C7) |
| Khách và điểm | C7 | Khách hàng (P4-C1..C7) |

Mọi baseline nhắc trong tài liệu truy về `reports/phase4b/tables.json`; không bịa mốc
mới, không gắn kết luận cố định làm title động cho mọi selection.

## Kiểm kế hoạch (chỉ đọc registry/TMDL, không render)

- 25/25 measure bindings tồn tại đúng folder/format; fields dimension/sort/filter tồn tại
  đúng bảng (xem `Log/phase5a/validation.json`).
- Không phát minh binding: mọi measure nêu tên có trong registry; mọi field trong TMDL;
  không SUM cờ numeric, không average tỷ lệ/số khách.
- Nguồn/P1/P2/P4/P4B/shell giữ hashes (xem run). Đây là chứng minh **kế hoạch khả thi**,
  chưa kiểm native canvas/render/tương tác — đó là Phase 5C.

# Model ngữ nghĩa GiaoNong Pilot2 — Phase 3

Kỹ thuật xong, trình Human Gate 3. Chưa measures (Phase 4), chưa dashboard.

Nguồn nạp: `data/curated/orders.csv` (SHA `0e0f603d…6d286c3`, 6.073 dòng, 29 cột).
Project mới: `pbi/GiaoNongPilot2.pbip` + `GiaoNongPilot2.SemanticModel/` + `GiaoNongPilot2.Report/` (shell trống).
TMDL do engine xuất từ model tự dựng qua MCP, không sao chép dự án cũ.

## Cách đọc đơn giản

Bảng đơn `Fact_Orders` là sổ chính: một dòng một đơn. Năm bảng còn lại là mục lục để lọc đúng:
ngày, khách, khu vực, khung giờ, nhóm khoảng cách. Bấm vào mục lục thì sổ tự lọc theo,
không nhân đôi đơn. Nhãn khách, tiền, cờ trễ/mưa, khung giờ vẫn nằm trên sổ theo nguồn,
đơn vị tiền và ngưỡng trễ còn pending nên chưa đặt tên tiền tệ hay viết công thức.

## Sơ đồ quan hệ ( fact nhiều → mục lục một, lọc một chiều, đều active )

```text
Dim_Date ──── order_date
Dim_Customer ─ customer_id
Dim_Zone ───── zone               ┌─────────────┐
Dim_TimeSlot ─ time_slot ────────>│ Fact_Orders │  6.073 dòng / order_id duy nhất
Dim_DistanceBand ─ band ──────────│ 29 cột nguồn│
                                  └─────────────┘
```

| Quan hệ | Từ (nhiều) | Đến (một) | Lọc |
|---|---|---|---|
| Fact_Orders_order_date_Dim_Date_Date | Fact_Orders.order_date | Dim_Date.Date | một chiều, active |
| Fact_Orders_customer_id_Dim_Customer_customer_id | Fact_Orders.customer_id | Dim_Customer.customer_id | một chiều, active |
| Fact_Orders_zone_Dim_Zone_zone | Fact_Orders.zone | Dim_Zone.zone | một chiều, active |
| Fact_Orders_time_slot_Dim_TimeSlot_time_slot | Fact_Orders.time_slot | Dim_TimeSlot.time_slot | một chiều, active |
| Fact_Orders_band_Dim_DistanceBand_band | Fact_Orders.distance_band_normalized | Dim_DistanceBand.distance_band_normalized | một chiều, active |

## Bảng và cột

| Bảng | Dòng (runtime) | Cột | Nguồn M |
|---|---|---|---|
| Fact_Orders | 6.073 | 29 cột curated (source_row_number ẩn, không cộng tổng) | SharedOrders qua |
| Dim_Date | 365 | Date, Year, MonthNumber, Month (sort theo MonthNumber), YearMonth (đánh dấu Date table) | lịch liên tục 01/01–31/12/2026, sinh động theo năm nguồn |
| Dim_Customer | 2.098 | customer_id (chỉ khóa ổn định) | distinct từ SharedOrders |
| Dim_Zone | 8 | zone | distinct từ SharedOrders |
| Dim_TimeSlot | 5 | time_slot (giữ nhãn nguồn, không suy ranh giờ) | distinct từ SharedOrders |
| Dim_DistanceBand | 4 | distance_band_normalized (nhãn đã duyệt) | distinct từ SharedOrders |

Truy vấn nguồn: parameter `DataFolder` → `E:/Practice_DSEA/DA/OpenSrcDA/GiaoNgon/data/curated`;
shared query `SharedOrders` đọc `orders.csv` UTF-8 BOM, 29 cột, culture `en-US`,
kiểu ngày/số/cờ/chữ rõ theo manifest; giữ null đơn hủy; không transform tiền/SLA mới.
Không measures (TotalMeasureCount 0), customer_type ở trên fact theo đơn.

## Đã kiểm (native, xem `reports/phase3/validation_native.json`)

- Desktop mở đúng project mới (PID 22652, cổng 53869), model `GiaoNongPilot2` nạp ~1,45 MB.
- Đếm runtime khớp nguồn: fact 6.073, khách 2.098, khu vực 8, khung giờ 5, nhóm 4, ngày 365.
- Lọc đủ 5 mục lục: ngày 01/03 có 26 đơn, Trưa 2.087 (trễ 257), ≥6 km 463 (trễ 250),
  Quận 1 có 963 đơn (trễ 114), mưa+trễ 469, khách phủ đủ 2.098, ngày không có đơn trả 0
  (đếm rỗng trong DAX ra BLANK nên query dùng COALESCE, lưu cả raw).
- Mồ côi 0 ở cả 5 quan hệ (raw BLANK, COALESCE ra 0, có ghi quy tắc).
- Tổng đủ 8 cột tiền khớp exact; giữ 348 đơn hủy, 1.320 đơn âm, null vận hành 348;
  lý do hủy là chuỗi rỗng 5.725 + có nội dung 348 (cột text giữ "", không phải null).
- Lịch phủ cả năm 2026 (01/01–31/12), 12 tháng; order_id duy nhất 6.073/6.073.
- Mở lại project sau lưu vẫn nạp đúng, Month sort còn giữ.
- Giới hạn ghi rõ: refresh offline qua MCP báo lỗi hệ thống trong môi trường này
  (đã vượt qua bằng Desktop load + refresh Full qua Desktop); chưa KPI/dashboard;
  tiền/SLA/nguồn nhãn còn pending.
- Lượt trước đóng Desktop bằng lệnh theo tên (quá rộng, đã ghi nhận); lượt sửa này chỉ
  đóng đúng PID sở hữu sau khi export đã lưu revision, và mở lại chứng minh bản lưu dùng được.

## Tái chạy và bằng chứng

`python -X utf8 scripts/phase3.py --run` dựng files + expected + log file/schema/provenance.
`Log/phase3/run.json` (lệnh/exit/hash), `Log/phase3/validation.json` (39 kiểm file),
`reports/phase3/expected.json` + `validation_native.json` (runtime thật).

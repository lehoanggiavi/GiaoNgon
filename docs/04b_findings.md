# Phát hiện và đề xuất Pilot2 — Phase 4B

Kỹ thuật xong, trình Human Gate 4B. Chưa dashboard, chưa report TEX.

Nguồn: 6.073 đơn (`data/curated/orders.csv`), kỳ 01/03–31/08/2026. Mọi số dưới đây đếm
lại từ nguồn; đường dẫn bảng số: `reports/phase4b/tables.json`. Đơn vị tiền là số ghi
nhận gốc, chưa gọi là VND. Nhãn trễ theo nguồn, chưa đồng nghĩa vi phạm SLA.

## Hiểu nhanh

Sổ đơn 6 tháng cho thấy ba nhóm nổi bật về trễ: buổi tối, lúc mưa và các đơn từ 6 km
trở lên; tháng 8 xấu nhất cả hủy lẫn trễ. Đơn hủy không thu được đồng nào nhưng vẫn
tốn tiền bồi thường.

## Đã thấy gì (mỗi ý: số thật → nghĩa → giới hạn)

**1. Tháng 8 xấu nhất kỳ.** 1.144 đơn (nhiều nhất), hủy 147 (12,8% so với 2,7–7,1%
các tháng trước), trễ 250/997 (25,1% so với 4,6–15,9%). Nghĩa: cuối kỳ vừa đông vừa
rối. Giới hạn: chưa biết tháng 8 khác gì (nhu cầu, thời tiết, nhân sự) — cần hỏi tiếp,
không đoán nguyên nhân.

**2. Buổi tối nổi bật so với các khung đã quan sát.** Giờ Tối có 2.135 đơn (35%),
hủy 198 (9,27%; các khung khác 2,42–4,17%), trễ 391/1.937 (20,19%; các khung khác
4,96–12,85%). 57% đơn hủy và 52% đơn trễ của cả kỳ rơi vào buổi tối. Nghĩa: ca tối là
ứng viên ưu tiên để soi vận hành. Giới hạn: chỉ so các nhóm đã quan sát, không suy
thành quy luật tăng dần theo giờ; chưa có ranh giờ thực và định mức ca.

**3. Trời mưa trễ gấp ba.** Mưa: trễ 469/2.001 (23,4%); không mưa: 281/3.724 (7,5%).
Hủy khi mưa 8,6% so với 4,1%. Nghĩa: mưa đi cùng đơn trễ/hủy nhiều hơn. Giới hạn: nhãn
mưa chưa rõ nguồn đo; mưa không chứng minh gây trễ (có thể do đường đông, thiếu tài xế
đúng lúc mưa). Không suy nhân quả.

**4. Trễ tăng dần qua từng nhóm khoảng cách đã quan sát.** Trễ theo nhóm chuẩn:
<2 km 4,30% (53/1.232); 2–<4 km 8,28% (241/2.910); 4–<6 km 18,01% (206/1.144);
≥6 km 56,95% (250/439). Hủy thì phẳng ~5–6% mọi nhóm. Nghĩa: trong dữ liệu quan sát,
nhóm xa hơn đi cùng tỷ lệ trễ cao hơn; hủy không theo khoảng cách. Giới hạn: đây là
mô tả các nhóm đã thấy, chưa chứng minh khoảng cách gây trễ và chưa có ngưỡng cam kết
theo km nên không gọi nhóm xa là “quá hạn cho phép”.

**5. Đơn hủy: không thu, vẫn tốn bồi thường.** 348 đơn hủy mang 27.426.000 giá trị
ghi nhận nhưng thu nhập 0, bồi thường 7.224.000. Toàn kỳ có 1.320 đơn chênh lệch ghi
nhận âm (21,74%), rải các khu vực ở tỷ lệ 19,75–22,99% — không khu vực nào vượt trội.
Nghĩa: hủy đi cùng chi phí bồi thường thấy được; đơn âm không phải lỗi để xóa.
Giới hạn: đây là chênh lệch ghi nhận, chưa phải lỗ kế toán đầy đủ (phạm vi chi phí
chưa xác nhận).

**6. Thời gian: đi đường nặng nhất, chờ xe lệch phải.** Trên 5.725 đơn xong: chuẩn bị
11,47 (trung vị 11,10), chờ tài xế 6,17 (trung vị 4,60 — lệch phải, có đuôi chờ lâu),
di chuyển 12,59, tổng 30,22 (trung vị 28,80). Nghĩa: di chuyển là bước tên dài nhất;
đuôi chờ xe dài đáng soi. Giới hạn: chưa xác nhận các bước có chồng nhau không nên
không cộng dồn bước và không chỉ tay bước nào gây trễ.

**7. Trễ đi cùng điểm thấp; khách lặp lại ở mức đếm.** Đơn trễ điểm trung bình 3,86
(n=750) so với đúng giờ 4,70 (n=4.975). 1.261/2.098 khách (60,1%) đặt từ 2 đơn trong kỳ.
Nghĩa: trải nghiệm trễ gắn với điểm thấp — chỉ là đi cùng nhau, chưa chứng minh trễ
làm mất điểm hay khách khó tính dễ gặp trễ. Nhãn Mới/Quay lại tính theo đơn, số lặp
lại theo lựa chọn, không phải giữ chân/rời bỏ (không có lịch sử ngoài kỳ).

## Bảng claims (truy vết đầy đủ)

| ID | Câu hỏi | KPI (contract P4) | Kỳ/nhóm | Tử/mẫu/n | Giá trị | Bảng số | Giới hạn |
|---|---|---|---|---|---|---|---|
| C1 | Lượng đơn theo tháng | Total/Cancelled/Late | 2026-03→08 | xem bảng | hủy 2,7%→12,8%; trễ 4,6%→25,1% | tables.json→month | Chưa rõ nguyên nhân tháng 8 |
| C2 | Hủy/trễ giờ nào | Cancelled/Late + Rate | 5 khung giờ | Tối: hủy 198/2135; trễ 391/1937 | 9,27%; 20,19% | →slot | Chưa ranh giờ thực/định mức |
| C3 | Mưa | Late + Rate | cờ 0/1 | trễ 469/2001 vs 281/3724 | 23,44% vs 7,55% | →rain | Nhãn mưa pending; không nhân quả |
| C4 | Khoảng cách | Late + Rate | 4 nhóm chuẩn | 53/1232 → 250/439 | 4,30% → 56,95% đơn điệu | →band | Chưa ngưỡng cam kết theo km |
| C5 | Tiền/đơn âm | Revenue/Profit/Loss | toàn kỳ + hủy | hủy: thu 0/bồi thường 7,2tr; âm 1320/6073, theo khu vực 19,75–22,99% | -7.224.000 (ghi nhận); 21,74% | →money* | Đơn vị gốc; chưa phải lỗ kế toán |
| C6 | Thời gian bước nào | Avg/Median + n riêng | 5.725 đơn xong | n=5725 mỗi bước | 11,47/6,17/12,59/30,22; med 28,80 | →times | Chưa xác nhận chồng lấn |
| C7 | Khách/điểm | Active/Repeat/Rating | toàn kỳ | lặp 1261/2098; điểm trễ 750 vs đúng giờ 4975 | 60,10%; 3,86 vs 4,70 | →cust/rating* | Không retention; điểm chỉ đi cùng |

## Một hành động ưu tiên (thử nghiệm, chưa phải thành tích)

**Ai làm:** người phụ trách vận hành ca tối cùng chủ dữ liệu.
**Làm gì:** chọn MỘT thay đổi để thử trước (ví dụ: phân tài xế ca Tối ở 2–3 khu vực
đông đơn nhất), giữ nguyên cách ghi nhãn. Trước thử phải chốt: vùng/ca/định nghĩa trễ
(SLA), rồi tính baseline trên cùng phạm vi đó ở kỳ so sánh đủ tương đồng (ví dụ cùng
ca Tối 2 tuần liền trước) — số lịch sử 20,19% toàn kỳ 6 tháng chỉ để tham khảo, không
làm baseline.
**Theo dõi số nào:** tỷ lệ trễ ca Tối kèm tử/mẫu/n, tỷ lệ hủy ca Tối kèm tử/mẫu, và tiền
bồi thường trên mỗi đơn ca Tối — tính lại từ nguồn, không trung bình tỷ lệ, không so
198 đơn hủy của 6 tháng với 2 tuần thử.
**Khi nào đánh giá:** hết kỳ thử so với baseline cùng phạm vi; nếu cỡ mẫu chưa đủ hoặc
kết quả dao động thì ghi “chưa kết luận”, không tự dừng/đổi hướng. **Cần hỏi chủ dữ
liệu trước:** ngưỡng trễ, ranh giờ ca, đơn vị tiền — không có thì không gọi
“đạt/không đạt”. Không cam kết ROI/target; đây là thử nghiệm đề xuất, chưa làm.

## Phụ lục: công thức dùng (tên theo registry Phase 4)

Total Orders = COUNTROWS; Cancellation Rate = hủy/(xong+hủy); Late Rate = trễ/đủ điều
kiện; trung bình = AVERAGE trên đơn xong có giá trị ≥0 (n riêng); Margin = tổng/tổng;
Repeat = khách ≥2 đơn trong lựa chọn. Đếm/tổng ra 0 khi trống; tỷ lệ/trung bình/trung vị
ra trống khi thiếu mẫu. Chi tiết: `reports/phase4/registry.json`, `docs/04_measures.md`.

## Kiểm chứng và giới hạn bàn giao

- Helper `scripts/phase4b.py --check`: tổng khớp P4, phân hoạch cộng đủ, tỷ lệ = tử/mẫu,
  không cộng median/distinct — 58/58 PASS (`Log/phase4b/validation.json`).
- Không chart mới (bảng đã đủ), không sửa model/report/Desktop/skill, không chạy lại
  pipeline hay 107 checks Phase 4. Không in mã khách/từng giao dịch.

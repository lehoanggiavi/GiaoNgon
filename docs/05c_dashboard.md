# Dashboard Pilot2 — bản bố cục để review

Supervisor đã tiếp quản Phase5C theo quyền được duyệt. OpenCode không được giao lượt mới.

## Giải thích dễ hiểu

Bản trước giống một tờ giấy chỉ viết ở nửa trên. Bản này đặt nhóm số ở góc trên
trái, biểu đồ chính bên phải và các ô phân tích phủ phần dưới, theo cách sắp xếp
của mẫu tham chiếu. Bốn trang đều dùng nền kem, thanh bên màu ấm và điểm nhấn cam.

Các biểu đồ thêm vào chỉ chia những chỉ số Pilot2 đã có theo tháng, khu vực,
khung giờ hoặc cờ mưa. Không lấy công thức, code, theme, mô hình hay kết quả mẫu.
Dữ liệu đầu vào vẫn là CSV người dùng cung cấp bên trong GiaoNgon.

Ví dụ **13,10% trễ** nghĩa là **750 đơn trễ trong 5.725 đơn đủ điều kiện**,
không phải chia cho toàn bộ 6.073 đơn. Chênh lệch ghi nhận50,86 triệu dùng đơn vị
nguồn; chưa kết luận là lợi nhuận kế toán hoặc tiền VND. Khách ≥2 lần được tính
lại trong kỳ đang chọn.

## Bố cục hiện tại

Canvas1280×720; nội dung x192–1272, thanh bên x0–180. Hai cột ô phân tích cách
nhau12px. Thẻ số có vùng riêng cho tên, giá trị và mẫu số/đơn vị để không cắt chữ.

| Trang | Nhóm số bên trái | Biểu đồ chính bên phải | Phần dưới |
|---|---|---|---|
| Tổng quan | 4 thẻ, 2×2, y76–264 | Số đơn theo tháng | Hủy/trễ theo tháng; hoàn tất/hủy theo khung giờ; tỷ lệ trễ và số đơn theo khu vực |
| Vận hành | 4 thẻ, 2×2, y140–308 | Tỷ lệ trễ theo nhóm km giảm dần | Tỷ lệ trễ theo khung giờ; 4 số thời gian; bảng khu vực; tỷ lệ trễ theo cờ mưa |
| Tài chính | 6 thẻ, 2×3, y140–360 | Thu nhập ghi nhận theo tháng | Thu nhập/chênh lệch theo tháng; tỷ lệ đơn âm; bảng khu vực; biên chênh lệch theo khu vực |
| Khách hàng | 5 thẻ, y76–308 | Điểm theo cờ đúng giờ/trễ | Nhãn khách theo đơn; khách có đơn/≥2 lần theo tháng; số đơn và khách theo khu vực |

Khung giờ/Mưa/Nhóm km ở hàng lọc riêng của Vận hành; Trạng thái ở hàng lọc riêng
của Tài chính. Ngày và Khu vực cấu hình đồng bộ; bookmark Xóa lọc về
01/03–31/08/2026 và tất cả khu vực. Biểu đồ điểm chỉ xét đơn hoàn tất và không
lọc các thẻ khách. Cần kiểm lại hành vi trên bản cuối.

## Đã kiểm và còn thiếu

- Đã bấm Save trong Desktop đúng PID14088/project Pilot2. Bản lưu còn đủ4 trang
  enhanced PBIR, không có report legacy rỗng.
- Đã xem cả4 ảnh native sau Save tại reports/phase5c/layout_review/.
  Số chính khớp baseline:6.073 đơn, hủy5,73%, trễ13,10%/mẫu số5.725,
  thu nhập203,34 triệu, chênh lệch50,86 triệu, 2.098 khách.
- Schema online trước Save:0 lỗi/0 cảnh báo. Cấu trúc sau Save:0 lỗi/0 cảnh báo,
  chế độ offline. Lần xin chạy schema online sau Save bị từ chối quyền, chưa chạy.
- Save native ghi lại metadata model.tmdl. Đã giữ bản sau Save làm bằng chứng,
  khôi phục đúng byte có SHA đã duyệt; không sửa công thức hoặc dữ liệu.
- **Chưa nghiệm thu Phase5C:** người dùng cần xem bố cục; còn kiểm bộ lọc riêng,
  reset xuyên trang, tương tác biểu đồ, trạng thái rỗng và mở lại đủ4 trang cuối.
  Kiểm một trang lưu/mở lại trước đó không thay kiểm bản4 trang cuối.

Bằng chứng/hash revision: Log/phase5c/layout_review.json.
Không mở Phase6 hoặc viết TEX/PDF trong lượt này.

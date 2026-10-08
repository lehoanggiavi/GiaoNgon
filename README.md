# GiaoNgon — phân tích kinh doanh giao đồ ăn

Phân tích 6.073 đơn giao đồ ăn bằng Python và Power BI, kết nối các chỉ số vận hành với vấn đề kinh doanh và đề xuất hành động có đo lường.

## Xem kết quả

- [Báo cáo kinh doanh PDF](docs/bao_cao_ban_giao.pdf): 8 trang, gồm phát hiện, ảnh dashboard và đề xuất ưu tiên.
- [Dashboard Power BI](pbi/GiaoNongPilot2.pbip): bốn trang Tổng quan, Vận hành, Tài chính và Khách hàng. Giữ các thư mục `.Report` và `.SemanticModel` bên cạnh file PBIP.
- [Ảnh dashboard hiện hành](reports/phase5c/final_reopen/).
- [Hướng dẫn bàn giao và giới hạn](docs/BAN_GIAO.md).

## Phát hiện và hướng hành động

- 348/6.073 đơn bị hủy; 750/5.725 đơn không hủy giao trễ, tương đương 13,10%.
- Lượng đơn tháng 8 tăng 24,35% so với tháng 3, trong khi tỷ lệ trễ tăng từ 5,97% lên 25,08%.
- Ca Tối chiếm 52,13% số đơn trễ và 56,90% số đơn hủy. Ưu tiên rà quy trình ca Tối, chốt định nghĩa trễ và thử một thay đổi nhỏ có đo trước–sau trên cùng phạm vi.

Các mối liên hệ trên chưa chứng minh nguyên nhân hay hiệu quả cải thiện đã đạt được. Đơn vị tiền tệ và toàn bộ chi phí kế toán chưa được xác nhận.

## Mở trên máy khác

1. Clone repo và mở `pbi/GiaoNongPilot2.pbip` bằng Power BI Desktop hỗ trợ PBIP.
2. Vào **Transform data → Edit parameters → DataFolder**, chọn đường dẫn tuyệt đối đến `data/curated` trong repo rồi Refresh.
3. Xem báo cáo và đối chiếu các số tổng trước khi sử dụng bộ lọc.

Nguồn ở `data/giaongon_orders_2026.csv`; dữ liệu chuẩn hóa ở `data/curated/orders.csv`. Notebook và script phân tích nằm trong `notebooks/` và `scripts/`. Không cần chạy lại pipeline để mở dashboard; các script tạo output có thể ghi đè bản hiện hành.

## Trạng thái

Bố cục bốn trang đã được duyệt và có ảnh mở lại bản lưu. Kiểm thử tương tác cuối cho bộ lọc, đồng bộ giữa trang, nút Xóa lọc và lựa chọn rỗng còn chưa hoàn tất; thao tác chuyển máy chưa được kiểm thử. Đây là bản bàn giao hiện hành, chưa phải xác nhận nghiệm thu toàn bộ chức năng.

Repo chứa dữ liệu, mã phân tích, mô hình Power BI, tài liệu và bằng chứng hình ảnh. Log điều phối, kế hoạch, bản sao lưu và cấu hình máy được giữ ở workspace cục bộ; các tham chiếu lịch sử đến chúng trong tài liệu không phải bằng chứng kiểm thử công khai của revision này.

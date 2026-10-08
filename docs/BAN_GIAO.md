# Bàn giao GiaoNong Pilot 2

Ngày bàn giao: **08/10/2026**. Báo cáo do supervisor trực tiếp viết theo yêu cầu của người dùng.

## Mở gì trước?

1. Đọc [báo cáo kinh doanh PDF](bao_cao_ban_giao.pdf): vấn đề lượng đơn/chất lượng giao, bằng chứng, ảnh cả bốn trang dashboard, ảnh hưởng kinh doanh, đề xuất và quyết định cần chốt. Bản hiện hành 8 trang; hướng dẫn sử dụng và nghiệm thu nằm riêng ở tài liệu này.
2. Mở [dashboard Power BI](../pbi/GiaoNongPilot2.pbip). Giữ cả hai thư mục `.Report` và `.SemanticModel` bên cạnh file này.
3. Khi cần sửa nội dung báo cáo, dùng [file TEX](bao_cao_ban_giao.tex).

Dashboard có bốn trang: **Tổng quan, Vận hành, Tài chính, Khách hàng**. Bố cục đã được người dùng duyệt. Đã mở lại và xem ảnh thật cả bốn trang tại [ảnh kiểm bản lưu](../reports/phase5c/final_reopen/).

## Các số có nghĩa gì?

- Có **6.073 đơn**, trong đó **348 đơn hủy**: cứ 100 đơn thì khoảng 6 đơn bị hủy.
- Có **750 đơn trễ trên 5.725 đơn đủ dữ liệu**, tương đương **13,10%**. Không lấy cả đơn hủy làm mẫu số của tỷ lệ trễ.
- Có **2.098 khách**, trong đó **1.261 khách đặt từ hai đơn trong kỳ**. Con số này chưa cho biết khách có tiếp tục mua sau kỳ hay không.
- Thu nhập ghi nhận **203,34 triệu**, chênh lệch ghi nhận **50,86 triệu** theo đơn vị của nguồn. Chưa xác nhận đơn vị tiền tệ và toàn bộ chi phí kế toán.

Phát hiện cần ưu tiên: ca Tối, lúc mưa và nhóm từ 6 km trở lên có tỷ lệ trễ cao. Đây là dấu hiệu cần tìm hiểu thêm; chưa chứng minh nguyên nhân. Một bước nên làm trước là trao đổi với phụ trách ca Tối, chốt định nghĩa trễ và thử một thay đổi nhỏ có đo trước–sau trên cùng phạm vi.

## Cách sử dụng

- Chọn trang bằng thanh bên trái. Trong chế độ chỉnh sửa của Desktop, nút điều hướng có thể cần **Ctrl + bấm**.
- Chọn kỳ và khu vực để xem một nhóm nhỏ hơn. Trang Vận hành có thêm khung giờ, mưa và nhóm khoảng cách; trang Tài chính có trạng thái đơn.
- Nút **Xóa lọc** được thiết kế để trở về kỳ 01/03–31/08/2026 và bỏ các lựa chọn riêng. Hành vi thực tế của bản cuối còn cần kiểm, vì vậy hãy nhìn lại các lựa chọn và số tổng sau khi dùng.
- Những tháng ngoài kỳ nguồn không có đơn; không diễn giải chúng là một giai đoạn kinh doanh đã được khảo sát.
- Khi chuyển máy: Power BI → **Transform data → Edit parameters → DataFolder**, chọn thư mục `GiaoNgon/data/curated` chứa `orders.csv`, sau đó Refresh. Chưa kiểm thử thao tác chuyển máy trong lần bàn giao này.

## Đã kiểm và còn thiếu

| Nội dung | Trạng thái |
|---|---|
| Hiểu và làm sạch dữ liệu, model, công thức, phân tích | Có bằng chứng và quyết định duyệt các phase trước trong PLAN/session |
| Bố cục bốn trang | Người dùng đã duyệt |
| Mở lại và xem bốn trang, các số chính | Có ảnh native ở `reports/phase5c/final_reopen` |
| Số trong báo cáo | Tính đối chiếu mới từ CSV Pilot2; xem `Log/final_delivery.json` |
| Bộ lọc, đồng bộ giữa trang, Xóa lọc, lựa chọn rỗng và chọn biểu đồ điểm | Chưa hoàn tất kiểm trên revision cuối |
| Hash report/model | Bản giao được ghi mới; có thay đổi so với mốc layout trước, không coi bằng chứng cũ là kiểm revision mới |

**Đây là bản bàn giao hiện hành, chưa phải xác nhận toàn bộ chức năng đã nghiệm thu.** Báo cáo không gắn nhãn toàn dự án đạt 100%. Dữ liệu nguồn, backup và bằng chứng kiểm cũ được giữ.

Đối chiếu lịch sử ghi nhận 17 file report Pilot2 thay đổi và 9 file của mẫu gốc thay đổi/không còn ở vị trí cũ. Chưa xác minh tác nhân; lần viết bàn giao này không sửa hoặc khôi phục các file đó. Hai CSV đầu vào Pilot2 giữ đúng hash. Model chỉ thêm tham chiếu văn hóa ngôn ngữ và khoảng trắng, không đổi bảng/công thức; file hiện hành được giữ.

## Sửa và tạo lại PDF

Máy hiện có XeLaTeX. Chạy hai lần từ `GiaoNgon/docs`, để file phụ ở thư mục tạm:

```powershell
$buildDir = Join-Path $env:TEMP 'giaonong-pilot2-report'
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
$reportOutputArg = '-output-directory=' + $buildDir
xelatex -interaction=nonstopmode -halt-on-error $reportOutputArg bao_cao_ban_giao.tex
xelatex -interaction=nonstopmode -halt-on-error $reportOutputArg bao_cao_ban_giao.tex
Copy-Item -LiteralPath (Join-Path $buildDir 'bao_cao_ban_giao.pdf') -Destination bao_cao_ban_giao.pdf
```

Giữ nguồn TEX, PDF, PBIP cùng report/model, CSV và bằng chứng. Không chạy lại các script chỉ để mở dashboard; các lệnh sinh dữ liệu/report có thể ghi đè output.

# Lam sach du lieu GiaoNong — Phase 2

Ky thuat da xong, cho Human Gate 2 duyet bang chuan hoa. Chua model/DAX/report/Desktop.

Nguon doc: `data/giaongon_orders_2026.csv` trong GiaoNgon (ban nguoi dung chuan bi).

## Cach doc don gian

Doc va xu ly lai tu CSV thanh mot bang sach de dung dan: giu nguyen 6,073 dong va 27 cot,
them 2 cot de do lai (nhom khoang cach ro rang + so thu tu dong goc).
Khong xoa don huy, khong dien so 0, khong du doan tien te/SLA.
Khong in ma khach hay tung giao dich; bao cao chi tong hop.

## Da thay gi, giu gi va vi sao

- Giu 27 cot goc nguyen gia tri (ngay ISO, so dau cham, o trong la thieu).
- Giu nhan goc `distance_band` (`>6 km` van nam do).
- Them `distance_band_normalized` voi bien ro rang nua mo:
  `[0,2)` → `<2 km`; `[2,4)` → `2–<4 km`; `[4,6)` → `4–<6 km`; `[6,+vo cuc)` → `≥6 km`.
- 32 dong dung 6 km la ly do doi nhan cuoi (nhan cu `>6 km` viet theo nghia den khong gom 6.0),
  khong phai chi co 32 nhan cuoi duoc doi: ca 463 dong tu 6 km tro len gio mang nghia `≥6 km` ro rang.
- `customer_type` giu theo tung don, khong gop thanh nhan co dinh theo khach.
- Giu tat ca don huy, don chenh lech am, o trong van hanh cua don huy. Khong loai outlier.
- Tien/SLA/mua/gio giu nhu nguon va ghi pending; cong thuc tai chinh/thoi gian chi de doi chieu.

## Bang chuyen nhan khoang cach

| khoang_km | nhan_chuan | dieu_kien |
|---|---|---|
| [0, 2) | <2 km | 0 <= km < 2 |
| [2, 4) | 2–<4 km | 2 <= km < 4 |
| [4, 6) | 4–<6 km | 4 <= km < 6 |
| [6, +vo cuc) | ≥6 km | km >= 6 |
| thieu/am/nonfinite | (trong) | khong dua vao nhom hop le |

Doi chieu nguon → chuan (thuc do):

| source | normalized | n |
|---|---|---|
| 2–4 km | 2–<4 km | 3093 |
| 4–6 km | 4–<6 km | 1217 |
| <2 km | <2 km | 1300 |
| >6 km | ≥6 km | 463 |

So dong dung 6 km (cac bien the chuoi deu phan tich thanh Decimal 6): 6.0 — tong 32 dong.

## Con chua biet (pending, khong tu dat quy tac)

- Don vi tien/scale; `order_value` co gom don huy khong; pham vi `revenue/profit` (hoan/thue/overhead).
- Nguong tre/SLA va nguon sinh co `is_late`; cach do co mua `is_rain`; ranh gio `time_slot`.
- Cac buoc thoi gian co chong nhau khong; don vi phut theo ten truong cho xac nhan.
- Thang `rating` 1–5 la gia thuyet du an; don profit am giu lai, chua phai loi de xoa.

## Tai chay va bang chung

`python -X utf8 scripts/phase2.py --run` chay build + validate doc lap va ghi log.
Ket qua chi tiet o `Log/phase2/run.json` (lenh/exit/moi truong/hash) va
`Log/phase2/validation.json` (tung phep so expected/actual).
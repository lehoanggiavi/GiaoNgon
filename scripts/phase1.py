"""Fresh read-only EDA; writes only the explicitly owned Phase 1 artifacts."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nbformat
import numpy as np
import pandas as pd
from nbclient import NotebookClient

BASE = Path(__file__).resolve().parents[1]
SOURCE = BASE.parent / "data/giaongon_orders_2026.csv"
OUT = BASE / "reports/phase1"
MONEY = "order_value delivery_fee discount commission rider_pay compensation revenue profit".split()
TIMES = "prep_min rider_wait_min travel_min delivery_min".split()
NUMERIC = ["distance_km", "is_rain", *MONEY, *TIMES, "is_late", "is_cancelled", "rating"]
OPS = ["travel_min", "delivery_min", "is_late", "rating"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def records(frame):
    return json.loads(frame.to_json(orient="records", force_ascii=False))


def stats(series, denominator):
    s = series.dropna()
    return {"n": int(len(s)), "denominator": int(denominator), "missing": int(denominator-len(s)),
            "coverage_pct": float(100*len(s)/denominator) if denominator else None,
            "sum": float(s.sum()) if len(s) else None, "mean": float(s.mean()) if len(s) else None,
            "median": float(s.median()) if len(s) else None}


def analyze():
    raw = pd.read_csv(SOURCE, dtype="string", keep_default_na=False)
    # Only empty/whitespace is missing; literal NA-like category names remain visible.
    raw = raw.mask(raw.apply(lambda s: s.str.strip().eq("")))
    d = raw.copy()
    for col in NUMERIC:
        d[col] = pd.to_numeric(raw[col], errors="coerce").astype(float)
    d["order_date"] = pd.to_datetime(raw["order_date"], format="%Y-%m-%d", errors="coerce")
    n = len(d)
    checks = []

    def check(name, expected, actual, basis="structural"):
        checks.append({"check": name, "expected": expected, "actual": actual,
                       "status": "PASS" if expected == actual else "FAIL", "basis": basis})

    profiles = []
    for col in raw:
        s = d[col]
        parsed = col in NUMERIC or col == "order_date"
        null = int(raw[col].isna().sum())
        failures = int((raw[col].notna() & s.isna()).sum()) if parsed else 0
        finite = s.dropna().map(math.isfinite) if col in NUMERIC else pd.Series(dtype=bool)
        bounds = s.dropna()
        p = {"column": col, "type": str(s.dtype), "null": null, "non_null": n-null,
             "distinct": int(raw[col].nunique()), "parse_failures": failures,
             "nonfinite": int((~finite).sum()) if col in NUMERIC else None,
             "min": None, "max": None, "labels": None}
        if len(bounds) and parsed:
            p.update(min=str(bounds.min().date()) if col == "order_date" else float(bounds.min()),
                     max=str(bounds.max().date()) if col == "order_date" else float(bounds.max()))
        if col not in ["order_id", "customer_id", "order_date"] and col not in NUMERIC:
            p["labels"] = {str(k): int(v) for k, v in raw[col].fillna("<missing>").value_counts().items()}
        if col in ["is_cancelled", "is_late", "is_rain", "rating"]:
            p["labels"] = {str(k): int(v) for k, v in raw[col].fillna("<missing>").value_counts().items()}
        profiles.append(p)
        check(f"{col}: null + non_null", n, p["null"]+p["non_null"])
        if parsed:
            check(f"{col}: parse failures", 0, failures)
        if col in NUMERIC:
            check(f"{col}: nonfinite", 0, p["nonfinite"])
    check("header columns", 27, len(d.columns), "PLAN observed header contract")
    check("duplicate full rows", 0, int(raw.duplicated().sum()))
    for col, pattern in [("order_id", r"GN\d{6}"), ("customer_id", r"KH\d{5}")]:
        check(f"{col}: missing", 0, int(raw[col].isna().sum()))
        check(f"{col}: format", 0, int((~raw[col].str.fullmatch(pattern).fillna(False)).sum()), "legacy project hypothesis")
    check("duplicate nonmissing order_id", 0, int(raw.loc[raw.order_id.notna(), "order_id"].duplicated().sum()))
    conflicting_keys=int(raw.drop_duplicates().loc[lambda f:f.order_id.notna(),'order_id'].duplicated().sum())
    check("duplicate order_id with different content", 0, conflicting_keys)
    for col in ["is_cancelled", "is_late", "is_rain"]:
        check(f"{col}: non-binary nonmissing", 0, int((d[col].notna() & ~d[col].isin([0, 1])).sum()), "project binary flag hypothesis")
    completed = d.is_cancelled.eq(0)
    cancelled = d.is_cancelled.eq(1)
    unknown = ~(completed | cancelled)
    counts = {"completed_by_project_rule": int(completed.sum()), "cancelled": int(cancelled.sum()), "unknown_status": int(unknown.sum())}
    check("status reconciliation", n, sum(counts.values()))
    cohort = []
    for label, mask in [("completed", completed), ("cancelled", cancelled), ("unknown", unknown)]:
        cohort.append({"cohort": label, "n": int(mask.sum()), **{f"{c}_missing": int(d.loc[mask,c].isna().sum()) for c in [*TIMES,"is_late","rating","cancel_reason"]}})
    for col in OPS:
        check(f"cancelled {col}: present", 0, int(d.loc[cancelled,col].notna().sum()), "CLAUDE delivered-only project rule")
        check(f"completed {col}: missing", 0, int(d.loc[completed,col].isna().sum()), "CLAUDE delivered-only project rule")
    check("cancelled reason missing", 0, int(d.loc[cancelled,"cancel_reason"].isna().sum()), "legacy project hypothesis")
    check("completed reason present", 0, int(d.loc[completed,"cancel_reason"].notna().sum()), "legacy project hypothesis")
    check("cancelled revenue nonzero", 0, int(d.loc[cancelled,"revenue"].ne(0).sum()), "legacy project rule; scope not accounting approval")
    for col in ["distance_km", *TIMES, *[c for c in MONEY if c != "profit"]]:
        check(f"{col}: negative", 0, int(d[col].lt(0).sum()), "plausibility hypothesis; profit may be negative")
    check("rating outside [1,5]", 0, int((d.rating.notna() & ~d.rating.between(1,5)).sum()), "legacy project hypothesis")
    # Formula checks test the project convention, not universal delivery/accounting semantics.
    formulas = [
        ("revenue = commission + delivery_fee - discount", d.revenue-(d.commission+d.delivery_fee-d.discount), 1e-8, "All source money cells are integer-valued; tolerance only absorbs float arithmetic."),
        ("profit = revenue - rider_pay - compensation", d.profit-(d.revenue-d.rider_pay-d.compensation), 1e-8, "All source money cells are integer-valued; no rounding of monetary mismatch."),
        ("delivery_min = prep_min + rider_wait_min + travel_min", d.delivery_min-d.prep_min-d.rider_wait_min-d.travel_min, .2+1e-9, "Source time precision 0.1; rounding four terms can accumulate up to 4 x 0.05 = 0.2 minutes; not an SLA.")]
    residuals = []
    for name, residual, tolerance, reason in formulas:
        valid = residual.notna() & np.isfinite(residual)
        r = residual[valid]
        residuals.append({"formula": name, "basis": "legacy project hypothesis", "n": int(valid.sum()), "denominator": n,
                          "missing": int((~valid).sum()), "tolerance": tolerance, "reason": reason,
                          "violations": int(r.abs().gt(tolerance).sum()), "max_abs": float(r.abs().max()) if len(r) else None,
                          "mean_residual": float(r.mean()) if len(r) else None})
        check(name, 0, residuals[-1]["violations"], "legacy project hypothesis at explicit tolerance")
    precision = {c: int((d[c].dropna()*10-(d[c].dropna()*10).round()).abs().gt(1e-8).sum()) for c in TIMES}
    check("time cells exceed 0.1 precision", 0, sum(precision.values()), "observed rounding basis")
    check("money cells noninteger", 0, int(sum((d[c].dropna()-d[c].dropna().round()).abs().gt(1e-8).sum() for c in MONEY)), "observed money precision basis")
    # Reconstruct actual source band labels from numeric bounds, rather than import old dictionaries.
    distance_labels = records(d.groupby("distance_band", dropna=False).distance_km.agg(["size","min","max"]).reset_index())
    boundary_counts = records(d[d.distance_km.isin([2,4,6])].groupby(["distance_km","distance_band"], dropna=False).size().rename("n").reset_index())
    band_checks=[]
    for label, part in d.groupby('distance_band',dropna=False):
        text=str(label); numbers=[float(x) for x in re.findall(r'\d+(?:\.\d+)?',text)]
        if len(numbers)==1 and text.startswith('<'):
            match=part.distance_km.lt(numbers[0]); interpretation='source label literal less than'
        elif len(numbers)==1 and text.startswith('>'):
            match=part.distance_km.gt(numbers[0]); interpretation='source label literal greater than; legacy script uses >= at last boundary'
        elif len(numbers)==2:
            match=part.distance_km.ge(numbers[0]) & part.distance_km.lt(numbers[1]); interpretation='legacy project half-open convention; source label alone does not confirm endpoints'
        else:
            band_checks.append({'label':text,'n':len(part),'status':'UNKNOWN','interpretation':'unrecognized bounds'}); continue
        mismatch=int((~match).sum())
        band_checks.append({'label':text,'n':len(part),'mismatches':mismatch,'status':'PASS' if mismatch==0 else 'FAIL','interpretation':interpretation})
        check(f'distance label {text}: membership',0,mismatch,interpretation)
    dates = d.order_date.dropna()
    missing_days = sorted(set(pd.date_range(dates.min(),dates.max()).strftime("%Y-%m-%d"))-set(dates.dt.strftime("%Y-%m-%d"))) if len(dates) else []
    period = {"min": str(dates.min().date()) if len(dates) else None, "max": str(dates.max().date()) if len(dates) else None,
              "valid_n": int(len(dates)), "distinct_days": int(dates.nunique()), "missing_days_within_observed_span": missing_days}
    late_valid = completed & d.is_late.isin([0,1]) & d.delivery_min.ge(0) & np.isfinite(d.delivery_min) & d.travel_min.ge(0) & np.isfinite(d.travel_min)
    summary = {"rows": n, "columns": len(d.columns), **counts, "cancel_denominator": int(d.is_cancelled.isin([0,1]).sum()),
               "late_numerator": int((late_valid & d.is_late.eq(1)).sum()), "late_denominator": int(late_valid.sum()),
               "distinct_customers": int(d.customer_id.nunique()), "customers_missing_rows": int(d.customer_id.isna().sum()),
               "duplicates": int(raw.duplicated().sum()),"duplicate_keys_different_content":conflicting_keys,
               "negative_profit_orders":int(d.profit.lt(0).sum()),"merchant_multiple_cuisine_n":int(d.groupby('merchant').cuisine.nunique().gt(1).sum())}
    summary["cancel_pct"] = 100*summary["cancelled"]/summary["cancel_denominator"] if summary["cancel_denominator"] else None
    summary["late_pct"] = 100*summary["late_numerator"]/summary["late_denominator"] if summary["late_denominator"] else None
    d["cohort"] = np.select([completed,cancelled], ["completed","cancelled"], default="unknown")

    def grouped(column):
        result = []
        for key, part in d.groupby(column, dropna=False, sort=True):
            flag = part.is_cancelled.isin([0,1])
            mask = late_valid.loc[part.index]
            denominator = int(mask.sum())
            cancellations = int(part.is_cancelled.eq(1).sum())
            result.append({"group": "<missing>" if pd.isna(key) else str(key), "orders": len(part),
                "cancel_n": cancellations, "cancel_denominator": int(flag.sum()), "cancel_pct": 100*cancellations/flag.sum() if flag.sum() else None,
                "late_n": int(part.loc[mask,"is_late"].eq(1).sum()), "late_denominator": denominator,
                "late_pct": float(100*part.loc[mask,"is_late"].mean()) if denominator else None,
                "late_coverage_of_completed_pct": 100*denominator/part.is_cancelled.eq(0).sum() if part.is_cancelled.eq(0).sum() else None,
                "delivery_n": denominator, "delivery_mean": float(part.loc[mask,"delivery_min"].mean()) if denominator else None,
                "delivery_median": float(part.loc[mask,"delivery_min"].median()) if denominator else None})
        return result

    d["month_observed"] = d.order_date.dt.strftime("%Y-%m")
    groups = {c: grouped(c) for c in ["month_observed","zone","time_slot","is_rain","distance_band","customer_type"]}
    for c, table in groups.items():
        check(f"{c}: rows reconcile", n, sum(r["orders"] for r in table))
    timing = [{"metric": c, **stats(d.loc[completed & d[c].ge(0) & np.isfinite(d[c]),c], int(completed.sum()))} for c in TIMES]
    financial = [{"cohort": label,"metric": c, **stats(d.loc[d.cohort.eq(label),c],int(d.cohort.eq(label).sum()))} for label in ["completed","cancelled","unknown"] for c in MONEY]
    customer_orders = d.groupby("customer_id", dropna=True).size()
    customer_summary = {"customers": int(len(customer_orders)), "with_2plus_orders": int(customer_orders.ge(2).sum()),
        "repeat_customer_pct": float(100*customer_orders.ge(2).mean()) if len(customer_orders) else None,
        "orders_per_customer_mean": float(customer_orders.mean()) if len(customer_orders) else None,
        "orders_per_customer_median": float(customer_orders.median()) if len(customer_orders) else None,
        "order_rows_covered": int(customer_orders.sum()), "denominator_rows": n,
        "label_conflicting_customers": int(d.groupby("customer_id").customer_type.nunique().gt(1).sum())}
    frequency = [{"orders_in_observed_period": int(k), "customers": int(v)} for k,v in customer_orders.value_counts().sort_index().items()]
    daily = records(d.groupby("order_date", dropna=False).size().rename("orders").reset_index().assign(order_date=lambda f:f.order_date.dt.strftime("%Y-%m-%d").fillna("<missing>")))
    profile = {"source": str(SOURCE), "sha256": sha(SOURCE), "summary": summary,"period": period,
        "columns": profiles, "checks": checks, "cohort_missing": cohort,"residuals": residuals,
        "time_precision_violations": precision, "distance_labels_observed": distance_labels,"distance_boundary_counts": boundary_counts,
        "distance_band_checks":band_checks,
        "semantics": {"metadata": "Header names only; no independent source data dictionary or unit declaration found.",
            "observed": "Counts, date span, labels, numeric precision and residuals freshly measured from source.",
            "project_rule": "CLAUDE: operational columns missing for cancelled; operations on completed. Legacy 02: completed := is_cancelled=0.",
            "hypothesis": "Legacy 01 formulas/ID patterns/rating range are checks against project conventions, not industry evidence.",
            "pending": ["Currency and scaling", "GMV includes cancelled order_value?", "Revenue/profit recognized accounting scope, refunds/taxes/overhead", "Late SLA and label generation", "Time step overlap and unit confirmation", "Distance endpoints and slot boundaries", "customer_type definition and history outside observed span"]}}
    aggregates = {"groups":groups,"timing_completed":timing,"financial_by_cohort":financial,"customer_summary":customer_summary,"customer_frequency":frequency,"daily":daily}
    return profile, aggregates


def table(rows, columns=None):
    if not rows:
        return "Không có bản ghi trong nhóm này."
    cols = columns or list(rows[0])
    def fmt(v):
        return "—" if v is None else f"{v:,.2f}" if isinstance(v,float) else str(v)
    return "| " + " | ".join(cols) + " |\n|" + "|".join(["---"]*len(cols)) + "|\n" + "\n".join("| " + " | ".join(fmt(r.get(c)) for c in cols) + " |" for r in rows)


def explanations(p,a):
    s,t,c = p["summary"],p["period"],a["customer_summary"]
    return [
        f"Đã đọc CSV gốc trực tiếp như mở một sổ đơn hàng. Có {s['rows']:,} dòng và {s['columns']} cột. Chỉ tính trong bộ nhớ, chưa sửa dữ liệu hoặc điền ô trống.",
        f"Mỗi dòng có một mã đơn riêng; ghi nhận {s['duplicates']} dòng trùng toàn bộ. Kỳ quan sát {t['min']} đến {t['max']}, có {t['distinct_days']} ngày có đơn và {len(t['missing_days_within_observed_span'])} ngày thiếu bên trong kỳ. Đây là kỳ thấy trong sổ, không phải ngày chụp hay toàn lịch sử kinh doanh.",
        f"Có {s['cancelled']:,}/{s['cancel_denominator']:,} đơn mang cờ hủy ({s['cancel_pct']:.2f}%). Trễ là {s['late_numerator']:,}/{s['late_denominator']:,} đơn đủ thông tin vận hành ({s['late_pct']:.2f}%). {s['completed_by_project_rule']:,} đơn cờ 0 được gọi là hoàn thành theo quy tắc dự án; các ô trống của đơn hủy vẫn giữ trống. Cờ trễ chưa cho biết ngưỡng cam kết giao hàng.",
        "Bảng thời gian chỉ dùng đơn cờ hủy bằng 0 có thời gian không âm và hữu hạn; n là số đơn dùng được. " + "; ".join(f"{r['metric']}: trung bình {r['mean']:.2f}, trung vị {r['median']:.2f}, n={r['n']:,}" for r in a['timing_completed']) + ". Trung bình giống chia đều tổng thời gian, trung vị là giá trị ở giữa. Chưa xác nhận các bước có chồng nhau không, nên thời gian dài hơn chưa tự xác định bên nào có lỗi.",
        f"order_value là giá trị đơn được ghi (reported GMV), khác revenue là thu nhập nền tảng theo công thức dự án; profit trừ rider_pay và compensation. Đơn hủy vẫn có thể mang order_value và chi phí. Có {s['negative_profit_orders']:,}/{s['rows']:,} đơn profit âm; đây là chênh lệch cần phân tích, chưa là lỗi để xóa. Các tổng dưới đây giữ đơn vị số gốc; chưa được gọi là VND hoặc lợi nhuận kế toán đầy đủ.",
        "So nhóm như so các trang trong cùng sổ: tỷ lệ hủy chia cho đơn có cờ hợp lệ, tỷ lệ trễ chia cho đơn hoàn thành đủ thông tin. Bảng ghi cả tử số, mẫu số và độ phủ để nhóm ít đơn không bị nhìn ngang nhóm lớn. Nhãn khu vực/giờ/mưa/khoảng cách giữ nguyên như nguồn; chênh lệch là quan sát, chưa chứng minh mưa hay khoảng cách gây trễ.",
        f"Có {c['customers']:,} mã khách; {c['with_2plus_orders']:,}/{c['customers']:,} khách có từ hai đơn trong kỳ ({c['repeat_customer_pct']:.2f}%). Mỗi khách trung bình {c['orders_per_customer_mean']:.2f} đơn, trung vị {c['orders_per_customer_median']:.0f} đơn. Nhãn Quay lại/Mới được đếm theo dòng đơn, khác việc tự đếm khách mua lặp lại. Không có lịch sử ngoài kỳ để đo giữ chân hoặc rời bỏ.",
        "Sai số dư (residual) là phần còn lệch khi ghép các khoản như cộng các dòng trong sổ. Công thức tài chính dùng dung sai 0.00000001 đơn vị số gốc; thời gian dùng 0.2 phút cộng sai số máy vì bốn số được làm tròn 0.1. Đây là dung sai kiểm tra, không là ngưỡng giao trễ. PASS chỉ nói số khớp công thức dự án, chưa xác nhận định nghĩa kế toán hay SLA."]


def build():
    for folder in [OUT,BASE/"docs",BASE/"notebooks",BASE/"Log/phase1"]:
        folder.mkdir(parents=True,exist_ok=True)
    p,a = analyze()
    write_json(OUT/"profile.json",p)
    write_json(OUT/"aggregates.json",a)
    notes = explanations(p,a)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10})
    daily = pd.DataFrame(a["daily"])
    fig,ax = plt.subplots(figsize=(10,3.5))
    ax.plot(pd.to_datetime(daily.order_date),daily.orders,color="#237A57",lw=1)
    ax.set(title="Số đơn theo ngày trong kỳ quan sát",ylabel="Đơn / ngày",xlabel="Ngày")
    fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(OUT/"01_daily_orders.png",dpi=150); plt.close(fig)
    fig,axes = plt.subplots(1,2,figsize=(12,4.5))
    for ax,col,title in zip(axes,["time_slot","is_rain"],["Trễ theo khung giờ","Trễ theo cờ mưa"]):
        rows = a["groups"][col]
        labels = [r["group"] if col!="is_rain" else {"0.0":"Không mưa (cờ 0)","1.0":"Có mưa (cờ 1)"}.get(r["group"],r["group"]) for r in rows]
        ax.bar(labels,[r["late_pct"] for r in rows],color="#357CA5")
        for i,r in enumerate(rows):
            ax.text(i,r["late_pct"]+.3,f"{r['late_pct']:.1f}%\n{r['late_n']}/{r['late_denominator']}",ha="center",fontsize=9)
        ax.set(title=title,ylabel="% trễ / đơn vận hành hợp lệ")
        ax.set_ylim(0,max(r["late_pct"] for r in rows)*1.35)
    fig.tight_layout(); fig.savefig(OUT/"02_late_groups.png",dpi=150); plt.close(fig)
    fig,ax = plt.subplots(figsize=(8,4))
    rows=a["timing_completed"]
    x=np.arange(len(rows)); ax.bar(x-.18,[r["mean"] for r in rows],.36,label="Trung bình"); ax.bar(x+.18,[r["median"] for r in rows],.36,label="Trung vị")
    ax.set_xticks(x,["Chuẩn bị","Chờ tài xế","Di chuyển","Tổng giao"]); ax.set(ylabel="Phút theo tên trường (chờ xác nhận)",title=f"Thời gian trên đơn hoàn thành; n={p['summary']['completed_by_project_rule']:,}")
    ax.legend(); fig.tight_layout(); fig.savefig(OUT/"03_time_steps.png",dpi=150); plt.close(fig)
    dictionary = {
        "order_id":"Mã đơn; kiểm khóa một dòng/đơn", "order_date":"Ngày ghi đơn; định dạng quan sát YYYY-MM-DD",
        "time_slot":"Nhãn khung giờ nguồn; thiếu giờ thực và ranh giới", "customer_id":"Mã khách; không in từng mã", "customer_type":"Nhãn Mới/Quay lại theo đơn; định nghĩa pending",
        "zone":"Khu vực nhãn nguồn", "merchant":"Nhà hàng nhãn nguồn", "cuisine":"Nhóm món nhãn nguồn",
        "distance_km":"Khoảng cách; tên trường gợi km, chờ xác nhận phương pháp đo", "distance_band":"Nhãn nhóm nguồn; xem min/max và điểm biên",
        "is_rain":"Cờ mưa 0/1; cách đo pending", "order_value":"Giá trị đơn ghi nhận; reported GMV, chưa phải revenue",
        "delivery_fee":"Phí giao ghi nhận", "discount":"Giảm giá ghi nhận", "commission":"Hoa hồng ghi nhận", "rider_pay":"Khoản trả tài xế ghi nhận",
        "compensation":"Bồi thường ghi nhận", "revenue":"Thu nhập theo đẳng thức dự án", "profit":"Chênh lệch sau rider_pay/compensation; phạm vi chi phí pending",
        "prep_min":"Thời gian chuẩn bị; tên gợi phút", "rider_wait_min":"Thời gian chờ tài xế; tên gợi phút", "travel_min":"Thời gian di chuyển; thiếu ở đơn hủy",
        "delivery_min":"Tổng thời gian giao; thiếu ở đơn hủy", "is_late":"Cờ trễ; SLA/nguồn tạo nhãn pending", "is_cancelled":"Cờ hủy; quy tắc dự án cờ 0 = hoàn thành",
        "cancel_reason":"Lý do hủy; thiếu ở đơn không hủy", "rating":"Điểm đánh giá; thang 1–5 là giả thuyết dự án"}
    lines=["# Hiểu dữ liệu GiaoNong — Phase 1 mới", "", "Đã tính lại từ CSV gốc và dừng trước làm sạch. Gate 1 chưa được duyệt.", "", "## Cách đọc", "", "Sổ đơn hàng có dòng đơn, ô thông tin và các nhóm. `n` là số ô/đơn dùng được; mẫu số (denominator) là số đối tượng đem so; độ phủ (coverage) là phần có đủ dữ liệu. Không xuất mã khách hoặc từng giao dịch.", "", "## Nguồn và mức độ xác nhận", "", f"Nguồn đọc: `{SOURCE}`. SHA-256: `{p['sha256']}`.", "", "- Metadata: chỉ có header CSV; chưa thấy dictionary độc lập về tiền, đơn vị hoặc SLA.", "- Quan sát: kỳ, dòng, nhãn, ô trống, số tài chính và thời gian được đo mới.", "- Quy tắc dự án: CLAUDE giữ ô vận hành trống ở đơn hủy; legacy `02_build_curated.py` gọi cờ hủy 0 là hoàn thành. Chỉ dùng để đối chiếu, không chạy script cũ.", "- Giả thuyết kiểm: công thức/ID/thang điểm từ legacy `01_profile_data.py`; nguồn số khớp không tự xác nhận nghiệp vụ.", "", "## Sáu câu hỏi", "", "### 1. Lượng đơn theo thời gian", "", notes[1], "", table(a['groups']['month_observed'],['group','orders','cancel_n','cancel_denominator','late_n','late_denominator']), "", "![Đơn theo ngày](../reports/phase1/01_daily_orders.png)", "", "### 2. Hủy và trễ", "", notes[2], "", table(p['cohort_missing']), "", table([r for r in p['columns'] if r['column']=='cancel_reason'],['column','labels']), "", "### 3. Thời gian ở từng bước", "", notes[3], "", table(a['timing_completed']), "", "![Các bước thời gian](../reports/phase1/03_time_steps.png)", "", "### 4. Giá trị đơn, thu nhập và chênh lệch chi phí", "", notes[4], "", table([r for r in a['financial_by_cohort'] if r['metric'] in ['order_value','revenue','profit']],['cohort','metric','n','denominator','sum','mean','median']), "", "### 5. Khu vực, giờ, mưa, khoảng cách", "", notes[5]]
    for col in ['zone','time_slot','is_rain','distance_band']:
        lines += ["",f"**{col}**", "", table(a['groups'][col],['group','orders','cancel_n','cancel_denominator','cancel_pct','late_n','late_denominator','late_pct','delivery_mean','delivery_median','late_coverage_of_completed_pct'])]
    lines += ["", "![Trễ theo nhóm với mẫu số](../reports/phase1/02_late_groups.png)", "", "### 6. Khách mua lặp lại trong kỳ", "",notes[6], "",table(a['groups']['customer_type'],['group','orders','cancel_n','cancel_denominator','late_n','late_denominator']), "",table(a['customer_frequency']), "", "## Ý nghĩa và bước tiếp theo", "", "Các nhóm có tỷ lệ trễ cao là nơi nên kiểm tra vận hành trước, nhưng phải so cả số đơn và điều kiện từng nhóm. Chưa có dữ liệu giờ thực, nguồn gán nhãn hoặc chi phí đầy đủ để khẳng định nguyên nhân hay tính ROI. Hành động quan trọng nhất là chốt định nghĩa ở Gate 1 trước khi tạo KPI và làm sạch.", "", "## Cần chủ dữ liệu chốt tại Gate 1", ""]
    lines += [f"- {q}" for q in p['semantics']['pending']]
    lines += ["", "Đặc biệt: nhãn `>6 km` trong nguồn có thể chứa đúng 6.0; xem bảng điểm biên bên dưới. Không tự đổi nhãn hay ngưỡng ở Phase 1.", "", "## Phụ lục kỹ thuật", "", "### Dictionary và profile 27 cột", "",table([{**r,'meaning':dictionary.get(r['column'],'Pending')} for r in p['columns']],['column','meaning','type','null','non_null','distinct','parse_failures','min','max']), "", "Nhãn và số đếm đầy đủ: `reports/phase1/profile.json → columns[].labels`. Không áp danh mục hoặc kỳ cũ làm expected; giá trị lạ vẫn hiện trong nhóm.", "", "### Điểm biên khoảng cách quan sát", "",table(p['distance_labels_observed']), "",table(p['distance_boundary_counts']), "",table(p['distance_band_checks']), "", "### Công thức và dung sai", "",notes[7], "",table(p['residuals'],['formula','n','denominator','missing','tolerance','violations','max_abs']), "", "### Kết quả DQ theo expected/actual", "",table(p['checks']), "", "Các checks là kiểm code/cấu trúc hoặc giả thuyết dự án. FAIL được giữ nguyên nếu xảy ra; pending nghiệp vụ không được đổi thành PASS. Đơn profit âm không tự là lỗi và không bị xóa. Dữ liệu không đủ để kiểm SLA, sự thật của cờ mưa, nguồn đơn, retention ngoài kỳ hoặc đối soát kế toán.", "", "### Tái chạy và bằng chứng", "", "`python -X utf8 scripts/phase1.py --run` chạy một lượt build + validation và ghi actual exit/hash/env. `--build` tạo profile/aggregate/docs/chart/notebook chưa chạy. `--validate` đếm bằng thư viện CSV độc lập và chạy notebook với kernel mới. Log command/actual exit/environment/hash nằm ở `Log/phase1/run.json`; kiểm notebook thật và stdlib nằm ở `Log/phase1/validation.json`. Không import legacy common.py hoặc ghi ra root."]
    (BASE/"docs/01_data_understanding.md").write_text("\n".join(lines),encoding="utf-8")
    nb=nbformat.v4.new_notebook(metadata={"kernelspec":{"name":"python3","display_name":"Python 3","language":"python"}})
    nb.cells=[nbformat.v4.new_markdown_cell("# EDA từ CSV gốc — Phase 1\nChạy kernel sạch; không sửa nguồn, không in mã khách/từng giao dịch. Mỗi đoạn code có lời giải thích ngay dưới.")]
    codes=[
        "from pathlib import Path\nimport sys\nfrom IPython.display import display, Image\nimport pandas as pd\nbase = Path.cwd().parent\nsys.path.insert(0, str(base / 'scripts'))\nfrom phase1 import analyze\np, a = analyze()\nprint({'source_sha256': p['sha256'], 'rows': p['summary']['rows'], 'columns': p['summary']['columns']})",
        "print(p['period'])\ndisplay(pd.DataFrame(a['groups']['month_observed']))\ndisplay(Image(filename=str(base/'reports/phase1/01_daily_orders.png')))",
        "print(p['summary'])\ndisplay(pd.DataFrame(p['cohort_missing']))\nprint(next(r['labels'] for r in p['columns'] if r['column']=='cancel_reason'))",
        "display(pd.DataFrame(a['timing_completed']))\ndisplay(Image(filename=str(base/'reports/phase1/03_time_steps.png')))",
        "display(pd.DataFrame(a['financial_by_cohort']).query(\"metric in ['order_value','revenue','profit']\"))",
        "for dimension in ['zone','time_slot','is_rain','distance_band']:\n    print(dimension)\n    display(pd.DataFrame(a['groups'][dimension]))\ndisplay(Image(filename=str(base/'reports/phase1/02_late_groups.png')))\nprint('Điểm biên khoảng cách:')\ndisplay(pd.DataFrame(p['distance_boundary_counts']))",
        "print(a['customer_summary'])\ndisplay(pd.DataFrame(a['groups']['customer_type']))\ndisplay(pd.DataFrame(a['customer_frequency']))",
        "display(pd.DataFrame(p['residuals']))\ncheck_status = pd.DataFrame(p['checks'])\nprint(check_status['status'].value_counts().to_dict())\ndisplay(check_status[check_status['status'] != 'PASS'])\nassert all(c['null']+c['non_null']==p['summary']['rows'] for c in p['columns'])\nprint('Null + non-null khớp ở mọi cột. Câu hỏi nghiệp vụ còn pending:', p['semantics']['pending'])"]
    for code,note in zip(codes,notes):
        nb.cells += [nbformat.v4.new_code_cell(code),nbformat.v4.new_markdown_cell(note)]
    nbformat.write(nb,BASE/"notebooks/01_eda.ipynb")
    print(json.dumps({"rows":p['summary']['rows'],"columns":p['summary']['columns'],"dq_status":dict(Counter(c['status'] for c in p['checks'])),"outputs":str(OUT)},ensure_ascii=False))


def validate():
    p=json.loads((OUT/"profile.json").read_text(encoding="utf-8")); a=json.loads((OUT/"aggregates.json").read_text(encoding="utf-8"))
    with SOURCE.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    independent={"rows":len(rows),"columns":len(rows[0]) if rows else 0,"status":dict(Counter(r['is_cancelled'] or '<missing>' for r in rows)),
                 "null_by_column":{c:sum(not r[c].strip() for r in rows) for c in rows[0]},"distinct_order_id":len({r['order_id'] for r in rows if r['order_id'].strip()}),
                 "distinct_customer_id":len({r['customer_id'] for r in rows if r['customer_id'].strip()})}
    comparisons=[{"check":"row_count","expected":independent['rows'],"actual":p['summary']['rows']},
                 {"check":"column_count","expected":independent['columns'],"actual":p['summary']['columns']},
                 {"check":"order_ids","expected":independent['distinct_order_id'],"actual":next(c['distinct'] for c in p['columns'] if c['column']=='order_id')},
                 {"check":"customer_ids","expected":independent['distinct_customer_id'],"actual":p['summary']['distinct_customers']}]
    for flag,key in [('0','completed_by_project_rule'),('1','cancelled')]:
        comparisons.append({"check":f"status_{flag}","expected":independent['status'].get(flag,0),"actual":p['summary'][key]})
    for col in p['columns']:
        comparisons.append({"check":f"null_{col['column']}","expected":independent['null_by_column'][col['column']],"actual":col['null']})
    for dimension in ['zone','time_slot','is_rain','distance_band','customer_type']:
        counts=Counter(r[dimension] or '<missing>' for r in rows)
        actual={r['group']:r['orders'] for r in a['groups'][dimension]}
        if dimension=='is_rain': actual={str(int(float(k))) if k!='<missing>' else k:v for k,v in actual.items()}
        comparisons.append({"check":f"groups_{dimension}","expected":dict(counts),"actual":actual})
    manifest=json.loads((BASE/'Log/source_and_reference_hashes.json').read_text(encoding='utf-8-sig'))
    changed=[name for name,expected in manifest['sha256'].items() if sha(BASE.parent/name)!=expected]
    comparisons.append({"check":"protected source/reference hashes changed","expected":[],"actual":changed})
    for check in comparisons: check['status']='PASS' if check['expected']==check['actual'] else 'FAIL'
    notebook_path=BASE/'notebooks/01_eda.ipynb'
    nb=nbformat.read(notebook_path,as_version=4)
    execution_error=None
    try:
        NotebookClient(nb,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(notebook_path.parent)}}).execute()
    except Exception as exc:
        execution_error=f'{type(exc).__name__}: {exc}'
    nbformat.write(nb,notebook_path)
    code=[cell for cell in nb.cells if cell.cell_type=='code']
    errors=[{'cell':i,'error':out.get('ename'),'message':out.get('evalue')} for i,cell in enumerate(nb.cells) if cell.cell_type=='code' for out in cell.get('outputs',[]) if out.output_type=='error']
    execution={'code_cells':len(code),'executed':sum(c.execution_count is not None for c in code),'cells_with_outputs':sum(bool(c.outputs) for c in code),
               'execution_counts':[c.execution_count for c in code],'uncaught_errors':errors,'runner_error':execution_error,
               'markdown_immediately_after_all_code':all(i+1<len(nb.cells) and nb.cells[i+1].cell_type=='markdown' for i,c in enumerate(nb.cells) if c.cell_type=='code'),
               'notebook_sha256':sha(notebook_path)}
    valid=not execution_error and not errors and execution['executed']==len(code) and execution['cells_with_outputs']==len(code) and execution['markdown_immediately_after_all_code'] and all(c['status']=='PASS' for c in comparisons)
    write_json(BASE/'Log/phase1/validation.json',{'stdlib_independent':independent,'comparisons':comparisons,'notebook':execution,'technical_status':'PASS' if valid else 'FAIL',
               'dq_status':dict(Counter(c['status'] for c in p['checks'])),'domain_gate':'PENDING; arithmetic pass does not authorize Phase 2'})
    print(json.dumps({'technical_status':'PASS' if valid else 'FAIL','independent_rows':len(rows),'comparisons':len(comparisons),'notebook':execution},ensure_ascii=False))
    if not valid: raise SystemExit(1)


def run():
    (BASE/'Log/phase1').mkdir(parents=True,exist_ok=True)
    result={'started_utc':datetime.utcnow().isoformat()+'Z','cwd':str(BASE),'source_sha256_before':sha(SOURCE),
            'script_sha256':sha(__file__),'plan_sha256':sha(BASE/'Plan/PLAN.md'),'skill_sha256':sha(BASE.parent/'docs/skill-drafts/da-hitl-supervisor/SKILL.md'),
            'environment':{'python_executable':sys.executable,'python_version':sys.version,'platform':platform.platform(),
                'pandas':pd.__version__,'numpy':np.__version__,'matplotlib':matplotlib.__version__,'nbformat':nbformat.__version__},
            'preflight_failure':{'command':"python -c [fresh CSV shape/dtypes/nulls/labels/ranges exploration]",'actual_exit':1,
                'error':'UnicodeEncodeError: cp1252 stdout cannot encode Vietnamese category labels','correction':'Use python -X utf8; data unchanged; not a validation retry'},
            'commands':[],'validation_policy':'one validation pass; technical correction only if needed; DQ findings retained'}
    exit_code=0
    for mode in ['--build','--validate']:
        command=[sys.executable,'-X','utf8',str(Path(__file__).resolve()),mode]
        start=datetime.utcnow().isoformat()+'Z'
        process=subprocess.run(command,cwd=BASE,capture_output=True,text=True,encoding='utf-8')
        result['commands'].append({'argv':command,'cwd':str(BASE),'started_utc':start,'finished_utc':datetime.utcnow().isoformat()+'Z',
                                  'actual_exit':process.returncode,'stdout':process.stdout,'stderr':process.stderr})
        if process.returncode:
            exit_code=process.returncode; break
    result['source_sha256_after']=sha(SOURCE)
    result['artifacts_sha256']={str(path.relative_to(BASE)):sha(path) for folder in ['reports/phase1','docs','notebooks','scripts'] for path in sorted((BASE/folder).glob('*')) if path.is_file()}
    result['finished_utc']=datetime.utcnow().isoformat()+'Z'; result['actual_exit']=exit_code
    write_json(BASE/'Log/phase1/run.json',result)
    print(json.dumps({'actual_exit':exit_code,'commands':[{'mode':r['argv'][-1],'actual_exit':r['actual_exit']} for r in result['commands']]},ensure_ascii=False))
    if exit_code: raise SystemExit(exit_code)


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--build',action='store_true'); parser.add_argument('--validate',action='store_true'); parser.add_argument('--run',action='store_true'); args=parser.parse_args()
    if sum([args.build,args.validate,args.run])!=1: parser.error('Choose exactly one of --build, --validate or --run')
    if args.run: run()
    elif args.build: build()
    else: validate()

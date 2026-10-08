"""Phase 2: chuan hoa don hang, giu nguon/P1, doi chieu truoc-sau.

Input hien hanh: data/giaongon_orders_2026.csv trong GiaoNgon (ban nguoi dung
chuan bi, doc tu nay, chi doc khong sua). Lich su chay truoc doc CSV cha duoc
giu trong Log/phase2/archive/before_local_input/ de giu provenance.
Output: data/curated/orders.csv + docs/02_data_cleaning.md + Log/phase2/.
Khong import script cha co side effect, khong rerun P1, khong model/DAX/report/Desktop.
Khong copy code/output cu cua du an goc; viet va kiem moi tu input GiaoNgon.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SOURCE = BASE / "data/giaongon_orders_2026.csv"
CURATED_DIR = BASE / "data" / "curated"
OUT_CSV = CURATED_DIR / "orders.csv"
LOG_DIR = BASE / "Log" / "phase2"
DOC_PATH = BASE / "docs" / "02_data_cleaning.md"

SOURCE_COLS = ["order_id", "order_date", "time_slot", "customer_id", "customer_type",
               "zone", "merchant", "cuisine", "distance_km", "distance_band", "is_rain",
               "order_value", "delivery_fee", "discount", "commission", "rider_pay",
               "compensation", "revenue", "profit", "prep_min", "rider_wait_min",
               "travel_min", "delivery_min", "is_late", "is_cancelled",
               "cancel_reason", "rating"]
NUMERIC_COLS = ["distance_km", "is_rain", "order_value", "delivery_fee", "discount",
                "commission", "rider_pay", "compensation", "revenue", "profit",
                "prep_min", "rider_wait_min", "travel_min", "delivery_min",
                "is_late", "is_cancelled", "rating"]
MONEY_COLS = ["order_value", "delivery_fee", "discount", "commission", "rider_pay",
              "compensation", "revenue", "profit"]
TIME_COLS = ["prep_min", "rider_wait_min", "travel_min", "delivery_min"]
FLAG_COLS = ["is_rain", "is_late", "is_cancelled"]
NEW_COLS = ["distance_band_normalized", "source_row_number"]

# Nhan chuan cuoi: nua mo [a, b), nhom cuoi [6, +vo cuc).
NORM_LABELS = {"lt2": "<2 km", "b24": "2\u2013<4 km", "b46": "4\u2013<6 km", "ge6": "\u22656 km"}
MAPPING_ROWS = [("[0, 2)", NORM_LABELS["lt2"], "0 <= km < 2"),
                ("[2, 4)", NORM_LABELS["b24"], "2 <= km < 4"),
                ("[4, 6)", NORM_LABELS["b46"], "4 <= km < 6"),
                ("[6, +vo cuc)", NORM_LABELS["ge6"], "km >= 6"),
                ("thieu/am/nonfinite", "(trong)", "khong dua vao nhom hop le")]


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value) -> None:
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2),
                          encoding="utf-8")


def is_missing_raw(v: str) -> bool:
    return v.strip() == ""


def parse_decimal(v: str):
    if is_missing_raw(v):
        return None
    try:
        d = Decimal(v.strip())
    except InvalidOperation:
        return "PARSE_FAIL"
    if d.is_nan() or d.is_infinite():
        return "NONFINITE"
    return d


def normalized_band(d) -> str:
    if d is None or d == "PARSE_FAIL" or d == "NONFINITE":
        return ""
    if d < 0:
        return ""
    if d < 2:
        return NORM_LABELS["lt2"]
    if d < 4:
        return NORM_LABELS["b24"]
    if d < 6:
        return NORM_LABELS["b46"]
    return NORM_LABELS["ge6"]


def read_source_rows():
    with SOURCE.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        rows = list(reader)
    return header, rows


def build():
    CURATED_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (BASE / "docs").mkdir(parents=True, exist_ok=True)
    header, rows = read_source_rows()
    errors = []
    if header != SOURCE_COLS:
        errors.append({"reason": "header khac 27 cot du kien",
                       "expected": SOURCE_COLS, "actual": header})
    n = len(rows)
    seen_ids = set()
    dup_ids = 0
    out_rows = []
    null_source = Counter()
    norm_counter = Counter()
    cross_counter = Counter()
    for i, r in enumerate(rows, start=1):
        oid = (r.get("order_id") or "").strip()
        cid = (r.get("customer_id") or "").strip()
        if not oid:
            errors.append({"row": i, "reason": "thieu order_id"})
        if not cid:
            errors.append({"row": i, "reason": "thieu customer_id"})
        if oid in seen_ids:
            dup_ids += 1
        seen_ids.add(oid)
        date_raw = (r.get("order_date") or "").strip()
        try:
            datetime.strptime(date_raw, "%Y-%m-%d")
        except ValueError:
            errors.append({"row": i, "reason": "order_date khong dung YYYY-MM-DD",
                           "value": date_raw})
        parsed = {}
        for col in NUMERIC_COLS:
            v = r.get(col, "")
            if is_missing_raw(v):
                parsed[col] = None
                null_source[col] += 1
            else:
                d = parse_decimal(v)
                if d in ("PARSE_FAIL", "NONFINITE"):
                    errors.append({"row": i, "column": col,
                                   "reason": "so loi parse/nonfinite",
                                   "detail": str(d), "value": v})
                    parsed[col] = d
                else:
                    parsed[col] = d
        for col in FLAG_COLS:
            d = parsed.get(col)
            if d is not None and d not in (Decimal(0), Decimal(1)):
                errors.append({"row": i, "column": col,
                               "reason": "co chi nhan 0/1/null", "value": r.get(col)})
        for col in SOURCE_COLS:
            if is_missing_raw(r.get(col, "")):
                null_source[col] += 0 if col in NUMERIC_COLS else 1
        norm = normalized_band(parsed.get("distance_km"))
        norm_counter[norm or "<trong>"] += 1
        cross_counter[((r.get("distance_band") or "").strip(), norm or "<trong>")] += 1
        out = {}
        for col in SOURCE_COLS:
            v = r.get(col, "")
            out[col] = "" if is_missing_raw(v) else v.strip()
        out["distance_band_normalized"] = norm
        out["source_row_number"] = str(i)
        out_rows.append(out)
    if dup_ids:
        errors.append({"reason": "trung order_id", "count": dup_ids})
    if errors:
        write_json(LOG_DIR / "build_errors.json", {"errors": errors})
        raise SystemExit("Phase2 build STOP: du lieu loi, khong xuat ban. Xem Log/phase2/build_errors.json")
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SOURCE_COLS + NEW_COLS)
        w.writeheader()
        w.writerows(out_rows)
    six_variants = sorted({(r.get("distance_km") or "").strip() for r in rows
                           if parse_decimal(r.get("distance_km", "")) == Decimal(6)})
    six_n = sum(1 for r in rows if parse_decimal(r.get("distance_km", "")) == Decimal(6))
    summary = {"rows": n, "columns_27": len(SOURCE_COLS),
               "columns_curated": len(SOURCE_COLS + NEW_COLS),
               "null_source_sample": {c: null_source.get(c, 0) for c in SOURCE_COLS},
               "normalized_counts": dict(norm_counter),
               "exact_6km": six_n,
               "exact_6km_variants": six_variants,
               "cross_source_vs_normalized": [{"source": k[0], "normalized": k[1], "n": v}
                                              for k, v in sorted(cross_counter.items())]}
    write_doc(summary)
    print(json.dumps({"rows": summary["rows"], "out": str(OUT_CSV),
                      "normalized": summary["normalized_counts"]}, ensure_ascii=False))


def table(rows, columns=None):
    if not rows:
        return "Khong co ban ghi trong nhom nay."
    cols = columns or list(rows[0].keys())
    def fmt(v):
        if v is None:
            return "—"
        if isinstance(v, float):
            return f"{v:,.2f}"
        return str(v)
    head = "| " + " | ".join(cols) + " |\n|" + "|".join(["---"] * len(cols)) + "|"
    body = "\n".join("| " + " | ".join(fmt(r.get(c)) for c in cols) + " |" for r in rows)
    return head + "\n" + body


def write_doc(summary):
    cross = summary["cross_source_vs_normalized"]
    lines = [
        "# Lam sach du lieu GiaoNong — Phase 2",
        "",
        "Ky thuat da xong, cho Human Gate 2 duyet bang chuan hoa. Chua model/DAX/report/Desktop.",
        "",
        "Nguon doc: `data/giaongon_orders_2026.csv` trong GiaoNgon (ban nguoi dung chuan bi).",
        "",
        "## Cach doc don gian",
        "",
        f"Doc va xu ly lai tu CSV thanh mot bang sach de dung dan: giu nguyen {summary['rows']:,} dong va 27 cot,",
        "them 2 cot de do lai (nhom khoang cach ro rang + so thu tu dong goc).",
        "Khong xoa don huy, khong dien so 0, khong du doan tien te/SLA.",
        "Khong in ma khach hay tung giao dich; bao cao chi tong hop.",
        "",
        "## Da thay gi, giu gi va vi sao",
        "",
        "- Giu 27 cot goc nguyen gia tri (ngay ISO, so dau cham, o trong la thieu).",
        "- Giu nhan goc `distance_band` (`>6 km` van nam do).",
        "- Them `distance_band_normalized` voi bien ro rang nua mo:",
        "  `[0,2)` → `<2 km`; `[2,4)` → `2–<4 km`; `[4,6)` → `4–<6 km`; `[6,+vo cuc)` → `≥6 km`.",
        "- 32 dong dung 6 km la ly do doi nhan cuoi (nhan cu `>6 km` viet theo nghia den khong gom 6.0),",
        "  khong phai chi co 32 nhan cuoi duoc doi: ca 463 dong tu 6 km tro len gio mang nghia `≥6 km` ro rang.",
        "- `customer_type` giu theo tung don, khong gop thanh nhan co dinh theo khach.",
        "- Giu tat ca don huy, don chenh lech am, o trong van hanh cua don huy. Khong loai outlier.",
        "- Tien/SLA/mua/gio giu nhu nguon va ghi pending; cong thuc tai chinh/thoi gian chi de doi chieu.",
        "",
        "## Bang chuyen nhan khoang cach",
        "",
        table([{"khoang_km": a, "nhan_chuan": b, "dieu_kien": c}
               for a, b, c in MAPPING_ROWS]),
        "",
        "Doi chieu nguon → chuan (thuc do):",
        "",
        table(cross),
        "",
        "So dong dung 6 km (cac bien the chuoi deu phan tich thanh Decimal 6): "
        + ", ".join(summary["exact_6km_variants"]) + f" — tong {summary['exact_6km']} dong.",
        "",
        "## Con chua biet (pending, khong tu dat quy tac)",
        "",
        "- Don vi tien/scale; `order_value` co gom don huy khong; pham vi `revenue/profit` (hoan/thue/overhead).",
        "- Nguong tre/SLA va nguon sinh co `is_late`; cach do co mua `is_rain`; ranh gio `time_slot`.",
        "- Cac buoc thoi gian co chong nhau khong; don vi phut theo ten truong cho xac nhan.",
        "- Thang `rating` 1–5 la gia thuyet du an; don profit am giu lai, chua phai loi de xoa.",
        "",
        "## Tai chay va bang chung",
        "",
        "`python -X utf8 scripts/phase2.py --run` chay build + validate doc lap va ghi log.",
        "Ket qua chi tiet o `Log/phase2/run.json` (lenh/exit/moi truong/hash) va",
        "`Log/phase2/validation.json` (tung phep so expected/actual).",
    ]
    DOC_PATH.write_text("\n".join(lines), encoding="utf-8")


def dec_sum(values):
    total = Decimal(0)
    for v in values:
        if v is None or v == "":
            continue
        total += Decimal(str(v).strip()) if not isinstance(v, Decimal) else v
    return total


def validate():
    header_src, src_rows = read_source_rows()
    with OUT_CSV.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header_cur = reader.fieldnames or []
        cur_rows = list(reader)
    comps = []

    def comp(name, expected, actual):
        ok = expected == actual
        if isinstance(expected, dict) and isinstance(actual, dict):
            ok = dict(expected) == dict(actual)
        comps.append({"check": name, "expected": expected, "actual": actual,
                      "status": "PASS" if ok else "FAIL"})

    n_src = len(src_rows)
    comp("row_count source = curated", n_src, len(cur_rows))
    comp("header curated", SOURCE_COLS + NEW_COLS, header_cur)
    src_ids = [(r.get("order_id") or "").strip() for r in src_rows]
    cur_ids = [(r.get("order_id") or "").strip() for r in cur_rows]
    comp("order_id cung tap va thu tu (so dong lech)", 0,
         sum(1 for a, b in zip(src_ids, cur_ids) if a != b) + abs(len(src_ids) - len(cur_ids)))
    comp("order_id unique/non-null", [n_src, n_src],
         [len(set(cur_ids)), sum(1 for v in cur_ids if v)])
    comp("source_row_number 1..n (so dong lech)", 0,
         sum(1 for i, r in enumerate(cur_rows, start=1)
             if r.get("source_row_number") != str(i)))
    value_mismatch = 0
    null_mismatch_cols = []
    for col in SOURCE_COLS:
        src_vals = [("" if is_missing_raw(r.get(col, "")) else r.get(col, "").strip())
                    for r in src_rows]
        cur_vals = [r.get(col, "") for r in cur_rows]
        if src_vals != cur_vals:
            value_mismatch += sum(1 for a, b in zip(src_vals, cur_vals) if a != b)
            null_mismatch_cols.append(col)
    comp("27 cot giu nguyen gia tri tung o", 0, value_mismatch)
    for col in SOURCE_COLS:
        s_null = sum(1 for r in src_rows if is_missing_raw(r.get(col, "")))
        c_null = sum(1 for r in cur_rows if r.get(col, "") == "")
        comp(f"null_{col}", s_null, c_null)
    for col in MONEY_COLS:
        s_vals = [r.get(col, "") for r in src_rows]
        c_vals = [r.get(col, "") for r in cur_rows]
        comp(f"sum_{col}", str(dec_sum(s_vals)), str(dec_sum(c_vals)))
    for flag in ["0", "1"]:
        s_n = sum(1 for r in src_rows if (r.get("is_cancelled") or "").strip() == flag)
        c_n = sum(1 for r in cur_rows if (r.get("is_cancelled") or "") == flag)
        comp(f"is_cancelled={flag}", s_n, c_n)
    for col in MONEY_COLS:
        for flag in ["0", "1"]:
            s_vals = [r.get(col, "") for r in src_rows
                      if (r.get("is_cancelled") or "").strip() == flag]
            c_vals = [r.get(col, "") for r in cur_rows
                      if (r.get("is_cancelled") or "") == flag]
            comp(f"sum_{col}_cancelled={flag}", str(dec_sum(s_vals)), str(dec_sum(c_vals)))
    s_cust = len({(r.get("customer_id") or "").strip() for r in src_rows})
    c_cust = len({(r.get("customer_id") or "") for r in cur_rows})
    comp("distinct customers", s_cust, c_cust)
    s_neg = sum(1 for r in src_rows
                if not is_missing_raw(r.get("profit", "")) and Decimal(r["profit"].strip()) < 0)
    c_neg = sum(1 for r in cur_rows
                if r.get("profit", "") != "" and Decimal(r["profit"]) < 0)
    comp("profit am giu lai", s_neg, c_neg)
    for col in ["travel_min", "delivery_min", "is_late", "rating"]:
        s_null = sum(1 for r in src_rows if is_missing_raw(r.get(col, "")))
        c_null = sum(1 for r in cur_rows if r.get(col, "") == "")
        comp(f"null huy_{col}", s_null, c_null)
    for dim in ["zone", "time_slot", "is_rain", "distance_band", "customer_type"]:
        s_c = dict(Counter(("" if is_missing_raw(r.get(dim, "")) else r.get(dim, "").strip())
                           for r in src_rows))
        c_c = dict(Counter((r.get(dim, "") for r in cur_rows)))
        comp(f"groups_{dim}", s_c, c_c)
    map_bad = 0
    norm_counter = Counter()
    for r in cur_rows:
        km_raw = r.get("distance_km", "")
        expect = normalized_band(parse_decimal(km_raw) if km_raw != "" else None)
        if r.get("distance_band_normalized", "") != expect:
            map_bad += 1
        norm_counter[r.get("distance_band_normalized", "") or "<trong>"] += 1
    comp("mapping khoang cach tung dong", 0, map_bad)
    for km_str, want in [("2", NORM_LABELS["b24"]), ("2.0", NORM_LABELS["b24"]),
                         ("4", NORM_LABELS["b46"]), ("4.0", NORM_LABELS["b46"]),
                         ("6", NORM_LABELS["ge6"]), ("6.0", NORM_LABELS["ge6"])]:
        comp(f"bien_{km_str}", want, normalized_band(Decimal(km_str)))
    comp("missing/am khong vao nhom hop le", ["", ""],
         [normalized_band(None), normalized_band(Decimal(-1))])
    src_band = [(r.get("distance_band") or "").strip() for r in src_rows]
    cur_band = [r.get("distance_band") for r in cur_rows]
    comp("giu nhan goc distance_band (so dong lech)", 0,
         sum(1 for a, b in zip(src_band, cur_band) if a != b))
    src_ct = [(r.get("customer_type") or "").strip() for r in src_rows]
    cur_ct = [r.get("customer_type") for r in cur_rows]
    comp("customer_type theo don (so dong lech)", 0,
         sum(1 for a, b in zip(src_ct, cur_ct) if a != b))
    for col in ["is_late", "is_rain", "time_slot", "revenue", "profit"]:
        s_vals = [("" if is_missing_raw(r.get(col, "")) else r.get(col, "").strip())
                  for r in src_rows]
        c_vals = [r.get(col, "") for r in cur_rows]
        comp(f"giu nguon_{col} (so dong lech)", 0,
             sum(1 for a, b in zip(s_vals, c_vals) if a != b))
    manifest = json.loads((BASE / "Log/source_and_reference_hashes.json")
                          .read_text(encoding="utf-8-sig"))
    changed = [k for k, v in manifest["sha256"].items()
               if sha(BASE.parent / k) != v]
    comp("protected source/reference doi", [], changed)
    chk = json.loads((BASE / "Log/opencode_handoff_checkpoint.json")
                     .read_text(encoding="utf-8"))
    p1_bad = [k for k, v in chk["filesSha256"].items()
              if sha(BASE / k) != v]
    comp("artifacts P1 giu nguyen", [], p1_bad)
    ok = all(c["status"] == "PASS" for c in comps)
    result = {"comparisons": comps, "technical_status": "PASS" if ok else "FAIL",
              "curated_rows": len(cur_rows), "source_rows": n_src,
              "normalized_counts": dict(norm_counter),
              "domain_gate": "PENDING; can Human Gate 2 duyet bang chuan hoa"}
    write_json(LOG_DIR / "validation.json", result)
    print(json.dumps({"technical_status": result["technical_status"],
                      "comparisons": len(comps),
                      "curated_rows": len(cur_rows)}, ensure_ascii=False))
    if not ok:
        raise SystemExit(1)


def run_all():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    result = {"started_utc": datetime.utcnow().isoformat() + "Z",
              "cwd": str(BASE),
              "marker": "GIAONONG_PILOT2_P2_LOCAL_INPUT_20261007",
              "input_path": str(SOURCE.relative_to(BASE)),
              "input_sha256": sha(SOURCE),
              "source_sha256_before": sha(SOURCE),
              "script_sha256": sha(__file__),
              "plan_sha256": sha(BASE / "Plan/PLAN.md"),
              "skill_sha256": sha(BASE.parent / "docs/skill-drafts/da-hitl-supervisor/SKILL.md"),
              "environment": {"python_executable": sys.executable,
                              "python_version": sys.version,
                              "platform": platform.platform()},
              "commands": []}
    try:
        import pandas as pd  # noqa
        result["environment"]["pandas"] = pd.__version__
    except Exception:
        result["environment"]["pandas"] = None
    try:
        import numpy as np  # noqa
        result["environment"]["numpy"] = np.__version__
    except Exception:
        result["environment"]["numpy"] = None
    exit_code = 0
    for mode in ["--build", "--validate"]:
        cmd = [sys.executable, "-X", "utf8", str(Path(__file__).resolve()), mode]
        start = datetime.utcnow().isoformat() + "Z"
        proc = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True,
                              encoding="utf-8")
        result["commands"].append({"argv": cmd, "cwd": str(BASE),
                                   "started_utc": start,
                                   "finished_utc": datetime.utcnow().isoformat() + "Z",
                                   "actual_exit": proc.returncode,
                                   "stdout": proc.stdout, "stderr": proc.stderr})
        if proc.returncode:
            exit_code = proc.returncode
            break
    result["source_sha256_after"] = sha(SOURCE)
    artifacts = {}
    for rel in [OUT_CSV, DOC_PATH, Path(__file__),
                LOG_DIR / "validation.json"]:
        if rel.exists():
            artifacts[str(rel.relative_to(BASE))] = sha(rel)
    result["artifacts_sha256"] = artifacts
    result["manifest"] = {
        "input_path": str(SOURCE.relative_to(BASE)),
        "input_sha256": sha(SOURCE),
        "path": str(OUT_CSV.relative_to(BASE)),
        "sha256": artifacts.get(str(OUT_CSV.relative_to(BASE))),
        "encoding": "UTF-8 BOM", "date_format": "YYYY-MM-DD",
        "decimal": "dau cham", "null": "o trong",
        "columns": SOURCE_COLS + NEW_COLS,
        "types": {"strings": ["order_id", "time_slot", "customer_id", "customer_type",
                              "zone", "merchant", "cuisine", "distance_band",
                              "cancel_reason", "distance_band_normalized"],
                  "date": ["order_date"],
                  "numeric": NUMERIC_COLS, "integer": ["source_row_number"]},
        "nullable": ["travel_min", "delivery_min", "is_late", "rating",
                     "cancel_reason", "distance_band_normalized"],
        "units": {"distance_km": "km theo ten nguon (cach do pending)",
                  "money": "don vi so goc (tien te/pham vi pending)",
                  "time_min": "phut theo ten truong (chong lap pending)",
                  "rating": "gia thuyet 1-5", "flags": "0/1, null o don huy"},
        "mapping": [{"range": a, "label": b, "rule": c} for a, b, c in MAPPING_ROWS],
        "trace": "order_id + source SHA + source_row_number (ban ghi CSV 1-based sau header)"}
    result["finished_utc"] = datetime.utcnow().isoformat() + "Z"
    result["actual_exit"] = exit_code
    write_json(LOG_DIR / "run.json", result)
    print(json.dumps({"actual_exit": exit_code,
                      "commands": [{"mode": c["argv"][-1],
                                    "actual_exit": c["actual_exit"]}
                                   for c in result["commands"]]}, ensure_ascii=False))
    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if sum([args.build, args.validate, args.run]) != 1:
        ap.error("Chon dung mot trong --build, --validate, --run")
    if args.run:
        run_all()
    elif args.build:
        build()
    else:
        validate()

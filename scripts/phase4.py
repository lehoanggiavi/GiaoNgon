"""Phase 4: expected tu curated (stdlib) + doi chieu outputs native da capture.

Khong chay query/model; chi tinh expected moi tu CSV va so voi
reports/phase4/native_results.json. Count/tien exact; rate/mean/median
sai so tuyet doi <= 1e-8 o gia tri chua format. Khong hardcode P1/P3.
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
from decimal import Decimal
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CURATED = BASE / "data" / "curated" / "orders.csv"
NATIVE = BASE / "reports" / "phase4" / "native_results.json"
LOG_DIR = BASE / "Log" / "phase4"
TOL = Decimal("0.00000001")

MONEY = ["order_value", "delivery_fee", "discount", "commission", "rider_pay",
         "compensation", "revenue", "profit"]


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows():
    with CURATED.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def mean(vals):
    return sum(vals) / len(vals) if vals else None


def median(vals):
    s = sorted(vals)
    n = len(s)
    if not n:
        return None
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2


def dec(x):
    return Decimal(str(x))


def expected():
    r = rows()
    comp = [x for x in r if x["is_cancelled"] == "0"]
    e = {"n": len(r)}
    e["total"] = len(r)
    e["completed"] = len(comp)
    e["cancelled"] = len(r) - len(comp)
    e["cancel_rate"] = e["cancelled"] / e["total"] if e["total"] else None
    elig = [x for x in comp if x["is_late"] != ""]
    e["eligible"] = len(elig)
    e["late"] = sum(1 for x in elig if x["is_late"] == "1")
    e["late_rate"] = e["late"] / e["eligible"] if e["eligible"] else None
    e["coverage"] = e["eligible"] / e["completed"] if e["completed"] else None
    t = {}
    for col, key in [("prep_min", "prep"), ("rider_wait_min", "wait"),
                     ("travel_min", "travel"), ("delivery_min", "delivery")]:
        vals = [dec(x[col]) for x in comp if x[col] != "" and dec(x[col]) >= 0]
        t[key] = {"mean": mean(vals), "n": len(vals)}
    t["delivery"]["median"] = median([dec(x["delivery_min"]) for x in comp
                                     if x["delivery_min"] != ""
                                     and dec(x["delivery_min"]) >= 0])
    e["time"] = t
    e["sums"] = {c: sum(dec(x[c]) if x[c] != "" else 0 for x in r) for c in MONEY}
    e["margin"] = (e["sums"]["profit"] / e["sums"]["revenue"]
                   if e["sums"]["revenue"] else None)
    e["loss"] = sum(1 for x in r if x["profit"] != "" and dec(x["profit"]) < 0)
    nn = sum(1 for x in r if x["profit"] != "")
    e["loss_rate"] = e["loss"] / nn if nn else None
    e["active"] = len({x["customer_id"] for x in r})
    c = Counter(x["customer_id"] for x in r)
    e["repeat"] = sum(1 for v in c.values() if v >= 2)
    e["repeat_rate"] = e["repeat"] / e["active"] if e["active"] else None
    e["opc"] = e["total"] / e["active"] if e["active"] else None
    rat = [dec(x["rating"]) for x in comp if x["rating"] != ""]
    e["rating"] = {"mean": mean(rat), "n": len(rat)}
    e["mar"] = sel(r, lambda x: x["order_date"].startswith("2026-03"))
    e["aug"] = sel(r, lambda x: x["order_date"].startswith("2026-08"))
    e["q1_total"] = sum(1 for x in r if x["zone"] == "Quận 1")
    e["q1_late"] = sum(1 for x in r if x["zone"] == "Quận 1" and x["is_late"] == "1")
    trua = [x for x in r if x["time_slot"] == "Trưa"]
    e["trua_total"] = len(trua)
    e["trua_rev"] = sum(dec(x["revenue"]) if x["revenue"] != "" else 0 for x in trua)
    e["trua_late"] = sum(1 for x in trua if x["is_late"] == "1")
    ge6 = [x for x in r if x["distance_band_normalized"] == "≥6 km"]
    e["ge6_total"] = len(ge6)
    e["ge6_late"] = sum(1 for x in ge6 if x["is_late"] == "1")
    rain = [x for x in r if x["is_rain"] == "1"]
    e["rain"] = {"total": len(rain),
                 "late": sum(1 for x in rain if x["is_late"] == "1"),
                 "cancel": sum(1 for x in rain if x["is_cancelled"] == "1")}
    e["combo"] = sum(1 for x in r if x["order_date"] == "2026-03-01"
                     and x["zone"] == "Gò Vấp")
    mc = Counter(x["customer_id"] for x in e["mar"]["rows"])
    e["repeat_mar"] = sum(1 for v in mc.values() if v >= 2)
    e["active_mar"] = len(mc)
    e["nulls"] = {c: sum(1 for x in r if x[c] == "")
                  for c in ["travel_min", "delivery_min", "is_late", "rating",
                            "cancel_reason"]}
    e["mar_elig"] = sum(1 for x in r if x["order_date"].startswith("2026-03")
                        and x["is_cancelled"] == "0" and x["is_late"] != "")
    e["aug_elig"] = sum(1 for x in r if x["order_date"].startswith("2026-08")
                        and x["is_cancelled"] == "0" and x["is_late"] != "")
    e["mar_lrate"] = e["mar"]["late"] / e["mar_elig"] if e["mar_elig"] else None
    e["aug_lrate"] = e["aug"]["late"] / e["aug_elig"] if e["aug_elig"] else None
    e["mar_crate"] = e["mar"]["cancel"] / e["mar"]["total"] if e["mar"]["total"] else None
    e["aug_crate"] = e["aug"]["cancel"] / e["aug"]["total"] if e["aug"]["total"] else None
    e["native_n"] = {}
    for col, k in [("prep_min", "prep"), ("rider_wait_min", "wait"),
                   ("travel_min", "trav"), ("rating", "rat")]:
        if k == "rat":
            e["native_n"][k] = sum(1 for x in comp if x[col] != "")
        else:
            e["native_n"][k] = sum(1 for x in comp if x[col] != ""
                                   and dec(x[col]) >= 0)
    top = Counter(x["customer_id"] for x in r).most_common(1)[0]
    e["topcust"] = {"total": top[1]}
    d20 = [dec(x["delivery_min"]) for x in comp if x["delivery_min"] != ""
           and dec(x["delivery_min"]) >= 0 and dec(x["delivery_min"]) <= 20]
    e["d20"] = {"n": len(d20), "mean": mean(d20), "median": median(d20)}
    return e


def sel(r, f):
    s = [x for x in r if f(x)]
    return {"rows": s, "total": len(s),
            "cancel": sum(1 for x in s if x["is_cancelled"] == "1"),
            "late": sum(1 for x in s if x["is_late"] == "1")}


def close(a, b):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if isinstance(a, Decimal) or isinstance(b, Decimal):
        return abs(Decimal(str(a)) - Decimal(str(b))) <= TOL
    if isinstance(a, float) or isinstance(b, float):
        return abs(float(a) - float(b)) <= 1e-8
    return a == b


def parse_raw(raw):
    """Parse actual truc tiep tu raw response (header + 1 dong). O trong = None (BLANK)."""
    lines = [ln for ln in raw.splitlines() if ln.strip() != ""]
    if len(lines) != 2:
        raise ValueError(f"raw phai co 2 dong, nhan {len(lines)}")
    header = next(csv.reader([lines[0]]))
    row = next(csv.reader([lines[1]]))
    if len(header) != len(row):
        raise ValueError("header/data lech so cot")
    cols = [h.strip().strip("[]") for h in header]
    out = {}
    for h, v in zip(cols, row):
        v = v.strip()
        out[h] = None if v == "" else v
    return out


def num(v):
    if v is None:
        return None
    try:
        return int(v)
    except ValueError:
        return Decimal(v)


def check():
    exp = expected()
    doc = json.loads(NATIVE.read_text(encoding="utf-8"))
    conn, op = doc.get("connection"), doc.get("operation")
    comps = []

    def comp(name, expected_v, actual_v):
        comps.append({"check": name, "expected": str(expected_v), "actual": str(actual_v),
                      "status": "PASS" if close(expected_v, actual_v) else "FAIL"})

    def actual(rec):
        for k in ["id", "dax", "status", "raw", "fields", "phase"]:
            if k not in rec:
                raise ValueError(f"record {rec.get('id')} thieu {k}")
        if not rec["dax"].lstrip().startswith("EVALUATE"):
            raise ValueError(f"record {rec['id']} thieu DAX day du")
        if rec["status"] != "ok":
            raise ValueError(f"record {rec['id']} status khong ok")
        parsed = parse_raw(rec["raw"])
        missing = [c for c in rec["fields"] if c not in parsed]
        if missing:
            raise ValueError(f"record {rec['id']} thieu cot raw {missing}")
        return {v: num(parsed[k]) for k, v in rec["fields"].items()}

    by_id = {}
    for rec in doc["records"]:
        by_id[rec["id"]] = actual(rec)
    comp("evidence connection/operation", True, bool(conn and op))

    # Reproducer truoc sua: actual phai khop du doan loi (chung minh bug co that)
    rp = by_id["repro_pre_late"]
    comp("repro elig/late=1 = 5725 (loi)", 5725, rp["elig_l1"])
    comp("repro rate/late=1 = grand (loi)", exp["late_rate"], rp["rate_l1"])
    comp("repro coverage/late=1 = 7.63 (loi)", Decimal("7.633333333333334"), rp["cov_l1"])
    comp("repro elig/late=0 = 5725 (loi)", 5725, rp["elig_l0"])
    rl = by_id["repro_pre_lossdel"]
    comp("repro loss/profit>=0 = 1320 (loi)", 1320, rl["loss_pge"])
    comp("repro avg/del<=20 = grand (loi)", exp["time"]["delivery"]["mean"], rl["avg_d20"])
    comp("repro cnt/del<=20 = 5725 (loi)", 5725, rl["cnt_d20"])

    # Sau sua: khop expected dung
    fl = by_id["fix_late"]
    comp("fix elig/late=1 = 750", 750, fl["elig_l1"])
    comp("fix rate/late=1 = 1", 1, fl["rate_l1"])
    comp("fix coverage/late=1 = 1", 1, fl["cov_l1"])
    comp("fix elig/late=0 = 4975", 4975, fl["elig_l0"])
    comp("fix late/late=0 = 0", 0, fl["late_l0"])
    fd = by_id["fix_lossdel"]
    comp("fix loss/profit>=0 = 0", 0, fd["loss_pge"])
    comp("fix lossrate/profit>=0 = 0", 0, fd["lossrate_pge"])
    comp("fix avg/del<=20", exp["d20"]["mean"], fd["avg_d20"])
    comp("fix med/del<=20", exp["d20"]["median"], fd["med_d20"])
    comp("fix cnt/del<=20", exp["d20"]["n"], fd["cnt_d20"])

    g = by_id["grand_orders_service"]
    comp("Total Orders", exp["total"], g["total"])
    comp("Completed Orders", exp["completed"], g["completed"])
    comp("Cancelled Orders", exp["cancelled"], g["cancelled"])
    comp("Cancellation Rate", exp["cancel_rate"], g["cancel_rate"])
    comp("Late Eligible Orders", exp["eligible"], g["eligible"])
    comp("Late Orders", exp["late"], g["late"])
    comp("Late Rate", exp["late_rate"], g["late_rate"])
    comp("Late Coverage", exp["coverage"], g["coverage"])
    t = by_id["grand_time"]
    for k, nk in [("prep", "avg_prep"), ("wait", "avg_wait"),
                  ("travel", "avg_travel"), ("delivery", "avg_delivery")]:
        comp(f"Avg {k}", exp["time"][k]["mean"], t[nk])
    comp("Median Delivery", exp["time"]["delivery"]["median"], t["med_delivery"])
    comp("Delivery Eligible", exp["time"]["delivery"]["n"], t["delig"])
    f = by_id["grand_finance"]
    for c in ["order_value", "revenue", "profit"]:
        comp(f"SUM {c}", exp["sums"][c], f[c])
    comp("Profit Margin", exp["margin"], f["margin"])
    comp("Loss Orders", exp["loss"], f["loss"])
    comp("Loss Rate", exp["loss_rate"], f["loss_rate"])
    cu = by_id["grand_customers"]
    comp("Active Customers", exp["active"], cu["active"])
    comp("Repeat Customers", exp["repeat"], cu["repeat"])
    comp("Repeat Rate", exp["repeat_rate"], cu["repeat_rate"])
    comp("Orders per Customer", exp["opc"], cu["opc"])
    comp("Avg Rating", exp["rating"]["mean"], cu["rating"])
    m = by_id["mar_aug_rates"]
    comp("Mar late rate", exp["mar_lrate"], m["mar_lrate"])
    comp("Mar eligible", exp["mar_elig"], m["mar_elig"])
    comp("Mar late", exp["mar"]["late"], m["mar_late"])
    comp("Aug late rate", exp["aug_lrate"], m["aug_lrate"])
    comp("Aug eligible", exp["aug_elig"], m["aug_elig"])
    comp("Aug late", exp["aug"]["late"], m["aug_late"])
    mc = by_id["mar_aug_cancel_c1"]
    comp("Mar cancel rate", exp["mar_crate"], mc["mar_crate"])
    comp("Aug cancel rate", exp["aug_crate"], mc["aug_crate"])
    comp("cancel=1 avg BLANK", None, mc["c1_avgd"])
    comp("cancel=1 rating BLANK", None, mc["c1_rat"])
    comp("cancel=1 late rate BLANK", None, mc["c1_lrate"])
    comp("cancel=1 coverage BLANK", None, mc["c1_cov"])
    comp("cancel=1 eligible", 0, mc["c1_elig"])
    comp("cancel=1 delig", 0, mc["c1_delig"])
    nn = by_id["native_n"]
    for k in ["prep", "wait", "trav", "rat"]:
        comp(f"native n {k}", exp["native_n"][k], nn[f"n_{k}"])
    tc = by_id["top_customer"]
    comp("topcust total", exp["topcust"]["total"], tc["top_total"])
    comp("topcust active", 1, tc["top_active"])
    comp("topcust repeat", 1, tc["top_repeat"])
    comp("topcust opc", exp["topcust"]["total"], tc["top_opc"])
    lc = by_id["live_counts_q1"]
    comp("fact rows live", exp["total"], lc["fact_rows"])
    comp("customers live", exp["active"], lc["customers"])
    comp("late Q1 live", exp["q1_late"], lc["late_q1"])
    comp("Q1 total live", exp["q1_total"], lc["q1_total"])
    vl = by_id["verify_late_contexts"]
    comp("trua late", exp["trua_late"], vl["trua_late"])
    comp("ge6 late", exp["ge6_late"], vl["ge6_late"])
    comp("rain late", exp["rain"]["late"], vl["rain_late"])
    comp("mar late v2", exp["mar"]["late"], vl["mar_late2"])
    comp("aug late v2", exp["aug"]["late"], vl["aug_late2"])
    comp("mar elig v2", exp["mar_elig"], vl["mar_elig2"])
    comp("aug elig v2", exp["aug_elig"], vl["aug_elig2"])
    comp("c1 late v2", 0, vl["c1_late"])
    comp("c1 elig v2", 0, vl["c1_elig2"])
    comp("c1 completed v2", 0, vl["c1_comp"])
    ct = by_id["ctx_totals"]
    comp("Q1 total", exp["q1_total"], ct["q1_total2"])
    comp("Trua total", exp["trua_total"], ct["trua_total"])
    comp("Trua revenue", exp["trua_rev"], ct["trua_rev"])
    comp("ge6 total", exp["ge6_total"], ct["ge6_total"])
    comp("rain total", exp["rain"]["total"], ct["rain_total"])
    comp("rain cancel", exp["rain"]["cancel"], ct["rain_cancel"])
    cm = by_id["ctx_mar_aug"]
    comp("Mar total", exp["mar"]["total"], cm["mar_total"])
    comp("Mar cancel", exp["mar"]["cancel"], cm["mar_cancel"])
    comp("Aug total", exp["aug"]["total"], cm["aug_total"])
    comp("Aug cancel", exp["aug"]["cancel"], cm["aug_cancel"])
    comp("repeat Mar", exp["repeat_mar"], cm["repeat_mar"])
    comp("active Mar", exp["active_mar"], cm["active_mar"])
    nl = by_id["ctx_nulls"]
    for k, nk in [("travel_min", "null_travel"), ("delivery_min", "null_delivery"),
                  ("is_late", "null_islate"), ("rating", "null_rating")]:
        comp(f"null {k}", exp["nulls"][k], nl[nk])
    comp("reason empty", exp["nulls"]["cancel_reason"], nl["reason_empty"])
    comp("reason nonempty", 348, nl["reason_nonempty"])
    ed = by_id["ctx_edges"]
    comp("empty total", 0, ed["empty_total"])
    comp("empty rate BLANK", None, ed["empty_rate"])
    comp("empty avg BLANK", None, ed["empty_avg"])
    comp("empty sel total", 0, ed["x_total"])
    comp("empty sel rate BLANK", None, ed["x_rate"])
    comp("empty sel avg BLANK", None, ed["x_avg"])
    comp("empty sel revenue", 0, ed["x_rev"])
    comp("combo", exp["combo"], ed["combo"])
    sg = by_id["ctx_single"]
    comp("onegroup total", 1, sg["one_total"])
    comp("onegroup repeat", 0, sg["one_repeat"])
    ok = all(c["status"] == "PASS" for c in comps)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "validation.json").write_text(
        json.dumps({"comparisons": comps,
                    "technical_status": "PASS" if ok else "FAIL",
                    "tolerance": "count/tien exact; rate/mean/median |sai so|<=1e-8",
                    "expected_source": "data/curated/orders.csv doc moi"},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"technical_status": "PASS" if ok else "FAIL",
                      "comparisons": len(comps),
                      "failed": [c["check"] for c in comps if c["status"] != "PASS"]},
                     ensure_ascii=False))
    if not ok:
        raise SystemExit(1)


def run_all():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    result = {"started_utc": datetime.utcnow().isoformat() + "Z", "cwd": str(BASE),
              "marker": "GIAONONG_PILOT2_P4_REVIEW_FIX_20261008",
              "model_input": "data/curated/orders.csv",
              "input_sha256": sha(CURATED),
              "script_sha256": sha(__file__),
              "plan_sha256": sha(BASE / "Plan/PLAN.md"),
              "skill_sha256": sha(BASE.parent / "docs/skill-drafts/da-hitl-supervisor/SKILL.md"),
              "environment": {"python_executable": sys.executable,
                              "python_version": sys.version,
                              "platform": platform.platform()},
              "commands": []}
    exit_code = 0
    proc = subprocess.run([sys.executable, "-X", "utf8", str(Path(__file__).resolve()),
                           "--check"], cwd=BASE, capture_output=True, text=True,
                          encoding="utf-8")
    start = datetime.utcnow().isoformat() + "Z"
    result["commands"].append({"argv": ["--check"], "cwd": str(BASE),
                               "started_utc": start,
                               "finished_utc": datetime.utcnow().isoformat() + "Z",
                               "actual_exit": proc.returncode,
                               "stdout": proc.stdout, "stderr": proc.stderr})
    exit_code = proc.returncode
    arts = {}
    for rel in ["scripts/phase4.py", "docs/04_measures.md",
                "reports/phase4/native_results.json", "reports/phase4/registry.json",
                "Log/phase4/validation.json"]:
        p = BASE / rel
        if p.exists():
            arts[rel] = sha(p)
    result["artifacts_sha256"] = arts
    result["finished_utc"] = datetime.utcnow().isoformat() + "Z"
    result["actual_exit"] = exit_code
    (LOG_DIR / "run.json").write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
    print(json.dumps({"actual_exit": exit_code}, ensure_ascii=False))
    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if sum([args.check, args.run]) != 1:
        ap.error("Chon dung mot trong --check, --run")
    if args.check:
        check()
    else:
        run_all()

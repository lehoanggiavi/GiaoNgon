"""Phase 4B: build bang so full-precision + check doc lap tu raw.

--build: tinh reports/phase4b/tables.json tu curated (so full precision,
  chi lam tron o prose). --check: doc RAW doc lap, tinh lai moi field
  dung trong C1-C7 va doi chieu (counts/tien exact, rate/mean/median 1e-8).
--smoke: ban sao in-memory doi vai nhom phai bi checker bat (khong ghi fixture).
"""
from __future__ import annotations

import argparse
import copy
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
RAW = BASE / "data" / "giaongon_orders_2026.csv"
CURATED = BASE / "data" / "curated" / "orders.csv"
TABLES = BASE / "reports" / "phase4b" / "tables.json"
LOG_DIR = BASE / "Log" / "phase4b"
TOL = 1e-8

MONEY = ["order_value", "delivery_fee", "discount", "commission", "rider_pay",
         "compensation", "revenue", "profit"]
SOURCE_COLS_27 = ["order_id", "order_date", "time_slot", "customer_id", "customer_type",
                  "zone", "merchant", "cuisine", "distance_km", "distance_band", "is_rain",
                  "order_value", "delivery_fee", "discount", "commission", "rider_pay",
                  "compensation", "revenue", "profit", "prep_min", "rider_wait_min",
                  "travel_min", "delivery_min", "is_late", "is_cancelled",
                  "cancel_reason", "rating"]


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def norm_band(km: Decimal):
    if km < 0:
        return None
    if km < 2:
        return "<2 km"
    if km < 4:
        return "2–<4 km"
    if km < 6:
        return "4–<6 km"
    return "≥6 km"


def mean(vals):
    return sum(vals) / len(vals) if vals else None


def median(vals):
    s = sorted(vals)
    n = len(s)
    if not n:
        return None
    m = n // 2
    return s[m] if n % 2 else (s[m - 1] + s[m]) / 2


def rate(num, denom):
    return num / denom if denom else None


def compute(rows, from_raw=False):
    if from_raw:
        rows = [dict(r, distance_band_normalized=norm_band(Decimal(r["distance_km"])))
                for r in rows]
    comp = [r for r in rows if r["is_cancelled"] == "0"]
    t = {"n": len(rows)}
    months = {}
    for m in sorted({r["order_date"][:7] for r in rows}):
        s = [r for r in rows if r["order_date"].startswith(m)]
        c = [r for r in s if r["is_cancelled"] == "0"]
        e = [r for r in c if r["is_late"] != ""]
        l = [r for r in e if r["is_late"] == "1"]
        months[m] = {"orders": len(s), "cancel": len(s) - len(c),
                     "eligible": len(e), "late": len(l),
                     "cancel_rate": {"num": len(s) - len(c), "denom": len(s),
                                     "value": rate(len(s) - len(c), len(s))},
                     "late_rate": {"num": len(l), "denom": len(e),
                                   "value": rate(len(l), len(e))}}
    t["month"] = months

    def grp(key):
        g = {}
        for k in sorted({r[key] for r in rows}):
            s = [r for r in rows if r[key] == k]
            c = [r for r in s if r["is_cancelled"] == "0"]
            e = [r for r in c if r["is_late"] != ""]
            l = [r for r in e if r["is_late"] == "1"]
            g[k] = {"orders": len(s), "cancel": len(s) - len(c),
                    "eligible": len(e), "late": len(l),
                    "cancel_rate": {"num": len(s) - len(c), "denom": len(s),
                                    "value": rate(len(s) - len(c), len(s))},
                    "late_rate": {"num": len(l), "denom": len(e),
                                  "value": rate(len(l), len(e))}}
        return g

    for dim in ["zone", "time_slot", "is_rain", "distance_band_normalized", "customer_type"]:
        key = {"zone": "zone", "time_slot": "slot", "is_rain": "rain",
               "distance_band_normalized": "band", "customer_type": "ctype"}[dim]
        t[key] = grp(dim)
    for col in ["prep_min", "rider_wait_min", "travel_min", "delivery_min"]:
        v = [float(Decimal(r[col])) for r in comp
             if r[col] != "" and Decimal(r[col]) >= 0]
        t[col] = {"n": len(v), "mean": mean(v), "median": median(v)}
    t["money"] = {c: int(sum(Decimal(r[c]) if r[c] != "" else 0 for r in rows))
                  for c in MONEY}
    t["money_cancelled"] = {
        c: int(sum(Decimal(r[c]) if r[c] != "" else 0 for r in rows
                   if r["is_cancelled"] == "1"))
        for c in ["order_value", "revenue", "profit", "compensation"]}
    neg = [r for r in rows if r["profit"] != "" and Decimal(r["profit"]) < 0]
    by_zone = Counter(r["zone"] for r in neg)
    zone_n = Counter(r["zone"] for r in rows)
    t["neg"] = {"n": len(neg),
                "by_zone": {k: {"n": v, "denom": zone_n[k],
                                "value": rate(v, zone_n[k])} for k, v in by_zone.items()},
                "by_slot": dict(Counter(r["time_slot"] for r in neg)),
                "by_rain": dict(Counter(r["is_rain"] for r in neg))}
    cc = Counter(r["customer_id"] for r in rows)
    t["cust"] = {"distinct": len(cc),
                 "repeat": sum(1 for v in cc.values() if v >= 2),
                 "freq": {str(k): v for k, v in sorted(Counter(cc.values()).items())}}
    rt = [float(Decimal(r["rating"])) for r in comp if r["rating"] != ""]
    t["rating"] = {"n": len(rt), "mean": mean(rt)}
    rl = [float(Decimal(r["rating"])) for r in comp
          if r["rating"] != "" and r["is_late"] == "1"]
    rn = [float(Decimal(r["rating"])) for r in comp
          if r["rating"] != "" and r["is_late"] == "0"]
    t["rating_late"] = {"n": len(rl), "mean": mean(rl)}
    t["rating_ontime"] = {"n": len(rn), "mean": mean(rn)}
    t["nulls"] = {c: sum(1 for r in rows if r[c] == "") for c in
                  ["travel_min", "delivery_min", "is_late", "rating", "cancel_reason"]}
    cross = Counter()
    mism = 0
    for r in rows:
        km = Decimal(r["distance_km"]) if r["distance_km"] != "" else None
        nb = norm_band(km) if km is not None else None
        cross[(r["distance_band_normalized"], nb)] += 1
        if nb != r["distance_band_normalized"]:
            mism += 1
    t["band_recompute"] = {"mismatches": mism,
                           "pairs": [{"curated": k[0], "recomputed": k[1], "n": v}
                                     for k, v in sorted(cross.items(),
                                                        key=lambda x: str(x[0]))]}
    flags = {r["is_late"] for r in comp if r["is_late"] != ""}
    t["late_flags_completed"] = sorted(flags)
    return t


def build():
    rows = read_rows(CURATED)
    t = compute(rows)
    t["_meta"] = {"source": "data/curated/orders.csv", "sha256": sha(CURATED),
                  "built_utc": datetime.utcnow().isoformat() + "Z",
                  "precision": "full; rounding only in prose"}
    TABLES.write_text(json.dumps(t, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"rows": t["n"], "out": str(TABLES.relative_to(BASE))},
                     ensure_ascii=False))


def close(a, b):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    try:
        return abs(float(a) - float(b)) <= TOL
    except (TypeError, ValueError):
        return a == b


def compare_tables(t, ref_label="tables.json"):
    comps = []

    def comp(name, expected_v, actual_v):
        comps.append({"check": name, "expected": str(expected_v), "actual": str(actual_v),
                      "status": "PASS" if close(expected_v, actual_v) else "FAIL"})

    raw = read_rows(RAW)
    cur = read_rows(CURATED)
    comp("raw rows = curated rows", len(raw), len(cur))
    comp("raw order_id set = curated", sorted(r["order_id"] for r in raw),
         sorted(r["order_id"] for r in cur))
    mism = sum(1 for a, b in zip(
        sorted(raw, key=lambda r: r["order_id"]),
        sorted(cur, key=lambda r: r["order_id"]))
        for c in SOURCE_COLS_27 if (a[c] or "").strip() != (b[c] or "").strip())
    comp("raw vs curated 27 cols cell mismatch", 0, mism)
    ref = compute(raw, from_raw=True)
    comp("tables n", ref["n"], t["n"])
    for m, g in ref["month"].items():
        for k in ["orders", "cancel", "eligible", "late"]:
            comp(f"month {m} {k}", g[k], t["month"][m][k])
        for rk in ["cancel_rate", "late_rate"]:
            comp(f"month {m} {rk}.num", g[rk]["num"], t["month"][m][rk]["num"])
            comp(f"month {m} {rk}.denom", g[rk]["denom"], t["month"][m][rk]["denom"])
            comp(f"month {m} {rk}.value", g[rk]["value"], t["month"][m][rk]["value"])
    for dim in ["zone", "slot", "rain", "band", "ctype"]:
        comp(f"{dim} keys", sorted(ref[dim]), sorted(t[dim]))
        for k, g in ref[dim].items():
            for f in ["orders", "cancel", "eligible", "late"]:
                comp(f"{dim}/{k} {f}", g[f], t[dim][k][f])
            for rk in ["cancel_rate", "late_rate"]:
                comp(f"{dim}/{k} {rk}", g[rk]["value"], t[dim][k][rk]["value"])
    for c in MONEY:
        comp(f"money {c}", ref["money"][c], t["money"][c])
    for c in ["order_value", "revenue", "profit", "compensation"]:
        comp(f"money_cancelled {c}", ref["money_cancelled"][c], t["money_cancelled"][c])
    for col in ["prep_min", "rider_wait_min", "travel_min", "delivery_min"]:
        for k in ["n", "mean", "median"]:
            comp(f"{col} {k}", ref[col][k], t[col][k])
    for k in ["n", "mean"]:
        comp(f"rating {k}", ref["rating"][k], t["rating"][k])
        comp(f"rating_late {k}", ref["rating_late"][k], t["rating_late"][k])
        comp(f"rating_ontime {k}", ref["rating_ontime"][k], t["rating_ontime"][k])
    comp("neg n", ref["neg"]["n"], t["neg"]["n"])
    for k, g in ref["neg"]["by_zone"].items():
        comp(f"neg zone {k}", g["value"], t["neg"]["by_zone"][k]["value"])
    comp("cust distinct", ref["cust"]["distinct"], t["cust"]["distinct"])
    comp("cust repeat", ref["cust"]["repeat"], t["cust"]["repeat"])
    comp("cust freq", ref["cust"]["freq"], t["cust"]["freq"])
    for c, v in ref["nulls"].items():
        comp(f"null {c}", v, t["nulls"][c])
    comp("band recompute mismatches", 0, t["band_recompute"]["mismatches"])
    comp("late flags only 0/1", True, set(ref["late_flags_completed"]) <= {"0", "1"})
    return comps


def check():
    t = json.loads(TABLES.read_text(encoding="utf-8"))
    comps = compare_tables(t)
    ok = all(c["status"] == "PASS" for c in comps)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "validation.json").write_text(
        json.dumps({"comparisons": comps, "technical_status": "PASS" if ok else "FAIL",
                    "expected_source": "data/giaongon_orders_2026.csv (raw) doc lap",
                    "tolerance": "counts/tien exact; rate/mean/median |sai so|<=1e-8"},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"technical_status": "PASS" if ok else "FAIL",
                      "comparisons": len(comps),
                      "failed": [c["check"] for c in comps if c["status"] != "PASS"]},
                     ensure_ascii=False))
    if not ok:
        raise SystemExit(1)


def smoke():
    t = json.loads(TABLES.read_text(encoding="utf-8"))
    bad = copy.deepcopy(t)
    zk = next(iter(bad["zone"]))
    bad["zone"][zk]["late"] += 7
    bad["money"]["revenue"] += 1000
    bad["prep_min"]["mean"] += 0.5
    bad["cust"]["repeat"] -= 3
    comps = compare_tables(bad)
    caught = [c["check"] for c in comps if c["status"] != "PASS"]
    need = ["zone", "money revenue", "prep_min mean", "cust repeat"]
    ok = all(any(n in c for c in caught) for n in need)
    print(json.dumps({"smoke": "PASS" if ok else "FAIL",
                      "mutated": [zk, "money.revenue", "prep_min.mean", "cust.repeat"],
                      "caught": len(caught), "sample": caught[:8]}, ensure_ascii=False))
    if not ok:
        raise SystemExit(1)


def run_all():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    result = {"started_utc": datetime.utcnow().isoformat() + "Z", "cwd": str(BASE),
              "marker": "GIAONONG_PILOT2_P4B_REVIEW_FIX_20261008",
              "raw_path": "data/giaongon_orders_2026.csv",
              "raw_sha256": sha(RAW),
              "curated_path": "data/curated/orders.csv",
              "curated_sha256": sha(CURATED),
              "script_sha256": sha(__file__),
              "plan_sha256": sha(BASE / "Plan/PLAN.md"),
              "skill_sha256": sha(BASE.parent / "docs/skill-drafts/da-hitl-supervisor/SKILL.md"),
              "environment": {"python_executable": sys.executable,
                              "python_version": sys.version,
                              "platform": platform.platform()},
              "commands": []}
    exit_code = 0
    for mode in ["--build", "--check", "--smoke"]:
        cmd = [sys.executable, "-X", "utf8", str(Path(__file__).resolve()), mode]
        start = datetime.utcnow().isoformat() + "Z"
        proc = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True,
                              encoding="utf-8")
        result["commands"].append({"argv": cmd, "cwd": str(BASE), "started_utc": start,
                                   "finished_utc": datetime.utcnow().isoformat() + "Z",
                                   "actual_exit": proc.returncode,
                                   "stdout": proc.stdout, "stderr": proc.stderr})
        if proc.returncode:
            exit_code = proc.returncode
            break
    arts = {}
    for rel in ["scripts/phase4b.py", "docs/04b_findings.md",
                "reports/phase4b/tables.json", "Log/phase4b/validation.json"]:
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
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if sum([args.build, args.check, args.smoke, args.run]) != 1:
        ap.error("Chon dung mot trong --build, --check, --smoke, --run")
    if args.run:
        run_all()
    elif args.build:
        build()
    elif args.check:
        check()
    else:
        smoke()

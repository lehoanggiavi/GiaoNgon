"""Phase 3: dung PBIP semantic model moi tu curated pilot, khong clone du an cu.

Doc TMDL definition tu metadata do engine xuat (mo hinh tu tao qua MCP),
viet .pbip/.pbism/report shell trong theo schema Microsoft, tinh expected
tu curated doc moi. Khong measures, khong dashboard. Kiem runtime native
(refresh/DAX) chay rieng qua MCP/Desktop, ket qua luu vao Log/phase3.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CURATED = BASE / "data" / "curated" / "orders.csv"
CURATED_SHA = "0e0f603d59b088f509cf9b5abd10f46b94e542bc11d80ddca767d64616d286c3"
ENGINE_META = Path("C:/Users/LEHOAN~1/AppData/Local/Temp/opencode/pilot2meta")
PBI = BASE / "pbi"
SEMANTIC = PBI / "GiaoNongPilot2.SemanticModel"
DEFINITION = SEMANTIC / "definition"
REPORT = PBI / "GiaoNongPilot2.Report"
LOG_DIR = BASE / "Log" / "phase3"
REP_DIR = BASE / "reports" / "phase3"

MONEY = ["order_value", "delivery_fee", "discount", "commission", "rider_pay",
         "compensation", "revenue", "profit"]


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value) -> None:
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2),
                          encoding="utf-8")


def read_curated():
    with CURATED.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def expected():
    rows = read_curated()
    n = len(rows)
    dates = sorted({r["order_date"] for r in rows})
    years = sorted({d[:4] for d in dates})
    cal_start = date(int(years[0]), 1, 1)
    cal_end = date(int(years[-1]), 12, 31)
    cal_days = (cal_end - cal_start).days + 1
    sums = {c: str(sum(Decimal(r[c]) if r[c] != "" else 0 for r in rows)) for c in MONEY}
    return {
        "curated_rows": n,
        "curated_sha256": sha(CURATED),
        "distinct_order_id": len({r["order_id"] for r in rows}),
        "distinct_customers": len({r["customer_id"] for r in rows}),
        "date_min": min(dates), "date_max": max(dates),
        "distinct_source_dates": len(dates),
        "calendar": {"start": str(cal_start), "end": str(cal_end), "days": cal_days},
        "dims": {
            "Dim_Customer": len({r["customer_id"] for r in rows}),
            "Dim_Zone": len({r["zone"] for r in rows}),
            "Dim_TimeSlot": len({r["time_slot"] for r in rows}),
            "Dim_DistanceBand": len({r["distance_band_normalized"] for r in rows}),
            "Dim_Date": cal_days,
        },
        "dim_labels": {
            "zone": sorted({r["zone"] for r in rows}),
            "time_slot": sorted({r["time_slot"] for r in rows}),
            "distance_band_normalized": sorted({r["distance_band_normalized"] for r in rows}),
        },
        "money_sums": sums,
        "cancelled": sum(1 for r in rows if r["is_cancelled"] == "1"),
        "negative_profit": sum(1 for r in rows if r["profit"] != "" and Decimal(r["profit"]) < 0),
        "nulls": {c: sum(1 for r in rows if r[c] == "")
                  for c in ["travel_min", "delivery_min", "is_late", "rating", "cancel_reason"]},
        "relationships": [
            {"from": "Fact_Orders.order_date", "to": "Dim_Date.Date"},
            {"from": "Fact_Orders.customer_id", "to": "Dim_Customer.customer_id"},
            {"from": "Fact_Orders.zone", "to": "Dim_Zone.zone"},
            {"from": "Fact_Orders.time_slot", "to": "Dim_TimeSlot.time_slot"},
            {"from": "Fact_Orders.distance_band_normalized",
             "to": "Dim_DistanceBand.distance_band_normalized"},
        ],
    }


SHELL_PAGE = "shellpage"

REPORT_FILES = {
    "definition.pbir": {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {"byPath": {"path": "../GiaoNongPilot2.SemanticModel"}},
    },
    "definition/version.json": {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "1.0.0",
    },
    "definition/report.json": {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/1.0.0/schema.json",
        "layoutOptimization": "None",
        "themeCollection": {"baseTheme": {"name": "CY24SU06", "reportVersionAtImport": "5.55",
                                          "type": "SharedResources"}},
    },
    "definition/pages/pages.json": {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": [SHELL_PAGE],
        "activePageName": SHELL_PAGE,
    },
    f"definition/pages/{SHELL_PAGE}/page.json": {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/1.0.0/schema.json",
        "name": SHELL_PAGE,
        "displayName": "Shell",
        "displayOption": "FitToPage",
        "width": 1280,
        "height": 720,
    },
}


def build():
    if sha(CURATED) != CURATED_SHA:
        raise SystemExit("Curated SHA khac nghiem thu P2, dung lai.")
    for d in [DEFINITION / "tables", REPORT / "definition" / "pages" / SHELL_PAGE,
              LOG_DIR, REP_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    if list(DEFINITION.glob("*.tmdl")):
        build_note = ("giu definition hien co (revision da sua qua native); "
                      "khong ghi de bang snapshot temp")
    else:
        for src in sorted(ENGINE_META.glob("*.tmdl")):
            shutil.copyfile(src, DEFINITION / src.name)
        for src in sorted((ENGINE_META / "tables").glob("*.tmdl")):
            shutil.copyfile(src, DEFINITION / "tables" / src.name)
        build_note = "tao definition lan dau tu snapshot engine"
    (SEMANTIC / "definition.pbism").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.0"}, ensure_ascii=False, indent=2), encoding="utf-8")
    (PBI / "GiaoNongPilot2.pbip").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [{"report": {"path": "GiaoNongPilot2.Report"}}]},
                                      ensure_ascii=False, indent=2), encoding="utf-8")
    for rel, obj in REPORT_FILES.items():
        (REPORT / rel).write_text(json.dumps(obj, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
    (PBI / ".gitignore").write_text("**/.pbi/localSettings.json\n**/.pbi/cache.abf\n",
                                    encoding="utf-8")
    exp = expected()
    write_json(REP_DIR / "expected.json", exp)
    print(json.dumps({"tables": 6, "relationships": 5, "fact_rows": exp["curated_rows"],
                      "calendar_days": exp["calendar"]["days"],
                      "build_note": build_note}, ensure_ascii=False))


def project_files():
    files = [PBI / "GiaoNongPilot2.pbip", PBI / ".gitignore",
             SEMANTIC / "definition.pbism"]
    files += sorted(DEFINITION.glob("*.tmdl"))
    files += sorted((DEFINITION / "tables").glob("*.tmdl"))
    for rel in REPORT_FILES:
        files.append(REPORT / rel)
    return files


def validate():
    exp = expected()
    saved = json.loads((REP_DIR / "expected.json").read_text(encoding="utf-8"))
    comps = []

    def comp(name, expected_v, actual_v):
        comps.append({"check": name, "expected": expected_v, "actual": actual_v,
                      "status": "PASS" if expected_v == actual_v else "FAIL"})

    comp("curated rows", exp["curated_rows"], saved["curated_rows"])
    comp("curated sha", CURATED_SHA, exp["curated_sha256"])
    for f in project_files():
        comp(f"file exists {f.relative_to(BASE)}", True, f.exists())
    for f in sorted(DEFINITION.glob("*.tmdl")) + sorted((DEFINITION / "tables").glob("*.tmdl")):
        comp(f"tmdl ton tai {f.name}", True, f.stat().st_size > 0)
    dim_date = (DEFINITION / "tables" / "Dim_Date.tmdl").read_text(encoding="utf-8")
    fact_tmdl = (DEFINITION / "tables" / "Fact_Orders.tmdl").read_text(encoding="utf-8")
    comp("Month sort theo MonthNumber trong file", True, "sortByColumn: MonthNumber" in dim_date)
    comp("source_row_number SummarizeBy none trong file", True, "summarizeBy: none" in fact_tmdl)
    rels = (DEFINITION / "relationships.tmdl").read_text(encoding="utf-8")
    comp("5 quan he trong file", 5, sum(1 for ln in rels.splitlines() if ln.startswith("relationship ")))
    expr = (DEFINITION / "expressions.tmdl").read_text(encoding="utf-8")
    comp("DataFolder tro curated GiaoNgon", True,
         "GiaoNgon/data/curated" in expr and "orders.csv" in expr)
    for rel in REPORT_FILES:
        try:
            obj = json.loads((REPORT / rel).read_text(encoding="utf-8"))
            comp(f"report json hop le {rel}", True, isinstance(obj, dict))
        except Exception as e:
            comps.append({"check": f"report json hop le {rel}", "expected": True,
                          "actual": f"LOI: {e}", "status": "FAIL"})
    pbir = json.loads((REPORT / "definition.pbir").read_text(encoding="utf-8"))
    comp("pbir tro dung model moi",
         "../GiaoNongPilot2.SemanticModel",
         pbir["datasetReference"]["byPath"]["path"])
    manifest = json.loads((BASE / "Log/source_and_reference_hashes.json")
                          .read_text(encoding="utf-8-sig"))
    changed = [k for k, v in manifest["sha256"].items()
               if sha(BASE.parent / k) != v and (BASE.parent / k).exists()]
    comp("protected baseline giu nguyen", [], changed)
    chk = json.loads((BASE / "Log/opencode_handoff_checkpoint.json").read_text(encoding="utf-8"))
    comp("artifacts P1 giu nguyen", [],
         [k for k, v in chk["filesSha256"].items() if sha(BASE / k) != v])
    sess = json.loads((BASE / "Log/session.json").read_text(encoding="utf-8"))
    p2 = sess.get("phase2ReviewedArtifactsSha256", {})
    comp("artifacts P2 giu nguyen", [],
         [k for k, v in p2.items() if "archive" not in k and sha(BASE / k) != v])
    ok = all(c["status"] == "PASS" for c in comps)
    write_json(LOG_DIR / "validation.json",
               {"comparisons": comps, "technical_status": "PASS" if ok else "FAIL",
                "expected": exp,
                "note": "Kiem file/schema/provenance. Kiem runtime native (refresh/DAX) chay rieng, xem Log/phase3/run.json"})
    print(json.dumps({"technical_status": "PASS" if ok else "FAIL",
                      "comparisons": len(comps)}, ensure_ascii=False))
    if not ok:
        raise SystemExit(1)


def run_all():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    result = {"started_utc": datetime.utcnow().isoformat() + "Z", "cwd": str(BASE),
              "marker": "GIAONONG_PILOT2_P3_REVIEW_FIX_20261007",
              "model_input": "data/curated/orders.csv",
              "input_sha256": sha(CURATED),
              "script_sha256": sha(__file__),
              "plan_sha256": sha(BASE / "Plan/PLAN.md"),
              "skill_sha256": sha(BASE.parent / "docs/skill-drafts/da-hitl-supervisor/SKILL.md"),
              "environment": {"python_executable": sys.executable,
                              "python_version": sys.version,
                              "platform": platform.platform()},
              "commands": [], "native": {}}
    exit_code = 0
    for mode in ["--build", "--validate"]:
        cmd = [sys.executable, "-X", "utf8", str(Path(__file__).resolve()), mode]
        start = datetime.utcnow().isoformat() + "Z"
        proc = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True, encoding="utf-8")
        result["commands"].append({"argv": cmd, "cwd": str(BASE), "started_utc": start,
                                   "finished_utc": datetime.utcnow().isoformat() + "Z",
                                   "actual_exit": proc.returncode,
                                   "stdout": proc.stdout, "stderr": proc.stderr})
        if proc.returncode:
            exit_code = proc.returncode
            break
    arts = {}
    for f in project_files() + [Path(__file__), LOG_DIR / "validation.json",
                                REP_DIR / "expected.json"]:
        if f.exists():
            arts[str(f.relative_to(BASE))] = sha(f)
    result["artifacts_sha256"] = arts
    result["finished_utc"] = datetime.utcnow().isoformat() + "Z"
    result["actual_exit"] = exit_code
    write_json(LOG_DIR / "run.json", result)
    print(json.dumps({"actual_exit": exit_code}, ensure_ascii=False))
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

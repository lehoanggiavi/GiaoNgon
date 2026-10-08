"""P5C Round1: sinh PBIR 4 trang Pilot2 tu spec 5B + dieu chinh supervisor.
Chay: python scripts/build_report_p5c.py
Ghi vao pbi/GiaoNongPilot2.Report/definition/. Khong dong den model/DAX.
"""
import json
import pathlib
import itertools
import argparse
import shutil
import copy

BASE = pathlib.Path(__file__).resolve().parents[1]
REP = BASE / "pbi" / "GiaoNongPilot2.Report"
DEF = REP / "definition"

VCONS = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json"
PAGE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"


IDS = itertools.count(1)
CREAM, SIDEBAR, CORAL, GREY, INK, MUTED = "#FDF6EE", "#F7E9D7", "#E8826A", "#A8A29E", "#292524", "#78716C"
NAMES = {"Total Orders": "Số đơn", "Cancelled Orders": "Đơn hủy", "Late Orders": "Đơn trễ",
         "Late Rate": "Tỷ lệ trễ", "Late Eligible Orders": "Đơn có cờ trễ",
         "Completed Orders": "Số đơn hoàn tất", "Recorded Revenue": "Thu nhập ghi nhận",
         "Recorded Profit": "Chênh lệch ghi nhận", "Loss Orders": "Đơn âm", "Avg Rating": "Điểm trung bình",
         "YearMonth": "Tháng", "zone": "Khu vực", "time_slot": "Khung giờ",
         "distance_band_normalized": "Nhóm km", "customer_type": "Nhãn khách", "is_late": "Cờ trễ",
         "Active Customers":"Khách có đơn", "Repeat Customers":"Khách ≥2 lần"}


def lit(value):
    if isinstance(value, bool):
        raw = str(value).lower()
    elif isinstance(value, (int, float)):
        raw = str(value) + ("L" if isinstance(value, int) else "D")
    else:
        raw = "'" + str(value).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": raw}}}


def fill(color):
    return {"solid": {"color": lit(color)}}


def obj(**properties):
    return [{"properties": properties}]


def container(background="#FFFFFF", title=None, padding=8):
    result = {"background": obj(show=lit(True), color=fill(background), transparency=lit(0)),
              "border": obj(show=lit(False)), "visualHeader": obj(show=lit(False)),
              "padding": obj(top=lit(padding), bottom=lit(padding), left=lit(padding), right=lit(padding)),
              "title": obj(show=lit(bool(title)), text=lit(title or ""), fontSize=lit(11),
                           fontColor=fill(INK), bold=lit(True), titleWrap=lit(True))}
    return result


def semantic_filter(table, column, values=None, dates=None):
    field = {"Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": column}}
    if dates:
        def comparison(kind, value):
            return {"Comparison": {"ComparisonKind": kind, "Left": field,
                                   "Right": {"Literal": {"Value": "datetime'" + value + "T00:00:00'"}}}}
        condition = {"And": {"Left": comparison(2, dates[0]), "Right": comparison(4, dates[1])}}
    else:
        condition = {"In": {"Expressions": [field], "Values": [[{"Literal": {"Value": str(v) + "L"}}] for v in values]}}
    return {"Version": 2, "From": [{"Name": "s", "Entity": table, "Type": 0}], "Where": [{"Condition": condition}]}


def date_filter(name):
    return {"name": name, "field": C("Dim_Date", "Date")["field"], "type": "Advanced",
            "filter": semantic_filter("Dim_Date", "Date", dates=("2026-03-01", "2026-08-31"))}


def hx(n=10):
    return f"{next(IDS):0{n * 2}x}"


def M(table, measure):
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": table}},
                                  "Property": measure}},
            "queryRef": f"{table}.{measure}", "nativeQueryRef": measure, "displayName": NAMES.get(measure, measure)}


def C(table, col):
    return {"field": {"Column": {"Expression": {"SourceRef": {"Entity": table}},
                                 "Property": col}},
            "queryRef": f"{table}.{col}", "nativeQueryRef": col, "displayName": NAMES.get(col, col)}


def visual(vtype, x, y, w, h, query, extra=None, z=1000):
    v = {"$schema": VCONS, "name": hx(), "position": {"x": x, "y": y, "z": z,
         "height": h, "width": w, "tabOrder": z},
         "visual": {"visualType": vtype, "query": query,
                    "visualContainerObjects": container()}}
    if extra:
        v["visual"].update(extra)
    if not query:
        del v["visual"]["query"]
    return v


def card(measures, x, y, w, h, label, z=1000):
    ms = measures if isinstance(measures, list) else [measures]
    auxiliary = {"Cancellation Rate": "Total Orders", "Late Coverage": "Completed Orders",
                 "Recorded Profit Margin": "Recorded Revenue", "Loss Rate": "Total Orders"}
    if len(ms) == 1 and ms[0] in auxiliary:
        ms.append(auxiliary[ms[0]])
    q = {"queryState": {"Values": {"projections": [M("Measure", ms[0])]}}}
    money = ms[0].startswith("Recorded ") and "Margin" not in ms[0]
    precision = 2 if any(t in ms[0] for t in ("Rate", "Margin", "Coverage", "Minutes", "Rating", "per Customer")) or money else 0
    has_footer = len(ms)>1 or money
    value_height=h-44 if has_footer else h-28
    value_font=24 if h>=90 else 20 if h>=76 else 18 if h>=72 else 16
    v=visual("card",x+12,y+24,w-24,value_height,q,z=z)
    v["visual"]["visualContainerObjects"]=container(padding=0)
    v["visual"]["objects"]={"labels":obj(fontSize=lit(value_font),color=fill(INK),bold=lit(True),
        labelDisplayUnits=lit(1000000 if money else 1),labelPrecision=lit(precision)),"categoryLabels":obj(show=lit(False))}
    # Giá trị và dòng mẫu số có vùng thật riêng; card mới tự co nội dung gây cắt số.
    output=[textbox("",x,y,w,h,background="#FFFFFF",z=z-1),v,
            textbox(label,x+12,y+5,w-24,20,size=9,bold=False,background="#FFFFFF",z=z+1),
            textbox("",x,y,w,3,background=CORAL,z=z+2)]
    if len(ms) > 1:
        prefix = "Mẫu số:" if ms[0] != "Avg Rating" else "Đơn hoàn tất:"
        if "Minutes" in ms[0]:
            prefix = "Số đơn có thời gian:"
        labelw = 118 if "Minutes" in ms[0] else 78
        output.append(textbox(prefix, x+12, y+h-20, labelw, 20, size=8, bold=False,background="#FFFFFF"))
        n = visual("card", x+12+labelw, y+h-20, w-labelw-22, 20,
                   {"queryState": {"Values": {"projections": [M("Measure", ms[1])]}}})
        n["visual"]["objects"] = {"labels": obj(fontSize=lit(9), color=fill(MUTED),
                                                 labelDisplayUnits=lit(1), labelPrecision=lit(0)),
                                     "categoryLabels": obj(show=lit(False))}
        n["visual"]["visualContainerObjects"] = container(padding=0)
        output.append(n)
    elif money:
        output.append(textbox("triệu · đơn vị theo nguồn", x+12, y+h-20, w-24, 20, size=8, bold=False,background="#FFFFFF"))
    return output


def textbox(text, x, y, w, h, size=20, bold=True, z=1000, background=None):
    if not text:
        v=visual("shape",x,y,w,h,{},z=z)
        v["visual"]["objects"]={"shape":obj(tileShape=lit("rectangle")),
                                  "fill":[{"properties":{"show":lit(True)}},{"selector":{"id":"default"},
                                          "properties":{"fillColor":fill(background or CREAM),"transparency":lit(0)}}],
                                  "outline":obj(show=lit(False))}
        v["visual"]["visualContainerObjects"]=container(background or CREAM,padding=0)
        return v
    return {"$schema": VCONS, "name": hx(),
            "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z},
            "visual": {"visualType": "textbox",
                       "visualContainerObjects": container(background or CREAM, padding=0),
                       "objects": {"general": [{
                           "properties": {
                               "paragraphs": [{
                                   "textRuns": [{
                                       "value": text,
                                       "textStyle": {"fontSize": str(size) + "pt",
                                                    "fontFamily": "Segoe UI", "color": INK,
                                                    "bold": bold}}]}]}}]}}}


def cartesian(vtype, category, ys, x, y, w, h, tooltips=None, sort_desc=None, z=1000, title=None):
    qs = {"Category": {"projections": [category]}, "Y": {"projections": ys}}
    if tooltips:
        qs["Tooltips"] = {"projections": tooltips}
    q = {"queryState": qs}
    if sort_desc:
        q["sortDefinition"] = {"sort": [{"field": sort_desc, "direction": "Descending"}],
                               "isDefaultSort": False}
    v = visual(vtype, x, y, w, h, q, z=z)
    v["visual"]["objects"] = {
        "categoryAxis": obj(showAxisTitle=lit(False), fontSize=lit(9), labelColor=fill(MUTED), axisType=lit("Categorical")),
        "valueAxis": obj(showAxisTitle=lit(False), fontSize=lit(9), labelColor=fill(MUTED)),
        "legend": obj(show=lit(len(ys)>1), position=lit("Top"), fontSize=lit(9), showTitle=lit(False)),
        "dataPoint": obj(defaultColor=fill(CORAL))}
    if len(ys)>1:
        v["visual"]["objects"]["dataPoint"] = [{"properties": {"fill": fill(color)}, "selector": {"metadata": s["queryRef"]}}
                                              for s,color in zip(ys, [GREY,CORAL])]
    v["visual"]["visualContainerObjects"]=container(title=title)
    return v


def tableex(cols, x, y, w, h, z=1000, title=None):
    v=visual("tableEx", x, y, w, h, {"queryState": {"Values": {"projections": cols}}},z=z)
    v["visual"]["visualContainerObjects"]=container(title=title)
    v["visual"]["objects"]={"columnHeaders":obj(fontSize=lit(9),fontColor=fill(INK),backColor=fill(SIDEBAR)),
                              "values":obj(fontSize=lit(9),fontColorPrimary=fill(INK)),"grid":obj(rowPadding=lit(3))}
    return v


def slicer(col, x, y, w, h, z=1000):
    v = visual("slicer", x, y, w, h, {"queryState": {"Values": {"projections": [col]}}}, z=z)
    isdate = col["queryRef"] == "Dim_Date.Date"
    label = {"Dim_Date.Date": "Kỳ", "Dim_Zone.zone": "Khu vực", "Fact_Orders.is_rain": "Mưa (0/1)",
             "Fact_Orders.is_cancelled": "Trạng thái (0/1)"}.get(col["queryRef"], col["displayName"])
    v["visual"]["visualContainerObjects"] = container(SIDEBAR if x<180 else "#F5EFE6", padding=0)
    v["visual"]["objects"] = {"data": obj(mode=lit("Between" if isdate else "Dropdown")),
                               "header": obj(show=lit(True), text=lit(label), textSize=lit(9), fontColor=fill(INK)),
                               "items": obj(textSize=lit(9), fontColor=fill(INK), padding=lit(0)),
                               "slider": obj(show=lit(False), color=fill(CORAL)),
                               "selection": obj(singleSelect=lit(False), selectAllCheckboxEnabled=lit(True))}
    if col["queryRef"] in ("Dim_Date.Date", "Dim_Zone.zone"):
        v["visual"]["syncGroup"] = {"groupName": "Pilot2_"+col["queryRef"], "fieldChanges": True, "filterChanges": True}
    if isdate:
        v["filterConfig"] = {"filters": [date_filter("Period"+v["name"])]}
    return v


def button(label, target, x, y, w=152, h=32, active=False, reset=False):
    v = visual("actionButton", x,y,w,h,{})
    v["visual"]["objects"] = {"text": [{"properties":{"show":lit(True)}},{"selector": {"id": "default"}, "properties": {
        "text": lit(label), "fontSize": lit(10), "bold": lit(active),
        "fontColor": fill("#FFFFFF" if active else INK)}}],
        "fill": [{"properties":{"show":lit(True)}},{"selector": {"id": "default"}, "properties": {
                 "fillColor": fill(CORAL if active else "#DED6CC"), "transparency": lit(0)}}],
        "shape":obj(tileShape=lit("rectangleRoundedByPixel"),rectangleRoundedCurve=lit(16)),
        "outline": obj(show=lit(False))}
    v["visual"]["visualContainerObjects"] = container(SIDEBAR,padding=0)
    v["visual"]["visualContainerObjects"]["visualLink"] = obj(show=lit(True),
        type=lit("Bookmark" if reset else "PageNavigation"),
        **({"bookmark": lit(target)} if reset else {"navigationSection": lit(target)}))
    return v


ME = "Measure"
F = "Fact_Orders"
DD = "Dim_Date"
DZ = "Dim_Zone"
DS = "Dim_TimeSlot"
DB = "Dim_DistanceBand"

PAGES = {}


def page(name, disp, visuals):
    pid = "ReportSection" + name
    visuals = [item for v in visuals for item in (v if isinstance(v,list) else [v])]
    # Slicer chung đồng bộ; slicer riêng chỉ lọc trang hiện tại.
    local_labels=[]
    for v in visuals:
        if v["visual"]["visualType"] == "textbox":
            if v["position"]["y"] == 14:
                v["position"]["height"] = 38
                v["visual"]["objects"]["general"][0]["properties"]["paragraphs"][0]["textRuns"][0]["textStyle"].update(fontFamily="Georgia",bold=True)
            if v["position"]["y"] == 48:
                v["position"]["height"] = 28
        if v["visual"]["visualType"] == "slicer":
            ref=v["visual"]["query"]["queryState"]["Values"]["projections"][0]["queryRef"]
            if ref == "Dim_Date.Date":
                v["position"].update(y=318,height=84)
            elif ref == "Dim_Zone.zone":
                v["position"].update(y=420,height=76)
            else:
                local={"Dim_TimeSlot.time_slot":206,"Fact_Orders.is_rain":476,
                       "Dim_DistanceBand.distance_band_normalized":746,"Fact_Orders.is_cancelled":206}
                label=v["visual"]["objects"]["header"][0]["properties"]["text"]["expr"]["Literal"]["Value"].strip("'")
                local_labels.append(textbox(label,local[ref],84,76,32,size=9,bold=False,background="#F5EFE6"))
                v["position"].update(x=local[ref]+76,y=76,width=156,height=48)
                v["visual"]["objects"]["header"]=obj(show=lit(False))
    visuals.extend(local_labels)
    visuals.insert(0,textbox("",0,0,180,720,background=SIDEBAR,z=0))
    visuals.extend([textbox("GiaoNóng Pilot2",14,20,152,32,size=13,background=SIDEBAR),
                    textbox("Giao hàng · 2026",14,52,152,28,size=9,bold=False,background=SIDEBAR),
                    textbox("BỘ LỌC",14,288,152,22,size=8,bold=True,background=SIDEBAR),
                    textbox("Dữ liệu đến 31/08/2026",1040,20,232,28,size=9,bold=False),
                    textbox("Kỳ nguồn: 01/03–31/08/2026",192,48,780,28,size=9,bold=False),
                    button("Xóa lọc", "ResetPilot2",14,508,reset=True),
                    textbox("Trở về kỳ nguồn",14,546,152,24,size=8,bold=False,background=SIDEBAR)])
    for i,(key,label) in enumerate((("tongquan","Tổng quan"),("vanhanh","Vận hành"),("taichinh","Tài chính"),("khachhang","Khách hàng"))):
        visuals.append(button(label,"ReportSection"+key,14,90+i*42,active=key==name))
    if name in ("vanhanh","taichinh"):
        visuals.insert(1,textbox("",192,72,1080,56,background="#F5EFE6",z=1))
        visuals.append(textbox("Chỉ lọc trong trang",1002,84,262,28,size=9,bold=False,background="#F5EFE6"))
    if name=="vanhanh":
        visuals.append(textbox("Thời gian: phút · Cờ mưa: 0 = không mưa, 1 = mưa theo nguồn",192,698,1080,22,size=8,bold=False))
    if name=="taichinh":
        visuals.append(textbox("Tiền: đơn vị theo nguồn · Trạng thái: 0 = hoàn tất, 1 = hủy · Chưa xác nhận phạm vi kế toán",192,698,1080,22,size=8,bold=False))
    if name=="khachhang":
        visuals.append(textbox("Khách được tính lại trong kỳ lọc · Nhãn khách theo từng đơn · Cờ trễ: 0 = đúng giờ, 1 = trễ theo nguồn",192,698,1080,22,size=8,bold=False))
    if name=="khachhang":
        rating=next(v for v in visuals if v["visual"].get("query",{}).get("queryState",{}).get("Category",{}).get("projections",[{}])[0].get("queryRef")=="Fact_Orders.is_late")
        rating["filterConfig"]={"filters":[{"name":"RatingCompletedOnly", "field": C("Fact_Orders","is_cancelled")["field"],
                                             "type":"Categorical", "filter": semantic_filter("Fact_Orders","is_cancelled",[0])}]}
    PAGES[pid] = (disp, visuals)
    return pid


def build(overview_only=False):
    legacy = REP / "report.json"
    if legacy.exists():
        if json.loads(legacy.read_text(encoding="utf-8-sig")).get("sections"):
            raise RuntimeError("Report legacy có nội dung: giữ nguyên và review trước khi chuyển PBIR")
        # Bản legacy rỗng đã được lưu tại Log/phase5c/takeover_before.
        legacy.unlink()
    # Bố cục tham chiếu: số 2x2 bên trái, biểu đồ lớn bên phải, 2x2 ô phía dưới.
    # Chỉ dùng measure/cột Pilot2 đã có; không nhập nội dung hay công thức mẫu.
    v = [textbox("Tổng quan vận hành",192,14,600,38),
         card("Total Orders",192,76,210,90,"Tổng số đơn"),
         card("Cancellation Rate",412,76,210,90,"Tỷ lệ hủy"),
         card(["Late Rate","Late Eligible Orders"],192,174,210,90,"Tỷ lệ trễ"),
         card("Recorded Profit",412,174,210,90,"Chênh lệch ghi nhận"),
         cartesian("lineChart",C(DD,"YearMonth"),[M(ME,"Total Orders")],636,76,636,188,
                   tooltips=[M(ME,"Cancelled Orders"),M(ME,"Late Orders")],title="Số đơn theo tháng"),
         cartesian("clusteredColumnChart",C(DD,"YearMonth"),[M(ME,"Cancelled Orders"),M(ME,"Late Orders")],
                   192,276,530,198,title="Đơn hủy và trễ theo tháng"),
         cartesian("clusteredColumnChart",C(DS,"time_slot"),[M(ME,"Completed Orders"),M(ME,"Cancelled Orders")],
                   734,276,538,198,title="Hoàn tất và hủy theo khung giờ"),
         cartesian("columnChart",C(DZ,"zone"),[M(ME,"Late Rate")],192,486,530,206,
                   tooltips=[M(ME,"Late Orders"),M(ME,"Late Eligible Orders")],title="Tỷ lệ trễ theo khu vực"),
         cartesian("barChart",C(DZ,"zone"),[M(ME,"Total Orders")],734,486,538,206,
                   sort_desc=M(ME,"Total Orders")["field"],title="Số đơn theo khu vực"),
         slicer(C(DD,"Date"),14,318,152,84),slicer(C(DZ,"zone"),14,420,152,76)]
    p1 = page("tongquan", "Tổng quan", v)
    v = [textbox("Vận hành giao hàng",192,14,600,38),
         card("Late Orders",192,140,210,80,"Số đơn trễ"),
         card(["Late Rate","Late Eligible Orders"],412,140,210,80,"Tỷ lệ trễ"),
         card("Late Coverage",192,228,210,80,"Độ phủ dữ liệu trễ"),
         card(["Median Delivery Minutes","Delivery Eligible Orders"],412,228,210,80,"Giao trung vị (phút)"),
         cartesian("columnChart",C(DB,"distance_band_normalized"),[M(ME,"Late Rate")],636,140,636,168,
                   tooltips=[M(ME,"Late Orders"),M(ME,"Late Eligible Orders")],
                   sort_desc=M(ME,"Late Rate")["field"],title="Tỷ lệ trễ từ cao xuống thấp · nhóm km"),
         cartesian("columnChart",C(DS,"time_slot"),[M(ME,"Late Rate")],192,320,530,174,
                   tooltips=[M(ME,"Late Orders"),M(ME,"Late Eligible Orders")],title="Tỷ lệ trễ theo khung giờ"),
         card("Avg Prep Minutes",734,320,263,83,"Chuẩn bị (phút)"),
         card("Avg Rider Wait Minutes",1009,320,263,83,"Chờ xe (phút)"),
         card("Avg Travel Minutes",734,411,263,83,"Di chuyển (phút)"),
         card("Avg Delivery Minutes",1009,411,263,83,"Giao trung bình (phút)"),
         tableex([C(DZ,"zone"),M(ME,"Cancelled Orders"),M(ME,"Late Orders"),M(ME,"Late Rate")],
                 192,506,530,186,title="Hủy và trễ theo khu vực"),
         cartesian("columnChart",C(F,"is_rain"),[M(ME,"Late Rate")],734,506,538,186,
                   tooltips=[M(ME,"Late Orders"),M(ME,"Late Eligible Orders")],title="Tỷ lệ trễ theo cờ mưa · 0 / 1"),
         slicer(C(DD,"Date"),14,318,152,84),slicer(C(DZ,"zone"),14,420,152,76),
         slicer(C(DS,"time_slot"),206,76,232,48),slicer(C(F,"is_rain"),476,76,232,48),
         slicer(C(DB,"distance_band_normalized"),746,76,232,48)]
    p2 = page("vanhanh", "Vận hành", v)
    v = [textbox("Tài chính ghi nhận",192,14,600,38),
         card("Recorded Order Value",192,140,210,68,"Giá trị đơn"),
         card("Recorded Revenue",412,140,210,68,"Thu nhập"),
         card("Recorded Profit",192,216,210,68,"Chênh lệch ghi nhận"),
         card("Recorded Profit Margin",412,216,210,68,"Biên chênh lệch"),
         card("Loss Orders",192,292,210,68,"Số đơn âm"),
         card("Loss Rate",412,292,210,68,"Tỷ lệ đơn âm"),
         cartesian("lineChart",C(DD,"YearMonth"),[M(ME,"Recorded Revenue")],636,140,636,220,
                   title="Thu nhập ghi nhận theo tháng · đơn vị nguồn"),
         cartesian("clusteredColumnChart",C(DD,"YearMonth"),[M(ME,"Recorded Revenue"),M(ME,"Recorded Profit")],
                   192,372,530,154,title="Thu nhập và chênh lệch theo tháng"),
         cartesian("columnChart",C(DZ,"zone"),[M(ME,"Loss Rate")],734,372,538,154,
                   tooltips=[M(ME,"Loss Orders"),M(ME,"Total Orders")],title="Tỷ lệ đơn âm theo khu vực"),
         tableex([C(DZ,"zone"),M(ME,"Recorded Revenue"),M(ME,"Recorded Profit"),M(ME,"Loss Orders")],
                 192,538,530,154,title="Số ghi nhận theo khu vực · đơn vị nguồn"),
         cartesian("barChart",C(DZ,"zone"),[M(ME,"Recorded Profit Margin")],734,538,538,154,
                   tooltips=[M(ME,"Recorded Profit"),M(ME,"Recorded Revenue")],title="Biên chênh lệch theo khu vực"),
         slicer(C(DD,"Date"),14,318,152,84),slicer(C(DZ,"zone"),14,420,152,76),
         slicer(C(F,"is_cancelled"),206,76,232,48)]
    p3 = page("taichinh", "Tài chính", v)
    v = [textbox("Khách hàng trong kỳ",192,14,600,38),
         card("Active Customers",192,76,210,72,"Khách trong kỳ"),
         card("Repeat Customers",412,76,210,72,"Khách ≥2 lần"),
         card(["Repeat Customer Rate","Active Customers"],192,156,210,72,"Tỷ lệ lặp lại"),
         card("Orders per Customer",412,156,210,72,"Số đơn / khách"),
         card(["Avg Rating","Completed Orders"],192,236,430,72,"Điểm trung bình"),
         cartesian("columnChart",C(F,"is_late"),[M(ME,"Avg Rating")],636,76,636,232,
                   tooltips=[M(ME,"Completed Orders")],title="Điểm theo cờ đúng giờ / trễ · 0 / 1"),
         cartesian("columnChart",C(F,"customer_type"),[M(ME,"Total Orders")],192,320,530,180,
                   title="Số đơn theo nhãn khách của nguồn"),
         cartesian("clusteredColumnChart",C(DD,"YearMonth"),[M(ME,"Active Customers"),M(ME,"Repeat Customers")],
                   734,320,538,180,title="Khách có đơn và khách ≥2 lần theo tháng"),
         cartesian("barChart",C(DZ,"zone"),[M(ME,"Total Orders")],192,512,530,180,
                   title="Số đơn theo khu vực",sort_desc=M(ME,"Total Orders")["field"]),
         cartesian("barChart",C(DZ,"zone"),[M(ME,"Active Customers")],734,512,538,180,
                   title="Khách có đơn theo khu vực",sort_desc=M(ME,"Active Customers")["field"]),
         slicer(C(DD,"Date"),14,318,152,84),slicer(C(DZ,"zone"),14,420,152,76)]
    p4 = page("khachhang", "Khách hàng", v)

    if overview_only:
        for pid in list(PAGES):
            if pid != p1:
                del PAGES[pid]
    reset_sections = {}
    for pid, (disp, visuals) in PAGES.items():
        pdir = DEF / "pages" / pid
        (pdir / "visuals").mkdir(parents=True, exist_ok=True)
        wanted={v["name"] for v in visuals}
        for old in (pdir/"visuals").iterdir():
            # Chỉ xóa visual ID do generator này sở hữu; không xóa chỉnh sửa của người khác.
            if old.is_dir() and old.name not in wanted and old.name.startswith("000000000000"):
                assert old.resolve().is_relative_to((DEF/"pages").resolve())
                shutil.rmtree(old)
        interactions=[]
        if pid==p4:
            rating=next(v for v in visuals if v.get("filterConfig",{}).get("filters",[{}])[0].get("name")=="RatingCompletedOnly")
            interactions=[{"source":rating["name"],"target":v["name"],"type":"NoFilter"}
                          for v in visuals if v["visual"]["visualType"] in ("cardVisual","card")]
        (pdir / "page.json").write_text(json.dumps({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
            "name": pid, "displayName": disp, "displayOption": "FitToPage",
            "height": 720, "width": 1280,
            "objects": {"background": obj(color=fill(CREAM),transparency=lit(0))},
            "visualInteractions": interactions}, ensure_ascii=False, indent=2), encoding="utf-8")
        reset_visuals={}
        for vv in visuals:
            vd = pdir / "visuals" / vv["name"]
            vd.mkdir(exist_ok=True)
            (vd / "visual.json").write_text(json.dumps(vv, ensure_ascii=False, indent=2),
                                            encoding="utf-8")
            if vv["visual"]["visualType"]=="slicer":
                fs=copy.deepcopy(vv.get("filterConfig",{}).get("filters",[]))
                for f in fs:
                    f["howCreated"]=0
                    f["expression"]=f.pop("field")
                reset_visuals[vv["name"]]={"filters":{"byName":{f["name"]:f for f in fs}},
                    "singleVisual":{"visualType":"slicer", "objects":{"merge":copy.deepcopy(vv["visual"]["objects"])}}}
        reset_sections[pid]={"visualContainers":reset_visuals}
    (DEF / "pages" / "pages.json").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": list(PAGES), "activePageName": p1},
        ensure_ascii=False, indent=2), encoding="utf-8")
    (DEF / "version.json").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0"}, ensure_ascii=False, indent=2), encoding="utf-8")
    (DEF / "report.json").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
        "themeCollection": {"baseTheme": {"name": "CY24SU06", "reportVersionAtImport":
                                          {"visual": "2.13.0", "report": "3.4.0", "page": "2.3.1"},
                                          "type": "SharedResources"}},
        "filterConfig":{"filters":[date_filter("SourcePeriod")]}},
        ensure_ascii=False, indent=2), encoding="utf-8")
    bd=DEF/"bookmarks"
    bd.mkdir(exist_ok=True)
    (bd/"bookmarks.json").write_text(json.dumps({"$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definition/bookmarksMetadata/1.0.0/schema.json", "items":[{"name":"ResetPilot2"}]},indent=2),encoding="utf-8")
    (bd/"ResetPilot2.bookmark.json").write_text(json.dumps({"$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definition/bookmark/1.0.0/schema.json",
        "displayName":"Xóa lọc", "name":"ResetPilot2", "options":{"suppressActiveSection":True,"suppressDisplay":True,"suppressData":False},
        "explorationState":{"version":"1.0","activeSection":p1,"sections":reset_sections}},ensure_ascii=False,indent=2),encoding="utf-8")
    assert len(PAGES)==(1 if overview_only else 4)
    assert all(len({v['name'] for v in vs})==len(vs) for _,vs in PAGES.values())
    assert all(0 <= v['position']['x'] <= 1280-v['position']['width'] and
               0 <= v['position']['y'] <= 720-v['position']['height']
               for _,vs in PAGES.values() for v in vs), 'Visual ngoài canvas'
    n = sum(len(v) for _, v in PAGES.values())
    print(json.dumps({"pages": len(PAGES), "visuals": n}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--overview-only", action="store_true")
    build(parser.parse_args().overview_only)

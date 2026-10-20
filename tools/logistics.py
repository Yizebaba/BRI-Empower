"""物流与贸易（免费、不要密钥）：
1. IMF PortWatch（ArcGIS FeatureServer，卫星 AIS 估算）：150 国港口近 30 天靠港次数、进出口量（公吨），与前 30 天比较；主要港口；28 个海上咽喉要道近 7 天通行。
2. UN Comtrade 公共预览接口（每次最多 500 条）：中国与各国的年度货物贸易额（出口、进口，美元）。
输出 data/logistics.json。用法：python3 tools/logistics.py
"""
import json, time, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

NOW = datetime.now(timezone.utc); iso = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")
UA = {"user-agent": "BRI-Empower (github.com/Yizebaba/BRI-Empower)"}
C = json.load(open("data/bri_countries.json"))["countries"]
ISO3 = [c["iso3"] for c in C]; NUM = {int(c["num"]): c["iso3"] for c in C}
PW = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/ArcGIS/rest/services/"
ERR = {}


def get(url, params=None, post=False):
    data = None
    if params and post: data = urllib.parse.urlencode(params).encode()   # 条件很长时用 POST（GET 的网址太长会被拒）
    elif params: url += "?" + urllib.parse.urlencode(params)
    h = dict(UA, **({"content-type": "application/x-www-form-urlencoded"} if data else {}))
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=120) as r: return json.loads(r.read())


def pw_stats(svc, where, group, stats):
    p = {"where": where, "groupByFieldsForStatistics": group, "f": "json",
         "outStatistics": json.dumps([{"statisticType": t, "onStatisticField": f, "outStatisticFieldName": o} for t, f, o in stats])}
    j = get(PW + svc + "/FeatureServer/0/query", p, post=True)
    if "error" in j: raise RuntimeError(str(j["error"])[:200])
    return [f["attributes"] for f in j.get("features", [])]


DSTR = {}
def latest_date(svc):
    a = pw_stats(svc, "1=1", "", [("max", "date", "d")]); v = a[0]["d"]
    if isinstance(v, str):   # 有的服务把 date 存成文本（YYYY-MM-DD…），比较时用字符串
        DSTR[svc] = True; return datetime.fromisoformat(v[:10]).replace(tzinfo=timezone.utc)
    return datetime.fromtimestamp(v / 1000, timezone.utc)
def DQ(svc, d): return ("'" + d.strftime("%Y-%m-%d") + "'") if DSTR.get(svc) else ("DATE '" + d.strftime("%Y-%m-%d") + "'")


out = {"generated": iso(NOW), "portwatch": {}, "comtrade": {}, "errors": ERR}
ports = {k: {} for k in ISO3}
try:
    end = latest_date("Daily_Ports_Data"); d30 = end - timedelta(days=30); d60 = end - timedelta(days=60)
    D = lambda d: DQ("Daily_Ports_Data", d)
    inlist = "ISO3 IN (" + ",".join("'" + k + "'" for k in ISO3) + ")"
    S = [("sum", "portcalls", "calls"), ("sum", "import", "imp"), ("sum", "export", "exp")]
    for row in pw_stats("Daily_Ports_Data", f"{inlist} AND date > {D(d30)}", "ISO3", S):
        ports[row["ISO3"]].update({"calls30": row["calls"], "import30": round(row["imp"] or 0), "export30": round(row["exp"] or 0)})
    for row in pw_stats("Daily_Ports_Data", f"{inlist} AND date > {D(d60)} AND date <= {D(d30)}", "ISO3", S):
        ports[row["ISO3"]].update({"calls_prev": row["calls"], "import_prev": round(row["imp"] or 0), "export_prev": round(row["exp"] or 0)})
    top = pw_stats("Daily_Ports_Data", f"{inlist} AND date > {D(d30)}", "ISO3,portname,portid", S)
    for row in sorted(top, key=lambda r: -(r["calls"] or 0)):
        L = ports[row["ISO3"]].setdefault("ports", [])
        if len(L) < 6: L.append({"name": row["portname"], "id": row["portid"], "calls30": row["calls"], "import30": round(row["imp"] or 0), "export30": round(row["exp"] or 0)})
    out["portwatch"] = {"source": "IMF PortWatch（Daily Ports Data）", "url": "https://portwatch.imf.org/", "data_until": iso(end), "window_days": 30, "countries": {k: v for k, v in ports.items() if v}}
except Exception as e: ERR["portwatch_ports"] = str(e)[:200]
try:
    end = latest_date("Daily_Chokepoints_Data"); d7 = end - timedelta(days=7); d14 = end - timedelta(days=14)
    D = lambda d: DQ("Daily_Chokepoints_Data", d)
    S = [("sum", "n_total", "n"), ("sum", "capacity", "cap")]
    cur = {r["portname"]: r for r in pw_stats("Daily_Chokepoints_Data", f"date > {D(d7)}", "portname,portid", S)}
    prev = {r["portname"]: r for r in pw_stats("Daily_Chokepoints_Data", f"date > {D(d14)} AND date <= {D(d7)}", "portname", S)}
    out["portwatch"]["chokepoints"] = {"data_until": iso(end), "window_days": 7, "items": sorted([{"name": k, "id": v.get("portid"), "transits7": v["n"], "capacity7": round(v["cap"] or 0), "transits_prev": (prev.get(k) or {}).get("n")} for k, v in cur.items()], key=lambda x: -(x["transits7"] or 0))}
except Exception as e: ERR["portwatch_chokepoints"] = str(e)[:200]
try:
    for yr in (NOW.year - 1, NOW.year - 2, NOW.year - 3):
        rows = get("https://comtradeapi.un.org/public/v1/preview/C/A/HS", {"reporterCode": 156, "period": yr, "cmdCode": "TOTAL", "flowCode": "X,M", "partner2Code": 0, "customsCode": "C00", "motCode": 0}).get("data") or []
        if len(rows) > 50: break
    cty = {}
    for r in rows:
        k = NUM.get(int(r.get("partnerCode") or 0))
        if not k: continue
        cty.setdefault(k, {})["export" if r.get("flowCode") == "X" else "import"] = r.get("primaryValue")
    out["comtrade"] = {"source": "UN Comtrade（中国申报，年度，美元）", "url": "https://comtradeplus.un.org/", "year": yr, "countries": cty}
except Exception as e: ERR["comtrade"] = str(e)[:200]
json.dump(out, open("data/logistics.json", "w"), ensure_ascii=False, separators=(",", ":"))
print("logistics:", len((out.get("portwatch") or {}).get("countries", {})), "countries with ports;", len(((out.get("portwatch") or {}).get("chokepoints") or {}).get("items", [])), "chokepoints;", len(out["comtrade"].get("countries", {})), "comtrade;", ERR)

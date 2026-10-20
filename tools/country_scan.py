"""150 个共建国家的国家级态势（免费一手来源，每 30 分钟）：
USGS 地震（M4.5+，近 7 天）、GDACS 灾害警报（近 14 天）、NASA EONET 自然事件（近 30 天）按国界归到国家；美国国务院旅行建议级别。
输出 data/country_live.json。用法：python3 tools/country_scan.py
"""
import json, re, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from shapely.geometry import shape, Point
from shapely.prepared import prep

NOW = datetime.now(timezone.utc); iso = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")
UA = {"user-agent": "BRI-Empower-scan (github.com/Yizebaba/BRI-Empower)"}
get = lambda u, raw=False: (lambda b: b if raw else json.loads(b))(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read())
C = json.load(open("data/bri_countries.json"))["countries"]
SH = {k: (shape(v), prep(shape(v).buffer(0.15))) for k, v in json.load(open("data/bri_shapes.json")).items()}
out = {c["iso3"]: {"quakes": [], "gdacs": [], "eonet": []} for c in C}; ERR = {}


def where(lat, lon):
    p = Point(lon, lat)
    for k, (g, pg) in SH.items():
        if pg.contains(p): return k
    return None


try:
    for f in get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson")["features"]:
        lo, la = f["geometry"]["coordinates"][:2]; k = where(la, lo); pr = f["properties"]
        if k: out[k]["quakes"].append({"t": iso(datetime.fromtimestamp(pr["time"] / 1000, timezone.utc)), "mag": pr.get("mag"), "text": pr.get("place"), "url": pr.get("url"), "lat": la, "lon": lo})
except Exception as e: ERR["usgs"] = str(e)[:120]
try:
    a = (NOW - timedelta(days=14)).strftime("%Y-%m-%d"); b = NOW.strftime("%Y-%m-%d")
    for f in get(f"https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?fromDate={a}&toDate={b}&alertlevel=Green;Orange;Red")["features"]:
        pr = f["properties"]; lo, la = f["geometry"]["coordinates"][:2]
        ks = {x.get("iso3") for x in (pr.get("affectedcountries") or []) if x.get("iso3")} or ({pr.get("iso3")} if pr.get("iso3") else set()) or {where(la, lo)}
        for k in ks:
            if k in out: out[k]["gdacs"].append({"t": (pr.get("fromdate") or "")[:19] + "Z", "type": pr.get("eventtype"), "level": pr.get("alertlevel"), "text": pr.get("name") or pr.get("eventname"), "url": (pr.get("url") or {}).get("report"), "lat": la, "lon": lo})
except Exception as e: ERR["gdacs"] = str(e)[:120]
try:
    for ev in get("https://eonet.gsfc.nasa.gov/api/v3/events?days=30")["events"]:
        g = (ev.get("geometry") or [])[-1:]
        if not g: continue
        c = g[0]["coordinates"]
        if g[0]["type"] != "Point": c = c[0][0] if isinstance(c[0][0], list) else c[0]
        k = where(c[1], c[0])
        if k: out[k]["eonet"].append({"t": g[0]["date"][:19] + "Z", "type": ",".join(x["title"] for x in ev.get("categories", [])), "text": ev["title"], "url": (ev.get("sources") or [{}])[0].get("url"), "lat": c[1], "lon": c[0]})
except Exception as e: ERR["eonet"] = str(e)[:120]
try:
    names = {c["iso3"]: {c["en"].lower(), c["en"].split(",")[0].lower()} for c in C}
    ALIAS = {"RUS": {"russia"}, "KOR": {"south korea", "korea, south"}, "LAO": {"laos"}, "IRN": {"iran"}, "SYR": {"syria"}, "VEN": {"venezuela"}, "BOL": {"bolivia"}, "TZA": {"tanzania"},
             "MDA": {"moldova"}, "COD": {"democratic republic of the congo"}, "COG": {"republic of the congo", "congo, republic of the", "republic of congo"}, "CIV": {"cote d'ivoire", "côte d'ivoire", "cote d ivoire", "côte d ivoire"}, "VNM": {"vietnam"}, "BRN": {"brunei"},
             "FSM": {"micronesia"}, "CPV": {"cabo verde"}, "GMB": {"the gambia", "gambia"}, "MKD": {"north macedonia"}, "TUR": {"turkey", "türkiye", "turkiye"}, "CZE": {"czechia", "czech republic"},
             "KGZ": {"kyrgyzstan", "kyrgyz republic", "the kyrgyz republic"}, "SVK": {"slovakia"}, "TLS": {"timor-leste"}, "BIH": {"bosnia and herzegovina"}, "MMR": {"burma", "burma (myanmar)"}, "PSE": set()}
    for k, v in ALIAS.items():
        if k in names: names[k] |= v
    for it in ET.fromstring(get("https://travel.state.gov/_res/rss/TAsTWs.xml", raw=True)).iter("item"):
        ti = (it.findtext("title") or "").strip(); nm = ti.split(" - ")[0].strip().lower(); m = re.search(r"Level (\d)", ti)
        for k, ns in names.items():
            if nm in ns:
                out[k]["us"] = {"level": int(m.group(1)) if m else None, "title": ti, "t": it.findtext("pubDate"), "url": it.findtext("link")}
except Exception as e: ERR["us_advisory"] = str(e)[:120]
for v in out.values():
    for k in ("quakes", "gdacs", "eonet"): v[k] = sorted(v[k], key=lambda x: x["t"], reverse=True)[:20]
json.dump({"generated": iso(NOW), "errors": ERR, "countries": out}, open("data/country_live.json", "w"), ensure_ascii=False, separators=(",", ":"))
print("country live:", sum(len(v["quakes"]) for v in out.values()), "quakes,", sum(len(v["gdacs"]) for v in out.values()), "gdacs,", sum(len(v["eonet"]) for v in out.values()), "eonet,", sum(1 for v in out.values() if v.get("us")), "advisories", ERR)

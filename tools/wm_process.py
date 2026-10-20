"""把每日从 World Monitor 取下来的原始数据（data/wm_raw/*.json）按 150 个共建国家整理成 data/wm.json，网页点国家时显示。
原始数据由定时任务经 World Monitor 连接器（免费账号，每天 5 次）取得：冲突事件、新闻与旅行建议、互联网中断、疾病疫情、机场。
用法：python3 tools/wm_process.py
"""
import json, os, re
from datetime import datetime, timezone

C = json.load(open("data/bri_countries.json"))["countries"]
I2 = {c["iso2"]: c["iso3"] for c in C}
NAMES = {}
for c in C:
    for n in {c["en"], c["en"].split(",")[0]}: NAMES[n.lower()] = c["iso3"]
ALIAS = {"russia": "RUS", "russian federation": "RUS", "south korea": "KOR", "korea, republic of": "KOR", "laos": "LAO", "iran": "IRN", "syria": "SYR", "venezuela": "VEN", "bolivia": "BOL",
         "tanzania": "TZA", "moldova": "MDA", "dr congo": "COD", "democratic republic of the congo": "COD", "congo": "COG", "republic of the congo": "COG", "ivory coast": "CIV",
         "cote d'ivoire": "CIV", "côte d'ivoire": "CIV", "vietnam": "VNM", "brunei": "BRN", "micronesia": "FSM", "cape verde": "CPV", "gambia": "GMB", "macedonia": "MKD",
         "turkey": "TUR", "türkiye": "TUR", "czechia": "CZE", "kyrgyzstan": "KGZ", "slovakia": "SVK", "east timor": "TLS", "bosnia-herzegovina": "BIH", "myanmar": "MMR", "burma": "MMR",
         "yemen": "YEM", "kampuchea": "KHM", "cambodia": "KHM", "serbia": "SRB", "eswatini": "SWZ", "uae": "ARE", "united arab emirates": "ARE", "egypt": "EGY", "china": "CHN"}
NAMES.update(ALIAS)


def to3(name=None, code=None):
    if code and code.upper() in I2: return I2[code.upper()]
    if not name: return None
    n = name.lower().strip(); n2 = re.sub(r"\s*\(.*?\)", "", n).strip()
    return NAMES.get(n) or NAMES.get(n2)


ms = lambda v: datetime.fromtimestamp(v / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if isinstance(v, (int, float)) and v > 0 else v
R = {}
def raw(n):
    p = f"data/wm_raw/{n}.json"
    return json.load(open(p)) if os.path.exists(p) else None
out = {k: {} for k in (c["iso3"] for c in C)}
def add(k, key, item):
    if k in out: out[k].setdefault(key, []).append(item)
meta = {}

c = raw("conflict")
if c and "data" in c:
    d = c["data"]; meta["conflict"] = {"cached_at": c.get("cached_at"), "truncation": d.get("truncation")}
    for e in (d.get("ucdp-events") or {}).get("events", []):
        add(to3(e.get("country")), "ucdp", {"t": ms(e.get("dateStart")), "a": e.get("sideA"), "b": e.get("sideB"), "deaths": e.get("deathsBest"), "src": e.get("sourceOriginal"), "lat": (e.get("location") or {}).get("latitude"), "lon": (e.get("location") or {}).get("longitude")})
    for e in (d.get("events") or {}).get("events", []):
        add(to3(e.get("country")), "unrest", {"t": ms(e.get("occurredAt")), "title": e.get("title"), "conf": e.get("confidence"), "urls": (e.get("sourceUrls") or [])[:3]})
    for s in (d.get("scores") or {}).get("ciiScores", []):
        k = to3(code=s.get("region"))
        if k in out: out[k]["cii"] = {"score": s.get("combinedScore"), "advisory": s.get("advisoryLevel"), "components": s.get("components")}

n = raw("news")
if n and "data" in n:
    d = n["data"]; meta["news"] = {"cached_at": n.get("cached_at")}
    adv = d.get("advisories-bootstrap") or {}
    for code, lvl in (adv.get("byCountry") or {}).items():
        k = to3(code=code)
        if k in out: out[k]["advisory"] = lvl
    for a in adv.get("advisories", []):
        add(to3(code=a.get("country")), "advisories", {"t": a.get("pubDate"), "title": a.get("title"), "url": a.get("link"), "source": a.get("source"), "level": a.get("level")})
    ins = d.get("insights") or {}; meta["brief"] = {"text": ins.get("worldBrief"), "t": ins.get("generatedAt")}
    pats = [(k, re.compile(r"\b" + re.escape(nm) + r"\b", re.I)) for nm, k in NAMES.items() if len(nm) > 3]
    for s in ins.get("topStories", []):
        txt = " ".join([s.get("primaryTitle") or ""] + (s.get("memberTitles") or []))
        for k in {k for k, p in pats if p.search(txt)}:
            add(k, "stories", {"t": ms(s.get("pubDate")), "title": s.get("primaryTitle"), "url": s.get("primaryLink"), "source": s.get("primarySource"), "sources": s.get("uniqueSourceCount"), "cred": s.get("credibilityScore")})

f = raw("infra")
if f and "data" in f:
    meta["infra"] = {"cached_at": f.get("cached_at")}
    for o in ((f["data"].get("outages") or {}).get("outages") or []):
        add(to3(o.get("country")), "outages", {"t": ms(o.get("detectedAt")), "end": ms(o.get("endedAt")) if o.get("endedAt") else None, "title": o.get("title"), "text": o.get("description"), "cause": o.get("cause"), "severity": (o.get("severity") or "").replace("OUTAGE_SEVERITY_", "").lower(), "url": o.get("link")})


def walk(o, fn):
    if isinstance(o, dict):
        if fn(o): return
        for v in o.values(): walk(v, fn)
    elif isinstance(o, list):
        for v in o: walk(v, fn)

h = raw("health")
if h:
    meta["health"] = {"cached_at": h.get("cached_at")}
    def ob(o):
        if "disease" in o or "diseaseName" in o:
            k = to3(o.get("country") or o.get("countryName"), o.get("countryCode") or o.get("iso2"))
            add(k, "outbreaks", {"t": ms(o.get("publishedAt") or o.get("date") or o.get("reportedAt")), "title": o.get("title") or o.get("disease") or o.get("diseaseName"), "url": o.get("url") or o.get("link"), "source": o.get("source")}); return True
    walk(h.get("data", h), ob)

a = raw("aviation")
if a:
    meta["aviation"] = {"cached_at": a.get("cached_at")}
    def ap(o):
        if "iata" in o and "severity" in o:
            if str(o.get("severity")).lower() not in ("normal", "severity_normal"):
                add(to3(o.get("country")), "airports", {"iata": o.get("iata"), "name": o.get("name"), "severity": o.get("severity"), "reason": o.get("reason") or o.get("description")})
            return True
    walk(a.get("data", a), ap)

for v in out.values():
    for k, L in v.items():
        if isinstance(L, list): v[k] = sorted(L, key=lambda x: str(x.get("t") or ""), reverse=True)[:25]
json.dump({"generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "source": "World Monitor MCP（免费账号）", "meta": meta,
           "countries": {k: v for k, v in out.items() if v}}, open("data/wm.json", "w"), ensure_ascii=False, separators=(",", ":"))
print("wm countries with data:", sum(1 for v in out.values() if v))

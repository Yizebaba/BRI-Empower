"""航空、铁路、公路的咽喉要道，覆盖全部 150 个共建国家，每天两次：
- 航空：每国主要国际机场（OurAirports 公开数据：大型机场；没有大型机场的取有定期航班的国际机场），另加几个航空枢纽。
- 铁路：中欧班列和跨境铁路的主要口岸。
- 公路：主要公路口岸 + 每一段陆地边境（Natural Earth 计算的接壤国家对，data/borders.json）。
每一处：
- 新闻：Google 新闻 RSS 近 7 天，按地名 + 关闭/中断/拥堵等词查，记条数和最近 3 条标题（标题原文）。
- 自然灾害：data/country_live.json 里 100 km 以内的地震、灾害警报、自然事件。
- 机场：World Monitor 机场状态（data/wm.json 的 airports，按 IATA 代码对上）。
不判断“是否中断”，只列有据可查的信号。输出 data/chokepoints_land.json。用法：python3 tools/chokepoints_land.py
"""
import csv, io, json, math, re, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from shapely.geometry import shape, Point
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

NOW = datetime.now(timezone.utc); iso = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")
UA = {"user-agent": "BRI-Empower (github.com/Yizebaba/BRI-Empower)"}
# 类别, 中文名, 英文名, 纬度, 经度, 相关国家, 新闻检索词
P = [
 ("rail", "阿拉山口—多斯特克", "Alashankou–Dostyk", 45.17, 82.57, ["CHN", "KAZ"], '"Alashankou" OR "Dostyk"'),
 ("rail", "霍尔果斯—阿腾科里", "Khorgos–Altynkol", 44.21, 80.38, ["CHN", "KAZ"], '"Khorgos" OR "Altynkol"'),
 ("rail", "二连浩特—扎门乌德", "Erenhot–Zamyn-Üüd", 43.65, 111.98, ["CHN", "MNG"], '"Erenhot" OR "Zamyn-Uud" OR "Erlian"'),
 ("rail", "满洲里—后贝加尔斯克", "Manzhouli–Zabaykalsk", 49.60, 117.43, ["CHN", "RUS"], '"Manzhouli" OR "Zabaykalsk"'),
 ("rail", "布列斯特—马拉舍维奇", "Brest–Małaszewicze", 52.08, 23.65, ["BLR", "POL"], '"Malaszewicze" OR "Brest-Terespol" OR "Belarus Poland border rail"'),
 ("rail", "跨里海通道（阿克套—巴库）", "Trans-Caspian (Aktau–Baku)", 42.4, 50.3, ["KAZ", "AZE"], '"Middle Corridor" OR "Trans-Caspian" OR "Aktau port"'),
 ("rail", "中老铁路磨憨—磨丁", "China–Laos Railway Mohan–Boten", 21.15, 101.69, ["CHN", "LAO"], '"Laos-China Railway" OR "China-Laos railway" OR "Boten"'),
 ("rail", "凭祥—同登", "Pingxiang–Dong Dang", 22.03, 106.75, ["CHN", "VNM"], '"Dong Dang" OR "Pingxiang" border'),
 ("rail", "萨雷阿加什（哈萨克斯坦—乌兹别克斯坦）", "Saryagash (Kazakhstan–Uzbekistan)", 41.45, 69.17, ["KAZ", "UZB"], '"Saryagash" OR "Keles" border rail'),
 ("rail", "萨拉赫斯（伊朗—土库曼斯坦）", "Sarakhs (Iran–Turkmenistan)", 36.54, 61.16, ["IRN", "TKM"], '"Sarakhs"'),
 ("rail", "卡皮科伊—拉齐（土耳其—伊朗）", "Kapıköy–Razi (Turkey–Iran)", 38.47, 44.36, ["TUR", "IRN"], '"Kapikoy" OR "Razi" border rail Iran Turkey'),
 ("rail", "巴库—第比利斯—卡尔斯铁路", "Baku–Tbilisi–Kars railway", 41.23, 43.25, ["AZE", "GEO", "TUR"], '"Baku-Tbilisi-Kars" OR "BTK railway"'),
 ("rail", "亚的斯亚贝巴—吉布提铁路", "Addis Ababa–Djibouti railway", 11.0, 42.3, ["ETH", "DJI"], '"Addis Ababa-Djibouti railway" OR "Ethio-Djibouti railway"'),
 ("rail", "坦赞铁路（通杜马—纳孔德）", "TAZARA (Tunduma–Nakonde)", -9.33, 32.77, ["TZA", "ZMB"], '"TAZARA" OR "Tunduma" OR "Nakonde"'),
 ("rail", "蒙巴萨—内罗毕标轨铁路", "Mombasa–Nairobi SGR", -2.5, 38.5, ["KEN"], '"Standard Gauge Railway" Kenya OR "Madaraka Express"'),
 ("rail", "廊开—塔纳楞（泰国—老挝）", "Nong Khai–Thanaleng (Thailand–Laos)", 17.88, 102.72, ["THA", "LAO"], '"Nong Khai" OR "Thanaleng" rail'),
 ("rail", "巴东勿刹（马来西亚—泰国）", "Padang Besar (Malaysia–Thailand)", 6.66, 100.32, ["MYS", "THA"], '"Padang Besar"'),
 ("rail", "雅万高铁", "Jakarta–Bandung high-speed railway", -6.6, 107.2, ["IDN"], '"Whoosh" OR "Jakarta-Bandung high-speed"'),
 ("rail", "匈塞铁路（贝尔格莱德—布达佩斯）", "Budapest–Belgrade railway", 46.1, 19.7, ["SRB", "HUN"], '"Budapest-Belgrade railway"'),
 ("rail", "比雷埃夫斯港铁路（中欧陆海快线）", "China–Europe Land-Sea Express (Piraeus)", 37.95, 23.62, ["GRC", "MKD", "SRB", "HUN"], '"Land-Sea Express" OR "Piraeus" rail freight'),
 ("road", "红其拉甫口岸", "Khunjerab Pass", 36.85, 75.43, ["CHN", "PAK"], '"Khunjerab"'),
 ("road", "托克哈姆口岸", "Torkham", 34.10, 71.10, ["PAK", "AFG"], '"Torkham"'),
 ("road", "查曼口岸", "Chaman", 30.92, 66.45, ["PAK", "AFG"], '"Chaman" border'),
 ("road", "伊尔克什坦口岸", "Irkeshtam", 39.68, 73.92, ["CHN", "KGZ"], '"Irkeshtam"'),
 ("road", "吐尔尕特口岸", "Torugart", 40.55, 75.39, ["CHN", "KGZ"], '"Torugart"'),
 ("road", "吉隆—热索瓦口岸", "Kerung–Rasuwagadhi", 28.28, 85.38, ["CHN", "NPL"], '"Rasuwagadhi" OR "Kerung" OR "Rasuwa"'),
 ("road", "友谊关", "Youyiguan (Friendship Pass)", 21.98, 106.71, ["CHN", "VNM"], '"Huu Nghi" OR "Friendship Pass" OR "Youyiguan"'),
 ("road", "上拉尔斯口岸", "Upper Lars", 42.74, 44.63, ["RUS", "GEO"], '"Upper Lars" OR "Verkhny Lars"'),
 ("road", "卡皮库莱口岸", "Kapıkule", 41.72, 26.36, ["TUR", "BGR"], '"Kapikule" OR "Kapitan Andreevo"'),
 ("road", "马拉巴口岸", "Malaba", 0.64, 34.27, ["KEN", "UGA"], '"Malaba" border'),
 ("road", "贝特布里奇口岸", "Beitbridge", -22.22, 30.00, ["ZAF", "ZWE"], '"Beitbridge"'),
 ("air", "迪拜国际机场", "Dubai (DXB)", 25.25, 55.36, ["ARE"], '"Dubai airport" OR "DXB"', "DXB"),
 ("air", "多哈哈马德机场", "Doha (DOH)", 25.27, 51.61, ["QAT"], '"Hamad International" OR "Doha airport"', "DOH"),
 ("air", "伊斯坦布尔机场", "Istanbul (IST)", 41.26, 28.74, ["TUR"], '"Istanbul Airport"', "IST"),
 ("air", "乌鲁木齐地窝堡机场", "Urumqi (URC)", 43.91, 87.47, ["CHN"], '"Urumqi airport" OR "Urumqi Diwopu"', "URC"),
 ("air", "阿拉木图机场", "Almaty (ALA)", 43.35, 77.04, ["KAZ"], '"Almaty airport"', "ALA"),
 ("air", "塔什干机场", "Tashkent (TAS)", 41.26, 69.28, ["UZB"], '"Tashkent airport"', "TAS"),
 ("air", "亚的斯亚贝巴机场", "Addis Ababa (ADD)", 8.98, 38.80, ["ETH"], '"Bole International" OR "Addis Ababa airport"', "ADD"),
 ("air", "新加坡樟宜机场", "Singapore (SIN)", 1.36, 103.99, ["SGP"], '"Changi Airport"', "SIN"),
 ("air", "吉隆坡机场", "Kuala Lumpur (KUL)", 2.75, 101.71, ["MYS"], '"KLIA" OR "Kuala Lumpur International Airport"', "KUL"),
 ("air", "曼谷素万那普机场", "Bangkok (BKK)", 13.69, 100.75, ["THA"], '"Suvarnabhumi"', "BKK"),
 ("air", "郑州新郑机场（货运）", "Zhengzhou (CGO, cargo)", 34.52, 113.84, ["CHN"], '"Zhengzhou airport" cargo', "CGO"),
]
INC = re.compile(r"clos|shut|block|suspend|halt|disrupt|strike|protest|stuck|stranded|queue|congest|delay|cancel|attack|flood|landslide|reopen|resum|backlog|ban|sanction|outage|storm|fog|evacuat", re.I)


def km(a, b, c, d):
    r = math.pi / 180; x = math.sin((c - a) * r / 2); y = math.sin((d - b) * r / 2)
    return 12742 * math.asin(math.sqrt(x * x + math.cos(a * r) * math.cos(c * r) * y * y))


def news(q):
    u = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q + " when:7d", "hl": "en", "gl": "US", "ceid": "US:en"})
    root = ET.fromstring(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read())
    out = []
    for it in root.iter("item"):
        t = it.findtext("title") or ""
        try: d = iso(parsedate_to_datetime(it.findtext("pubDate")).astimezone(timezone.utc))
        except Exception: d = None
        out.append({"t": d, "title": t, "url": it.findtext("link"), "inc": bool(INC.search(t))})
    return sorted(out, key=lambda x: x["t"] or "", reverse=True)


CL = json.load(open("data/country_live.json")).get("countries", {})
WM = json.load(open("data/wm.json")).get("countries", {})
CT = {c["iso3"]: c for c in json.load(open("data/bri_countries.json"))["countries"]}
I2 = {c["iso2"]: c["iso3"] for c in CT.values()}
try: OLD = {(x["kind"], x["en"]): x for x in json.load(open("data/chokepoints_land.json")).get("items", [])}
except Exception: OLD = {}
ERR = {}

# 每国主要机场（OurAirports，公有领域）
have = {p[7] for p in P if len(p) > 7}
try:
    rows = list(csv.DictReader(io.StringIO(urllib.request.urlopen(urllib.request.Request("https://davidmegginson.github.io/ourairports-data/airports.csv", headers=UA), timeout=120).read().decode("utf-8"))))
    by = {}
    for r in rows:
        k = I2.get(r["iso_country"])
        if k and r.get("iata_code") and r.get("scheduled_service") == "yes" and r["type"] in ("large_airport", "medium_airport"): by.setdefault(k, []).append(r)
    for k, L in by.items():
        big = [r for r in L if r["type"] == "large_airport"]
        pick = big[: (6 if k in ("CHN", "RUS") else 3)] or [r for r in L if "international" in r["name"].lower()][:2] or L[:1]
        for r in pick:
            if r["iata_code"] in have: continue
            have.add(r["iata_code"])
            P.append(("air", f"{CT[k]['zh']} · {r['name']}（{r['iata_code']}）", f"{r['name']} ({r['iata_code']})", float(r["latitude_deg"]), float(r["longitude_deg"]), [k], f'"{r["name"]}"', r["iata_code"]))
except Exception as ex: ERR["ourairports"] = str(ex)[:160]

# 每一段陆地边境
BL = {}
for b in json.load(open("data/borders.json"))["pairs"]:
    zh = f"{b['a_zh']}—{b['b_zh']}边境"; en = f"{b['a_en']}–{b['b_en']} border"
    P.append(("road", zh, en, b["lat"], b["lon"], [x for x in (b["a"], b["b"]) if x in CT], f'"{b["a_en"]}" "{b["b_en"]}" border (closed OR closure OR crossing OR checkpoint OR reopen)', None, True))
    BL[en] = shape(b["line"])


def one(p):
    kind, zh, en, la, lo, cs, q = p[:7]; iata = p[7] if len(p) > 7 else None; border = len(p) > 8
    e = {"kind": kind, "zh": zh, "en": en, "lat": la, "lon": lo, "countries": cs}
    if border: e["border"] = True
    try:
        n = news(q); inc = [x for x in n if x["inc"]]
        e["news7"] = len(n); e["incidents7"] = len(inc); e["latest"] = (inc or n)[:3]
    except Exception as ex:
        ERR[en] = str(ex)[:80]; o = OLD.get((kind, en)) or {}
        for k in ("news7", "incidents7", "latest"):
            if k in o: e[k] = o[k]
        e["stale"] = True
    hz = []
    for k in cs:
        for key in ("quakes", "gdacs", "eonet"):
            for x in (CL.get(k) or {}).get(key) or []:
                if x.get("lat") is None: continue
                dkm = BL[en].distance(Point(x["lon"], x["lat"])) * 111 if border else km(la, lo, x["lat"], x["lon"])
                if dkm <= (50 if border else 100): hz.append({"t": x["t"], "src": key, "text": x.get("text"), "km": round(dkm)})
    e["hazards"] = sorted(hz, key=lambda x: x["t"], reverse=True)[:3]
    if iata:
        for k in cs:
            for a in (WM.get(k) or {}).get("airports") or []:
                if a.get("iata") == iata: e["airport"] = {"severity": a.get("severity"), "reason": a.get("reason")}
    time.sleep(1.0)
    return e


with ThreadPoolExecutor(3) as ex: items = list(ex.map(one, P))
json.dump({"generated": iso(NOW), "window_days": 7, "items": items, "errors": dict(list(ERR.items())[:30]), "n_errors": len(ERR)}, open("data/chokepoints_land.json", "w"), ensure_ascii=False, separators=(",", ":"))
print("chokepoints:", len(items), {k: sum(1 for x in items if x["kind"] == k) for k in ("air", "rail", "road")}, "errors", len(ERR))

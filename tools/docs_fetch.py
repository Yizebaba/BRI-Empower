"""全文和摘要类文档（免费），每周一次，给 MiroFish 种子文档用：
1. 维基百科（英文，CC BY-SA）：国家条目导言；“中国—该国关系”条目全文；与“一带一路”和该国相关的条目导言（搜索）。
2. 世界银行文献库（Documents & Reports API，search.worldbank.org/api/v3/wds）：该国最新的报告、项目文件（标题、类型、日期、摘要）。
3. OpenAlex（学术论文，CC0）：关于“一带一路”和该国的论文（标题、年份、期刊、摘要）。不用密钥时每天有少量免费额度。
4. ReliefWeb（联合国人道协调厅）：该国最新报告正文节选。需要预先批准的 appname；没有批准时跳过。
输出 data/docs/<ISO3>.json。用法：python3 tools/docs_fetch.py [ISO3,…]
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

NOW = datetime.now(timezone.utc)
UA = {"user-agent": "BRI-Empower/1.0 (https://github.com/Yizebaba/BRI-Empower; seed documents)", "accept": "application/json"}
C = json.load(open("data/bri_countries.json"))["countries"]
ONLY = set(sys.argv[1].split(",")) if len(sys.argv) > 1 and sys.argv[1] else None
os.makedirs("data/docs", exist_ok=True)
STAT = {"wiki": 0, "wb": 0, "openalex": 0, "reliefweb": 0}; ERR = {}
WIKI_NAME = {"KOR": "South Korea", "LAO": "Laos", "IRN": "Iran", "SYR": "Syria", "VEN": "Venezuela", "BOL": "Bolivia", "TZA": "Tanzania", "MDA": "Moldova", "RUS": "Russia",
             "COD": "Democratic Republic of the Congo", "COG": "Republic of the Congo", "CIV": "Ivory Coast", "VNM": "Vietnam", "BRN": "Brunei", "FSM": "Federated States of Micronesia",
             "CPV": "Cape Verde", "GMB": "The Gambia", "MKD": "North Macedonia", "TUR": "Turkey", "CZE": "Czech Republic", "KGZ": "Kyrgyzstan", "SVK": "Slovakia", "TLS": "East Timor",
             "BIH": "Bosnia and Herzegovina", "MMR": "Myanmar", "PSE": "State of Palestine", "EGY": "Egypt", "YEM": "Yemen", "GIN": "Guinea", "STP": "São Tomé and Príncipe"}


def get(url, tries=3, headers=None):
    for i in range(tries):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=headers or UA), timeout=60).read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503): time.sleep(8 * (i + 1)); continue
            raise
        except Exception:
            if i == tries - 1: raise
            time.sleep(5)


def wiki_extract(titles, intro=True, chars=None):
    p = {"action": "query", "prop": "extracts", "explaintext": 1, "redirects": 1, "format": "json", "titles": "|".join(titles)}
    if intro: p["exintro"] = 1
    j = get("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(p))
    out = []
    for pg in (j.get("query", {}).get("pages") or {}).values():
        t = (pg.get("extract") or "").strip()
        if t: out.append({"title": pg["title"], "url": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(pg["title"].replace(" ", "_")), "text": t[:chars] if chars else t})
    return out


def wiki(c, name):
    d = {}
    d["country"] = wiki_extract([name], intro=True, chars=6000)
    # 中国—该国关系条目：常见写法 China–X relations / X–China relations
    rel = []
    for t in (f"China–{name} relations", f"{name}–China relations", f"China–{name} relations".replace("–", "-")):
        rel = wiki_extract([t], intro=False, chars=30000)
        if rel: break
    d["relations"] = [r for r in rel if "relations" in r["title"].lower()]
    s = get("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": f'"{name}" "Belt and Road" China', "srlimit": 8, "format": "json"}))
    skip = {name, "Belt and Road Initiative"} | {r["title"] for r in d["relations"]}
    titles = [x["title"] for x in s.get("query", {}).get("search", []) if x["title"] not in skip and not x["title"].startswith(("List of", "Foreign relations of"))][:8]
    d["bri"] = [x for x in (wiki_extract(titles, intro=True, chars=4000) if titles else []) if name.lower() in (x["title"] + " " + x["text"]).lower()][:5]
    STAT["wiki"] += 1
    return d


def worldbank(c):
    p = {"format": "json", "count_exact": c["en"].split(",")[0], "rows": 80, "os": 0, "srt": "docdt", "order": "desc",
         "fl": "docdt,docty,display_title,abstracts,url,repnb,majdocty,projn,count"}
    j = get("https://search.worldbank.org/api/v3/wds?" + urllib.parse.urlencode(p))
    out = []
    for v in (j.get("documents") or {}).values():
        if not isinstance(v, dict) or not v.get("display_title"): continue
        ab = v.get("abstracts")
        ab = (ab.get("cdata!") if isinstance(ab, dict) else ab) or ""
        out.append({"title": v.get("display_title"), "date": (v.get("docdt") or "")[:10], "type": v.get("docty") or v.get("majdocty"), "project": v.get("projn"),
                    "abstract": re.sub(r"\s+", " ", ab).strip()[:1500], "url": v.get("url")})
    STAT["wb"] += 1
    LOW = ("procurement plan", "disclosable", "environmental and social commitment", "stakeholder engagement", "implementation status", "letter", "memorandum", "minutes", "aide memoire", "auditing", "audit", "financial statement", "terms of reference")
    out = [x for x in out if not any(w in (str(x["type"]) + " " + str(x["title"])).lower() for w in LOW)]
    out.sort(key=lambda x: (bool(x["abstract"]), x["date"]), reverse=True)
    return out[:12]


def openalex(c, name):
    q = f'"Belt and Road" {name}'
    j = get("https://api.openalex.org/works?" + urllib.parse.urlencode({"search": q, "per-page": 8, "sort": "relevance_score:desc",
            "select": "id,display_name,publication_year,primary_location,abstract_inverted_index,doi,cited_by_count", "mailto": "bri-empower@users.noreply.github.com"}))
    out = []
    for w in j.get("results") or []:
        inv = w.get("abstract_inverted_index") or {}
        pos = sorted((i, word) for word, ii in inv.items() for i in ii)
        ab = " ".join(wd for _, wd in pos)
        src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name")
        out.append({"title": w.get("display_name"), "year": w.get("publication_year"), "venue": src, "cited": w.get("cited_by_count"), "abstract": ab[:2000], "url": w.get("doi") or w.get("id")})
    STAT["openalex"] += 1
    return out


RW_OK = True
def reliefweb(c):
    global RW_OK
    if not RW_OK: return []
    body = {"filter": {"field": "primary_country.iso3", "value": c["iso3"].lower()}, "fields": {"include": ["title", "body", "source.shortname", "date.original", "url_alias"]},
            "sort": ["date.original:desc"], "limit": 6}
    try:
        r = urllib.request.Request("https://api.reliefweb.int/v2/reports?appname=" + os.environ.get("RW_APPNAME", "BRIEmpower-seeddocs-k7q2xm"), data=json.dumps(body).encode(), headers=dict(UA, **{"content-type": "application/json"}))
        j = json.loads(urllib.request.urlopen(r, timeout=60).read())
    except Exception as e:
        RW_OK = False; ERR["reliefweb"] = (str(e) + " " + (e.read().decode("utf-8", "ignore")[:200] if hasattr(e, "read") else ""))[:300]; return []
    out = []
    for x in j.get("data") or []:
        f = x.get("fields") or {}
        out.append({"title": f.get("title"), "date": ((f.get("date") or {}).get("original") or "")[:10], "source": ", ".join(s.get("shortname", "") for s in f.get("source") or []),
                    "text": re.sub(r"\n{3,}", "\n\n", f.get("body") or "")[:3000], "url": f.get("url_alias")})
    STAT["reliefweb"] += 1
    return out


for c in C:
    k = c["iso3"]
    if ONLY and k not in ONLY: continue
    name = WIKI_NAME.get(k) or c["en"].split(",")[0]
    p = f"data/docs/{k}.json"
    old = json.load(open(p)) if os.path.exists(p) else {}
    d = {"iso3": k, "generated": NOW.strftime("%Y-%m-%dT%H:%M:%SZ")}
    for key, fn in (("wikipedia", lambda: wiki(c, name)), ("worldbank", lambda: worldbank(c)), ("openalex", lambda: openalex(c, name)), ("reliefweb", lambda: reliefweb(c))):
        try: d[key] = fn()
        except Exception as e:
            ERR.setdefault(key, str(e)[:160]); d[key] = old.get(key) or ([] if key != "wikipedia" else {})
        time.sleep(0.6)
    if k == "CHN": d["openalex"] = []
    json.dump(d, open(p, "w"), ensure_ascii=False, separators=(",", ":"))
    print(k, {x: (len(d[x]) if isinstance(d[x], list) else sum(len(v) for v in d[x].values())) for x in ("wikipedia", "worldbank", "openalex", "reliefweb")}, flush=True)
print("docs:", STAT, ERR)
if ERR.get("reliefweb"): print("::notice::reliefweb " + ERR["reliefweb"].replace("\n", " "))

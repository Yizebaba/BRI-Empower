"""150 国基本面（免费、不要密钥），每周一次：
1. 世界银行开放数据（api.worldbank.org）：经济规模、增长、三次产业占比、制造业、通胀、外债、偿债、外资、就业、城市化、电力和互联网普及等，各取最近一个有值的年份。
2. Wikidata（query.wikidata.org）：国家元首、政府首脑（现任）、首都、货币、官方语言、中央银行、执政党。
输出 data/country_facts.json。用法：python3 tools/country_facts.py
"""
import json, time, urllib.parse, urllib.request
from datetime import datetime, timezone

NOW = datetime.now(timezone.utc)
UA = {"user-agent": "BRI-Empower (github.com/Yizebaba/BRI-Empower)", "accept": "application/json"}
C = json.load(open("data/bri_countries.json"))["countries"]; ISO = {c["iso3"] for c in C}
WB = {"NY.GDP.MKTP.CD": "GDP（现价美元）", "NY.GDP.MKTP.KD.ZG": "GDP 实际增长率（%）", "NY.GDP.PCAP.CD": "人均 GDP（现价美元）", "SP.POP.TOTL": "人口",
      "NV.AGR.TOTL.ZS": "农林牧渔业增加值占 GDP（%）", "NV.IND.TOTL.ZS": "工业（含建筑业）增加值占 GDP（%）", "NV.IND.MANF.ZS": "制造业增加值占 GDP（%）", "NV.SRV.TOTL.ZS": "服务业增加值占 GDP（%）",
      "FP.CPI.TOTL.ZG": "通货膨胀率（CPI，%）", "SL.UEM.TOTL.ZS": "失业率（%，ILO 估算）", "BX.KLT.DINV.CD.WD": "外国直接投资净流入（美元）", "DT.DOD.DECT.CD": "外债总额（美元）",
      "DT.TDS.DECT.EX.ZS": "外债还本付息占出口收入（%）", "GC.DOD.TOTL.GD.ZS": "中央政府债务占 GDP（%）", "NE.EXP.GNFS.ZS": "货物和服务出口占 GDP（%）", "NE.IMP.GNFS.ZS": "货物和服务进口占 GDP（%）",
      "BN.CAB.XOKA.GD.ZS": "经常账户余额占 GDP（%）", "FI.RES.TOTL.CD": "外汇储备（含黄金，美元）", "TX.VAL.FUEL.ZS.UN": "燃料出口占商品出口（%）", "TX.VAL.MMTL.ZS.UN": "矿石和金属出口占商品出口（%）",
      "TX.VAL.FOOD.ZS.UN": "食品出口占商品出口（%）", "TX.VAL.MANF.ZS.UN": "制成品出口占商品出口（%）", "ST.INT.ARVL": "入境游客（人次）", "BX.TRF.PWKR.DT.GD.ZS": "侨汇收入占 GDP（%）",
      "SP.URB.TOTL.IN.ZS": "城镇人口比例（%）", "EG.ELC.ACCS.ZS": "通电人口比例（%）", "IT.NET.USER.ZS": "互联网用户比例（%）", "SL.AGR.EMPL.ZS": "农业就业占比（%）", "SL.IND.EMPL.ZS": "工业就业占比（%）", "SL.SRV.EMPL.ZS": "服务业就业占比（%）"}
out = {"generated": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"), "labels": WB, "countries": {k: {"wb": {}} for k in ISO}, "errors": {}}


def get(url, tries=4):
    for i in range(tries):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read())
        except Exception as e: err = e; time.sleep(10 * (i + 1))
    raise err


for code in WB:
    try:
        j = get(f"https://api.worldbank.org/v2/country/all/indicator/{code}?format=json&mrnev=1&per_page=500")
        for r in (j[1] if len(j) > 1 and j[1] else []):
            k = r.get("countryiso3code")
            if k in ISO and r.get("value") is not None: out["countries"][k]["wb"][code] = [r["value"], r.get("date")]
    except Exception as e: out["errors"][code] = str(e)[:120]
    time.sleep(0.5)

Q = """SELECT ?iso ?p ?vLabel ?vEn WHERE { VALUES ?iso { %s } ?c wdt:P298 ?iso .
 { ?c p:P35 ?s . ?s ps:P35 ?v . FILTER NOT EXISTS { ?s pq:P582 ?e } BIND("hos" AS ?p) } UNION
 { ?c p:P6 ?s . ?s ps:P6 ?v . FILTER NOT EXISTS { ?s pq:P582 ?e } BIND("hog" AS ?p) } UNION
 { ?c wdt:P36 ?v . BIND("capital" AS ?p) } UNION { ?c wdt:P38 ?v . BIND("currency" AS ?p) } UNION
 { ?c wdt:P37 ?v . BIND("language" AS ?p) } UNION { ?c wdt:P1304 ?v . BIND("central_bank" AS ?p) } UNION
 { ?c wdt:P1906 ?v . BIND("hos_office" AS ?p) } UNION { ?c wdt:P1313 ?v . BIND("hog_office" AS ?p) } UNION
 { ?c wdt:P2208 ?v . BIND("legislature" AS ?p) } UNION { ?c wdt:P194 ?v . BIND("legislature" AS ?p) }
 OPTIONAL { ?v rdfs:label ?vEn FILTER(lang(?vEn)="en") }
 SERVICE wikibase:label { bd:serviceParam wikibase:language "zh-cn,zh-hans,zh,en". } }"""
keys = sorted(ISO)
for i in range(0, len(keys), 30):
    try:
        q = Q % " ".join(f'"{k}"' for k in keys[i:i + 30])
        j = get("https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(q))
        for b in j["results"]["bindings"]:
            k = b["iso"]["value"]; p = b["p"]["value"]; zh = b.get("vLabel", {}).get("value"); en = b.get("vEn", {}).get("value")
            if not zh or zh.startswith("Q") and zh[1:].isdigit(): zh = en
            L = out["countries"][k].setdefault(p, [])
            if zh and [zh, en] not in L: L.append([zh, en])
    except Exception as e: out["errors"]["wikidata_%d" % i] = str(e)[:160]
    time.sleep(2)
json.dump(out, open("data/country_facts.json", "w"), ensure_ascii=False, separators=(",", ":"))
print("facts:", sum(1 for v in out["countries"].values() if v["wb"]), "wb;", sum(1 for v in out["countries"].values() if v.get("hos")), "wikidata;", out["errors"])

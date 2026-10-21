"""各国货物贸易（UN Comtrade 公共预览接口，免费、不要密钥，每次最多 500 条），每周一次。
每个国家：
1. 本国申报：对全世界的进出口，按 HS 两位章（97 个行业大类）；主要贸易伙伴（总额）。
2. 本国没有申报的年份：用其他国家对它的申报（镜像数据）得出主要伙伴。
3. 中国申报的对该国进出口，按 HS 两位章。
输出 data/trade/<ISO3>.json 和 data/trade_index.json。用法：python3 tools/trade.py [ISO3,…]
"""
import json, os, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

NOW = datetime.now(timezone.utc)
U = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
C = json.load(open("data/bri_countries.json"))["countries"]
ONLY = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
NUM = {int(c["num"]): c["iso3"] for c in C}
os.makedirs("data/trade", exist_ok=True)
NAMES = {}
YEARS = [NOW.year - 1, NOW.year - 2, NOW.year - 3]


def get(**p):
    p = dict({"partner2Code": 0, "customsCode": "C00", "motCode": 0, "includeDesc": "true"}, **p)
    for i in range(5):
        try:
            r = urllib.request.urlopen(urllib.request.Request(U + "?" + urllib.parse.urlencode(p), headers={"user-agent": "BRI-Empower"}), timeout=90)
            time.sleep(1.2); return json.loads(r.read()).get("data") or []
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(20 * (i + 1)); continue
            if e.code >= 500: time.sleep(10); continue
            return []
        except Exception: time.sleep(10)
    return []


def chapters(rows):
    d = {}
    for r in rows:
        k = str(r.get("cmdCode")); NAMES[k] = r.get("cmdDesc") or NAMES.get(k)
        d.setdefault(k, {})["x" if r.get("flowCode") == "X" else "m"] = r.get("primaryValue")
    return sorted([{"hs": k, "x": v.get("x"), "m": v.get("m")} for k, v in d.items()], key=lambda z: -((z["x"] or 0) + (z["m"] or 0)))


def partners(rows, mirror=False):
    d = {}
    for r in rows:
        code = int(r.get("reporterCode" if mirror else "partnerCode") or 0)
        if code == 0: continue
        nm = r.get("reporterDesc" if mirror else "partnerDesc") or str(code)
        f = r.get("flowCode")
        if mirror: f = {"X": "M", "M": "X"}.get(f, f)   # 对方的出口 = 本国的进口
        e = d.setdefault(code, {"code": code, "iso3": NUM.get(code), "name": nm})
        e["x" if f == "X" else "m"] = r.get("primaryValue")
    return sorted(d.values(), key=lambda z: -((z.get("x") or 0) + (z.get("m") or 0)))[:25]


idx = {}
for c in C:
    k = c["iso3"]; n = int(c["num"])
    if ONLY and k not in ONLY: continue
    out = {"iso3": k, "generated": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"), "source": "UN Comtrade（comtradeplus.un.org），年度，美元，HS 两位章"}
    if k != "CHN":
        for y in YEARS:   # 本国申报：主要伙伴
            rows = get(reporterCode=n, period=y, cmdCode="TOTAL", flowCode="X,M")
            if rows:
                out["year"] = y; out["partners"] = partners(rows); out["partners_basis"] = "本国申报"
                w = [r for r in rows if int(r.get("partnerCode") or -1) == 0]
                out["total"] = {("x" if r["flowCode"] == "X" else "m"): r.get("primaryValue") for r in w}
                out["industries"] = chapters(get(reporterCode=n, period=y, cmdCode="AG2", flowCode="X,M", partnerCode=0))
                break
        if "partners" not in out:   # 没有申报：用各国对它的申报（镜像）
            for y in YEARS:
                rows = get(partnerCode=n, period=y, cmdCode="TOTAL", flowCode="X,M")
                if len(rows) > 10:
                    out["year"] = y; out["partners"] = partners(rows, mirror=True); out["partners_basis"] = "镜像：各国对它的申报"
                    out["total"] = {"x": sum(p.get("x") or 0 for p in out["partners"]), "m": sum(p.get("m") or 0 for p in out["partners"])}
                    break
        for y in YEARS:   # 中国对该国（中国申报）
            rows = get(reporterCode=156, partnerCode=n, period=y, cmdCode="AG2", flowCode="X,M")
            if rows: out["china"] = {"year": y, "industries": chapters(rows)}; break
    else:
        for y in YEARS:
            rows = get(reporterCode=156, period=y, cmdCode="AG2", flowCode="X,M", partnerCode=0)
            if rows:
                out["year"] = y; out["industries"] = chapters(rows)
                out["partners"] = partners(get(reporterCode=156, period=y, cmdCode="TOTAL", flowCode="X,M")); out["partners_basis"] = "本国申报"; break
    json.dump(out, open(f"data/trade/{k}.json", "w"), ensure_ascii=False, separators=(",", ":"))
    idx[k] = {"year": out.get("year"), "basis": out.get("partners_basis"), "n_ind": len(out.get("industries") or []), "n_partners": len(out.get("partners") or []), "china_year": (out.get("china") or {}).get("year")}
    print(k, idx[k], flush=True)
old = {}
try: old = json.load(open("data/trade_index.json"))
except Exception: pass
allidx = dict(old.get("countries") or {}); allidx.update(idx)
names = dict(old.get("hs_names") or {}); names.update({k: v for k, v in NAMES.items() if v})
json.dump({"generated": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"), "source": "UN Comtrade 公共预览接口", "countries": allidx, "hs_names": names}, open("data/trade_index.json", "w"), ensure_ascii=False, indent=0)
print("trade:", len(idx), "countries")

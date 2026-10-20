"""按国家整理 AidData 全球中国发展融资地理数据集 v3.0 的项目（只取 data/bri_countries.json 里的 150 国）。
输出 data/countries/<ISO3>.json（项目清单）和 data/aiddata_summary.json（每国项目数、承诺金额、主要行业）。
数据：https://github.com/aiddata/gcdf-geospatial-data （ODC-By；OSM 部分 ODbL）。用法：python3 tools/aiddata_countries.py <gcdf 仓库目录>
"""
import csv, json, os, sys
from collections import defaultdict, Counter
SRC = sys.argv[1]
C = {c["iso3"]: c for c in json.load(open("data/bri_countries.json"))["countries"]}
ST = {"Completion": "已完工", "Implementation": "在建", "Pipeline: Commitment": "已承诺", "Pipeline: Pledge": "意向", "Suspended": "暂停", "Cancelled": "取消"}
P = defaultdict(dict)
for r in csv.DictReader(open(f"{SRC}/input_data/gcdf_v3/final_input.csv", encoding="utf-8")):
    iso = r["Recipient.ISO-3"]
    if iso not in C: continue
    pid = r["AidData.Record.ID"]
    if pid in P[iso]: continue
    try: amt = round(float(r["Amount.(Constant.USD.2021)"]))
    except Exception: amt = None
    P[iso][pid] = {"id": int(pid), "title": r["Title"], "status": ST.get(r["Status"], r["Status"]), "sector": r["Sector.Name"].title(), "year": r["Commitment.Year"],
                   "amount": amt, "infra": r["Infrastructure"] == "Yes", "osm": r["OSM.link"], "precise": r["Level.of.precision"] == "PRECISE"}
os.makedirs("data/countries", exist_ok=True)
summ = {}
for iso, d in P.items():
    L = sorted(d.values(), key=lambda x: -(x["amount"] or 0))
    json.dump({"iso3": iso, "source": "AidData GCDF v3.0 geospatial (2000–2021 commitments)", "projects": L}, open(f"data/countries/{iso}.json", "w"), ensure_ascii=False, separators=(",", ":"))
    summ[iso] = {"n": len(L), "usd": sum(x["amount"] or 0 for x in L), "sectors": Counter(x["sector"] for x in L).most_common(3)}
json.dump({"source": "AidData GCDF v3.0 geospatial", "countries": summ}, open("data/aiddata_summary.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(len(summ), "countries,", sum(v["n"] for v in summ.values()), "projects")

"""生成 MiroFish 需要的种子文档（“现实种子”）：把本项目的真实数据整理成 Markdown，按国家分组。
MiroFish 从这些文档里抽取实体和关系建知识图谱，再生成智能体做模拟。推演要求（让 AI 推演什么）不在这里写，由使用者在网页表单里自己填。

输入：data/projects.json、data/live.json、data/wm.json、data/reference.json、data/sources.json
输出：seeds/<NPL|LAO|PAK>/*.md 和 seeds/index.json
用法：python3 tools/seed_docs.py
只有内容变化时才改写文件（生成时间不算变化），避免无意义的提交。
"""
import json, math, os, re
from datetime import datetime, timezone

D = lambda p: json.load(open(p)) if os.path.exists(p) else {}
P = D("data/projects.json").get("projects", [])
L = D("data/live.json")
W = D("data/wm.json")
R = D("data/reference.json").get("tests", [])
SRC = {s["id"]: s for s in D("data/sources.json").get("sources", [])}
CN = {"NPL": "尼泊尔", "LAO": "老挝", "PAK": "巴基斯坦"}
EN = {"NPL": "Nepal", "LAO": "Laos", "PAK": "Pakistan"}
ST = {"Completion": "已完工", "Implementation": "在建", "Pipeline: Commitment": "已承诺", "Pipeline: Pledge": "意向"}
NEWS = "新闻（Google 新闻 RSS）"


def km(a, b, c, d):
    r = math.pi / 180; x = math.sin((c - a) * r / 2); y = math.sin((d - b) * r / 2)
    return 12742 * math.asin(math.sqrt(x * x + math.cos(a * r) * math.cos(c * r) * y * y))


def nearest(lat, lon, ps):
    best = (1e9, None)
    for p in ps:
        for ring in p["rings"]:
            for x, y in ring:
                d = km(lat, lon, y, x)
                if d < best[0]: best = (d, p)
    return best


def bj(t):
    if not t: return "未知"
    try: return datetime.fromisoformat(t.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M UTC")
    except Exception: return str(t)


def cite(i): s = SRC.get(i, {}); return f"{s.get('name', i)}，{s.get('url', '')}"


def projects_doc(c, ps):
    o = [f"# {CN[c]}（{EN[c]}）的中国融资项目档案", "",
         f"资料来源：{cite('aiddata')}。下列 {len(ps)} 个项目的名称、融资方、金额、状态和承诺年份均摘自该数据集原文；位置是数据集按 OpenStreetMap 要素画出的范围。", ""]
    for p in ps:
        b = p["bbox"]
        o += [f"## {p['name']}（{p['name_en']}）", "",
              f"- 类别：{p['kind']}", f"- 所在国：{CN[c]}",
              f"- 状态：{ST.get(p['status'], p['status'])}（AidData 原文：{p['status']}）",
              f"- 承诺年份：{p['commit_year']}",
              f"- AidData 记录号：{p['aiddata_id']}；记录原文：{p['title']}",
              f"- 位置：中心点约北纬 {p['centroid'][0]}°、东经 {p['centroid'][1]}°；范围北纬 {b[0]}–{b[2]}°、东经 {b[1]}–{b[3]}°（定位精度：{p['precision']}）",
              f"- OpenStreetMap：{p['osm']}"]
        if p.get("note"): o.append(f"- 备注：{p['note']}")
        o.append("")
    return "\n".join(o)


def situation_doc(c, ps):
    C = (L.get("countries") or {}).get(c) or {}
    ad = C.get("advisory") or {}; io = C.get("ioda")
    o = [f"# {CN[c]}项目周边近期态势（截至 {bj(L.get('generated'))}）", "",
         "本文件由程序从公开来源自动汇编，每条注明来源和时间，内容是来源原文的转述。", "", "## 国家层面", ""]
    if ad.get("us"): o.append(f"- 美国国务院旅行建议：{ad['us'].get('title')}（发布 {ad['us'].get('t')}）。来源：{ad['us'].get('url')} ")
    if ad.get("uk"): o.append(f"- 英国外交部旅行建议最近更新于 {bj(ad['uk'].get('t'))}，更新说明：{(ad['uk'].get('change') or '').strip()}。来源：{ad['uk'].get('url')} ")
    if io: o.append(f"- IODA 近 7 天记录到全国性网络中断告警 {io.get('n')} 条。来源：{cite('ioda')}")
    o.append("")
    for p in ps:
        it = ((L.get("projects") or {}).get(p["id"]) or {}).get("items") or []
        geo = [i for i in it if i["src"] != NEWS]; inc = [i for i in it if i["src"] == NEWS and i.get("kind") == "事件相关"]
        gen = [i for i in it if i["src"] == NEWS and i.get("kind") != "事件相关"]
        o += [f"## {p['name']}", ""]
        if geo:
            o.append("周边自然事件（地震 150 km、灾害警报 300 km、NASA 自然事件 150 km 以内）：")
            o += [f"- {bj(i['t'])}，{i['src']}：{i['text']}，距项目 {i.get('km')} km。{i.get('url') or ''}" for i in geo[:10]]
        else: o.append("周边自然事件：扫描期间没有记录。")
        if inc:
            o.append(""); o.append("近 7 天新闻中与事故、灾害、安全相关的报道（标题原文）：")
            o += [f"- {bj(i['t'])}：{i['text']}。{i.get('url') or ''}" for i in inc[:12]]
        if gen:
            o.append(""); o.append("近 7 天其他相关报道（标题原文，按项目名匹配，可能含无关报道）：")
            o += [f"- {bj(i['t'])}：{i['text']}" for i in gen[:8]]
        o.append("")
    wc = (W.get("countries") or {}).get(c)
    if wc and not wc.get("error"):
        o += ["## 已核实的冲突事件（UCDP，经 World Monitor）", "",
              f"UCDP 候选数据版本 {wc.get('ucdp_version')}，World Monitor 缓存于 {bj(wc.get('cached_at'))}。UCDP 只收录有人员死亡的有组织暴力事件，通常比实际发生晚几周。", ""]
        ev = sorted(wc.get("ucdp") or [], key=lambda e: e.get("t") or "", reverse=True)
        for e in ev[:30]:
            d, np_ = nearest(e["lat"], e["lon"], ps)
            o.append(f"- {(e.get('t') or '')[:10]}：{e.get('a')} 与 {e.get('b')} 发生冲突，死亡 {e.get('deaths')} 人，地点北纬 {e['lat']:.3f}°、东经 {e['lon']:.3f}°，距最近项目（{np_['name'] if np_ else ''}）{d:.0f} km。UCDP 引用来源：{e.get('src')}")
        if not ev: o.append("- 近期没有记录。")
        if wc.get("unrest"):
            o += ["", "GDELT 动荡信号（World Monitor 标注为未核实的媒体信号，可信度低）：" + "；".join(u.get("title", "") for u in wc["unrest"])]
        o.append("")
    return "\n".join(o)


def history_doc(c):
    ts = [t for t in R if t.get("country") == c]
    if not ts: return None
    o = [f"# {CN[c]}项目周边的历史事件（参考事实）", "", "以下每条事实摘自公开的权威或主流来源，逐条注明出处；来源之间不一致的地方原样保留。", ""]
    for t in ts:
        o += [f"## {t['title']}", "", f"- 发生时间：{t.get('onset') or '不详'}（{t.get('onset_note', '')}）",
              f"- 地点：北纬 {t['location'][0]}°、东经 {t['location'][1]}°（{t.get('location_note', '')}）",
              f"- 成因：{t.get('cause')}", f"- 伤亡：{t.get('casualties')}"]
        o += [f"- 影响：{x}" for x in t.get("impacts") or []]
        for x in t.get("timeline") or []: o.append(f"- 时间线：{x[0]} {x[1]}")
        o += [f"- 来源：{s[0]} {s[1]}" for s in t.get("sources") or []]
        o.append("")
    return "\n".join(o)


def sources_doc():
    o = ["# 数据来源说明", "", "本组种子文档里的事实全部来自下列公开数据源：", ""]
    for s in SRC.values():
        if s["id"] == "mirofish": continue
        o.append(f"- {s['name']}：{s['url']}。许可：{s['license']}。更新：{s['cadence']}。用途：{s['use']}。")
    return "\n".join(o) + "\n"


def write(path, text):
    old = open(path).read() if os.path.exists(path) else None
    norm = lambda s: re.sub(r"截至 [^）]*）", "", s or "")
    if old is not None and norm(old) == norm(text): return False
    open(path, "w").write(text); return True


CT = {c["iso3"]: c for c in D("data/bri_countries.json").get("countries", [])}
AS = D("data/aiddata_summary.json").get("countries", {})
CL = D("data/country_live.json"); WC = (W.get("countries") or {})
LVZ = {1: "一级（正常注意）", 2: "二级（加强注意）", 3: "三级（重新考虑出行）", 4: "四级（不要前往）"}


def country_profile(k):
    c = CT[k]; a = AS.get(k); o = [f"# {c['zh']}（{c['en']}）：中国融资项目概况", ""]
    o.append(f"- 所属区域：{c['region']}；共建“一带一路”国家（来源：{CT and 'Green Finance & Development Center，截至 2025 年 5 月'}）" + (f"；备注：{c['note']}" if c.get("note") else ""))
    if not a: o += ["", "AidData 全球中国发展融资地理数据集 v3.0 没有收录这个国家带位置的项目。"]; return "\n".join(o) + "\n"
    o.append(f"- AidData 收录 2000–2021 年承诺的项目 {a['n']} 个，承诺金额合计约 {a['usd']/1e8:.1f} 亿美元（2021 年不变价）；主要行业：" + "、".join(f"{x[0]}（{x[1]}）" for x in a["sectors"]))
    try: pj = json.load(open(f"data/countries/{k}.json"))["projects"]
    except Exception: pj = []
    o += ["", "## 金额最大的项目（AidData 原文）", ""]
    for x in pj[:25]:
        o.append(f"- {x['title']}（{x['sector']}，{x['status']}，{x['year']} 年承诺" + (f"，约 {x['amount']/1e6:.0f} 百万美元" if x.get("amount") else "") + f"）。{x['osm']}")
    o += ["", f"来源：{cite('aiddata')}"]
    return "\n".join(o) + "\n"


def country_situation(k):
    c = CT[k]; w = WC.get(k) or {}; l = (CL.get("countries") or {}).get(k) or {}
    o = [f"# {c['zh']}（{c['en']}）近期态势", "", "每条注明来源和时间，内容是来源原文的转述。", ""]
    if l.get("us"): o.append(f"- 美国国务院旅行建议：{l['us']['title']}（{l['us'].get('t')}）。{l['us'].get('url')} ")
    if w.get("advisory"): o.append(f"- World Monitor 汇总的旅行建议级别：{w['advisory']}")
    if w.get("cii"): o.append(f"- World Monitor 综合不稳定指数（CII）：{w['cii'].get('score')}/100")
    for key, title, fmt in (
        ("ucdp", "已核实的冲突事件（UCDP，经 World Monitor）", lambda e: f"{(e.get('t') or '')[:10]}：{e.get('a')} 与 {e.get('b')}，死亡 {e.get('deaths')} 人。UCDP 引用来源：{e.get('src')}"),
        ("outages", "互联网中断（Cloudflare Radar，经 World Monitor）", lambda e: f"{bj(e.get('t'))}：{e.get('title')}。{e.get('text') or ''} {e.get('url') or ''} "),
        ("stories", "国际新闻要闻（经 World Monitor）", lambda e: f"{bj(e.get('t'))}：{e.get('title')}（{e.get('source')}）。{e.get('url') or ''} "),
        ("advisories", "各国政府旅行建议更新（经 World Monitor）", lambda e: f"{bj(e.get('t'))}：{e.get('source')} {e.get('title')}。{e.get('url') or ''} "),
        ("outbreaks", "疫情（经 World Monitor）", lambda e: f"{bj(e.get('t'))}：{e.get('title')}。{e.get('url') or ''} ")):
        if w.get(key): o += ["", f"## {title}", ""] + [f"- {fmt(e)}" for e in w[key][:15]]
    for key, title, fmt in (
        ("quakes", "地震（USGS，M4.5+，近 7 天）", lambda e: f"{bj(e['t'])}：M{e.get('mag')}，{e.get('text')}。{e.get('url') or ''} "),
        ("gdacs", "灾害警报（GDACS，近 14 天）", lambda e: f"{bj(e['t'])}：{e.get('level')} 级 {e.get('type')}，{e.get('text')}。{e.get('url') or ''} "),
        ("eonet", "自然事件（NASA EONET，近 30 天）", lambda e: f"{bj(e['t'])}：{e.get('type')}，{e.get('text')}。{e.get('url') or ''} ")):
        if l.get(key): o += ["", f"## {title}", ""] + [f"- {fmt(e)}" for e in l[key][:15]]
    if len(o) <= 4: o.append("近期各来源都没有记录。")
    return "\n".join(o) + "\n"


idx = {"note": "MiroFish 种子文档，由 tools/seed_docs.py 从 data/ 自动生成；推演时按所选国家自动上传。", "sources": "seeds/00_sources.md", "scopes": {}}
changed = 0
os.makedirs("seeds", exist_ok=True); changed += write("seeds/00_sources.md", sources_doc())
for k, c in CT.items():
    os.makedirs(f"seeds/{k}", exist_ok=True)
    ps = [p for p in P if p["country"] == k]
    docs = [("01_profile.md", country_profile(k)), ("02_situation.md", country_situation(k) + ("\n" + situation_doc(k, ps) if ps else "")),
            ("03_projects_detail.md", projects_doc(k, ps) if ps else None), ("04_history.md", history_doc(k) if ps else None)]
    files = []
    for name, text in docs:
        p = f"seeds/{k}/{name}"
        if text is None:
            if os.path.exists(p): os.remove(p); changed += 1
            continue
        changed += write(p, text)
        files.append({"path": p, "title": text.splitlines()[0].lstrip("# "), "bytes": len(text.encode())})
    idx["scopes"][k] = {"name": c["zh"], "region": c["region"], "files": files}
for old in ("seeds/NPL/01_projects.md", "seeds/LAO/01_projects.md", "seeds/PAK/01_projects.md", "seeds/NPL/03_history.md", "seeds/LAO/03_history.md", "seeds/PAK/03_history.md", "seeds/NPL/00_sources.md", "seeds/LAO/00_sources.md", "seeds/PAK/00_sources.md"):
    if os.path.exists(old): os.remove(old)
idx["generated"] = L.get("generated")
json.dump(idx, open("seeds/index.json", "w"), ensure_ascii=False, separators=(",", ":"))
print("seed docs changed:", changed, "countries:", len(idx["scopes"]))

"""生成 MiroFish 需要的种子文档（“现实种子”）：把本项目的真实数据整理成 Markdown，按国家分组。
MiroFish 从这些文档里抽取实体和关系建知识图谱，再生成智能体做模拟。推演要求（让 AI 推演什么）不在这里写，由使用者在网页表单里自己填。

输入：data/projects.json、data/live.json、data/wm.json、data/reference.json、data/sources.json
输出：seeds/<NPL|LAO|PAK>/*.md 和 seeds/index.json
用法：python3 tools/seed_docs.py
只有内容变化时才改写文件（生成时间不算变化），避免无意义的提交。
"""
import collections, glob, json, math, os, re
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
FX = D("data/country_facts.json"); FC = FX.get("countries") or {}; WBL = FX.get("labels") or {}
TI = D("data/trade_index.json"); HSN = TI.get("hs_names") or {}; HSZ = D("data/hs2_zh.json")
LG = D("data/logistics.json")
LVZ = {1: "一级（正常注意）", 2: "二级（加强注意）", 3: "三级（重新考虑出行）", 4: "四级（不要前往）"}
ZHC = {c["iso3"]: c["zh"] for c in CT.values()}
PZH = {"USA": "美国", "Japan": "日本", "Germany": "德国", "India": "印度", "France": "法国", "United Kingdom": "英国", "Canada": "加拿大", "Australia": "澳大利亚", "Netherlands": "荷兰", "Belgium": "比利时",
       "Spain": "西班牙", "Switzerland": "瑞士", "Brazil": "巴西", "Mexico": "墨西哥", "China, Hong Kong SAR": "中国香港", "China, Macao SAR": "中国澳门", "Other Asia, nes": "中国台湾地区（Comtrade 记作 Other Asia, nes）",
       "Ireland": "爱尔兰", "Denmark": "丹麦", "Sweden": "瑞典", "Finland": "芬兰", "Norway": "挪威", "Colombia": "哥伦比亚", "Taiwan": "中国台湾地区", "Areas, nes": "未列明地区", "Bunkers": "船用燃料", "Free Zones": "自由区"}


def usd(v):
    if v is None: return "无数据"
    a = abs(v)
    return f"{v/1e8:.2f} 亿美元" if a >= 1e8 else f"{v/1e4:.0f} 万美元" if a >= 1e4 else f"{v:.0f} 美元"


def hsname(h): return f"{HSZ.get(h, '')}（HS {h}，{(HSN.get(h) or '')[:70].rstrip(' ;,')}）"


# AidData 标题里的出资方（“X provides …”），归一成中文名
VERB = r"(?:provides?|grants?|donates?|issues?|signs?|lends?|offers?|finances?|pledges?|commits?|contributes?|disburses?|extends?|funds?|awards?|approves?|builds?|constructs?|delivers?|supports?|sends?|dispatches?|hands? over|establishes?|agrees?|underwrites?|participates?|co-finances?)\b"
NORM = [(r"^(the )?chinese government$|^government of china$|^china$|^people's republic of china$", "中国政府"), (r"chinese embassy|embassy of china|chinese ambassador|chinese consulate", "中国驻当地使领馆"),
        (r"^cdb$|china development bank", "国家开发银行（China Development Bank）"), (r"eximbank|export-import bank of china", "中国进出口银行（China Eximbank）"),
        (r"^icbc|industrial and commercial bank", "中国工商银行（ICBC）"), (r"^bank of china", "中国银行（Bank of China）"), (r"china construction bank", "中国建设银行（China Construction Bank）"),
        (r"agricultural bank of china", "中国农业银行"), (r"^hanban", "汉办 / 孔子学院总部（Hanban）"), (r"^mofcom|ministry of commerce", "中国商务部（MOFCOM）"), (r"^cidca", "国家国际发展合作署（CIDCA）"),
        (r"^sinosure", "中国出口信用保险公司（Sinosure）"), (r"silk road fund", "丝路基金（Silk Road Fund）"), (r"medical team", "中国援外医疗队"), (r"^cnpc|china national petroleum", "中国石油天然气集团（CNPC）"),
        (r"^sinohydro|^powerchina", "中国电建 / 水电建设集团（PowerChina / Sinohydro）"), (r"^chec|china harbour", "中国港湾工程（CHEC）"), (r"^cmec|china machinery engineering", "中国机械设备工程（CMEC）"),
        (r"^zte", "中兴通讯（ZTE）"), (r"^huawei", "华为（Huawei）"), (r"^cscec|china state construction", "中国建筑（CSCEC）"), (r"^crbc|china road and bridge", "中国路桥（CRBC）"), (r"^cccc|china communications construction", "中国交建（CCCC）"),
        (r"^crec|china railway group|china railway engineering", "中国中铁（CREC）"), (r"^crcc|china railway construction", "中国铁建（CRCC）"), (r"three gorges", "中国三峡集团（China Three Gorges）"), (r"gezhouba", "葛洲坝集团（Gezhouba）"),
        (r"state grid", "国家电网（State Grid）"), (r"^sinopec", "中国石化（Sinopec）"), (r"^cnooc", "中国海油（CNOOC）"), (r"^citic", "中信集团（CITIC）"), (r"^cosco", "中远海运（COSCO）"), (r"^china merchants", "招商局集团（China Merchants）")]
SOE = [x for x in NORM if x[1].startswith(("中国石油", "中国电建", "中国港湾", "中国机械", "中兴", "华为", "中国建筑", "中国路桥", "中国交建", "中国中铁", "中国铁建", "中国三峡", "葛洲坝", "国家电网", "中国石化", "中国海油", "中信", "中远", "招商局"))]


def actor(raw):
    r = raw.strip().lower()
    for pat, zh in NORM:
        if re.search(pat, r): return zh
    return raw.strip()


def funders(pj):
    f = {}
    for x in pj:
        t = re.sub(r"^\[[^\]]*\]\s*", "", x.get("title") or "")
        m = re.match(r"(.{3,90}?)\s+(?:and\s+.{3,60}?\s+)?" + VERB, t)
        names = {actor(m.group(1))} if m else set()
        for pat, zh in SOE:   # 标题里提到的中资企业（承建、合作方）
            if re.search(r"\b" + pat.lstrip("^").split("|")[0], t, re.I): names.add(zh)
        for n in names:
            e = f.setdefault(n, {"n": 0, "usd": 0, "ex": []}); e["n"] += 1; e["usd"] += x.get("amount") or 0
            if len(e["ex"]) < 4: e["ex"].append(x)
    return sorted(f.items(), key=lambda kv: (-kv[1]["usd"], -kv[1]["n"]))


def pj_of(k):
    try: return json.load(open(f"data/countries/{k}.json"))["projects"]
    except Exception: return []


def tr_of(k):
    try: return json.load(open(f"data/trade/{k}.json"))
    except Exception: return {}


def L2(lst): return "、".join(f"{a}（{b}）" if b and b != a else a for a, b in lst) if lst else "无数据"


def doc_country(k):
    c = CT[k]; f = FC.get(k) or {}; wb = f.get("wb") or {}
    o = [f"# {c['zh']}（{c['en']}）国家概况与经济结构", "", f"{c['zh']}属于{c['region']}，是共建“一带一路”国家（Green Finance & Development Center 名单，截至 2025 年 5 月）" + (f"，备注：{c['note']}" if c.get("note") else "") + "。", ""]
    o += ["## 国家机构与领导人（Wikidata，现任）", "",
          f"- 国家元首：{L2(f.get('hos'))}；职位：{L2(f.get('hos_office'))}",
          f"- 政府首脑：{L2(f.get('hog'))}；职位：{L2(f.get('hog_office'))}",
          f"- 立法机构：{L2(f.get('legislature'))}", f"- 中央银行：{L2(f.get('central_bank'))}",
          f"- 首都：{L2(f.get('capital'))}；货币：{L2(f.get('currency'))}；官方语言：{L2(f.get('language'))}", ""]
    if wb:
        o += ["## 经济与社会指标（世界银行开放数据，各取最近一个有值的年份）", ""]
        for code, lab in WBL.items():
            if code in wb:
                v, y = wb[code]
                vs = usd(v) if "美元" in lab and "%" not in lab else (f"{v/1e4:.0f} 万" if v >= 1e5 else f"{v:,.0f}") if code in ("SP.POP.TOTL", "ST.INT.ARVL") else f"{v:.1f}"
                o.append(f"- {lab.replace('（美元）','').replace('（现价美元）','（现价）')}：{vs}（{y} 年）")
        o.append("")
        ag, ind, srv, mf = (wb.get(x, [None])[0] for x in ("NV.AGR.TOTL.ZS", "NV.IND.TOTL.ZS", "NV.SRV.TOTL.ZS", "NV.IND.MANF.ZS"))
        if ag is not None and ind is not None and srv is not None:
            o += [f"产业结构：农业约占 GDP 的 {ag:.0f}%，工业（含建筑业）约 {ind:.0f}%" + (f"（其中制造业约 {mf:.0f}%）" if mf is not None else "") + f"，服务业约 {srv:.0f}%。", ""]
    o += [f"来源：世界银行开放数据 https://data.worldbank.org/country/{k} ；Wikidata https://www.wikidata.org/ （CC0）。"]
    return "\n".join(o) + "\n"


def doc_actors(k):
    c = CT[k]; f = FC.get(k) or {}; pj = pj_of(k); tr = tr_of(k); w = WC.get(k) or {}; l = (CL.get("countries") or {}).get(k) or {}
    o = [f"# {c['zh']}（{c['en']}）：与“一带一路”相关的参与方", "", "下面列出在本国事务中能发声、会行动的真实主体，以及它们之间有据可查的关系。每条注明来源。", ""]
    o += ["## 本国政府与机构", ""]
    for key, lab in (("hos", "国家元首"), ("hog", "政府首脑")):
        for zh, en in f.get(key) or []: o.append(f"- {zh}" + (f"（{en}）" if en and en != zh else "") + f"：{c['zh']}现任{lab}。来源：Wikidata")
    for key, lab in (("legislature", "立法机构"), ("central_bank", "中央银行")):
        for zh, en in f.get(key) or []: o.append(f"- {zh}" + (f"（{en}）" if en and en != zh else "") + f"：{c['zh']}的{lab}。来源：Wikidata")
    o.append(f"- {c['zh']}政府各部门：AidData 记录中的借款方、受援方和项目实施方。")
    fs = funders(pj)
    if fs:
        o += ["", "## 中国方面的出资方和企业（AidData 项目标题原文统计，2000–2021 年承诺）", ""]
        for n, e in fs[:20]:
            ex = "；".join(f"{x['year']} 年 {x['title'][:110]}" for x in e["ex"][:3])
            o.append(f"- {n}：在{c['zh']}出现在 {e['n']} 个项目中" + (f"，涉及金额约 {usd(e['usd'])}" if e["usd"] else "") + f"。例：{ex}")
    if tr.get("partners"):
        o += ["", f"## 主要贸易伙伴（UN Comtrade，{tr.get('year')} 年，{tr.get('partners_basis')}）", ""]
        for p in tr["partners"][:12]:
            nm = ZHC.get(p.get("iso3")) or PZH.get(p.get("name")) or p.get("name")
            o.append(f"- {nm}：{c['zh']}对其出口 {usd(p.get('x'))}，自其进口 {usd(p.get('m'))}")
    adv = [e.get("source") for e in (w.get("advisories") or []) if e.get("source")]
    if l.get("us") or adv:
        o += ["", "## 发布旅行建议的外国政府", ""]
        if l.get("us"): o.append(f"- 美国国务院：{l['us']['title']}。{l['us'].get('url')}")
        for s in sorted(set(adv)): o.append(f"- {s}：近期发布或更新了对{c['zh']}的旅行建议（经 World Monitor）")
    med = collections.Counter(e.get("source") for e in (w.get("stories") or []) if e.get("source"))
    if med:
        o += ["", "## 近期报道该国的媒体（经 World Monitor 新闻聚合）", ""] + [f"- {m}：{n} 篇相关报道" for m, n in med.most_common(12)]
    uc = w.get("ucdp") or []
    if uc:
        pairs = collections.Counter((e.get("a"), e.get("b")) for e in uc)
        o += ["", "## 武装冲突的当事方（UCDP，经 World Monitor）", ""] + [f"- {a} 与 {b}：{n} 起有人员死亡的事件" for (a, b), n in pairs.most_common(10)]
    o += ["", "## 国际与多边机构", "", "- 世界银行、国际货币基金组织（IMF）、亚洲基础设施投资银行（AIIB）、联合国相关机构：本组文档引用的数据来自世界银行、IMF PortWatch、UN Comtrade；具体贷款关系以各机构公开记录为准。"]
    return "\n".join(o) + "\n"


def doc_trade(k):
    c = CT[k]; tr = tr_of(k)
    o = [f"# {c['zh']}（{c['en']}）：行业、贸易与物流", ""]
    if tr.get("total"): o += [f"货物贸易总额（UN Comtrade，{tr.get('year')} 年，{tr.get('partners_basis')}）：出口 {usd(tr['total'].get('x'))}，进口 {usd(tr['total'].get('m'))}。", ""]
    ind = tr.get("industries") or []
    if ind:
        o += [f"## 全部行业的进出口（HS 两位章，{tr.get('year')} 年，本国申报，对全世界）", "", "| 行业 | 出口 | 进口 |", "|---|---|---|"]
        o += [f"| {hsname(r['hs'])} | {usd(r.get('x'))} | {usd(r.get('m'))} |" for r in ind if r["hs"] != "TOTAL"]
        o.append("")
    elif k != "CHN": o += ["本国没有向 UN Comtrade 申报近三年的分行业数据。", ""]
    ch = tr.get("china") or {}
    if ch.get("industries"):
        o += [f"## 中国与{c['zh']}的分行业贸易（中国海关向 UN Comtrade 申报，{ch.get('year')} 年）", "", "| 行业 | 中国出口到该国 | 中国自该国进口 |", "|---|---|---|"]
        o += [f"| {hsname(r['hs'])} | {usd(r.get('x'))} | {usd(r.get('m'))} |" for r in ch["industries"] if r["hs"] != "TOTAL"]
        o.append("")
    pw = ((LG.get("portwatch") or {}).get("countries") or {}).get(k)
    if pw:
        o += [f"## 港口（IMF PortWatch，截至 {bj((LG.get('portwatch') or {}).get('data_until'))} 的近 30 天，卫星船舶信号估算）", "",
              f"全国靠港 {pw.get('calls30')} 次（前 30 天 {pw.get('calls_prev')} 次），进口约 {pw.get('import30')} 公吨，出口约 {pw.get('export30')} 公吨。"]
        o += [f"- {x['name']}港：靠港 {x['calls30']} 次，进口约 {x['import30']} 公吨，出口约 {x['export30']} 公吨" for x in pw.get("ports", [])]
        o.append("")
    o.append("来源：UN Comtrade https://comtradeplus.un.org/ ；IMF PortWatch https://portwatch.imf.org/ 。金额为现价美元。")
    return "\n".join(o) + "\n"


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


def country_profile_finance(k):
    t = country_profile(k)
    return t.replace("：中国融资项目概况", "：中国融资项目（AidData）", 1)


TEN = {"01_country.md": "Country & economy", "02_actors.md": "Actors", "03_industries_trade.md": "Industries, trade & logistics", "04_china_finance.md": "Chinese finance (AidData)",
       "05_situation.md": "Recent situation", "06_projects_detail.md": "Key project dossiers", "07_history.md": "Historical events"}
idx = {"note": "MiroFish 种子文档，由 tools/seed_docs.py 从 data/ 自动生成；推演时按所选国家自动上传。", "sources": "seeds/00_sources.md", "scopes": {}}
changed = 0
os.makedirs("seeds", exist_ok=True); changed += write("seeds/00_sources.md", sources_doc())
for k, c in CT.items():
    os.makedirs(f"seeds/{k}", exist_ok=True)
    ps = [p for p in P if p["country"] == k]
    docs = [("01_country.md", doc_country(k)), ("02_actors.md", doc_actors(k)), ("03_industries_trade.md", doc_trade(k)),
            ("04_china_finance.md", country_profile_finance(k)), ("05_situation.md", country_situation(k) + ("\n" + situation_doc(k, ps) if ps else "")),
            ("06_projects_detail.md", projects_doc(k, ps) if ps else None), ("07_history.md", history_doc(k) if ps else None)]
    keep = {n for n, t in docs if t is not None}
    for old in glob.glob(f"seeds/{k}/*.md"):
        if os.path.basename(old) not in keep: os.remove(old); changed += 1
    files = []
    for name, text in docs:
        if text is None: continue
        p = f"seeds/{k}/{name}"
        changed += write(p, text)
        files.append({"path": p, "title": text.splitlines()[0].lstrip("# "), "title_en": TEN.get(name, name), "bytes": len(text.encode())})
    idx["scopes"][k] = {"name": c["zh"], "en": c["en"], "region": c["region"], "files": files}
idx["generated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
json.dump(idx, open("seeds/index.json", "w"), ensure_ascii=False, separators=(",", ":"))
print("seed docs changed:", changed, "countries:", len(idx["scopes"]))

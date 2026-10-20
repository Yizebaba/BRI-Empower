"""一带一路共建国家清单（150 个，含中国）：Green Finance & Development Center（Nedopil 2025，数据截至 2025 年 5 月）
https://greenfdc.org/countries-of-the-belt-and-road-initiative-bri/ 。意大利（2023 年退出）、巴拿马（2025 年退出）不计入。
note=未确认：该来源注明奥地利、尼日尔、俄罗斯未确认签署完整谅解备忘录或否认，刚果（布）没有签署日期。
中心点取 Natural Earth 1:50m 国界的最大多边形质心（太平洋岛国等取全部多边形质心）。
用法：node 先生成 tools/_ne50.json（见 bri_basemap.js 同一套包），再 python3 tools/bri_countries.py → data/bri_countries.json
"""
import json, sys
R = {"ECA": "欧洲和中亚", "SSA": "撒哈拉以南非洲", "MENA": "中东和北非", "LAC": "拉美和加勒比", "SA": "南亚", "EAP": "东亚和太平洋"}
C = [
 # ISO3, 中文, 区域, 备注
 ("ALB","阿尔巴尼亚","ECA",""),("ARM","亚美尼亚","ECA",""),("AUT","奥地利","ECA","未确认"),("AZE","阿塞拜疆","ECA",""),("BLR","白俄罗斯","ECA",""),
 ("BIH","波黑","ECA",""),("BGR","保加利亚","ECA",""),("HRV","克罗地亚","ECA",""),("CYP","塞浦路斯","ECA",""),("CZE","捷克","ECA",""),("EST","爱沙尼亚","ECA",""),
 ("GEO","格鲁吉亚","ECA",""),("GRC","希腊","ECA",""),("HUN","匈牙利","ECA",""),("KAZ","哈萨克斯坦","ECA",""),("KGZ","吉尔吉斯斯坦","ECA",""),("LVA","拉脱维亚","ECA",""),
 ("LTU","立陶宛","ECA",""),("LUX","卢森堡","ECA",""),("MDA","摩尔多瓦","ECA",""),("MNE","黑山","ECA",""),("MKD","北马其顿","ECA",""),("POL","波兰","ECA",""),
 ("PRT","葡萄牙","ECA",""),("ROU","罗马尼亚","ECA",""),("RUS","俄罗斯","ECA","未确认"),("SRB","塞尔维亚","ECA",""),("SVK","斯洛伐克","ECA",""),("SVN","斯洛文尼亚","ECA",""),
 ("TJK","塔吉克斯坦","ECA",""),("TUR","土耳其","ECA",""),("TKM","土库曼斯坦","ECA",""),("UKR","乌克兰","ECA",""),("UZB","乌兹别克斯坦","ECA",""),
 ("AGO","安哥拉","SSA",""),("BEN","贝宁","SSA",""),("BWA","博茨瓦纳","SSA",""),("BDI","布隆迪","SSA",""),("CPV","佛得角","SSA",""),("CMR","喀麦隆","SSA",""),
 ("CAF","中非","SSA",""),("TCD","乍得","SSA",""),("COM","科摩罗","SSA",""),("COD","刚果（金）","SSA",""),("COG","刚果（布）","SSA","未确认"),("CIV","科特迪瓦","SSA",""),
 ("GNQ","赤道几内亚","SSA",""),("ERI","厄立特里亚","SSA",""),("ETH","埃塞俄比亚","SSA",""),("GAB","加蓬","SSA",""),("GMB","冈比亚","SSA",""),("GHA","加纳","SSA",""),
 ("GIN","几内亚","SSA",""),("GNB","几内亚比绍","SSA",""),("KEN","肯尼亚","SSA",""),("LSO","莱索托","SSA",""),("LBR","利比里亚","SSA",""),("MDG","马达加斯加","SSA",""),
 ("MWI","马拉维","SSA",""),("MLI","马里","SSA",""),("MRT","毛里塔尼亚","SSA",""),("MOZ","莫桑比克","SSA",""),("NAM","纳米比亚","SSA",""),("NER","尼日尔","SSA","未确认"),
 ("NGA","尼日利亚","SSA",""),("RWA","卢旺达","SSA",""),("SEN","塞内加尔","SSA",""),("SYC","塞舌尔","SSA",""),("SLE","塞拉利昂","SSA",""),("SOM","索马里","SSA",""),
 ("ZAF","南非","SSA",""),("SSD","南苏丹","SSA",""),("SDN","苏丹","SSA",""),("TZA","坦桑尼亚","SSA",""),("TGO","多哥","SSA",""),("UGA","乌干达","SSA",""),
 ("ZMB","赞比亚","SSA",""),("ZWE","津巴布韦","SSA",""),
 ("DZA","阿尔及利亚","MENA",""),("BHR","巴林","MENA",""),("DJI","吉布提","MENA",""),("EGY","埃及","MENA",""),("IRN","伊朗","MENA",""),("IRQ","伊拉克","MENA",""),
 ("KWT","科威特","MENA",""),("LBN","黎巴嫩","MENA",""),("LBY","利比亚","MENA",""),("MLT","马耳他","MENA",""),("MAR","摩洛哥","MENA",""),("OMN","阿曼","MENA",""),
 ("QAT","卡塔尔","MENA",""),("SAU","沙特阿拉伯","MENA",""),("SYR","叙利亚","MENA",""),("TUN","突尼斯","MENA",""),("ARE","阿联酋","MENA",""),("YEM","也门","MENA",""),
 ("JOR","约旦","MENA",""),
 ("ATG","安提瓜和巴布达","LAC",""),("ARG","阿根廷","LAC",""),("BRB","巴巴多斯","LAC",""),("BOL","玻利维亚","LAC",""),("CHL","智利","LAC",""),("COL","哥伦比亚","LAC",""),
 ("CRI","哥斯达黎加","LAC",""),("CUB","古巴","LAC",""),("DMA","多米尼克","LAC",""),("DOM","多米尼加","LAC",""),("ECU","厄瓜多尔","LAC",""),("SLV","萨尔瓦多","LAC",""),
 ("GRD","格林纳达","LAC",""),("GUY","圭亚那","LAC",""),("HND","洪都拉斯","LAC",""),("JAM","牙买加","LAC",""),("NIC","尼加拉瓜","LAC",""),("PER","秘鲁","LAC",""),
 ("SUR","苏里南","LAC",""),("TTO","特立尼达和多巴哥","LAC",""),("URY","乌拉圭","LAC",""),("VEN","委内瑞拉","LAC",""),
 ("AFG","阿富汗","SA",""),("BGD","孟加拉国","SA",""),("MDV","马尔代夫","SA",""),("NPL","尼泊尔","SA",""),("PAK","巴基斯坦","SA",""),("LKA","斯里兰卡","SA",""),
 ("BRN","文莱","EAP",""),("KHM","柬埔寨","EAP",""),("CHN","中国","EAP","发起国"),("COK","库克群岛","EAP",""),("FJI","斐济","EAP",""),("IDN","印度尼西亚","EAP",""),
 ("KIR","基里巴斯","EAP",""),("KOR","韩国","EAP",""),("LAO","老挝","EAP",""),("MYS","马来西亚","EAP",""),("FSM","密克罗尼西亚联邦","EAP",""),("MNG","蒙古","EAP",""),
 ("MMR","缅甸","EAP",""),("NZL","新西兰","EAP",""),("NIU","纽埃","EAP",""),("PNG","巴布亚新几内亚","EAP",""),("PHL","菲律宾","EAP",""),("WSM","萨摩亚","EAP",""),
 ("SGP","新加坡","EAP",""),("SLB","所罗门群岛","EAP",""),("THA","泰国","EAP",""),("TLS","东帝汶","EAP",""),("TON","汤加","EAP",""),("VUT","瓦努阿图","EAP",""),
 ("VNM","越南","EAP",""),
]
if __name__ == "__main__":
    import pycountry
    from shapely.geometry import shape
    ne = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "tools/_ne50.json"))   # {numeric: geometry}
    MAN = {"COK": (-21.24, -159.78), "NIU": (-19.05, -169.87), "TON": (-21.18, -175.2), "KIR": (1.87, -157.36), "FSM": (6.92, 158.16), "MDV": (3.2, 73.22), "SYC": (-4.68, 55.49),
           "MLT": (35.9, 14.45), "BHR": (26.07, 50.55), "SGP": (1.35, 103.82), "ATG": (17.07, -61.8), "BRB": (13.19, -59.54), "DMA": (15.41, -61.37), "GRD": (12.12, -61.68), "CPV": (15.12, -23.6), "COM": (-11.88, 43.87), "WSM": (-13.76, -172.1), "FJI": (-17.71, 178.07)}
    out = []
    for iso3, zh, reg, note in C:
        c = pycountry.countries.get(alpha_3=iso3)
        if iso3 in MAN: lat, lon = MAN[iso3]
        else:
            g = shape(ne[str(int(c.numeric))]); poly = max(g.geoms, key=lambda p: p.area) if g.geom_type == "MultiPolygon" else g
            p = poly.representative_point() if iso3 in ("RUS", "CHL", "IDN", "PHL", "NZL", "FJI", "VUT", "SLB", "PNG", "HRV", "VNM", "MYS") else poly.centroid
            lat, lon = round(p.y, 2), round(p.x, 2)
        out.append({"iso3": iso3, "iso2": c.alpha_2, "num": c.numeric, "en": getattr(c, "common_name", None) or c.name, "zh": zh, "region": R[reg], "lat": lat, "lon": lon, "note": note})
    json.dump({"source": "Green Finance & Development Center, Countries of the Belt and Road Initiative (Nedopil 2025, data as of May 2025), https://greenfdc.org/countries-of-the-belt-and-road-initiative-bri/",
               "count": len(out), "countries": out}, open("data/bri_countries.json", "w"), ensure_ascii=False, indent=0)
    print(len(out))

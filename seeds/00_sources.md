# 数据来源说明

本组种子文档里的事实全部来自下列公开数据源：

- 共建“一带一路”国家清单（150 国）：https://greenfdc.org/countries-of-the-belt-and-road-initiative-bri/。许可：Green Finance & Development Center，注明来源可用。更新：静态（截至 2025 年 5 月）。用途：网页覆盖的国家范围。
- AidData 全球中国发展融资地理数据集 v3.0：https://github.com/aiddata/gcdf-geospatial-data。许可：ODC-By 1.0；OSM 要素 ODbL。更新：静态（2000–2021 年承诺的项目）。用途：150 国的中国融资项目清单（8,951 个）和 11 个重点项目的范围。
- USGS 地震目录（M2.5+，近 7 天）：https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php。许可：美国政府作品，公有领域。更新：每 30 分钟。用途：按国界归到 150 个国家；11 个重点项目周边。
- GDACS 全球灾害警报协调系统：https://www.gdacs.org/。许可：欧盟委员会 JRC / 联合国 OCHA，注明来源可用。更新：每 30 分钟。用途：按国界归到 150 个国家；11 个重点项目周边。
- NASA EONET 自然事件：https://eonet.gsfc.nasa.gov/。许可：NASA 开放数据。更新：每 30 分钟。用途：按国界归到 150 个国家；11 个重点项目周边。
- Google 新闻 RSS（按项目名查近 7 天）：https://news.google.com/。许可：标题和链接，版权归原媒体。更新：每 30 分钟。用途：项目相关报道和事件线索。
- IODA 互联网中断检测（佐治亚理工）：https://ioda.inetintel.cc.gatech.edu/。许可：学术开放数据，注明来源。更新：每 30 分钟。用途：所在国近 7 天断网告警。
- 美国国务院旅行建议：https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories.html。许可：美国政府作品。更新：每 30 分钟。用途：150 国的旅行建议级别。
- 英国外交部旅行建议：https://www.gov.uk/foreign-travel-advice。许可：Open Government Licence v3.0。更新：每 30 分钟。用途：最近更新时间和更新摘要。
- World Monitor（UCDP 冲突事件、各国旅行建议、国际新闻要闻、Cloudflare 断网、疫情、机场）：https://www.worldmonitor.app/。许可：World Monitor 服务条款；UCDP 数据 CC BY 4.0。更新：每天一次（免费账号每天 5 次调用，每次取全球数据）。用途：每个国家的冲突、新闻、断网、旅行建议。
- Natural Earth 1:50m 国界：https://www.naturalearthdata.com/。许可：公有领域。更新：静态。用途：网页地图底图。
- 偏差测试参考事实（ICIMOD、Eos、全印广播、ProPakistani、老挝通讯社等）：data/reference.json。许可：各来源原文链接见文件。更新：手工整理。用途：4 起真实事件的权威事实，用来量化平台的偏差。
- IMF PortWatch 港口与海上咽喉要道：https://portwatch.imf.org/。许可：IMF / 牛津大学，公开数据，注明来源。更新：每天一次（数据本身约晚几天）。用途：各国港口近 30 天靠港次数、进出口量（公吨），28 个咽喉要道通行。
- UN Comtrade 联合国商品贸易统计：https://comtradeplus.un.org/。许可：联合国统计司，公开预览接口。更新：每周。用途：各国对全世界的进出口（97 个行业大类，HS 两位章）、主要贸易伙伴、中国对各国的分行业贸易；本国没申报的用镜像数据。
- 世界银行开放数据（World Development Indicators）：https://data.worldbank.org/。许可：CC BY 4.0。更新：每周取一次，各指标取最近一个有值的年份。用途：经济规模、增长、三次产业和制造业占比、通胀、外债、偿债、外资、就业结构、城市化、通电和互联网。
- Wikidata：https://www.wikidata.org/。许可：CC0。更新：每周。用途：现任国家元首、政府首脑、立法机构、中央银行、首都、货币、官方语言（种子文档里的真实主体）。
- 维基百科（英文）：https://en.wikipedia.org/。许可：CC BY-SA 4.0。更新：每周。用途：国家条目导言、“中国—该国关系”条目全文、与“一带一路”相关的条目导言（种子文档）。
- 世界银行文献库（Documents & Reports）：https://documents.worldbank.org/。许可：世界银行使用条款，多数为 CC BY 3.0 IGO。更新：每周。用途：每国最新的报告和项目文件：标题、类型、日期、摘要（种子文档）。
- OpenAlex 学术论文库：https://openalex.org/。许可：CC0。更新：每周。用途：关于“一带一路”和该国的论文：标题、年份、期刊、摘要（种子文档）。
- ReliefWeb（联合国人道协调厅）：https://reliefweb.int/。许可：按各报告来源。更新：每周（需要批准的 appname，没有时跳过）。用途：每国最新的人道报告正文节选（种子文档）。
- 航空、铁路、公路咽喉要道（150 国）：https://github.com/Yizebaba/BRI-Empower/blob/main/tools/chokepoints_land.py。许可：新闻标题版权归原媒体；灾害数据见 USGS、GDACS、NASA；机场状态见 World Monitor。更新：每天两次。用途：每国主要国际机场、跨境铁路口岸、主要公路口岸和每一段陆地边境：近 7 天中断类报道、附近灾害、机场状态。
- OurAirports 机场数据：https://ourairports.com/data/。许可：公有领域。更新：每天两次读取。用途：150 国的主要国际机场名单和位置。

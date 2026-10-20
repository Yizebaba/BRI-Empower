# 数据来源说明

本组种子文档里的事实全部来自下列公开数据源：

- AidData 全球中国发展融资地理数据集 v3.0：https://github.com/aiddata/gcdf-geospatial-data。许可：ODC-By 1.0；OSM 要素 ODbL。更新：静态（2000–2021 年承诺的项目）。用途：项目清单、范围（多边形）、融资方、状态、承诺年份。
- USGS 地震目录（M2.5+，近 7 天）：https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php。许可：美国政府作品，公有领域。更新：每 30 分钟。用途：项目 150 km 内的地震。
- GDACS 全球灾害警报协调系统：https://www.gdacs.org/。许可：欧盟委员会 JRC / 联合国 OCHA，注明来源可用。更新：每 30 分钟。用途：项目 300 km 内的洪水、气旋、地震等警报。
- NASA EONET 自然事件：https://eonet.gsfc.nasa.gov/。许可：NASA 开放数据。更新：每 30 分钟。用途：项目 150 km 内的火山、风暴、滑坡、野火等。
- Google 新闻 RSS（按项目名查近 7 天）：https://news.google.com/。许可：标题和链接，版权归原媒体。更新：每 30 分钟。用途：项目相关报道和事件线索。
- IODA 互联网中断检测（佐治亚理工）：https://ioda.inetintel.cc.gatech.edu/。许可：学术开放数据，注明来源。更新：每 30 分钟。用途：所在国近 7 天断网告警。
- 美国国务院旅行建议：https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories.html。许可：美国政府作品。更新：每 30 分钟。用途：国家风险级别 1–4。
- 英国外交部旅行建议：https://www.gov.uk/foreign-travel-advice。许可：Open Government Licence v3.0。更新：每 30 分钟。用途：最近更新时间和更新摘要。
- World Monitor（UCDP 冲突事件、GDELT 动荡信号）：https://www.worldmonitor.app/。许可：World Monitor 服务条款；UCDP 数据 CC BY 4.0。更新：每天一次（免费账号每天 5 次调用）。用途：所在国已核实的有伤亡冲突事件。
- Natural Earth 1:50m 国界：https://www.naturalearthdata.com/。许可：公有领域。更新：静态。用途：网页地图底图。
- 偏差测试参考事实（ICIMOD、Eos、全印广播、ProPakistani、老挝通讯社等）：data/reference.json。许可：各来源原文链接见文件。更新：手工整理。用途：4 起真实事件的权威事实，用来量化平台的偏差。

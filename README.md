# 一带一路赋能 · BRI-Empower

一带一路项目周边的实时态势、可以引用的数据源、自动生成的 MiroFish 种子文档，以及按你自己写的要求运行的 MiroFish 推演。

网页：https://yizebaba.github.io/BRI-Empower/

覆盖 150 个共建国家（Green Finance & Development Center 清单，截至 2025 年 5 月）；中国融资项目 8,951 个（AidData GCDF v3.0）；其中 11 个重点项目（尼泊尔、老挝、巴基斯坦）有项目周边的逐条监测。

## 它怎么运转

| 环节 | 做什么 | 在哪里 |
|---|---|---|
| 扫描 | 每 30 分钟：150 国的地震、灾害警报、自然事件、美国旅行建议；11 个重点项目周边（另加 Google 新闻、IODA、英国旅行建议） | `scan.yml` → `data/country_live.json`、`data/live.json` |
| World Monitor | 每天一次取全球数据（冲突事件、新闻要闻与旅行建议、断网、疫情、机场），按国家整理 | 定时任务 → `data/wm_raw/` → `tools/wm_process.py` → `data/wm.json` |
| 种子文档 | 把以上数据整理成 MiroFish 需要的 Markdown（项目档案、周边态势、历史事实、来源说明），每条注明来源 | `tools/seed_docs.py` → `seeds/` |
| 推演 | 你在网页上写推演要求并提交；珠峰仓库的 mirofish 工作流（project=bri）把所选范围的种子文档和你的要求自动上传给 MiroFish，建图谱、模拟、写报告 | Yizebaba/EVEREST- 的 `mirofish.yml` → 它的 events 分支 `mirofish-bri/` |
| 网页 | 3D 地球、态势、推演表单、种子文档、数据源、偏差测试 | `site/`（GitHub Pages） |

推演要求只能由你自己写，系统不替你生成。

## 第一次使用

不用在本仓库设置任何密钥，访客也不需要 GitHub 令牌。谁推演谁出密钥：在网页“推演”标签填自己的模型接口（任意 OpenAI 兼容接口）和 Zep 密钥，提交到珠峰的 Worker 排队；珠峰仓库（Yizebaba/EVEREST-）的 mirofish 工作流用 GitHub OIDC 身份领取并运行，密钥领取后即删除。网页由工作流推到 gh-pages 分支自动发布。

种子文档（seeds/<ISO3>/）每国 5–7 份：国家概况与经济结构（世界银行、Wikidata）、参与方（政府与领导人、中国出资方和企业、贸易伙伴、媒体、冲突当事方）、全部行业的进出口和物流（UN Comtrade、IMF PortWatch）、中国融资项目（AidData）、近期态势（World Monitor、USGS、GDACS、NASA EONET 等）。

## 数据和许可

数据源、许可和引用方式见 `data/sources.json`，网页“数据源”标签里也有。MiroFish（AGPL-3.0）在推演时从它的官方仓库按固定版本拉取，本仓库不包含也不修改它的代码。

## 关联项目

珠峰平台（EVEREST）：https://github.com/Yizebaba/EVEREST- 。两个项目分开维护。

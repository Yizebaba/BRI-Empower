# 一带一路 全量 预鉴 · Belt and Road Full-Scope Foresight

网页 / Website：https://yizebaba.github.io/BRI-Empower/ · 文档 / Docs：https://yizebaba.github.io/BRI-Empower/about.html

> 如果，看见未来的不同可能；如果，未来可以事先预演；那么决策的胜率会有多高呢？

把 150 个“一带一路”共建国家的公开数据，加上使用者自己的资料，交给 AI 群体智能推演引擎，生成代表政府、企业、媒体、当地居民等各方的智能体，在模拟社会里对一项决策做出反应，输出推演报告和全过程数据。

Public data on the 150 Belt and Road partner countries, plus the user's own documents, feed an AI swarm-intelligence engine whose agents (governments, companies, media, residents…) react to a decision in a simulated society; the output is a report and the full process data.

## 功能 / Features

| 功能 | 说明 |
|---|---|
| 推演（默认标签） | 选 0–5 个国家，勾选种子文档，上传自己的资料（PDF/Markdown/TXT，最多 20 个、单个 50 MB、合计 100 MB），自己写推演要求，用自己的模型密钥运行。轮数默认自动。 |
| 结果 | 网页阅读；下载 PDF、Word、Markdown、HTML 报告和 CSV 过程数据。每份文件带“推演内容，不是事实”标注和免责声明。 |
| 国家 | 150 国的冲突、灾害、断网、新闻、旅行建议、概况、贸易（97 个行业）、中国融资项目；海运、航空、铁路、公路咽喉要道和每段陆地边境。 |
| 种子文档 | 每国 5–8 份，自动生成，可阅读和下载。 |
| 数据源 / 推演测试 | 每个数据源的许可、更新频率、用途；用 4 起真实事件检验数据的准确度。 |
| 中英文 | 全站中英文切换。 |
| 定制推演 | “定制推演 ✉”按钮打开写信页（yizebaba@gmail.com），可选紧急程度：标准、加急、特急、紧急。 |

## 数据更新 / Data refresh

| 工作流 | 频率 | 内容 |
|---|---|---|
| `scan.yml` | 每 30 分钟 | 地震、灾害警报、自然事件、旅行建议、重点项目周边新闻；重新生成种子文档 |
| World Monitor 定时任务 | 每天 | 冲突、新闻要闻、断网、疫情、机场 → `data/wm.json` |
| `logistics.yml` | 每天 2 次 | IMF PortWatch 港口和海上咽喉要道 |
| `chokepoints.yml` | 每天 2 次 | 航空、铁路、公路咽喉要道和陆地边境 |
| `trade.yml` | 每周一 | UN Comtrade 贸易、世界银行指标、Wikidata 机构和领导人 |
| `docs.yml` | 每周三 | 维基百科、世界银行文献库、OpenAlex 论文（ReliefWeb 待批准） |
| `pages.yml` | 网页改动时 | 发布 `site/` 到 GitHub Pages |

## 推演怎么运行 / How a run works

网页把推演要求、所选种子文档、上传的文件和使用者自己的模型与 Zep 密钥提交给珠峰平台的 Cloudflare Worker 排队；珠峰仓库（Yizebaba/EVEREST-）的 `mirofish-queue.yml` 每 5 分钟派出任务，`mirofish.yml` 用 GitHub OIDC 身份领取（密钥和文件领取后即从服务器删除），运行推演并把结果和导出文件存到它的 events 分支 `mirofish-bri/`。本仓库不需要任何密钥，访客也不需要 GitHub 令牌。

注意：自助推演的推演要求和报告会出现在公开的推演记录里。

## 数据和许可 / Data and licences

数据源、许可和引用方式见 `data/sources.json`（网页“数据源”标签）。推演引擎为开源项目 MiroFish（github.com/666ghj/MiroFish，AGPL-3.0），运行时按固定版本拉取，本仓库不包含也不修改它的代码。

推演结果是模拟，不是事实或预测，也不构成投资、法律或安全建议。

## 关联项目 / Related

珠峰平台（EVEREST）：https://github.com/Yizebaba/EVEREST- 。两个项目分开维护。

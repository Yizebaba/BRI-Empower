# 一带一路赋能 · BRI-Empower

一带一路项目周边的实时态势、可以引用的数据源、自动生成的 MiroFish 种子文档，以及按你自己写的要求运行的 MiroFish 推演。

网页：https://yizebaba.github.io/BRI-Empower/

样品范围：尼泊尔 5 个、老挝 2 个、巴基斯坦 4 个，共 11 个中国融资项目（AidData 全球中国发展融资地理数据集 v3.0）。

## 它怎么运转

| 环节 | 做什么 | 在哪里 |
|---|---|---|
| 扫描 | 每 30 分钟查一次项目周边：USGS 地震、GDACS 灾害警报、NASA EONET、Google 新闻、IODA 断网、美英旅行建议 | `.github/workflows/scan.yml` → `data/live.json` |
| 冲突事件 | 每天一次经 World Monitor 读取 UCDP 已核实的冲突事件 | 定时任务 → `data/wm.json` |
| 种子文档 | 把以上数据整理成 MiroFish 需要的 Markdown（项目档案、周边态势、历史事实、来源说明），每条注明来源 | `tools/seed_docs.py` → `seeds/` |
| 推演 | 你在网页上写推演要求并提交；工作流把所选范围的种子文档和你的要求自动上传给 MiroFish，建图谱、模拟、写报告 | `.github/workflows/drill.yml` → `runs/<编号>/` |
| 网页 | 3D 地球、态势、推演表单、种子文档、数据源、偏差测试 | `site/`（GitHub Pages） |

推演要求只能由你自己写，系统不替你生成。

## 第一次使用需要的设置

1. **Settings → Pages**：Source 选 GitHub Actions。
2. **Settings → Secrets and variables → Actions**，新建 4 个 Secret（MiroFish 用）：
   - `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL_NAME`：任意 OpenAI 格式的模型接口（如 DeepSeek：`https://api.deepseek.com`、`deepseek-chat`）。
   - `ZEP_API_KEY`：Zep Cloud 的密钥。
3. 在网页的“推演”标签连接 GitHub：新建一个 Fine-grained token，只选本仓库，Actions 权限选 Read and write。令牌只存在你自己的浏览器里。

## 数据和许可

数据源、许可和引用方式见 `data/sources.json`，网页“数据源”标签里也有。MiroFish（AGPL-3.0）在推演时从它的官方仓库按固定版本拉取，本仓库不包含也不修改它的代码。

## 关联项目

珠峰平台（EVEREST）：https://github.com/Yizebaba/EVEREST- 。两个项目分开维护。

# StrataSense 扫描报告（v0.1）

- run_id: `run_20260209_150406`
- ts_utc: `2026-02-09T07:04:06Z`
- root: `D:\Dev\Tools\StrataSense`

## 分层信息源清单（v0.1 固化）

### L1
- **The Economist**（media）：只看 Leaders/Briefing/Special Report
- **Financial Times**（media）：优先 Big Read，避免 breaking news
- **CFR (Council on Foreign Relations)**（think_tank）：Backgrounders 作为结构校准

### L2
- **IEA (International Energy Agency)**（org）：能源约束：WEO/月报摘要
- **USGS (Mineral Commodity Summaries)**（gov）：矿产供给集中度/产地分布
- **ASML Updates**（company）：算力瓶颈：技术/产能/限制

### L3
- **FRED**（dataset）：宏观数据验证器（信贷/就业/流动性等）
- **BlackRock Investment Outlook**（institution）：大资金可执行世界观
- **OECD / MSCI**（institution）：跨地区/指数层对照

### L4
- **Bloomberg Markets / Odd Lots**（media）：情绪温度计：看争论点，不跟单
- **X/Twitter (严格白名单)**（social）：只关注数据派/研究员，禁 KOL 喊单
- **Reddit (r/investing 等)**（social）：反向指标：识别共识化/过热

### L5
- **Execution (外部系统)**（boundary）：StrataSense 不负责交易执行

## v0.1 说明
- 本次 scan 不联网、不做观点，只冷存框架与清单。
- 后续扩展应遵守：单入口 / 默认沉默 / 冷存优先 / 不被执行层反向绑架。

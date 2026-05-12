# Skill Catalog

> 统计口径：基于 `C:\Users\Administrator\.codex\skills` 目录递归检索到的 `SKILL.md` 汇总，并按 `name` 去重。当前共 69 个唯一 skill。
> 说明：`调用示例` 列给的是推荐触发话术，不是唯一格式；一般既可以直接点名 skill，也可以通过自然语言描述场景让 Codex 自动匹配。
> 编码说明：本文件已重建为 UTF-8 中文内容，避免旧版错误转码导致的乱码。

## 基础系统与工具

| 名称 | 主要用途 | 适合什么时候用 | 调用示例 |
| --- | --- | --- | --- |
| `api-doc-integration-builder` | 抓取技术 API 文档站、跟踪子页面、构建本地语料，并带引用回答问题或生成接入指南。 | 需要读 API 文档、做集成、从官方 docs 回答问题时。 | `请用 api-doc-integration-builder 分析这个 API 文档并输出接入指南：<url>` |
| `claude-mem` | 检索和保存跨会话记忆、历史决策与长期备注。 | 需要查以前的结论、修复记录，或保存可复用上下文时。 | `请用 claude-mem 查一下我们之前关于支付回调的结论` |
| `connect-apps` | 连接 Gmail、Slack、GitHub 等外部应用并直接执行动作。 | 需要发邮件、发消息、建 issue、同步外部系统时。 | `请用 connect-apps 在 Slack 发一条项目更新` |
| `imagegen` | 生成或编辑位图图像，例如海报、插画、贴图、透明抠图素材。 | 需要直接产出位图视觉素材，而不是代码或 SVG 时。 | `请用 imagegen 生成一张极简科技风横幅` |
| `openai-docs` | 仅使用 OpenAI 官方资料回答 API、模型、升级与最佳实践问题。 | 问题涉及 OpenAI 产品、OpenAI API、模型选型或升级路径时。 | `请用 openai-docs 给我一份 GPT-5.4 升级建议` |
| `plugin-creator` | 创建 Codex 插件骨架，补齐 `.codex-plugin/plugin.json` 和可选结构。 | 需要初始化本地插件或补充插件目录结构时。 | `请用 plugin-creator 帮我创建一个新插件骨架` |
| `skill-creator` | 设计或更新 skill 的触发条件、结构和工作流说明。 | 需要创建新 skill，或改造现有 skill 时。 | `请用 skill-creator 帮我设计一个处理日志排查的 skill` |
| `skill-installer` | 从 curated 列表或 GitHub 仓库安装 skill 到本地。 | 需要安装现成 skill，或先查看有哪些可安装 skill 时。 | `请用 skill-installer 安装一个适合调试前端的 skill` |
| `web-access` | 进行联网搜索、网页抓取、登录态站点操作与动态页面读取。 | 需要联网核验网页信息、抓数据、操作动态页面时。 | `请用 web-access 登录这个站点并抓取订单列表` |
| `xcrawl` | 通过 XCrawl API 做单页抓取、格式选择、同步/异步执行和 JSON 抽取。 | 明确要用 XCrawl 抓取 URL、抽取结构化 JSON，且本地已有 `~/.xcrawl/config.json` API key 时。 | `请用 xcrawl 抓取这个页面并按 JSON schema 提取字段：<url>` |

## Khazix Skills

| 名称 | 主要用途 | 适合什么时候用 | 调用示例 |
| --- | --- | --- | --- |
| `neat-freak` | 会话收尾知识库清理，同步项目文档、根目录 AI 指南和 agent 记忆，避免知识过期。 | 一个开发阶段结束、准备交接、文档或记忆可能和代码不一致时。 | `请用 neat-freak 收尾整理一下这个项目` |
| `hv-analysis` | 横纵分析法深度研究：纵向追历史，横向比同类，最终产出排版后的 PDF 研究报告。 | 需要系统研究一个产品、公司、概念、技术或人物，而不是只查一句定义时。 | `请用 hv-analysis 深度研究一下 Cursor` |
| `khazix-writer` | 按「数字生命卡兹克」的口吻写中文公众号长文，内置风格规则、禁用词和自检体系。 | 需要把素材、链接、PDF、转写稿或散乱想法写成中文公众号长文时。 | `请用 khazix-writer 把这些素材写成一篇公众号文章` |

## 浏览器、自动化与远程协作

| 名称 | 主要用途 | 适合什么时候用 | 调用示例 |
| --- | --- | --- | --- |
| `ayiya-web-control` | 使用持久 Chrome 配置和 Playwright CDP 自动化网页流程，支持登录态、表单、点击、下载和断点续跑。 | 需要稳定操作网站、复用登录态、下载文件或长时间执行网页任务时。 | `请用 ayiya-web-control 登录这个后台并导出订单数据` |
| `browse` | 用快速无头浏览器做 QA、dogfooding、截图、状态断言和页面 diff。 | 需要测试站点、验证表单、抓取证据、检查响应式布局时。 | `请用 browse 打开这个页面并验证注册流程` |
| `gstack` | 通用 GStack 浏览器入口，用于打开站点、交互验证和页面检查。 | 需要直接用 GStack 浏览器看页面、做交互或排查问题时。 | `请用 gstack 打开这个站点并检查首页状态` |
| `open-gstack-browser` | 启动可见的 GStack Browser，让你实时观察 AI 浏览器操作。 | 需要打开带侧边栏的可视 Chromium 窗口时。 | `请用 open-gstack-browser 打开浏览器` |
| `pair-agent` | 把你的浏览器访问权共享给另一个远程 agent。 | 需要让另一个 agent 协助操作当前浏览器时。 | `请用 pair-agent 把这个浏览器共享给远程 agent` |
| `playwright` | 通过终端驱动真实浏览器，执行导航、表单、截图、抓取等流程。 | 需要脚本化浏览器自动化、复现 UI 流程或抓取页面内容时。 | `请用 playwright 跑一遍注册流程并截图` |
| `setup-browser-cookies` | 把真实 Chromium 的 cookies 导入无头浏览器会话。 | 需要在 QA 前复用登录态、测试受保护页面时。 | `请用 setup-browser-cookies 导入这个站点的登录态` |

## 社媒热榜与数据采集

| 名称 | 主要用途 | 适合什么时候用 | 调用示例 |
| --- | --- | --- | --- |
| `baidu-cdp` | 通过影刀浏览器 CDP 抓取百度热搜榜、词条搜索页、主要文章、评论和 800 字内 AI 摘要，并写入 `media-coding` 数据库。 | 需要采集百度热搜榜，或实现/排查百度热搜爬虫和落库流程时。 | `请用 baidu-cdp 抓取百度热搜榜并存入数据库` |
| `bilibili-blogger-deep-capture` | 分批抓取 B 站 UP 主主页的全部视频，补齐视频元数据、互动指标、前 50 条评论、本地媒体缓存和视频内容分析。 | 需要做 B 站博主主页全量采集、断点续跑，或补齐 `blogger_posts` 的评论和视频证据时。 | `请用 bilibili-blogger-deep-capture 抓取这个 B 站 UP 主主页的全部视频和评论` |
| `bilibili-cdp` | 抓取、实现或排查 B 站综合热门、排行榜、热搜、视频详情、指标和评论采集流程。 | 需要刷新 B 站热榜数据，或维护 `media-coding` 里的 B 站热点抓取脚本时。 | `请用 bilibili-cdp 刷新 B 站热榜和排行数据` |
| `douyin-cdp` | 通过影刀浏览器 CDP 抓取抖音创作者中心热点榜、热门内容、视频证据、评论和数据库字段。 | 需要采集抖音热点/创作者指数，或维护相关 CDP 抓取脚本时。 | `请用 douyin-cdp 刷新抖音热点数据` |
| `douyin-blogger-deep-capture` | 用低风险 CDP 元数据采集、滚动小批次抓取、即时本地视频缓存、安全评论读取和本地视频理解，完成抖音博主主页深度采集。 | 需要分批抓取抖音博主主页、断点续跑评论和视频缓存，或继续补齐 `blogger_posts` 的内容证据时。 | `请用 douyin-blogger-deep-capture 抓取这个抖音博主主页并分批补齐评论和视频缓存` |
| `webo-cdp` | 通过影刀浏览器 CDP 抓取微博热搜、详情页首条微博、互动数据、热门评论和摘要。 | 需要采集微博热搜，或修复微博热搜作者、评论、落库不准的问题时。 | `请用 webo-cdp 更新微博热搜数据` |
| `xiaodouya-ip-backend` | 打开新榜小豆芽 Windows 客户端，按当前 IP 名匹配账号管理器列表，检查灰色登录状态，并采集自有账号后台作品数据。 | 需要采集 IP 中心自有账号后台数据、作品互动走势或素材证据时。 | `请用 xiaodouya-ip-backend 抓取 我是Ayiya 的后台作品数据` |

## 文档与文件处理

| 名称 | 主要用途 | 适合什么时候用 | 调用示例 |
| --- | --- | --- | --- |
| `docx` | 创建、读取、编辑 `.docx`，支持目录、页眉页脚、重排内容、替换图片等。 | 需要产出或修改正式 Word 文档时。 | `请用 docx 把这份提纲整理成正式 Word 报告` |
| `pdf` | 读取 PDF、抽取文本和表格、OCR、拆分合并、加水印、填表等。 | 需要处理 PDF 阅读或生产任务时。 | `请用 pdf 提取这个 PDF 里的表格并合并成一个文件` |
| `pptx` | 创建、读取、编辑演示文稿，支持结构调整、合并拆分和模板化输出。 | 需要产出或修改可演示的幻灯片文件时。 | `请用 pptx 把这份方案做成 10 页汇报稿` |
| `xlsx` | 处理 `.xlsx/.xlsm/.csv/.tsv`，支持清洗、计算、格式化、图表和结构重建。 | 需要清洗表格、补公式、输出最终电子表格时。 | `请用 xlsx 清洗这份 CSV 并补出汇总表` |

## 设计、前端与创意探索

| 名称 | 主要用途 | 适合什么时候用 | 调用示例 |
| --- | --- | --- | --- |
| `create-colleague` | 把同事资料蒸馏为可复用的 AI Skill 或 Persona。 | 需要沉淀团队成员画像和协作模板时。 | `请用 create-colleague 为张三生成一个 AI Skill` |
| `design-consultation` | 研究产品和竞品，提出完整设计系统，并生成 `DESIGN.md`。 | 新项目需要建立统一视觉和交互设计基线时。 | `请用 design-consultation 为这个项目生成 DESIGN.md` |
| `design-html` | 把已确认的设计方案落成生产可用的 HTML/CSS。 | 已有设计方案，准备做最终静态落地页或页面实现时。 | `请用 design-html 把这个落地页方案实现成最终页面` |
| `design-shotgun` | 快速生成多套设计方向，对比后继续迭代收敛。 | 需要探索视觉风格、布局方向或首页方案时。 | `请用 design-shotgun 给我出 4 个首页视觉方案` |
| `develop-web-game` | 为 HTML/JS Web 游戏建立实现、试玩、截图和报错检查闭环。 | 在做 Web 游戏玩法迭代、调试交互和渲染问题时。 | `请用 develop-web-game 帮我迭代这个小游戏的碰撞逻辑` |
| `figma` | 通过 Figma MCP 获取设计上下文、截图、变量和资产，并映射到代码。 | 任务涉及 Figma 链接、节点 ID、设计还原或 Figma 到代码时。 | `请用 figma 按这个节点实现 React 组件：<figma-url>` |
| `frontend-design` | 生成高质量网页、组件和前端视觉实现，避免模板化 AI 风格。 | 需要设计并实现页面、组件、落地页、仪表盘时。 | `请用 frontend-design 做一个营销落地页` |
| `office-hours` | 在编码前做产品和项目 brainstorming，梳理问题、切入点和方案。 | 你有一个产品想法，想判断值不值得做或怎么切入时。 | `请用 office-hours 帮我判断这个点子值不值得做` |

## 计划评审与自动规划

| 名称 | 主要用途 | 适合什么时候用 | 调用示例 |
| --- | --- | --- | --- |
| `autoplan` | 自动串行执行 CEO、设计、工程和 DX 评审，并代做关键决策。 | 已经有计划文档，想一键跑完整个 review 流程时。 | `请用 autoplan 自动 review 这份实现计划` |
| `plan-ceo-review` | 从 CEO 或 Founder 视角复盘计划的范围、野心和产品方向。 | 想判断方案是不是过于保守，是否应该扩大或收缩范围时。 | `请用 plan-ceo-review 帮我看看这个方案是不是太保守` |
| `plan-design-review` | 从设计评审角度检查 UI/UX 方案并给出改进建议。 | 准备实现前，想先找出视觉层级和交互体验问题时。 | `请用 plan-design-review 评审这个后台设计方案` |
| `plan-devex-review` | 从开发者体验角度审视 API、SDK、CLI、文档和工具链设计。 | 方案面向开发者，需要评估上手成本和体验时。 | `请用 plan-devex-review 评审这个开发者平台方案` |
| `plan-eng-review` | 从工程经理视角检查架构、数据流、边界条件和测试覆盖。 | 准备开工前，想先把技术方案锁清楚时。 | `请用 plan-eng-review 过一遍这个实现方案` |

## 质量、调试与安全审计

| 名称 | 主要用途 | 适合什么时候用 | 调用示例 |
| --- | --- | --- | --- |
| `benchmark` | 建立性能基线并比较前后回归，包括 Web Vitals 和资源体积。 | 需要做页面性能对比、监控回归或看加载速度变化时。 | `请用 benchmark 测一下这个页面的性能回归` |
| `canary` | 部署后持续监控线上页面错误、性能回归和视觉异常。 | 刚发布完，需要盯住线上站点是否稳定时。 | `请用 canary 监控这次部署后的首页状态` |
| `design-review` | 用设计师视角做线上 UI 质检，找出视觉和交互问题并修正。 | 页面已经做出来，想做一轮视觉 QA 和设计打磨时。 | `请用 design-review 审一下这个页面的视觉质量` |
| `devex-review` | 实测开发者体验，从安装、文档到 CLI 流程做审查和评分。 | 需要检查文档、SDK、CLI 或开发者入口是否好用时。 | `请用 devex-review 跑一遍这个项目的 getting started` |
| `health` | 运行类型检查、lint、测试和死代码等项，输出代码健康分。 | 想快速了解当前代码库整体健康度时。 | `请用 health 给这个仓库做一次健康检查` |
| `qa` | 系统化 QA 测试 Web 应用，并对发现的问题直接修复。 | 你要的不只是 bug 报告，而是边测边修的闭环时。 | `请用 qa 测这个站点并把问题修掉` |
| `qa-only` | 系统化 QA 测试，但只输出报告，不做修复。 | 只想拿到缺陷报告、复现步骤和截图证据时。 | `请用 qa-only 给我一份这个站点的 QA 报告` |
| `review` | 在落地前对 diff 或 PR 做结构化代码审查。 | 需要在合并前检查潜在 bug、风险和测试缺口时。 | `请用 review 看一下这次改动有没有明显风险` |
| `retro` | 做周度工程回顾，分析提交、产出、质量和个人或团队趋势。 | 需要做周报式 retrospective 或复盘本周开发表现时。 | `请用 retro 给我做本周工程 retrospective` |

## 调试、知识沉淀与安全分析

| 名称 | 主要用途 | 适合什么时候用 | 调用示例 |
| --- | --- | --- | --- |
| `checkpoint` | 保存并恢复当前工作状态、关键决策和剩余事项。 | 会话快结束、要切分支或之后继续接着干时。 | `请用 checkpoint 保存当前进度` |
| `cso` | 做安全审计、威胁建模、依赖供应链和 CI/CD 安全检查。 | 需要从安全负责人视角审计项目和流程时。 | `请用 cso 给这个项目做一次安全审计` |
| `investigate` | 按“先找根因，再决定修法”的方式系统化排查问题。 | 遇到报错、500、未知回归或复杂故障时。 | `请用 investigate 帮我查这个 500 错误` |
| `learn` | 管理 gstack 的项目经验沉淀，支持检索、清理和导出。 | 想查历史经验、复盘以前踩过的坑或清理旧结论时。 | `请用 learn 看看我们之前记录过哪些上线故障` |

## 安全边界与行为控制

| 名称 | 主要用途 | 适合什么时候用 | 调用示例 |
| --- | --- | --- | --- |
| `careful` | 对高风险操作给出额外警告，例如删除、重置或危险数据库操作。 | 你明确希望 agent 在破坏性操作前更加保守时。 | `请用 careful 进入安全模式` |
| `freeze` | 把编辑范围冻结到某个目录，阻止越界改动。 | 调试时只允许改某个模块，避免顺手改坏别处时。 | `请用 freeze 只允许修改 backend/src/auth` |
| `guard` | 同时开启危险命令提醒和目录冻结，属于更完整的安全模式。 | 既要限制编辑范围，又要防止危险命令误操作时。 | `请用 guard 锁定这个目录并开启最高安全保护` |
| `pua` | 在高压排障场景提升执行强度和穷尽度。 | 你希望 agent 别停在分析，继续死磕把问题查到底时。 | `请用 pua 模式把这个问题彻底查到底` |
| `unfreeze` | 清除 `freeze` 设下的目录限制。 | 局部排查结束，需要恢复正常编辑范围时。 | `请用 unfreeze 解除目录限制` |

## 发布、交付与运维

| 名称 | 主要用途 | 适合什么时候用 | 调用示例 |
| --- | --- | --- | --- |
| `document-release` | 在代码交付后同步 README、ARCHITECTURE、CHANGELOG 等文档。 | 功能已完成或已合并，想把文档和版本说明补齐时。 | `请用 document-release 更新这次发布相关文档` |
| `gstack-upgrade` | 升级 gstack 到最新版本并查看更新内容。 | 需要把本地 gstack 更新到最新时。 | `请用 gstack-upgrade 升级 gstack` |
| `land-and-deploy` | 合并 PR、等待 CI 与部署完成，并检查生产环境健康度。 | PR 已就绪，准备真正落地到生产时。 | `请用 land-and-deploy 合并并验证这次部署` |
| `setup-deploy` | 为 `land-and-deploy` 配置部署平台、生产 URL 和健康检查。 | 第一次接入自动部署流程，或部署配置不完整时。 | `请用 setup-deploy 配置这个项目的部署信息` |
| `ship` | 运行 ship 流程，覆盖测试、评审、版本、提交、推送和 PR 创建。 | 代码基本完成，准备发起 PR 或推进交付时。 | `请用 ship 把这次改动整理好并创建 PR` |
| `vercel-deploy` | 创建、推广、验证或调试 Vercel 部署，优先走 preview，再在明确授权下发布 production。 | 需要在 Vercel 上部署、验证、提升预发到正式，或排查预览/生产发布问题时。 | `请用 vercel-deploy 帮我把这个项目部署到 Vercel 并验证` |
| `vercel-deploy-hardening` | 排查 Vercel 上浏览器、CLI、别名和运行时日志相互矛盾的部署故障。 | 遇到假 CORS、旧前端哈希资源、只在 Vercel 出现的 Prisma SQLite 故障，或 CLI 与线上状态不一致时。 | `请用 vercel-deploy-hardening 帮我排查这个 Vercel 线上异常` |

## 本次更新

本次已按当前机器上的 `C:\Users\Administrator\.codex\skills` 实际目录重新核对并补齐漏列 skill：

`bilibili-blogger-deep-capture`、`bilibili-cdp`、`douyin-blogger-deep-capture`。

同时将已不存在的旧条目 `douyin-profile-cdp` 更正为当前实际存在的 `douyin-blogger-deep-capture`，并把顶部唯一 skill 统计更新为 69。

## 补充说明

| 项目 | 说明 |
| --- | --- |
| 自动触发 | 如果你的需求和某个 skill 的描述高度匹配，Codex 可能会直接自动使用它。 |
| 显式点名 | 最稳妥的方式是在请求里直接写 skill 名称，例如 `请用 review ...`、`请用 docx ...`。 |
| 文件类 skill | `docx`、`pdf`、`pptx`、`xlsx` 这类 skill，最好在请求里明确输入文件、输出格式和交付物。 |
| 规划类 skill | `office-hours`、`autoplan`、`plan-*`、`design-consultation` 更适合在编码前先用，能减少返工。 |
| 浏览器类 skill | `gstack`、`browse`、`playwright`、`open-gstack-browser`、`setup-browser-cookies` 适合搭配使用。 |
| 去重规则 | 本目录里 `gstack-upgrade` 存在两个同名实现目录，但 catalog 按 `name` 去重，只保留一个条目。 |
| 目录范围 | 本文件只统计 `C:\Users\Administrator\.codex\skills` 下递归找到的 skill，不包含插件缓存目录和其他外部仓库中的 skill。 |

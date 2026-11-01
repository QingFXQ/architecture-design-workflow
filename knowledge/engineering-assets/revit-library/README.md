> 公开版不附带原生资产库。下文数量与验证为历史记录；使用前准备有权使用的文件并设置 `REVIT_ASSET_ROOT` 或 `--root`，详见 [环境接入](../../../docs/SETUP.md)。本机路径仅为示意。

# Revit 原生工程、项目样板与族文件数据库

本库已有真实文件，不再只有工程经验文档。二进制及生成索引放在本机 **`./local/resources\Revit-Asset-Library`**；仓库只维护采集程序、来源、调用方法和验证摘要。换机器可以改 `REVIT_ASSET_ROOT` 或传 `--root`，不把 E 盘路径写成所有人的强制设置。

双击本机库内 **`浏览原生工程与族库.html`**，可搜索中文用途、筛选文件种类和宿主版本、查看原文件内嵌预览。数据库为 **`database/revit-assets.sqlite`**，另有 `manifests/inventory.csv` 和 `assets.json`，可用表格软件查看。

## 已收录的原件

2026-10-30 实际盘点：

| 类别 | 原生文件数 | 内容与用途 |
| --- | ---: | --- |
| 可载入族 RFA | 2,583 | 官方米制门窗、家具、幕墙相关族、结构柱梁、图框、注释、详图及机电；包括官方样例族和中文预制族 |
| 项目样板 RTE | 16 | 中文建筑／施工／结构／机电样板及英文米制、商业、住宅、概念样板；保留原文件身份 |
| 族样板 RFT | 125 | 中文与英文米制作者样板，用来新建族，不是可以直接载入项目的族 |
| 工程样例 RVT | 20 | 13 个 2021 安装样例＋7 个 Snowdon Towers 多专业工程 |
| 配套类型目录 TXT | 272 | 随对应族保留同名文件，不只拿 RFA 丢掉类型目录 |
| 比赛参考 PDF | 4 | CIC 2024 冠军、两支并列亚军的原海报及主办方获奖公告，共 17 页；不计入原生工程数 |

原生文件共 **2,744 个、约 2.06 GiB**；其中 2,737 个的文件版本为 2021，7 个为 2024。原生文件和辅助目录均保留来源层级，不写入 Git。实际数量及错误记录见 [verification.json](verification.json)。

## 先用哪些

| 当前问题 | 建议原件 | 读取／借鉴范围 |
| --- | --- | --- |
| 新建中文建筑工程 | `originals/Autodesk-2021-Templates-CHS/DefaultCHSCHS.rte` | 从样板创建工作项目；核项目单位、文字和线型，按本次任务调整 |
| 学习一套工程如何成图 | `originals/Autodesk-2021-Samples/rac_advanced_sample_project.rvt` | 看原生构件、视图、图纸之间如何组织；不是照搬住宅／学校功能 |
| 建筑与结构、设备如何协同 | 同目录两份 `BIM_Projekt_Golden_Nugget-…rvt` | 保留相关文件一起另存；链接、共享坐标、明细表需在工作副本核实 |
| 学习较新的完整多专业工程 | `originals/Autodesk-Snowdon-2024/` 七个原文件 | 建筑、电气、幕墙、暖通、给排水、场地、结构；需要 Revit 2024 或更新版本，不可在 2021 打开 |
| 门、窗、桌椅、结构构件 | 搜索 `门`／`窗`／`家具`／`结构梁` | 先读族类别、类型尺寸与宿主；复制选中 RFA 及同名 TXT，载入工作项目做一个实例 |
| 自制门窗或注释族 | 搜索 `族样板` 并筛 RFT | 从相应宿主和类别样板开始，避免用通用几何冒充门窗或楼梯 |

墙、楼板、屋顶及部分楼梯是系统族，通常在 RTE／RVT 中复用，不能要求所有建筑对象都有独立 RFA。RFT 是作者样板，RTE 是项目起点，RVT 是工程示例，索引不会混为同一种“族文件”。

## 给 Agent 的直接调用

在仓库根目录运行，Python 解释器按当前环境选择：

```powershell
python tools/revit_assets/library.py search "窗" --kind family --revit 2021 --limit 6
python tools/revit_assets/library.py search "工程模板" --kind project_template --revit 2021
python tools/revit_assets/library.py search "Snowdon" --kind project --revit 2024
python tools/revit_assets/library.py types --id <检索结果的id>
python tools/revit_assets/library.py stage --id <检索结果的id> --dest ./local/resources\Temp\Revit工作副本 --revit 2021
```

`search` 默认筛到 2021 可打开的已知版本；需要其他宿主就传真实年份。`--all-versions` 只供研究。`types` 读取 PartAtom 已公开的类型参数、数值及其显示单位；它不能提供所有实例约束、所有宿主规则或认证性能。`stage` 复制原件与关联类型目录，重跑不增加副本，不覆盖已改动的工作文件；工程链接需要把同组模型一起复制。

调用顺序是 **任务／类别 → 版本过滤 → 看预览与类型 → 工作副本载入／新建 → 小样对象和图面核验 → 扩展使用**。不要求把整库载入项目，也不要求先浏览上千张缩略图。性能参数、耐火等级必须有适用证明；不能给普通门改个名字就当甲级门。

## 比赛资源的实际边界

- **已取得**：[CIC BIM Competition 2024 官方获奖作品页](https://www.bim.cic.hk/en/events/page/winning_entries_2024)发布的冠军 Polyers、亚军 B Impressive、亚军 HKMU 原海报。获奖身份由主办方公告交叉核实。用于研究工程协同、信息组织和作品表达，**不是公开的 RVT／RTE**。
- **已核奖项、待申请模型**：清华 BIMNet，buildingSMART openBIM 2025 学生研究获奖项目。原始数据涉及 Matterport 授权与申请，GitHub 的作者代码许可不等于模型数据许可。登记入口，不自动提交个人信息或代发申请。
- **待核线索**：第三方“亚泰图书馆龙图杯”网盘页面，奖项与复用权未独立确认且下载设验证门槛；WorldSkills 官方数字建造竞赛，目前未取得公开原生工程。均不进入默认可用工程结果。

“最厉害”落实为有来源的完整工程和获奖证据，不以网盘标题或模型体量作质量判断。不能把官方基础族说成冠军团队自制族，也不能把赛事要求 PDF 说成获奖模型。

三套已取得海报的具体可借鉴内容见[比赛文件阅读](competition-readings.md)，后续结合官方工程看实际对象和图纸组织。

## 验证层级与维护

本轮所有 2,744 个文件核过 Revit OLE 文件头、`BasicFileInfo` 年份并计算 SHA-256；可读族提取 `PartAtom` 的真实类别／类型及参数，无法读取的字段留空或标来源推断。提取 2,744 个内嵌预览，并人工查看代表族与 20 个工程预览。版本取文件本身，不取下载页面年份。

**尚未逐件在 Revit 打开、载入和成图**。当前状态 `native-container-verified`，不能提升为 `host-verified`。本轮没有修改当前打开的用户项目。使用时在工作副本检查类型、单位、宿主切割、可见性和目标图面；安装样板不是已经按某课程仿宋／纸幅等要求定制过的模板。

新增资源维护 `sources.json`，保存主办方／作者链接、实际文件版本、获取方式和权限状态。下列采集只在明确需要更新资源时执行，不作为每次画图的前置步骤：

```powershell
python tools/revit_assets/library.py collect-local
python tools/revit_assets/library.py collect-web
python tools/revit_assets/library.py build
python tools/revit_assets/library.py browser
```

采集不会安装／升级 Revit。旧版不能直接打开新版原生文件，不以改扩展名、改年份或 IFC 中转冒充无损降版。

测试与依赖说明见 [工具说明](../../../tools/revit_assets/README.md)。

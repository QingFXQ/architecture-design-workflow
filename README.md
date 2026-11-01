# Architecture Design Workflow · 建筑设计智能体工作流

把任务书、场地、案例研究、可编辑模型、工程图和最终展板连成一条能实际执行的制作流程。适合建筑课程设计与非商业学习实践；可从零开始，也可接续已有 Blender／SketchUp／Revit／CAD 方案。

**第一次使用：读本页 → 让智能体读 [AGENTS.md](AGENTS.md) → 提供任务书与项目目录 → 从当前阶段开始制作。** 可直接复制[启动提示词](prompts/START_HERE.md)。

仓库提供工作方法、技能文档、案例笔记、检索与检查脚本。设计软件、模型服务和 MCP 连接由使用者自己的环境提供；下载仓库不会自动安装或连接软件。

## 1. 使用前准备

| 必需／可选 | 需要准备 | 用途 |
| --- | --- | --- |
| 必需 | 能读写本地文件的智能体、独立项目目录 | 读取资料、维护当前进度和交付物 |
| 必需 | 任务书、场地资料、已有成果、最新要求 | 确定边界；缺项登记，不凭空定尺寸 |
| 按制作路线 | Blender 或 SketchUp；Revit 或 CAD，以及可用的连接／脚本入口 | 建模、制图、导出和看图；按项目选择，无需全部具备 |
| 运行脚本时 | Python 3.10+ | 基础离线检索与清单检查，无需模型服务 |
| 按需 | 图像生成、PDF 渲染、DXF、原生族库、语义检索依赖 | 对应任务需要时再配置 |

没有软件连接时，可先读任务书、整理功能面积、核场地、研究案例和准备版面容量。只能把实际未完成的建模、出图列为待办。软件已打开也不代表连接可用，须查询当前软件、文件和版本。

## 2. 五步上手

### 第一步：取得仓库

```bash
git clone https://github.com/QingFXQ/architecture-design-workflow.git
cd architecture-design-workflow
```

也可选择 GitHub 的 **Code → Download ZIP**，解压后让智能体读取该目录。仓库与实际设计项目分开放置；已有项目无需搬家。

### 第二步：把项目交给智能体

提供仓库位置、项目目录、任务书／场地文件、已有模型、当前目标及不能改变的内容。新项目按[项目模板](templates/PROJECT_TEMPLATE.md)建立简短 `PROJECT.md` 和 `BRIEF.md`；已有记录直接沿用。

若工具只自动读取项目根目录的 AGENTS.md，把[项目入口模板](templates/PROJECT_AGENTS.md)合并进去并填写工作流仓库真实路径，保留原指令。不能自动发现 AGENTS.md 的工具，在对话中明确要求先读。

### 第三步：检查本次需要的环境

先列实际可用文件、软件版本和连接，只读确认活动模型与指定文件一致。参考[环境接入](docs/SETUP.md)。不照搬作者机器的路径、IP、端口、族 ID 或历史部署结论。

### 第四步：选择当前起点

按下表从已有成果接续。方案已定就核尺寸并深化，工程已建就接着制作；不强迫重做概念、重建模型或逐项重复审批。

### 第五步：实际制作，持续记录

在授权范围内连续研究、设计、建模、看图修正和保存。重要批次留下当前源文件、相关图面证据、未完成项及下一动作；工具成功或零警告不能视为完成。

## 3. 整个工作流如何运转

```text
任务书＋真实场地＋最新反馈
  → Blender／SU 可编辑概念与方案
  → 核尺寸、功能、流线、结构、场地和面积口径
  → Revit／CAD 代表样板 → 成套标准平立剖与总平
  → Blender 深化立面、室内外空间与表现基底
  → 真实排版参考 → 实际纸面预案 → 按需分析图
  → 同版图件汇总 → PDF 渲染检查 → 交付封版
```

这是制作依赖顺序，允许回到模型修改；Blender／SU 全程可用。当前智能体连续负责，`agents/` 是能力参考，不要求多智能体接力。详见 [PIPELINE_WORKFLOW](workflows/PIPELINE_WORKFLOW.md)。

| 阶段 | 实际工作 | 进入下一步的依据 |
| --- | --- | --- |
| 任务与场地 | 提取必交图、纸幅／比例、功能面积；核单位、北向、尺寸、入口与高差 | 项目记录、可信基准和明确未知项 |
| 概念与方案 | 在可编辑模型里组织体块、功能、结构概念、连续交通与主要空间；按需查案例 | 当前模型、代表平剖／三维、设计取舍；假设与冻结项分开 |
| 尺寸校准 | 核轮廓、层高、轴网、交通核、洞口、场地定位及面积差额 | 可追溯几何基准；建筑／楼板／净面积和目标／估算／实测分列 |
| 工程制作 | 取相关技能与工程样例；典型原生构件和代表平剖看图通过后扩展 | 可编辑图纸源、实际对象与完整图面核验 |
| 表现深化 | 核多软件坐标；设计亮点、立面、材料与机位；AI 从真实底图润色 | 对应版本模型和图像；建筑改动同步受影响图纸 |
| 排版与分析 | 看真实参考，按最终毫米放必交图，再做解释设计的分析 | 可读板面预案、真实空间／流线分析 |
| 最终交付 | 核齐图件、比例、字体、标高及版本；渲染 PDF 看整板与局部 | 当前有效 PDF、源文件和限制；用户接受后封版 |

优先解决**结构、功能、主流线与空间审美**。家具合理整齐、不穿墙堵路，深度服从任务书。总平和地形来自真实资料；AI 图像不得悄悄增加楼层、结构或开口。

## 4. 按问题找入口

| 当前任务 | 先读 |
| --- | --- |
| 从零或接续方案 | [概念](workflows/CONCEPT_WORKFLOW.md)、[全程模型](workflows/CONTINUOUS_MODEL_WORKFLOW.md) |
| 研究空间／场地问题 | [案例研究](docs/RAG.md)、[建筑案例库](knowledge/architecture-case-rag/README.md) |
| Revit／CAD 制作 | [制图生产](workflows/DRAWING_PRODUCTION_WORKFLOW.md)、[工程资产](workflows/ENGINEERING_ASSET_WORKFLOW.md) |
| 找方法、族、模板或恢复故障 | [技能索引](docs/SKILL_LIBRARY.md)、[原生资产](knowledge/engineering-assets/revit-library/README.md) |
| 效果、展板和分析图 | [表现排版](workflows/PRESENTATION_WORKFLOW.md)、[排版案例](knowledge/presentation-cases/README.md) |
| 反馈、经验和交付复核 | [反馈](workflows/FEEDBACK_WORKFLOW.md)、[维护](workflows/SKILL_MAINTENANCE_WORKFLOW.md)、[交付检查](tools/delivery/README.md) |

只读命中的技能和必要参考，不一次加载所有文档。旧 Gate、固定角色和机器配置的历史记录不覆盖当前主线。

## 5. 不连接软件也能试用

在仓库根目录执行。Windows 若没有 `python` 可用 `py -3`，macOS／Linux 可用 `python3`：

```bash
# 工程方法：离线检索，不执行建模
python tools/engineering_assets/find_asset.py --software revit --task "门切不开墙"

# 首次构建文字元数据索引，再离线检索；不下载模型
python knowledge/architecture-case-rag/scripts/build_index.py
python knowledge/architecture-case-rag/scripts/search_cases.py --mode lexical --query "图书馆夜间独立开放" --max 3

# 排版参考：返回来源和方法，不下载图片
python tools/presentation_cases/find_case.py --query "竖版 主图"

# 检查方法索引
python tools/engineering_assets/find_asset.py --check --self-test
python tools/presentation_cases/find_case.py --check
```

基础检索使用 Python 标准库。语义检索、DXF 样例和 PDF 检查的可选依赖见[环境接入](docs/SETUP.md)。

## 6. 资料与公开版本边界

公开版包含工作流、技能、自写方法笔记、来源链接、脚本和样例；不附带私人任务书、学生身份、课程 RVT、聊天／交接日志、模型缓存或完整第三方资产库。历史数量和验证记录不代表新机器已部署或新项目已完成。

Revit 原生库需自行准备有权使用的文件，设置 `REVIT_ASSET_ROOT` 或 `--root`。案例原图、文章、字体和上游软件仍归各自权利人；详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

图书馆两张竖 A1、仿宋等档案是可选项目预设。新任务以自己的任务书与教师要求为准，不继承身份、精确指标或项目尺度。

## 7. 目录与维护

| 目录 | 内容 |
| --- | --- |
| `workflows/` | 制作主线、迭代与交付方法 |
| `skills/` | 按任务选读的设计、工程与表现技能 |
| `knowledge/` | 案例笔记、操作卡、来源与样例 |
| `tools/` | 检索、检查与可选接入辅助程序 |
| `templates/` | 项目入口、进度与交付清单模板 |
| `prompts/`、`agents/` | 启动提示词、专项提示词与能力参考 |
| `research/`、`benchmarks/`、`docs/` | 方法研究、验证记录与详细说明；历史文档明确降级 |

反馈落到原流程／技能和相关样例，注明验证范围；不将离线测试冒充宿主验收。课程设计不等于结构计算或正式审图。见[贡献说明](CONTRIBUTING.md)。

## 8. 许可：公开源码，非商业使用

自有代码、工作流、提示词和文档采用 [PolyForm Noncommercial License 1.0.0](LICENSE)。允许许可范围内的非商业学习、研究、使用、修改与分享；分发保留许可及 Required Notice。商业用途需另行取得权利人授权，具体以许可全文为准。

含非商用限制，因此这是 **source-available（源码公开）** 项目，不宣称符合 [OSI 开源定义](https://opensource.org/osd)。第三方组件继续遵循各自许可。

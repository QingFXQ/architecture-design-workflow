# 案例检索如何帮助实际设计

建筑方法用本页的案例库；展板／图组／主次与背景参考用[排版案例库](../knowledge/presentation-cases/README.md)。两者都要求看原始图面、迁移具体方法，不用检索数量或写卡代替实际设计。

案例库是可检索的设计笔记。它服务当前问题，不要求每个阶段重新检索，不用“搜了多少篇／写了多少卡”证明设计完成。

## 什么时候用

遇到具体矛盾、缺少可比较方法、用户要求找案例时使用。已有足够依据的局部修改可以直接做；没有命中不强凑案例，也不默认停止整个设计。

例如：高处入口如何连到水岸公共活动、开放内梯如何与三层阅览带形成整体、夜间自习如何独立运营、两个体量如何通过结构／立面接口协调。

## 实际工作链

1. 写出当前问题与不可随意改变的条件；复合问题按需要拆开，不固定要求2—4条。
2. 本地检索少量相关方法；用户给定参考优先仔细解读，必要时websearch补案例及图纸。
3. 真正打开相关来源、平剖／照片判断，记录哪些是原文事实、图面可见、推断或资料缺失。文字检索命中不等于已经读懂图片。
4. 把可迁移方法在Blender／SU工作模型或平剖草案中试出来，按本项目场地、功能、流线与空间判断。
5. 在现有DESIGN_THESIS／任务记录简短记“问题—来源—操作—模型／图面位置—采用或淘汰理由”。不强制新交接卡、固定案例数或人工批准步骤。

研究和建模可来回迭代，见[全程工作模型](../workflows/CONTINUOUS_MODEL_WORKFLOW.md)。

## 本地工具

```powershell
# 默认auto：尝试章节语义，服务／索引不可用则明确回退离线文字检索
python knowledge/architecture-case-rag/scripts/search_cases.py --query "夜间独立开放如何设置入口与闭馆边界" --max 3

# 不需要Ollama，直接文字匹配及少量设计同义词；不冒充语义或看图
python knowledge/architecture-case-rag/scripts/search_cases.py --mode lexical --query "高差台地与滨水公共活动"

# 旧精确筛选仍保留，不接受自然语言query以免忽略问题
python knowledge/architecture-case-rag/scripts/search_cases.py --mode baseline --problem topography

# 明确要求语义／hybrid时，失败就报错，不静默换方式
python knowledge/architecture-case-rag/scripts/search_cases.py --mode semantic --query "开放楼梯与阅读空间"
```

语义检索依赖embedding：案例索引和查询必须使用匹配的模型／维度。当前预设为qwen3-embedding:0.6b。lexical是明确标记的回退，不是用关键词冒充语义RAG。auto查询有界，不通过一个检索请求暗中安装或启动软件。

**未来正式部署允许安装必要的小型embedding模型和依赖，不因它是本地模型就当高负载重复询问。** 先核已有环境／缓存；下载到用户指定数据盘，复用已有模型，不顺带装大模型或重排服务。阅读／修改仓库文档不等于授权在当前电脑部署。本机模型和缓存统一放在 `./local/resources`（模型 `Ollama\models`，缓存 `Cache`），不继续新增到C盘或D盘；其他机器按其用户指定目录配置。项目源文件留在项目目录。已有模型迁移须经用户授权、校验后清理原件，活动聊天数据库待应用退出后迁移。

lexical标明文字证据和未查看图纸，缺口不作正面证据；它可能只部分相关，需要实际阅读。图面URL不等于看过图，任何模式都不能自动替代设计判断。

`--format card`保留兼容，便于需要时归档证据，不再是每轮必填关卡。已有标签与原案例字段保留。参数与索引细节见[案例库README](../knowledge/architecture-case-rag/README.md)。

## 资料边界与改进方向

2026-10-28核查：128份案例、1881段文字索引；14份带library标签。数字是本次快照，未来按文件统计。

部分图种字段不统一、部分案例缺关键图纸／尺度／运营资料；星级不是内容都齐全的保证。图片URL不是本地已验证图纸。遇到问题按需要补原始证据，不复制无来源的完整案例叙述。

本地库适合复用已知案例与既有分析；websearch适合补缺和找新方向。资料不足时可以提出明确标注的设计假设并建模试验，但不能把假设写成案例事实或规范结论。

工程操作问题另走[工程资产入口](../workflows/ENGINEERING_ASSET_WORKFLOW.md)，不要用建筑案例代替Revit／CAD的宿主、约束和打印知识。

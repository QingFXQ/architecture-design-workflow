# 工程资产怎么真正用到画图

适用于Revit与原生CAD任务，不依赖独立Agent身份，不新增Gate。目标是用已有工程方法和小样减少重写、误判及返工，而不是增加资料阅读量。

## 开工入口

1. 用当前具体任务查[工程资产索引](../knowledge/engineering-assets/catalog.json)；可直接看条目，也可运行：
   `python tools/engineering_assets/find_asset.py --software revit --task "门切不开墙"`
2. 先读命中的操作卡与所指向的相关段落，只取当前需要的例子。没有匹配就说明缺口，不宣称已有工程资产。
3. 区分对象方法和调用工具：API可以创建原生墙／楼板，并不因为“用了代码”就属于几何替代；也不能把DirectShape外观相似当作原生构件。
4. 需要RFA／RFT／RTE／RVT时，直接查[原生工程与族数据库](../knowledge/engineering-assets/revit-library/README.md)，按真实宿主版本筛选，选中后复制工作文件与类型目录。先看类别／类型及代表预览，再在工作副本核宿主、单位与目标图面；不凭文件名假定兼容。DWT／DWG资产仍须按实际取得情况说明。
5. 执行前只确定与结果有关的类别／宿主／约束、单位、编辑范围和预期图面；用已核小样扩大应用。不是重新走一整套审计。
6. 修改后读真实对象并实际看相关图面；新增信息只简短写入现有任务记录：用了什么／做了什么／如何确认／还缺什么，不另造交接包。

## 证据等级不能混淆

- **reference-reviewed**：方法及来源已检查，不等于软件运行通过。
- **project-evidence**：有本项目历史记录，注明软件／版本和限制；不自动算新项目已验证。
- **offline-tested**：脚本在真实文件上生成、读回或渲染过；不等于AutoCAD／Revit宿主验收。
- **native-container-verified**：实际取得Revit原生文件，核过容器、版本、哈希和可提取元数据；仍不等于逐件打开／载入／出图通过。
- **host-verified**：在指定宿主版本实际执行并核对象＋图面，有对应证据才使用。
- **unverified**：待核，不进入默认生产操作。

索引只返回少量相关路径与等级，不全文塞进上下文，不安装嵌入模型或建立新服务。

## 反馈回流

发现旧条目错误时修订原条目及其示例／检查表，不只在项目里再放一份冲突补丁。保留来源和修正边界。项目端口、ID、课程字体、纸张和性能阈值不直接提升为通用规则。

读了skill不算“应用完成”。小样尺寸、洞口／约束、视图表达或PDF中真实可见效果才是证据。

## 当前资产边界

[CAD可运行小样](../knowledge/engineering-assets/examples/cad-parametric/README.md)演示DXF墙线真实断口、20窗共享块、柱网、尺寸和离线预览。它没有通过AutoCAD宿主验收，也不是完整施工图模板。

Revit方法优先复用已有[revit-expert](../skills/revit-expert/SKILL.md)与修订后的[model-hardening](../skills/revit-model-hardening/SKILL.md)；原生内容使用[RV-05](../knowledge/engineering-assets/cards/RV-05-native-library.md)。本库没有把图书馆RVT冒充通用模板，也没有修改用户当前打开的项目。AutoCAD正式制作读[cad-production](../skills/cad-production/SKILL.md)。

## 2026-10-28落地状态

- 首批8类操作卡，指向已有工程资料和新CAD样例；12个来自实际失败／任务的检索场景通过离线测试。
- 旧model-hardening、API笔记、图形参考与检查表同步纠错，稳定检查项编号保留；既有Revit技能、CAD技能、生产提示词、项目模板和本仓库AGENTS均有入口。
- CAD小样8项离线检查通过：真实读回、共享定义、墙开口、标注显示、重跑不增长、改参数更新、保护非本任务文件和单位拒错；已实际打开PNG检查。结果在[VERIFICATION.json](../knowledge/engineering-assets/examples/cad-parametric/VERIFICATION.json)。
- 此阶段尚无Revit／AutoCAD宿主重验，Revit二进制缺口已于下段更新；DWT／DWG原生工程资产仍未补齐。不把后来的离线采集算成本阶段宿主验收。
- 2026-10-29已整合为单主控与全程模型主线；本段旧工程测试日期仍保留。新增[制图生产流程](DRAWING_PRODUCTION_WORKFLOW.md)、[技能库索引](../docs/SKILL_LIBRARY.md)和[反馈回写](SKILL_MAINTENANCE_WORKFLOW.md)。不自动提交或推送仓库。

## 2026-10-30原生库落地

新增RV-05，主库在E盘，共2,744个原生文件：2,583 RFA、16 RTE、125 RFT、20 RVT；附272个类型目录和CIC比赛4份官方参考PDF。可按中文用途、类别与版本检索，并复制带类型目录的工作文件。7个2024版Snowdon项目与2737个2021文件分开筛选。完整来源、数据库、验收边界与后续入库方法均在[原生库入口](../knowledge/engineering-assets/revit-library/README.md)。

后续任务用已有索引选材，不反复复制整库、重新下载或全量读取参数。对首次使用的族／模板做相关小样核验，把实际宿主版本与结果回填；未取得的比赛原生模型只登记候选，不混入可用资源。

# 工作区使用说明

当前执行依据是[主流程](../workflows/PIPELINE_WORKFLOW.md)、用户最新要求和项目当前文件。本仓库支持从概念到工程图、表现和PDF；不要求部署多Agent平台才能使用。

## 开始一个项目

1. 用[项目模板](../templates/PROJECT_TEMPLATE.md)记录任务书、场地、交付与当前依据文件；简单项目无需九份台账。
2. 在Blender或SU实际研究体块、空间和功能，截图自查，再按需AI预览；案例用[RAG／websearch](RAG.md)补充。
3. 确定方案后核尺寸、场地坐标／标高、主要功能与面积口径；采用[制图流程](../workflows/DRAWING_PRODUCTION_WORKFLOW.md)和[工程资产](../workflows/ENGINEERING_ASSET_WORKFLOW.md)，在Revit或CAD制作标准建筑图。
4. 导出Blender继续立面、场地与表现，变化同步受影响图件；真实底图后再AI润色。
5. 看优秀[排版案例](../knowledge/presentation-cases/README.md)，先做板面预案再选分析图，最后按[表达交付流程](../workflows/PRESENTATION_WORKFLOW.md)输出PDF。
6. 从实际故障和用户反馈更新[skill库](../workflows/SKILL_MAINTENANCE_WORKFLOW.md)。

## 目录与状态

`agents/`是能力说明，`skills/`是按需操作方法，`knowledge/`是案例／经验／样板索引，`tools/`是辅助程序，`templates/`是可选起步材料。当前主控可全部执行；历史角色和Gate不再自动生效，见[协作方式](TEAM_ARCHITECTURE.md)。

资料存在、离线脚本通过、项目曾使用、当前宿主实测是不同事实。[TOOLS](TOOLS.md)和各工具验证文件记录边界，不凭安装提示词、历史时间点或工具数量宣布本机可用。

SketchUp与AutoCAD部署提示词已收录，只有未来明确要求本机部署才执行。没有SU就用已有Blender，不因流程建议安装所有软件。小embedding模型在实际部署任务中可安装，文档修改不等于部署任务。

本用户新增缓存和模型使用 `./local/resources`；项目源文件和交付跟随其项目目录，其他使用者按其指定磁盘。大日志、向量索引和base64只输出摘要。

## 自动化能检查什么

工程资产检索工具定位方法，RAG定位案例证据，[交付检查工具](../tools/delivery/README.md)检查清单、修订、纸幅和基本打印参数；它们不代替实际看模型、看整图和建筑判断，也不会自动批准历史Gate。

本轮修订依据与已验证内容见[实战修订记录](WORKFLOW_REVISION_20261029.md)。旧部署、旧验收和历史项目记录保留原日期，不伪装为2026-10-29重新运行的结果。

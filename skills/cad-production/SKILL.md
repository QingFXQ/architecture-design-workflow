---
name: cad-production
description: 在原生CAD或DXF中制作、接手和修改建筑平立剖、图块、标注与布局发布，按任务复用工程经验及参数化样例。不是安装工具或强制转换Revit模型。
---

# CAD建筑制图：先用工程资产，再选操作工具

按用户、任务书和交付选择CAD路线，不要求先建Revit。若本机无CAD，可制作并验证DXF，明确DWG／宿主未测。

## 任务入口

先用[工程资产索引](../../workflows/ENGINEERING_ASSET_WORKFLOW.md)找当前问题，不全文读取所有资料：

- 接手DWG／场地坐标／缺字体：[CAD-01](../../knowledge/engineering-assets/cards/CAD-01-intake.md)。
- 墙线、重复窗块与尺寸：[CAD-02](../../knowledge/engineering-assets/cards/CAD-02-parametric.md)，含可运行DXF小样。
- 布局／比例／线宽／PDF：[CAD-03](../../knowledge/engineering-assets/cards/CAD-03-layout-plot.md)。
- AutoLISP／SCR／重复执行／格式交换：[CAD-04](../../knowledge/engineering-assets/cards/CAD-04-batch-exchange.md)。

连接缺失且用户要求部署时再读[AutoCAD部署提示词](../../prompts/AUTOCAD_MCP_DEPLOYMENT.md)，普通绘图不自动重装。

## 做工程的必要决定

- 先核当前文档、真实单位、坐标／UCS、源图与版本，保护外参、块、图层、标注及未保存工作。
- 绘图方式按任务选择：MCP查询／交互，Python参数与批量DXF，AutoLISP／SCR／已验证API在宿主内操作。重复构件优先块／阵列，不发数百次单实体调用。
- 图层不替代块／组组织；共享定义按规格复用。门窗在平面墙线形成真实开口，楼梯上下方向与相邻层对得上，不用遮挡假装完成。
- 修改范围稳定可识别，重跑不叠加，不整图清空；修改已有用户DWG前建立合适恢复点。
- 样例不是正式建筑方案；按当前参数修改，实际读回实体、开口和尺寸，再查看整张图。
- 模型尺寸、视口比例、纸面文字及打印缩放分开处理。用项目制图要求，不把图书馆课程字体／双线预设硬编码到所有项目。
- DXF与DWG能力分开；离线PDF渲染不等于AutoCAD发布已验证，文件非空不证明完整。

图形语言沿用[drawing-standard](../drawing-standard/SKILL.md)适用部分；其Revit专属检查不套用到纯CAD。此入口不新增独立Agent或人工审批。

按当前问题取用[CAD工程绘图经验](references/architectural-drawing-lessons.md)，包含图层、Block、真实墙断口、标注和布局发布。

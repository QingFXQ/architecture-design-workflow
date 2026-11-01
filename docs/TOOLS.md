# 工具与证据边界

2026-10-29为工作流整理，不是所有软件重新部署／验收。旧版本、工具数量、端口、机器和测试记录见[原清单](history/pre-20261029/docs/TOOLS.md)，不得当作本机当前状态。

| 工具／路线 | 当前仓库具备什么 | 使用时怎样确认 |
| --- | --- | --- |
| Blender | 研究资料、持续工作模型／表现流程；真实项目已有操作反馈 | 查当前版本、插件及活动文件，截图和对象一起核；设计可从概念开始 |
| SketchUp | 部署提示词、选型、固定上游安装包／探针与离线工具发现记录 | 用户要求实际部署后查最新稳定版、Ruby Bridge和真实宿主；本轮未安装SU |
| Revit | 原生构件／视图／导出资料，model-hardening，真实项目经验 | 查实际宿主／连接／文档与相关操作小样；不把历史26工具清单或8080端口硬编码到所有环境 |
| AutoCAD | 通用部署提示词、CAD技能及工程操作卡 | 区分完整版／LT和实际后端；提示词收录不等于已安装或已跑DWG |
| Python＋DXF | 可运行参数化样板、共享窗Block、读回／PDF／PNG验证 | 参看样板VERIFICATION；离线通过不等于AutoCAD发布验收 |
| RAG | 本地案例和auto检索，语义不可用时明确离线文字回退 | 使用--query；具体说明见[RAG](RAG.md)，不要求常驻服务或每阶段写卡 |
| 图片生成／超分 | render-fidelity与真实模型基底流程 | 用当前可用工具；不规定某个旧模型已部署，生成后看几何／文字／直线 |
| PDF | 表达流程和交付检查工具；PyMuPDF可作实际纸幅／字体检查 | 用安装环境真实运行并渲染看整版和局部，清单成功不代表美感通过 |

## 本地部署模板

[SketchUp MCP](../prompts/SKETCHUP_MCP_DEPLOYMENT.md)、[AutoCAD MCP](../prompts/AUTOCAD_MCP_DEPLOYMENT.md)。未来部署先查上游最新README／release、已有软件与配置，再备份、安装和真实验收。保留Python、PowerShell和宿主脚本能力，不逐个MCP创建大量重复构件；SU不假定有Blender式后台模式。

## 已有检索与检查程序

- [工程资产](../workflows/ENGINEERING_ASSET_WORKFLOW.md)：`python tools/engineering_assets/find_asset.py --software revit --task "门切不开墙"`。
- [排版案例](../knowledge/presentation-cases/README.md)：`python tools/presentation_cases/find_case.py --query "竖版 主图"`。
- [交付检查](../tools/delivery/README.md)：`python tools/delivery/check_delivery.py path/to/DELIVERY.json`。
- 旧studio_state／项目插件的Gate字段按其历史项目使用；它们不是新项目必填流程，不用旧字段阻断当前生产。

## 资源位置

本机新增模型／依赖缓存／大临时文件使用./local/resources；工程与交付文件仍跟随项目。已有路径可能是到E盘的兼容链接，先核实际目标，不能重复复制。缓存迁移不会自动终止当前软件，活动Codex数据待退出后迁移。

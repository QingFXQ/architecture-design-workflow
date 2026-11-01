# 环境接入：先读取与检索，再按需连接软件

## 基础环境

能读写文件的智能体即可使用工作流。Python 3.10+ 可运行基础检索与清单检查。本仓库不绑定智能体品牌，不附软件许可证、云端 API 权限或已配置 MCP 服务。

先读任务书、项目记录和当前目标，再选本次所需软件。没有 Revit 仍可从 Blender／SU 设计，也可按用户允许用 CAD 制图；要求原生 BIM 的任务则不能以网格替代。

## 按路线接入

| 路线 | 使用前实际核实 | 入口 |
| --- | --- | --- |
| Blender | 版本、连接／脚本入口、活动 blend、单位与对象、视图获取 | [全程模型](../workflows/CONTINUOUS_MODEL_WORKFLOW.md)、[工具边界](TOOLS.md) |
| SketchUp | 软件版本、Ruby 插件、实际宿主通信；不假定后台模式 | [部署提示词](../prompts/SKETCHUP_MCP_DEPLOYMENT.md)、[集成](../tools/sketchup-mcp/README.md) |
| Revit | 宿主年份、连接、活动工程路径、只读查询；核族／宿主／事务封装 | [revit-expert](../skills/revit-expert/SKILL.md)、[接入参考](../tools/revit-mcp/README.md) |
| CAD | 完整版／LT 差异、DWG／DXF、图层单位、导出与打印 | [cad-production](../skills/cad-production/SKILL.md)、[部署提示词](../prompts/AUTOCAD_MCP_DEPLOYMENT.md) |
| 图像／PDF | 当前生成／渲染工具、输入输出路径和实际图像页面 | [润色](../skills/render-fidelity/SKILL.md)、[交付检查](../tools/delivery/README.md) |

历史文档的 Revit 2021、8080、Windows／SSH 等是某次环境证据；按当前后端官方说明核实，不复制旧主机信息。MCP 是接入选择之一，已有 CLI、API、脚本或人工导入导出同样可用。

## 按需 Python 依赖

基础工程索引、排版索引、文字案例索引使用标准库。需要 DXF 样例或 PDF 实际检查时，可在自己选择的虚拟环境按需安装：

```bash
python -m venv .venv
# 激活该环境后安装对应任务需要的依赖
python -m pip install ezdxf matplotlib PyMuPDF
```

DXF 见[参数样例](../knowledge/engineering-assets/examples/cad-parametric/README.md)，清单检查不替代 PDF 视觉审查。

## 案例检索

先运行根 README 的 `build_index.py`，再用 `--mode lexical`，无需 Ollama 或模型下载。索引由案例 Markdown 重建。语义检索按[案例库](../knowledge/architecture-case-rag/README.md)配置当前服务；`auto` 失败会明确回退文字，显式 `semantic`／`hybrid` 则需要有效索引与服务。模型和向量缓存不随公开版分发。

## 原生资产库

公开版只有方法与来源，不含完整 RFA／RVT／RTE／RFT。先准备有权使用的文件，修改 sources 的本地安装路径，按[资产工具](../tools/revit_assets/README.md)构建数据库，再指定真实目录：

```bash
python tools/revit_assets/library.py --root ./local/revit-assets search "窗" --revit 2021
```

这要求指定目录已有构建好的数据库；空目录不是资产库。年份换为宿主兼容版本。工作副本中核类别、单位、宿主和图面，原件不升级保存。

用户指定资源目录优先，未指定则选空间合适的位置并记录。源文件与交付跟随项目，恢复点与过程文件分开；不复制作者盘符，不自动迁移数据库或下载大型资源。

> 历史参考，不作为当前执行指令。以根 AGENTS.md 与 PIPELINE_WORKFLOW 为准。

# 工具接入清单

本清单区分“仓库中有资料”“已完成静态核查”“已在真实软件中验证”。未完成实机测试的工具只能作为候选链路，不能作为已可交付的生产能力。

可选部署任务模板：[AutoCAD MCP](../../../../prompts/AUTOCAD_MCP_DEPLOYMENT.md)、[SketchUp MCP](../../../../prompts/SKETCHUP_MCP_DEPLOYMENT.md)。AutoCAD可独立制图，SU与Blender可按使用者选择；不要求所有项目先经过Revit。模板收录不代表已安装或实机验证，具体流程整合仍按后续工作流修订处理。

已有工程知识按[工程资产入口](../../../../workflows/ENGINEERING_ASSET_WORKFLOW.md)使用。`python tools/engineering_assets/find_asset.py --software revit --task "门切不开墙"`返回少量相关路径与验证等级；`--check --self-test`核索引和典型任务路由。不是新MCP／RAG服务，也不访问宿主或自动执行建模。

## 1. Revit MCP

- **位置**：[`tools/revit-mcp/`](../../../../tools/revit-mcp)；上游固定浅克隆在 `tools/revit-mcp/repo/`，当前记录的提交为 `86cf7057785f2423fc0d0892c9a5d9c93deb1aa3`。
- **用途**：让执行器（Codex、DSH 或其他已配置的 MCP 客户端）经 MCP 读取 Revit 状态、创建基础构件/房间/标高/轴网/尺寸、查询材料与房间数据、标注和执行受控操作。它服务 Drawing Production，不替代 Gate B 的方案输入或 Gate C 的人工图纸检查。
- **接入方式**：Windows 上启动 Revit 插件和 `npx -y mcp-server-for-revit`。链路是 `执行器 → MCP stdio → Windows MCP server → localhost:8080 → Revit 插件 → Revit API`。执行器与 Revit 同机时直连；跨机时经 SSH stdio，且 npm server 仍须在 Revit 同一台 Windows 主机运行，不能在另一台机器直接运行后跨网连接。
- **工具数量与范围**：已从源码注册核对到 **26 个**工具：查询/过滤（`ai_element_filter`、当前视图/选择/族/材料/统计/房间数据）；创建（标高、轴网、线性、点式、面式、房间、结构框架、尺寸）；操作（元素操作、删除、着色、房间/墙标注）；项目数据 SQLite 读写；`say_hello`；以及动态 C# 执行 `send_code_to_revit`。空的 `modify_element.ts`、`search_modules.ts`、`use_module.ts` 不计为可调用工具。
- **验证状态**：2026-08-13 已在 Windows `YOUR_REVIT_HOST` 的 Revit 2021 完成插件安装、8080、26 tool discovery 与两项只读端到端验证（活动视图、模型统计）。插件实装于 `C:\ProgramData\Autodesk\Revit\Addins\2021\`。2026-10-04 至 10-19 的真实课程项目已实际使用 `send_code_to_revit` 1,771 次，创建 123 个 Room、墙/门/楼梯/家具并导出 33 页 PDF；最新回读 0 非正面积、0 warnings。这些是项目证据，**不等于 TEST_PLAN 8 项逐项验收**；正式记录仍待补。
- **每次使用**：启动 `C:\Program Files\Autodesk\Revit 2021\Revit.exe`、启用命令并点击 `Revit MCP Switch` 后，运行 `python tools/revit-mcp/scripts/smoke_revit_mcp.py`（Windows；其他平台按本机解释器调整）。两项只读检查均通过后才可进入 `TEST_PLAN.md` 的写入测试；真实项目写入不能替代该测试计划。详见 [`SETUP.md`](../../../../tools/revit-mcp/SETUP.md)、[`TEST_PLAN.md`](../../../../tools/revit-mcp/TEST_PLAN.md)。

`send_code_to_revit` 能动态编译 C#，属于高权限入口；默认只对已批准、范围明确、可回滚的 Issue 使用。Scheme 验证须遵守 [`SCHEME_DRAWING_REVIEW.md`](../../../../workflows/SCHEME_DRAWING_REVIEW.md) 的授权与回读要求；正式 Drawing 仍需 Gate B。禁止用它绕过方案确认或批量破坏模型。

## 2. Blender MCP

- **位置**：仓库的 `tools/blender-mcp/` 当前为空；可执行接入方案和证据在 [`research/blender-upscale/blender-mcp-survey.md`](../../../../research/blender-upscale/blender-mcp-survey.md)。
- **用途**：Gate C 后，将 Revit 导出的 FBX 在 Blender 中核对几何、生成 3—5 个低成本相机预览、基础光材质和渲染底图；不修改已批准的建筑几何。
- **推荐接入**：采用 `ahujasid/blender-mcp`。Windows Blender GUI 安装/启用上游 `addon.py`，其本地 socket 监听 `127.0.0.1:9876`。执行器与 Blender 同机时直接连接 `127.0.0.1:9876`；跨机时由另一台机器安装 `uv` 后用 `uvx --python 3.11 blender-mcp` 启动 MCP server，并保持 SSH 隧道：`ssh -N -L 9876:127.0.0.1:9876 仁@YOUR_REVIT_HOST`。9876 仅走 loopback + SSH，不向局域网暴露。
- **关键路径**：Windows Steam Blender 4.3 的 addons 根目录为 `/path/to/user-home Foundation\Blender\4.3\scripts\addons\`；优先用 *Edit → Preferences → Add-ons → Install…* 安装，而不是手工复制后假定已启用。Blender 内按 `N` 打开 BlenderMCP，保持 `localhost:9876` 并点击 **Connect to Claude**。
- **验证状态**：上游方案、socket 拓扑、SSH 设计和本机 Blender CLI headless 渲染能力已在调研中核实；**Windows addon、SSH 登录、MCP 端到端连接与实际 FBX 工作流均未验证**。主选 addon 不能在 background 模式充当 MCP 服务，headless 渲染可用但与 addon 服务是两件事。
- **人工动作**：安装并启用 addon，确认 Windows OpenSSH Server/防火墙仅开放 SSH，建立隧道后测试 BlenderMCP 面板连接；再由用户在 Gate D 选择候选机位或手工摆机位。

## 3. 本地超分

超分只提高输出尺寸和清晰度，不得修改建筑几何。始终保留原始 PNG，写入新文件，并在超分后检查直线、开口、楼层、柱网、文字与重复纹理。

| 档位 | 工具与位置 | 接入方式 | 验证状态 | 需要的人工决定 |
| --- | --- | --- | --- | --- |
| 最小/保守 | `waifu2x-ncnn-vulkan`；方案在 [`research/blender-upscale/upscaler-survey.md`](../../../../research/blender-upscale/upscaler-survey.md) | 下载 macOS release，CLI 用 `-n -1/-0` 和 2×或4×输出 PNG | release 与 Apple Silicon Vulkan 支持已调研；本机尚未安装/跑图 | 是否以保真和速度优先；先用一张代表图 A/B |
| 质量优先（Mac） | `chaiNNer` + PyTorch MPS | 安装 universal DMG，在 Dependency Manager 安装 PyTorch，用节点链“输入→已验证 SR 模型→保存” | 应用与 MPS 支持已调研；模型（含 4x-UltraSharp）实际加载兼容性待验证 | 是否接受节点式工作流及模型测试时间 |
| 高质量生成式细化（Windows） | ComfyUI + `4x-UltraSharp` + `ComfyUI_UltimateSDUpscale` | 权重放入 `models/upscale_models`，先确定性基础 SR，再 tile diffusion 细化 | 工作流与路径已调研；本项目 ComfyUI/权重/显存尚未实测 | 是否允许细化改变像素纹理；保留基础 SR 作为回退 |

目录 `tools/upscaler/` 当前为空；它不是已安装工具的证明。需用户先选择档位，再做单图可逆试跑并记录参数、模型、seed（如有）和输出版本。

## 4. Architecture Case RAG 检索

- **位置**：[`knowledge/architecture-case-rag/`](../../../../knowledge/architecture-case-rag)，案例在 `cases/`，来源清单在 `sources/`，字段模板在 `templates/case-template.md`。
- **用途**：按建筑问题检索可迁移的方法与证据，支持 Concept/Scheme；不是“找一张像的图”，更不是生成设计结论的替代品。
- **接入方式**：先按 [`knowledge/architecture-case-rag/README.md`](../../../../knowledge/architecture-case-rag/README.md) 使用 `scripts/search_cases.py --query`；v1 默认 section-level semantic（Benchmark 的 Recall@5/MRR 最佳），可显式 `--mode hybrid` 结合 metadata/tag/keyword evidence，并叠加 `type`、`site`、`strategy`、年份与关键词。召回后必须阅读 evidence sections、来源、图面可用性和“不可照搬”章节，输出 RAG_TRANSFER_CARD（证据—方法—适用条件—风险）。
- **验证状态**：当前案例数由 `build_index.py` 实时统计；本轮重建为 128 条案例与 1,881 个可检索 section。`build_semantic_index.py` 使用本机 Ollama `qwen3-embedding:0.6b` 建立 section embeddings；`search_cases.py --query` 默认 semantic fast mode，并提供 `--mode hybrid` 及可选 `--quality-mode` 本地 LLM evidence rerank。它仍是轻量本地文件检索，不是云服务或自动设计系统；测试结果以本次仓库验证记录为准。
- **人工动作**：metadata baseline 不需要额外安装；semantic/hybrid 与 quality rerank 需要本机 Ollama 及对应已安装模型。案例方法是否适用仍由 Concept/Scheme 结合项目条件判断；不要把当前轻量本地索引扩张成服务化平台。

## 5. 图片生成模型与 `render-fidelity`

- **位置/用途**：属于 Visualization 的 Gate D 后处理链；具体图像模型可由执行器当前可用的图片生成能力或经批准的外部服务提供。
- **接入方式**：输入必须是 Gate C 已检查的 Revit/Blender 基准图及模型版本；只有 Gate D 已确认相机才能生成。提示词和图像审查都执行 `render-fidelity`：可变材质、光影、天空、环境、植被、人物和氛围；禁止变体量、层数、门窗、入口、连廊、柱和关键空间，禁止增删已确认构件。
- **验证状态**：这是流程约束，不是某个已部署模型的验收。任何生成图仍须与平面、剖面、三维基准逐项核对；图像调用成功不代表真实性通过。
- **人工动作**：用户在 Gate D 选择机位；发现生成图违背不变项时，退回基础渲染重生成，不以修图掩盖错误。

## 6. 项目状态核对

- **位置**：[`tools/studio_state/`](../../../../tools/studio_state)。
- **用途**：只读核对 `project.yaml` 与 `DECISIONS.md`、`ARTIFACTS.csv` 及文件系统，发现面积、Gate、决策、blocker、产物字节数和 git HEAD 的不一致。
- **用法**：在项目根目录运行 `python "/path/to/architecture-design-workflow/tools/studio_state/check_state.py" --root "."`；支持 `--json`、`--strict`、`--verbose`、`--root`。
- **检查**：面积加总、Gate A/B 与决策记录、决策 ID、blocker 证据、next 字段、artifact 路径/字节数、日志索引行数、仓库 HEAD。
- **边界**：不改图、不设计、不自动通过 Gate；发现不一致只报告。
- **依赖**：PyYAML。

## 7. DSH 项目插件

- **位置**：[`plugins/wuchang-studio/`](../../../../plugins/wuchang-studio)；本地安装后在 DSH 中提供三个工具。
- **`wuchang_state`**：调用 `tools/studio_state/check_state.py`，返回面积、Gate、决策、blocker、artifact 与 git HEAD 的对账结果。
- **`wuchang_revit_read`**：通过本地 Revit MCP 只读查看当前视图和模型统计；不创建、不修改、不删除构件。
- **`wuchang_review`**：读取或追加 `REVIEW_MATRIX.csv` 的绘图包/功能包审查记录；只追加，不通过 Gate。
- **边界**：插件不自动设计、不替代用户 Gate、不写 Revit 模型；正式写入仍走 `mcp_call.py` 和 `send_code_to_revit`，先备份并回读。
